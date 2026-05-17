"""
处理层模块（Processing Layer）
提供数据处理、转换、验证等功能
"""

from typing import Dict, Any, Optional, List, Union, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
import re
import hashlib

from src.core.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# 数据处理器接口
# ============================================================================

class DataProcessor(ABC):
    """数据处理器抽象接口"""

    @abstractmethod
    def process(self, data: Any) -> Any:
        """处理数据"""
        pass

    @abstractmethod
    def validate(self, data: Any) -> bool:
        """验证数据"""
        pass


class TextProcessor(DataProcessor):
    """文本处理器接口"""

    @abstractmethod
    def clean(self, text: str) -> str:
        """清理文本"""
        pass

    @abstractmethod
    def normalize(self, text: str) -> str:
        """标准化文本"""
        pass

    @abstractmethod
    def tokenize(self, text: str) -> List[str]:
        """分词"""
        pass


class VectorProcessor(DataProcessor):
    """向量处理器接口"""

    @abstractmethod
    def normalize_vector(self, vector: List[float]) -> List[float]:
        """归一化向量"""
        pass

    @abstractmethod
    def compute_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """计算距离"""
        pass


# ============================================================================
# 实现类
# ============================================================================

class BasicTextProcessor(TextProcessor):
    """基础文本处理器"""

    def __init__(self):
        self._stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                          "have", "has", "had", "do", "does", "did", "will", "would", "could",
                          "should", "may", "might", "must", "shall", "can", "need", "dare",
                          "ought", "used", "to", "of", "in", "for", "on", "with", "at",
                          "by", "from", "up", "about", "into", "over", "after", "and", "but",
                          "or", "as", "if", "when", "than", "because", "while", "although",
                          "though", "that", "which", "who", "whom", "this", "these", "those",
                          "what", "where", "why", "how", "all", "each", "every", "both",
                          "few", "more", "most", "other", "some", "such", "no", "nor", "not",
                          "only", "own", "same", "so", "than", "too", "very"}

    def process(self, data: Any) -> Any:
        if isinstance(data, str):
            return self.clean(data)
        return data

    def validate(self, data: Any) -> bool:
        return isinstance(data, str) and len(data.strip()) > 0

    def clean(self, text: str) -> str:
        """清理文本：去除多余空格、特殊字符"""
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\n.?!,;:()\-\[\]{}]', '', text)
        return text

    def normalize(self, text: str) -> str:
        """标准化文本：转小写、去除停用词"""
        text = text.lower()
        tokens = self.tokenize(text)
        tokens = [t for t in tokens if t not in self._stopwords]
        return ' '.join(tokens)

    def tokenize(self, text: str) -> List[str]:
        """分词：简单的空格分词"""
        text = re.sub(r'[^\w\s]', ' ', text)
        return [t for t in text.split() if t]


class AdvancedTextProcessor(BasicTextProcessor):
    """高级文本处理器"""

    def __init__(self):
        super().__init__()
        self._html_pattern = re.compile(r'<[^>]+>')
        self._url_pattern = re.compile(r'https?://\S+|www\.\S+')
        self._email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

    def clean(self, text: str) -> str:
        """高级清理：去除HTML、URL、邮箱等"""
        text = super().clean(text)
        text = self._html_pattern.sub('', text)
        text = self._url_pattern.sub('', text)
        text = self._email_pattern.sub('', text)
        return text

    def tokenize(self, text: str) -> List[str]:
        """高级分词：支持中英文"""
        text = self.clean(text)
        tokens = []
        
        # 中文分词（简单实现）
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                tokens.append(char)
        
        # 英文分词
        english_parts = re.findall(r'[a-zA-Z]+', text)
        tokens.extend(english_parts)
        
        # 数字
        numbers = re.findall(r'\d+', text)
        tokens.extend(numbers)
        
        return tokens


class EmbeddingProcessor(VectorProcessor):
    """嵌入向量处理器"""

    def process(self, data: Any) -> Any:
        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            return self.normalize_vector(data)
        return data

    def validate(self, data: Any) -> bool:
        return isinstance(data, list) and len(data) > 0 and all(isinstance(x, (int, float)) for x in data)

    def normalize_vector(self, vector: List[float]) -> List[float]:
        """L2归一化"""
        norm = sum(x ** 2 for x in vector) ** 0.5
        if norm == 0:
            return vector
        return [x / norm for x in vector]

    def compute_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦距离"""
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have the same length")
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(x ** 2 for x in vec1) ** 0.5
        norm2 = sum(x ** 2 for x in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 1.0
        
        similarity = dot_product / (norm1 * norm2)
        return 1 - similarity


# ============================================================================
# 数据转换器
# ============================================================================

class DataTransformer:
    """数据转换器"""

    def __init__(self):
        self._transformers: Dict[str, Callable] = {}

    def register(self, name: str, transformer: Callable):
        """注册转换器"""
        self._transformers[name] = transformer

    def transform(self, name: str, data: Any) -> Any:
        """应用转换器"""
        if name not in self._transformers:
            raise ValueError(f"Transformer '{name}' not found")
        return self._transformers[name](data)

    def apply_all(self, data: Any) -> Any:
        """应用所有转换器"""
        result = data
        for name, transformer in self._transformers.items():
            try:
                result = transformer(result)
            except Exception as e:
                logger.warning(f"Transformer {name} failed: {e}")
        return result


class DocumentTransformer(DataTransformer):
    """文档转换器"""

    def __init__(self):
        super().__init__()
        self.text_processor = AdvancedTextProcessor()
        self.register('clean', self.text_processor.clean)
        self.register('normalize', self.text_processor.normalize)
        self.register('strip_whitespace', lambda x: x.strip() if isinstance(x, str) else x)


# ============================================================================
# 数据验证器
# ============================================================================

class DataValidator:
    """数据验证器"""

    def __init__(self):
        self._validators: Dict[str, Callable[[Any], bool]] = {}

    def register(self, name: str, validator: Callable[[Any], bool]):
        """注册验证器"""
        self._validators[name] = validator

    def validate(self, name: str, data: Any) -> bool:
        """验证数据"""
        if name not in self._validators:
            raise ValueError(f"Validator '{name}' not found")
        return self._validators[name](data)

    def validate_all(self, validations: Dict[str, Any]) -> bool:
        """批量验证"""
        for name, data in validations.items():
            if not self.validate(name, data):
                return False
        return True


class DocumentValidator(DataValidator):
    """文档验证器"""

    def __init__(self):
        super().__init__()
        self.register('non_empty', lambda x: isinstance(x, str) and len(x.strip()) > 0)
        self.register('min_length', lambda x: isinstance(x, str) and len(x) >= 10)
        self.register('max_length', lambda x: isinstance(x, str) and len(x) <= 1000000)
        self.register('valid_id', lambda x: isinstance(x, str) and re.match(r'^[\w-]+$', x))


# ============================================================================
# 数据编码器/解码器
# ============================================================================

class DataEncoder(ABC):
    """数据编码器接口"""

    @abstractmethod
    def encode(self, data: Any) -> bytes:
        """编码数据"""
        pass

    @abstractmethod
    def decode(self, data: bytes) -> Any:
        """解码数据"""
        pass


class HashEncoder(DataEncoder):
    """哈希编码器"""

    def __init__(self, algorithm: str = 'sha256'):
        self._algorithm = algorithm

    def encode(self, data: Any) -> bytes:
        """生成哈希值"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif isinstance(data, bytes):
            pass
        else:
            data = str(data).encode('utf-8')
        
        h = hashlib.new(self._algorithm)
        h.update(data)
        return h.digest()

    def decode(self, data: bytes) -> Any:
        """哈希不可逆，返回十六进制表示"""
        return data.hex()


# ============================================================================
# 工厂函数
# ============================================================================

def get_text_processor() -> TextProcessor:
    """获取文本处理器"""
    return AdvancedTextProcessor()


def get_vector_processor() -> VectorProcessor:
    """获取向量处理器"""
    return EmbeddingProcessor()


def get_document_transformer() -> DocumentTransformer:
    """获取文档转换器"""
    return DocumentTransformer()


def get_document_validator() -> DocumentValidator:
    """获取文档验证器"""
    return DocumentValidator()


def get_hash_encoder() -> HashEncoder:
    """获取哈希编码器"""
    return HashEncoder()
