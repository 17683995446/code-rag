"""
自然语言到代码转换器 (NL2Code)
将自然语言查询转换为代码搜索查询
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class IntentCategory(Enum):
    """意图类别"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    AUTHENTICATE = "authenticate"
    VALIDATE = "validate"
    TRANSFORM = "transform"
    HANDLE_ERROR = "handle_error"
    CONFIGURE = "configure"
    TEST = "test"
    OPTIMIZE = "optimize"
    LOG = "log"
    CACHE = "cache"
    PARALLEL = "parallel"


@dataclass
class NL2CodeResult:
    """NL2Code转换结果"""
    original_query: str
    intent: IntentCategory
    code_keywords: List[str]
    code_patterns: List[str]
    search_queries: List[str]
    confidence: float
    reasoning: str


class NL2CodeConverter:
    """
    自然语言到代码转换器
    将用户的自然语言查询转换为代码相关的搜索查询
    """

    # 意图映射规则
    INTENT_PATTERNS = {
        IntentCategory.SEARCH: {
            'keywords': ['search', 'find', 'lookup', 'query', 'filter'],
            'actions': ['search_{}', 'find_{}', 'query_{}'],
            'context': ['lookup', 'find', 'retrieve']
        },
        IntentCategory.CREATE: {
            'keywords': ['create', 'add', 'new', 'make', 'generate', 'produce', 'register'],
            'actions': ['add_user', 'create_record', 'new_instance', 'make_object'],
            'context': ['initialize', 'setup', 'instantiate']
        },
        IntentCategory.READ: {
            'keywords': ['get', 'fetch', 'retrieve', 'load', 'read', 'find', 'search', 'query'],
            'actions': ['get_user', 'fetch_data', 'retrieve_record', 'load_file'],
            'context': ['select', 'filter', 'where', 'from']
        },
        IntentCategory.UPDATE: {
            'keywords': ['update', 'modify', 'edit', 'change', 'set', 'replace', 'alter'],
            'actions': ['update_user', 'modify_record', 'edit_data', 'change_config'],
            'context': ['patch', 'put', 'merge', 'overwrite']
        },
        IntentCategory.DELETE: {
            'keywords': ['delete', 'remove', 'drop', 'erase', 'clear', 'destroy', 'unregister'],
            'actions': ['delete_user', 'remove_record', 'drop_table', 'clear_cache'],
            'context': ['destroy', 'cleanup', 'purge']
        },
        IntentCategory.AUTHENTICATE: {
            'keywords': ['login', 'authenticate', 'authorize', 'sign_in', 'verify', 'validate_token'],
            'actions': ['authenticate_user', 'login_user', 'verify_token', 'check_permission'],
            'context': ['jwt', 'oauth', 'session', 'credential']
        },
        IntentCategory.VALIDATE: {
            'keywords': ['validate', 'check', 'verify', 'ensure', 'test', 'assert', 'confirm'],
            'actions': ['validate_input', 'check_data', 'verify_format', 'ensure_constraints'],
            'context': ['schema', 'rule', 'constraint', 'guard']
        },
        IntentCategory.TRANSFORM: {
            'keywords': ['transform', 'convert', 'parse', 'format', 'encode', 'decode', 'serialize'],
            'actions': ['transform_data', 'convert_format', 'parse_json', 'serialize_object'],
            'context': ['map', 'filter', 'reduce', 'pipeline']
        },
        IntentCategory.HANDLE_ERROR: {
            'keywords': ['handle', 'error', 'exception', 'try', 'catch', 'fallback', 'retry'],
            'actions': ['handle_error', 'catch_exception', 'retry_request', 'fallback_method'],
            'context': ['try_except', 'error_boundary', 'graceful_degradation']
        },
        IntentCategory.CONFIGURE: {
            'keywords': ['config', 'setup', 'configure', 'settings', 'options', 'initialize'],
            'actions': ['configure_app', 'setup_database', 'init_config', 'load_settings'],
            'context': ['environment', 'env', 'parameter', 'option']
        },
        IntentCategory.TEST: {
            'keywords': ['test', 'mock', 'simulate', 'stub', 'fixture', 'assert'],
            'actions': ['test_function', 'mock_api', 'create_fixture', 'assert_result'],
            'context': ['pytest', 'unittest', 'case', 'suite']
        },
        IntentCategory.OPTIMIZE: {
            'keywords': ['optimize', 'performance', 'fast', 'efficient', 'improve', 'speed'],
            'actions': ['optimize_query', 'cache_result', 'batch_process', 'lazy_load'],
            'context': ['index', 'cache', 'pool', 'lazy']
        },
        IntentCategory.LOG: {
            'keywords': ['log', 'debug', 'trace', 'monitor', 'metric', 'report'],
            'actions': ['log_message', 'debug_info', 'track_metric', 'report_error'],
            'context': ['logger', 'console', 'syslog', 'prometheus']
        },
        IntentCategory.CACHE: {
            'keywords': ['cache', 'memoize', 'store', 'remember', 'memorize'],
            'actions': ['cache_data', 'memoize_function', 'store_result', 'invalidate_cache'],
            'context': ['redis', 'memcached', 'ttl', 'evict']
        },
        IntentCategory.PARALLEL: {
            'keywords': ['async', 'parallel', 'concurrent', 'thread', 'process', 'await'],
            'actions': ['run_async', 'process_parallel', 'execute_concurrent', 'await_result'],
            'context': ['threading', 'multiprocessing', 'asyncio', 'concurrent']
        }
    }

    # 领域关键词映射
    DOMAIN_KEYWORDS = {
        'database': ['database', 'db', 'sql', 'query', 'table', 'row', 'column', 'mongodb'],
        'web': ['http', 'request', 'response', 'api', 'endpoint', 'route', 'url'],
        'file': ['file', 'directory', 'path', 'read', 'write', 'folder'],
        'user': ['user', 'account', 'profile', 'permission', 'role'],
        'auth': ['auth', 'login', 'password', 'token', 'session', 'jwt', 'oauth'],
        'api': ['api', 'rest', 'graphql', 'endpoint', 'http', 'json'],
        'test': ['test', 'mock', 'fixture', 'assert', 'pytest', 'unittest'],
        'config': ['config', 'settings', 'env', 'environment', 'variable']
    }

    def __init__(self):
        self.conversion_cache: Dict[str, NL2CodeResult] = {}

    def convert(self, query: str) -> NL2CodeResult:
        """
        将自然语言查询转换为代码搜索查询
        
        Args:
            query: 自然语言查询
            
        Returns:
            NL2Code转换结果
        """
        if query in self.conversion_cache:
            return self.conversion_cache[query]
        
        query_lower = query.lower()
        
        intent = self._detect_intent(query_lower)
        
        code_keywords = self._extract_code_keywords(query_lower)
        
        code_patterns = self._generate_code_patterns(intent, code_keywords)
        
        search_queries = self._generate_search_queries(query, intent, code_keywords)
        
        confidence = self._calculate_confidence(intent, code_keywords)
        
        reasoning = self._generate_reasoning(intent, code_keywords)
        
        result = NL2CodeResult(
            original_query=query,
            intent=intent,
            code_keywords=code_keywords,
            code_patterns=code_patterns,
            search_queries=search_queries,
            confidence=confidence,
            reasoning=reasoning
        )
        
        self.conversion_cache[query] = result
        
        return result

    def _detect_intent(self, query: str) -> IntentCategory:
        """检测查询意图"""
        scores = {}
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            score = 0
            
            for keyword in patterns['keywords']:
                if keyword in query:
                    score += 2
            
            for action in patterns['actions']:
                if action in query:
                    score += 3
            
            for context in patterns['context']:
                if context in query:
                    score += 1
            
            if score > 0:
                scores[intent] = score
        
        if not scores:
            return IntentCategory.SEARCH
        
        return max(scores.items(), key=lambda x: x[1])[0]

    def _extract_code_keywords(self, query: str) -> List[str]:
        """提取代码相关关键词"""
        keywords = []
        
        for domain, domain_words in self.DOMAIN_KEYWORDS.items():
            for word in domain_words:
                if word in query:
                    keywords.append(word)
        
        action_words = ['function', 'method', 'class', 'module', 'import', 'def', 'return', 'async']
        for word in action_words:
            if word in query:
                keywords.append(word)
        
        common_words = ['user', 'data', 'file', 'api', 'request', 'response', 'error', 'config']
        for word in common_words:
            if word in query:
                keywords.append(word)
        
        return list(set(keywords))

    def _generate_code_patterns(self, intent: IntentCategory, keywords: List[str]) -> List[str]:
        """生成代码搜索模式"""
        patterns = []
        
        intent_patterns = {
            IntentCategory.CREATE: ['def create_{}(', 'def add_{}(', 'def new_{}('],
            IntentCategory.READ: ['def get_{}(', 'def fetch_{}(', 'def retrieve_{}('],
            IntentCategory.UPDATE: ['def update_{}(', 'def modify_{}(', 'def edit_{}('],
            IntentCategory.DELETE: ['def delete_{}(', 'def remove_{}(', 'def drop_{}('],
            IntentCategory.AUTHENTICATE: ['def authenticate(', 'def login(', 'def verify_token('],
            IntentCategory.VALIDATE: ['def validate(', 'def check_{}(', 'def verify('],
            IntentCategory.TRANSFORM: ['def transform(', 'def convert(', 'def parse('],
            IntentCategory.HANDLE_ERROR: ['try:', 'except:', 'def handle_error(', 'try_except'],
            IntentCategory.CONFIGURE: ['def config', 'def setup(', 'def initialize('],
            IntentCategory.TEST: ['def test_', 'def mock_', '@pytest.fixture'],
            IntentCategory.OPTIMIZE: ['def optimize(', '@cache', 'def lazy_'],
            IntentCategory.LOG: ['logger.', 'log.', 'logging.'],
            IntentCategory.CACHE: ['@cache', 'def memoize(', 'cache.set('],
            IntentCategory.PARALLEL: ['async def', 'await ', 'asyncio.']
        }
        
        if intent in intent_patterns:
            patterns.extend(intent_patterns[intent])
        
        # 为SEARCH意图添加模式
        if intent == IntentCategory.SEARCH:
            patterns.extend(['def search_{}(', 'def find_{}(', 'query ='])
        
        for keyword in keywords[:3]:
            patterns.append(f"def {keyword}_")
            patterns.append(f"class {keyword.capitalize()}")
        
        return patterns[:10]

    def _generate_search_queries(self, query: str, intent: IntentCategory, keywords: List[str]) -> List[str]:
        """生成搜索查询"""
        queries = []
        
        queries.append(query)
        
        intent_keywords = self.INTENT_PATTERNS[intent]['keywords']
        if intent_keywords:
            queries.append(f"{intent_keywords[0]} {''.join(keywords[:2])}")
        
        if keywords:
            for keyword in keywords[:3]:
                queries.append(f"{keyword} code")
                queries.append(f"example {keyword}")
        
        queries.append(f"{intent.value} implementation")
        
        queries.append(f"{intent.value} python example")
        
        return list(set(queries))[:5]

    def _calculate_confidence(self, intent: IntentCategory, keywords: List[str]) -> float:
        """计算转换置信度"""
        base_confidence = 0.5
        
        if len(keywords) > 0:
            base_confidence += 0.1 * min(len(keywords), 3)
        
        intent_patterns = self.INTENT_PATTERNS[intent]
        keyword_count = sum(1 for kw in intent_patterns['keywords'] 
                          if any(k in keywords for k in [kw]))
        base_confidence += 0.05 * keyword_count
        
        return min(base_confidence, 1.0)

    def _generate_reasoning(self, intent: IntentCategory, keywords: List[str]) -> str:
        """生成推理说明"""
        reasoning_parts = []
        
        reasoning_parts.append(f"识别为{intent.value}意图")
        
        if keywords:
            reasoning_parts.append(f"相关关键词: {', '.join(keywords[:3])}")
        
        intent_description = {
            IntentCategory.SEARCH: "搜索和查找数据",
            IntentCategory.CREATE: "创建一个新的资源或对象",
            IntentCategory.READ: "读取或获取数据",
            IntentCategory.UPDATE: "更新现有资源",
            IntentCategory.DELETE: "删除资源",
            IntentCategory.AUTHENTICATE: "用户认证和授权",
            IntentCategory.VALIDATE: "验证输入或数据",
            IntentCategory.TRANSFORM: "转换数据格式",
            IntentCategory.HANDLE_ERROR: "处理错误和异常",
            IntentCategory.CONFIGURE: "配置和初始化",
            IntentCategory.TEST: "编写测试代码",
            IntentCategory.OPTIMIZE: "优化性能",
            IntentCategory.LOG: "日志记录",
            IntentCategory.CACHE: "缓存数据",
            IntentCategory.PARALLEL: "并行或异步处理"
        }
        
        if intent in intent_description:
            reasoning_parts.append(intent_description[intent])
        
        return " | ".join(reasoning_parts)


class QueryExpansionEngine:
    """
    查询扩展引擎
    基于NL2Code结果扩展更多搜索查询
    """

    def __init__(self):
        self.converter = NL2CodeConverter()

    def expand(self, query: str, num_variants: int = 10) -> List[Dict]:
        """
        扩展查询，生成多个变体
        
        Args:
            query: 原始查询
            num_variants: 生成变体数量
            
        Returns:
            查询变体列表
        """
        nl2code_result = self.converter.convert(query)
        
        variants = []
        
        for search_query in nl2code_result.search_queries:
            variants.append({
                'query': search_query,
                'type': 'generated',
                'confidence': nl2code_result.confidence
            })
        
        for pattern in nl2code_result.code_patterns[:5]:
            variants.append({
                'query': pattern,
                'type': 'pattern',
                'confidence': 0.7
            })
        
        variants.extend(self._expand_by_synonyms(nl2code_result.code_keywords))
        
        variants.extend(self._expand_by_language(nl2code_result))
        
        variants.extend(self._expand_by_framework(nl2code_result))
        
        seen = set()
        unique_variants = []
        for variant in variants:
            if variant['query'] not in seen:
                seen.add(variant['query'])
                unique_variants.append(variant)
        
        return unique_variants[:num_variants]

    def _expand_by_synonyms(self, keywords: List[str]) -> List[Dict]:
        """通过同义词扩展"""
        synonyms = {
            'create': ['add', 'new', 'make', 'generate'],
            'get': ['fetch', 'retrieve', 'load', 'read'],
            'update': ['modify', 'edit', 'change', 'alter'],
            'delete': ['remove', 'drop', 'erase'],
            'user': ['account', 'profile', 'member'],
            'data': ['information', 'record', 'entity'],
        }
        
        variants = []
        for keyword in keywords:
            if keyword in synonyms:
                for syn in synonyms[keyword]:
                    variants.append({
                        'query': f"{syn} {keyword}",
                        'type': 'synonym',
                        'confidence': 0.6
                    })
        
        return variants

    def _expand_by_language(self, nl2code_result: NL2CodeResult) -> List[Dict]:
        """通过编程语言扩展"""
        languages = ['python', 'javascript', 'java', 'go', 'rust']
        
        variants = []
        for lang in languages:
            if nl2code_result.code_keywords:
                for keyword in nl2code_result.code_keywords[:2]:
                    variants.append({
                        'query': f"{keyword} {lang}",
                        'type': 'language',
                        'confidence': 0.5
                    })
        
        return variants

    def _expand_by_framework(self, nl2code_result: NL2CodeResult) -> List[Dict]:
        """通过框架扩展"""
        frameworks = {
            'python': ['django', 'flask', 'fastapi'],
            'javascript': ['react', 'vue', 'node'],
            'java': ['spring', 'springboot'],
        }
        
        variants = []
        for lang, frame_list in frameworks.items():
            for frame in frame_list:
                if nl2code_result.code_keywords:
                    variants.append({
                        'query': f"{nl2code_result.code_keywords[0]} {frame}",
                        'type': 'framework',
                        'confidence': 0.4
                    })
        
        return variants


def nl2code(query: str) -> Dict:
    """
    便捷函数：自然语言转代码搜索
    
    Args:
        query: 自然语言查询
        
    Returns:
        转换结果字典
    """
    converter = NL2CodeConverter()
    result = converter.convert(query)
    
    return {
        'original_query': result.original_query,
        'intent': result.intent.value,
        'code_keywords': result.code_keywords,
        'code_patterns': result.code_patterns,
        'search_queries': result.search_queries,
        'confidence': result.confidence,
        'reasoning': result.reasoning
    }


def expand_queries(query: str, num_variants: int = 10) -> List[Dict]:
    """
    便捷函数：扩展查询
    
    Args:
        query: 原始查询
        num_variants: 变体数量
        
    Returns:
        查询变体列表
    """
    engine = QueryExpansionEngine()
    return engine.expand(query, num_variants)
