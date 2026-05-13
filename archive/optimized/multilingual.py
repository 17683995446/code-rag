import os
import re
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


@dataclass
class LanguageConfig:
    primary_language: str = "auto"
    fallback_to_english: bool = True
    chinese_tokenizer: str = "jieba"
    enable_mixed: bool = True


class ChineseTokenizer:
    def __init__(self):
        self.tokenizer = None
        self._load_tokenizer()

    def _load_tokenizer(self):
        try:
            import jieba
            jieba.initialize()
            self.tokenizer = jieba
        except ImportError:
            try:
                import pkuseg
                self.tokenizer = pkuseg.pkuseg()
            except ImportError:
                self.tokenizer = None

    def tokenize(self, text: str) -> List[str]:
        if self.tokenizer is None:
            return self._simple_tokenize(text)

        try:
            if hasattr(self.tokenizer, 'cut'):
                return list(self.tokenizer.cut(text))
            else:
                return self.tokenizer.cut(text)
        except Exception:
            return self._simple_tokenize(text)

    def _simple_tokenize(self, text: str) -> List[str]:
        tokens = []
        current = ""

        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                if current:
                    tokens.extend(current.split())
                    current = ""
                tokens.append(char)
            elif char.isspace():
                if current:
                    tokens.extend(current.split())
                    current = ""
            else:
                current += char

        if current:
            tokens.extend(current.split())

        return tokens


class LanguageDetector:
    def __init__(self):
        self.chinese_chars = 0
        self.total_chars = 0
        self.threshold = 0.3

    def detect(self, text: str) -> str:
        self.chinese_chars = 0
        self.total_chars = 0

        for char in text:
            if char.isalpha():
                self.total_chars += 1
                if '\u4e00' <= char <= '\u9fff':
                    self.chinese_chars += 1

        if self.total_chars == 0:
            return "english"

        chinese_ratio = self.chinese_chars / self.total_chars

        if chinese_ratio > self.threshold:
            return "chinese"

        code_patterns = [
            r'\bdef\s+\w+',
            r'\bclass\s+\w+',
            r'\bfunction\s+\w+',
            r'\bconst\s+\w+',
            r'\bimport\s+\w+',
            r'\{[\s\n]*\}',
            r'\(\s*\)',
        ]

        for pattern in code_patterns:
            if re.search(pattern, text):
                return "code"

        return "english"

    def detect_mixed(self, text: str) -> Dict[str, float]:
        chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        japanese_count = sum(1 for c in text if '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff')
        korean_count = sum(1 for c in text if '\uac00' <= c <= '\ud7af')

        total = max(len(text), 1)

        return {
            "chinese": chinese_count / total,
            "japanese": japanese_count / total,
            "korean": korean_count / total,
            "other": 1 - (chinese_count + japanese_count + korean_count) / total
        }


class MultilingualEmbeddingEngine:
    def __init__(
        self,
        config: LanguageConfig = None,
        cache_size: int = 10000
    ):
        self.config = config or LanguageConfig()
        self.cache_size = cache_size
        self.cache: Dict[str, List[float]] = {}
        self._cache_lock = threading.Lock()

        self.language_detector = LanguageDetector()
        self.chinese_tokenizer = ChineseTokenizer()

        self.model = None
        self._use_sentence_transformers = False
        self._lock = threading.Lock()

    def _load_model(self):
        if self.model is not None:
            return

        with self._lock:
            if self.model is not None:
                return

            try:
                from sentence_transformers import SentenceTransformer

                if self.config.enable_mixed:
                    model_name = "paraphrase-multilingual-MiniLM-L12-v2"
                else:
                    model_name = "all-MiniLM-L6-v2"

                self.model = SentenceTransformer(model_name, device="cpu")
                self._use_sentence_transformers = True

            except ImportError:
                self.model = self._create_fallback_embedder()
                self._use_sentence_transformers = False

    def _create_fallback_embedder(self):
        english_keywords = [
            'function', 'class', 'def', 'return', 'if', 'else', 'for', 'while',
            'import', 'export', 'const', 'let', 'var', 'async', 'await', 'try',
            'catch', 'throw', 'new', 'this', 'self', 'public', 'private',
            'static', 'void', 'int', 'string', 'bool', 'float', 'list', 'dict',
            'map', 'set', 'array', 'object', 'interface', 'type', 'enum',
        ]

        chinese_keywords = [
            '函数', '类', '定义', '返回', '如果', '否则', '循环', '导入',
            '导出', '常量', '变量', '异步', '等待', '尝试', '捕获', '抛出',
            '公开', '私有', '静态', '接口', '类型', '枚举', '对象', '数组',
        ]

        all_keywords = english_keywords + chinese_keywords

        return {
            'keywords': {w: i % 384 for i, w in enumerate(all_keywords)},
            'dimension': 384
        }

    def encode(
        self,
        texts: Union[str, List[str]],
        show_progress: bool = False,
        normalize: bool = True
    ) -> Union[List[float], List[List[float]]]:
        if isinstance(texts, str):
            texts = [texts]

        self._load_model()

        cached_results = []
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            with self._cache_lock:
                if cache_key in self.cache:
                    cached_results.append((i, self.cache[cache_key]))
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)

        results = [None] * len(texts)

        for idx, embedding in cached_results:
            results[idx] = embedding

        if uncached_texts:
            new_embeddings = self._encode_batch(uncached_texts, show_progress, normalize)

            for i, (idx, embedding) in enumerate(zip(uncached_indices, new_embeddings)):
                results[idx] = embedding

                with self._cache_lock:
                    if len(self.cache) < self.cache_size:
                        cache_key = self._get_cache_key(uncached_texts[i])
                        self.cache[cache_key] = embedding

        return results[0] if len(results) == 1 else results

    def _encode_batch(
        self,
        texts: List[str],
        show_progress: bool,
        normalize: bool
    ) -> List[List[float]]:
        if self._use_sentence_transformers:
            return self._encode_with_transformers(texts, show_progress, normalize)
        else:
            return self._encode_fallback(texts)

    def _encode_with_transformers(
        self,
        texts: List[str],
        show_progress: bool,
        normalize: bool
    ) -> List[List[float]]:
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=show_progress,
            normalize_embeddings=normalize,
            convert_to_numpy=True
        )

        return embeddings.tolist()

    def _encode_fallback(self, texts: List[str]) -> List[List[float]]:
        keywords = self.model['keywords']
        dim = self.model.get('dimension', 384)

        import numpy as np

        results = []
        for text in texts:
            vector = np.zeros(dim, dtype=np.float32)

            chinese_tokens = self.chinese_tokenizer.tokenize(text)
            for token in chinese_tokens:
                if token in keywords:
                    vector[keywords[token]] += 1

            words = text.lower().split()
            for word in words:
                if word in keywords:
                    vector[keywords[word]] += 0.5

                if len(word) > 3:
                    hash_val = int(hashlib.md5(word.encode()).hexdigest()[:4], 16)
                    vector[hash_val % dim] += 0.3

            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm

            results.append(vector.tolist())

        return results

    def _get_cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def encode_query(
        self,
        query: str,
        language_hint: str = None
    ) -> List[float]:
        detected_lang = language_hint or self.language_detector.detect(query)

        enhanced_query = query

        if detected_lang == "chinese":
            tokens = self.chinese_tokenizer.tokenize(query)
            significant_tokens = [t for t in tokens if len(t) > 1 and '\u4e00' <= t[0] <= '\u9fff']
            if significant_tokens:
                enhanced_query = query + " " + " ".join(significant_tokens)

        return self.encode(enhanced_query, show_progress=False)[0]


class CodeAwareEmbedder:
    def __init__(self, base_engine: MultilingualEmbeddingEngine = None):
        self.base_engine = base_engine or MultilingualEmbeddingEngine()

        self.code_patterns = {
            'function_def': r'(?:def|function|fn)\s+(\w+)',
            'class_def': r'class\s+(\w+)',
            'import': r'(?:import|from)\s+([\w.]+)',
            'variable': r'(?:const|let|var)\s+(\w+)',
            'decorator': r'@(\w+)',
        }

    def encode(self, code: str, is_code: bool = None) -> List[float]:
        if is_code is None:
            is_code = self._is_code(code)

        if is_code:
            return self._encode_code(code)
        else:
            return self.base_engine.encode(code)

    def _is_code(self, text: str) -> bool:
        code_indicators = [
            r'\bdef\s+\w+\s*\(',
            r'\bclass\s+\w+\s*[:{]',
            r'\bfunction\s+\w+\s*\(',
            r'=>\s*\{',
            r'\{\s*\}',
            r'\[\s*\]',
            r';\s*$',
        ]

        for pattern in code_indicators:
            if re.search(pattern, text):
                return True

        bracket_balance = text.count('{') + text.count('[') + text.count('(')
        bracket_balance -= text.count('}') + text.count(']') + text.count(')')

        if abs(bracket_balance) > 2:
            return True

        return False

    def _encode_code(self, code: str) -> List[float]:
        semantic_parts = []

        for pattern_name, pattern in self.code_patterns.items():
            matches = re.findall(pattern, code)
            for match in matches:
                if isinstance(match, tuple):
                    semantic_parts.extend(match)
                else:
                    semantic_parts.append(match)

        docstring_match = re.search(r'"""(.*?)"""', code, re.DOTALL)
        if not docstring_match:
            docstring_match = re.search(r"'''(.*?)'''", code, re.DOTALL)

        if docstring_match:
            docstring = docstring_match.group(1).strip()
            semantic_parts.append(docstring)

        semantic_text = " ".join(semantic_parts)

        comment_lines = re.findall(r'#\s*(.+)$', code, re.MULTILINE)
        comment_lines.extend(re.findall(r'//\s*(.+)$', code, re.MULTILINE))
        comments = " ".join(comment_lines)

        combined_text = f"{code[:500]} {semantic_text} {comments[:200]}"

        return self.base_engine.encode(combined_text, show_progress=False)


class EmbeddingEnsemble:
    def __init__(self, engines: List = None, weights: List[float] = None):
        self.engines = engines or []
        self.weights = weights or []

        if self.engines and not self.weights:
            self.weights = [1.0 / len(self.engines)] * len(self.engines)

    def add_engine(self, engine, weight: float = 1.0):
        self.engines.append(engine)
        self.weights.append(weight)

        total = sum(self.weights)
        self.weights = [w / total for w in self.weights]

    def encode(
        self,
        texts: Union[str, List[str]],
        show_progress: bool = False
    ) -> Union[List[float], List[List[float]]]:
        if not self.engines:
            return self._empty_encoding(texts)

        all_embeddings = []
        for engine in self.engines:
            try:
                embeddings = engine.encode(texts, show_progress=False)
                all_embeddings.append(embeddings)
            except Exception:
                pass

        if not all_embeddings:
            return self._empty_encoding(texts)

        if isinstance(texts, str):
            combined = [sum(w * e[i] for w, e in zip(self.weights, all_embeddings))
                       for i in range(len(all_embeddings[0]))]
            return combined
        else:
            results = []
            for j in range(len(texts)):
                combined = [sum(w * e[j][i] for w, e in zip(self.weights, all_embeddings))
                           for i in range(len(all_embeddings[0][0]))]
                results.append(combined)
            return results

    def _empty_encoding(self, texts):
        if isinstance(texts, str):
            return [0.0] * 384
        return [[0.0] * 384 for _ in texts]


class StreamingEncoder:
    def __init__(self, engine, batch_size: int = 100):
        self.engine = engine
        self.batch_size = batch_size

    def encode_streaming(
        self,
        texts: List[str],
        callback: callable = None,
        show_progress: bool = True
    ):
        total = len(texts)
        for i in range(0, total, self.batch_size):
            batch = texts[i:i + self.batch_size]

            embeddings = self.engine.encode(batch, show_progress=False)

            if callback:
                for j, embedding in enumerate(embeddings):
                    callback(i + j, embedding, total)

            yield from zip(range(i, min(i + self.batch_size, total)), embeddings)

    def encode_parallel(
        self,
        texts: List[str],
        max_workers: int = 4
    ) -> List[List[float]]:
        import numpy as np

        chunk_size = max(1, len(texts) // max_workers)
        chunks = [texts[i:i + chunk_size] for i in range(0, len(texts), chunk_size)]

        all_embeddings = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.engine.encode, chunk): i
                for i, chunk in enumerate(chunks)
            }

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    embeddings = future.result()
                    all_embeddings.append((idx, embeddings))
                except Exception:
                    pass

        all_embeddings.sort(key=lambda x: x[0])

        results = []
        for _, embeddings in all_embeddings:
            if isinstance(embeddings[0], list):
                results.extend(embeddings)
            else:
                results.append(embeddings)

        return results


class EmbeddingCache:
    def __init__(self, storage_path: str = "./data/embedding_cache", max_size: int = 100000):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size

        self.memory_cache: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, text: str) -> Optional[List[float]]:
        key = hashlib.md5(text.encode()).hexdigest()

        with self._lock:
            if key in self.memory_cache:
                self._hits += 1
                return self.memory_cache[key]

        disk_path = self.storage_path / f"{key}.npy"
        if disk_path.exists():
            try:
                import numpy as np
                embedding = np.load(str(disk_path)).tolist()
                with self._lock:
                    if len(self.memory_cache) < self.max_size:
                        self.memory_cache[key] = embedding
                self._hits += 1
                return embedding
            except Exception:
                pass

        self._misses += 1
        return None

    def put(self, text: str, embedding: List[float]):
        key = hashlib.md5(text.encode()).hexdigest()

        with self._lock:
            if len(self.memory_cache) >= self.max_size:
                oldest_key = next(iter(self.memory_cache))
                del self.memory_cache[oldest_key]

            self.memory_cache[key] = embedding

        try:
            import numpy as np
            disk_path = self.storage_path / f"{key}.npy"
            np.save(str(disk_path), np.array(embedding))
        except Exception:
            pass

    def clear(self):
        with self._lock:
            self.memory_cache.clear()

        for f in self.storage_path.glob("*.npy"):
            try:
                f.unlink()
            except Exception:
                pass

    def stats(self) -> Dict:
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0

            return {
                "memory_cache_size": len(self.memory_cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate
            }
