"""
BM25关键词搜索 - 产品级
与向量搜索结合的混合搜索
"""

import re
import math
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass

try:
    from ..base_layer import get_logger, get_settings
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)
    class SimpleSettings:
        pass
    def get_settings():
        return SimpleSettings()

logger = get_logger(__name__)


@dataclass
class BM25Result:
    """BM25搜索结果"""
    doc_id: int
    score: float
    text: str
    metadata: Dict


class BM25Index:
    """
    产品级BM25索引
    支持高效的关键词搜索
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.settings = get_settings()
        self.k1 = k1
        self.b = b
        
        # 索引数据
        self.documents: List[str] = []
        self.metadatas: List[Dict] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        
        # 倒排索引
        self.term_freqs: Dict[str, List[Tuple[int, int]]] = defaultdict(list)
        self.doc_freqs: Dict[str, int] = defaultdict(int)
        
        # 停用词
        self.stop_words = self._get_default_stop_words()
        
        # 同义词扩展
        self.synonyms = self._get_synonyms()
    
    def _get_synonyms(self) -> Dict[str, List[str]]:
        """获取同义词映射 - 扩展版，基于真实项目测试"""
        return {
            # 函数相关
            'function': ['method', 'func', 'procedure', 'routine', 'def'],
            'method': ['function', 'func', 'procedure'],
            'class': ['object', 'type', 'entity', 'cls'],
            
            # 测试相关
            'test': ['testing', 'unittest', 'pytest', 'spec', 'case', 'check'],
            'testing': ['test', 'tests', 'testcase', 'testing'],
            
            # 配置相关
            'config': ['configuration', 'settings', 'setup', 'cfg', 'env', 'option'],
            'configuration': ['config', 'settings', 'setup', 'options'],
            
            # 初始化
            'init': ['initialize', 'constructor', '__init__', 'setup', 'new'],
            'initialize': ['init', 'setup', 'constructor', 'create'],
            
            # 错误处理
            'error': ['exception', 'fail', 'fault', 'bug', 'issue', 'problem'],
            'exception': ['error', 'fail', 'fault', 'throw', 'raise'],
            
            # 日志
            'log': ['logging', 'logger', 'output', 'debug', 'print', 'trace'],
            'logging': ['log', 'logger', 'output', 'debug'],
            
            # API & Web
            'api': ['interface', 'endpoint', 'service', 'route', 'url', 'path'],
            'interface': ['api', 'contract', 'protocol'],
            'route': ['path', 'url', 'endpoint', 'api'],
            'request': ['req', 'http', 'query', 'get', 'post'],
            'response': ['res', 'result', 'reply', 'return'],
            
            # 数据库
            'db': ['database', 'data', 'storage', 'sql', 'table', 'query'],
            'database': ['db', 'data', 'storage', 'sql'],
            
            # 缓存
            'cache': ['caching', 'memory', 'buffer', 'redis', 'memcached'],
            'caching': ['cache', 'memory', 'buffer'],
            
            # 工具
            'util': ['utility', 'helper', 'tool', 'utils', 'helper'],
            'utility': ['util', 'helper', 'tool'],
            
            # 定义
            'def': ['define', 'definition', 'function', 'declare'],
            'define': ['definition', 'def', 'declare'],
            
            # 导入
            'import': ['include', 'require', 'use', 'from', 'load'],
            'include': ['import', 'require', 'load'],
            
            # 返回
            'return': ['returns', 'result', 'output', 'yield', 'send'],
            
            # 变量
            'variable': ['var', 'let', 'const', 'parameter', 'arg', 'argument'],
            'arg': ['argument', 'parameter', 'param', 'variable'],
            
            # 类型
            'string': ['str', 'text', 'char'],
            'number': ['int', 'integer', 'float', 'numeric', 'decimal'],
            'list': ['array', 'collection', 'items', 'sequence'],
            'dict': ['dictionary', 'map', 'object', 'hash', 'kv'],
            
            # 异步
            'async': ['await', 'promise', 'callback', 'future', 'task'],
            'await': ['async', 'wait', 'yield'],
            
            # 类定义
            'definition': ['def', 'define', 'implement', 'create', 'declare'],
            
            # 模块
            'module': ['mod', 'package', 'file', 'library', 'lib'],
            'package': ['module', 'library', 'lib'],
            
            # 异常
            'raise': ['throw', 'exception', 'error', 'trigger'],
            'throw': ['raise', 'exception', 'error'],
            
            # Flask/Web相关 - 基于真实测试
            'app': ['application', 'flask', 'server', 'webapp'],
            'application': ['app', 'flask', 'server'],
            'context': ['ctx', 'environment', 'state', 'scope'],
            'session': ['cookie', 'user', 'auth', 'token'],
            'template': ['render', 'view', 'html', 'jinja'],
            'render': ['template', 'view', 'generate', 'display'],
            'decorator': ['wrapper', '@', 'annotation'],
            'middleware': ['filter', 'hook', 'interceptor'],
            'client': ['browser', 'user', 'test'],
            'auth': ['authentication', 'login', 'security'],
            'authentication': ['auth', 'login', 'security', 'verify'],
        }

    def add_document(self, text: str, metadata: Optional[Dict] = None) -> int:
        """添加文档"""
        doc_id = len(self.documents)
        
        # 分词
        tokens = self._tokenize(text)
        doc_len = len(tokens)
        
        # 统计词频
        term_count = defaultdict(int)
        for token in tokens:
            term_count[token] += 1
        
        # 更新倒排索引
        for term, count in term_count.items():
            self.term_freqs[term].append((doc_id, count))
            self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1
        
        # 存储文档
        self.documents.append(text)
        self.metadatas.append(metadata or {})
        self.doc_lengths.append(doc_len)
        
        # 更新平均文档长度
        total_len = sum(self.doc_lengths)
        self.avg_doc_length = total_len / len(self.doc_lengths) if self.doc_lengths else 0
        
        return doc_id

    def add_documents(self, texts: List[str], 
                     metadatas: Optional[List[Dict]] = None) -> List[int]:
        """批量添加文档"""
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        doc_ids = []
        for text, metadata in zip(texts, metadatas):
            doc_id = self.add_document(text, metadata)
            doc_ids.append(doc_id)
        
        return doc_ids

    def search(self, query: str, k: int = 10) -> List[BM25Result]:
        """搜索"""
        if not self.documents:
            return []
        
        # 分词查询
        query_tokens = self._tokenize(query)
        
        # 查询扩展：添加同义词
        expanded_tokens = self._expand_query(query_tokens)
        
        # 计算得分
        doc_scores = defaultdict(float)
        N = len(self.documents)
        
        for token in expanded_tokens:
            if token not in self.term_freqs:
                continue
            
            # IDF计算
            df = self.doc_freqs[token]
            idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
            
            # 对每个文档计算得分
            for doc_id, freq in self.term_freqs[token]:
                doc_len = self.doc_lengths[doc_id]
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
                
                # 基础BM25得分
                base_score = idf * numerator / denominator
                
                # 添加位置权重（文档开头更重要）
                position_weight = self._calculate_position_weight(doc_id, token)
                
                # 添加关键词密度得分
                density_score = self._calculate_density_score(doc_id, expanded_tokens)
                
                # 综合得分
                doc_scores[doc_id] += base_score * (1 + position_weight + density_score)
        
        # 模糊匹配：如果没有匹配到，尝试模糊搜索
        if not doc_scores:
            doc_scores = self._fuzzy_search(query_tokens)
        else:
            # 添加模糊匹配的补充得分
            fuzzy_scores = self._fuzzy_search(query_tokens)
            for doc_id, fuzzy_score in fuzzy_scores.items():
                doc_scores[doc_id] += fuzzy_score * 0.2  # 模糊得分权重较低
        
        # 排序
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 返回结果
        results = []
        for doc_id, score in sorted_docs[:k]:
            results.append(BM25Result(
                doc_id=doc_id,
                score=score,
                text=self.documents[doc_id],
                metadata=self.metadatas[doc_id]
            ))
        
        return results
    
    def _calculate_position_weight(self, doc_id: int, token: str) -> float:
        """计算位置权重（文档开头的内容更重要）"""
        text = self.documents[doc_id].lower()
        token_lower = token.lower()
        
        try:
            # 找到token在文档中的位置
            pos = text.find(token_lower)
            if pos == -1:
                return 0.0
            
            # 计算相对位置（前20%最重要）
            relative_pos = pos / len(text)
            
            if relative_pos < 0.2:
                return 0.3  # 文档开头有更高权重
            elif relative_pos < 0.5:
                return 0.1  # 中间部分
            else:
                return 0.0  # 结尾部分不重要
        except:
            return 0.0
    
    def _calculate_density_score(self, doc_id: int, query_tokens: List[str]) -> float:
        """计算关键词密度得分"""
        text = self.documents[doc_id].lower()
        tokens_lower = [t.lower() for t in query_tokens]
        
        # 计算匹配的token数量
        matched = 0
        for token in tokens_lower:
            if token in text:
                matched += 1
        
        # 计算密度
        density = matched / len(tokens_lower) if tokens_lower else 0
        
        # 密度越高得分越高
        return density * 0.2
    
    def _expand_query(self, tokens: List[str]) -> List[str]:
        """查询扩展：添加同义词"""
        expanded = list(tokens)
        
        for token in tokens:
            if token in self.synonyms:
                expanded.extend(self.synonyms[token])
        
        return expanded
    
    def _fuzzy_search(self, query_tokens: List[str]) -> Dict[int, float]:
        """模糊搜索：处理拼写错误和变体"""
        fuzzy_scores = defaultdict(float)
        
        for token in query_tokens:
            for doc_id, text in enumerate(self.documents):
                text_lower = text.lower()
                
                # 精确匹配
                if token in text_lower:
                    fuzzy_scores[doc_id] += 0.5
                
                # 前缀匹配
                for word in text_lower.split():
                    if word.startswith(token) or token.startswith(word):
                        fuzzy_scores[doc_id] += 0.3
                
                # 子串匹配
                if any(token in word for word in text_lower.split()):
                    fuzzy_scores[doc_id] += 0.2
        
        return fuzzy_scores

    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        # 转小写
        text = text.lower()
        
        # 移除标点，提取单词
        tokens = re.findall(r'\b\w+\b', text)
        
        # 过滤停用词和短词
        tokens = [
            token for token in tokens 
            if token not in self.stop_words and len(token) > 1
        ]
        
        return tokens

    def _get_default_stop_words(self) -> set:
        """获取默认停用词"""
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'down', 'over', 'under', 'again',
            'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
            'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
            'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
            'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don',
            'should', 'now', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours',
            'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves',
            'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself',
            'it', 'its', 'itself', 'they', 'them', 'their', 'theirs',
            'themselves', 'what', 'which', 'who', 'whom', 'this', 'that',
            'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did',
            'doing', 'if', 'because', 'as', 'until', 'while', 'of', 'about',
            'against', 'between', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
            'did', 'doing', 'would', 'could', 'should', 'ought', 'i', 'me',
            'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your',
            'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
            'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they',
            'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who',
            'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was',
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
            'do', 'does', 'did', 'doing', 'if', 'because', 'as', 'until',
            'while', 'of', 'about', 'against', 'between', 'into', 'through',
            'during', 'before', 'after', 'above', 'below', 'is', 'are', 'was',
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
            'do', 'does', 'did', 'doing', 'would', 'could', 'should', 'ought',
            'def', 'class', 'import', 'from', 'return', 'if', 'else', 'for',
            'while', 'try', 'except', 'with', 'as', 'function', 'var', 'let',
            'const', 'public', 'private', 'protected', 'static', 'void'
        }

    def __len__(self) -> int:
        return len(self.documents)


class HybridSearch:
    """
    混合搜索
    结合BM25关键词搜索和向量搜索
    """

    def __init__(self, bm25_weight: float = 0.5, vector_weight: float = 0.5):
        self.bm25_index = BM25Index()
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.settings = get_settings()

    def add_documents(self, texts: List[str], 
                     metadatas: Optional[List[Dict]] = None):
        """添加文档到BM25索引"""
        self.bm25_index.add_documents(texts, metadatas)

    def search(self, query: str, vector_results: List, 
               k: int = 10) -> List:
        """
        混合搜索
        结合BM25和向量搜索结果
        """
        # BM25搜索
        bm25_results = self.bm25_index.search(query, k * 2)
        
        # 创建结果映射
        result_map = {}
        
        # 添加向量结果
        for i, vec_result in enumerate(vector_results):
            doc_id = getattr(vec_result, 'doc_id', i)
            result_map[doc_id] = {
                'result': vec_result,
                'vector_score': vec_result.score if hasattr(vec_result, 'score') else 1.0 / (i + 1)
            }
        
        # 添加BM25结果
        for bm25_result in bm25_results:
            if bm25_result.doc_id in result_map:
                result_map[bm25_result.doc_id]['bm25_score'] = bm25_result.score
            else:
                result_map[bm25_result.doc_id] = {
                    'result': bm25_result,
                    'bm25_score': bm25_result.score,
                    'vector_score': 0.0
                }
        
        # 计算混合得分
        final_results = []
        for doc_id, data in result_map.items():
            bm25_score = data.get('bm25_score', 0.0)
            vector_score = data.get('vector_score', 0.0)
            
            # 归一化
            max_bm25 = max(r.score for r in bm25_results) if bm25_results else 1.0
            max_vector = max(r.score if hasattr(r, 'score') else 1.0/(i+1) 
                            for i, r in enumerate(vector_results)) if vector_results else 1.0
            
            norm_bm25 = bm25_score / max_bm25 if max_bm25 > 0 else 0
            norm_vector = vector_score / max_vector if max_vector > 0 else 0
            
            # 混合得分
            hybrid_score = (self.bm25_weight * norm_bm25 + 
                          self.vector_weight * norm_vector)
            
            final_results.append({
                'result': data['result'],
                'hybrid_score': hybrid_score,
                'bm25_score': bm25_score,
                'vector_score': vector_score
            })
        
        # 排序
        final_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        # 返回前k个
        return [r['result'] for r in final_results[:k]]

    def clear(self):
        """清空索引"""
        self.bm25_index = BM25Index()


# 便捷函数
def create_bm25_index() -> BM25Index:
    """创建BM25索引"""
    return BM25Index()


def create_hybrid_search(bm25_weight: float = 0.5, 
                        vector_weight: float = 0.5) -> HybridSearch:
    """创建混合搜索"""
    return HybridSearch(bm25_weight, vector_weight)
