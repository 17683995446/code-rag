#!/usr/bin/env python3
"""
Code RAG v12.0 - 语义搜索增强测试
测试新添加的语义搜索功能
"""

import sys
from pathlib import Path

# Add project path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from code_rag.search_layer.semantic_search_enhancement import (
    SemanticSearchEnhancer,
    CodePatternMatcher,
    RelevanceRankingEngine,
    QueryType,
    enhance_search
)


def print_header(title):
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def test_query_analysis():
    """测试查询分析功能"""
    print_header("🔍 测试 1: 查询类型分析")
    
    enhancer = SemanticSearchEnhancer()
    
    test_queries = [
        {
            "query": "how to create a user in Python",
            "expected": "自然语言查询",
            "language": "python"
        },
        {
            "query": "similar code to user authentication",
            "expected": "相似度查询",
            "language": None
        },
        {
            "query": "def function that queries database",
            "expected": "代码模式查询",
            "language": "python"
        },
        {
            "query": "user authentication implementation",
            "expected": "关键词/语义查询",
            "language": None
        },
        {
            "query": "implement REST API in JavaScript",
            "expected": "自然语言查询",
            "language": "javascript"
        }
    ]
    
    for test in test_queries:
        result = enhancer.analyze_query(test['query'])
        print(f"\n  查询: '{test['query']}'")
        print(f"    类型: {result.query_type.value}")
        print(f"    意图: {result.intent or '无'}")
        print(f"    语言: {result.language or '未检测'}")
        print(f"    扩展查询: {result.expanded_queries[:3]}")


def test_query_expansion():
    """测试查询扩展功能"""
    print_header("🔄 测试 2: 查询扩展")
    
    enhancer = SemanticSearchEnhancer()
    
    queries = [
        "how to validate user input",
        "create database connection",
        "implement caching mechanism"
    ]
    
    for query in queries:
        print(f"\n  原始查询: '{query}'")
        expanded = enhancer.generate_search_queries(query, num_variants=5)
        print(f"  扩展查询 ({len(expanded)} 个):")
        for i, q in enumerate(expanded, 1):
            print(f"    {i}. {q}")


def test_code_pattern_matching():
    """测试代码模式匹配"""
    print_header("🎨 测试 3: 代码模式匹配")
    
    matcher = CodePatternMatcher()
    
    code = """
import os
from typing import List, Dict
import asyncio

class DataProcessor:
    def __init__(self, config: Dict):
        self.config = config
        self.cache = {}
    
    @property
    def name(self) -> str:
        return self.config.get('name', 'processor')
    
    async def process_data(self, data: List) -> Dict:
        results = []
        for item in data:
            processed = await self.transform(item)
            results.append(processed)
        return {'items': results, 'count': len(results)}
    
    async def transform(self, item):
        return item.upper() if isinstance(item, str) else item

def create_processor(config_path: str) -> DataProcessor:
    import json
    with open(config_path) as f:
        config = json.load(f)
    return DataProcessor(config)
    """
    
    print(f"\n  正在分析代码...")
    patterns = matcher.find_all_patterns(code, language='python')
    
    for pattern_name, matches in patterns.items():
        print(f"\n  模式 '{pattern_name}': {len(matches)} 个匹配")
        for i, match in enumerate(matches[:3], 1):
            preview = match['match'][:60].replace('\n', ' ')
            print(f"    {i}. 行{match['line_start']}: {preview}...")


def test_relevance_ranking():
    """测试相关性排序"""
    print_header("📊 测试 4: 相关性排序")
    
    ranker = RelevanceRankingEngine()
    
    query = "user authentication login"
    search_query = SemanticSearchEnhancer().analyze_query(query)
    
    candidates = [
        {
            'text': 'def authenticate_user(username, password): return check_credentials(username, password)',
            'bm25_score': 0.8,
            'semantic_score': 0.7,
            'metadata': {'language': 'python', 'category': 'auth'}
        },
        {
            'text': 'class User: def login(self): self.session = create_session()',
            'bm25_score': 0.6,
            'semantic_score': 0.8,
            'metadata': {'language': 'python', 'category': 'user'}
        },
        {
            'text': 'SELECT * FROM users WHERE username = ?',
            'bm25_score': 0.3,
            'semantic_score': 0.4,
            'metadata': {'language': 'sql', 'category': 'database'}
        },
        {
            'text': 'console.log("Hello World")',
            'bm25_score': 0.1,
            'semantic_score': 0.2,
            'metadata': {'language': 'javascript', 'category': 'utils'}
        }
    ]
    
    ranked = ranker.rerank_results(candidates, search_query)
    
    print(f"\n  原始查询: '{query}'")
    print(f"\n  排序结果:")
    for i, result in enumerate(ranked, 1):
        print(f"\n  {i}. 相关性分数: {result['relevance_score']:.3f}")
        print(f"     文本: {result['text'][:60]}...")
        print(f"     BM25: {result.get('bm25_score', 0):.2f}, 语义: {result.get('semantic_score', 0):.2f}")
        print(f"     语言: {result['metadata']['language']}, 类别: {result['metadata']['category']}")


def test_enhance_search():
    """测试便捷搜索增强函数"""
    print_header("🚀 测试 5: 便捷搜索增强")
    
    queries = [
        "how to implement caching in Python",
        "find similar code for rate limiting",
        "REST API error handling best practices"
    ]
    
    for query in queries:
        print(f"\n  查询: '{query}'")
        result = enhance_search(query)
        print(f"    类型: {result['type']}")
        print(f"    意图: {result['intent'] or '无'}")
        print(f"    语言: {result['language'] or '未检测'}")
        print(f"    扩展查询:")
        for q in result['all_queries'][:3]:
            print(f"      - {q}")


def test_multilingual_detection():
    """测试多语言检测"""
    print_header("🌐 测试 6: 多语言检测")
    
    enhancer = SemanticSearchEnhancer()
    
    queries = [
        "implement decorator in Python Flask",
        "use async await in JavaScript/TypeScript",
        "Spring Boot REST controller Java",
        "Rust ownership and borrowing",
        "Go goroutine and channel",
        "React component lifecycle"
    ]
    
    print(f"\n  多语言检测结果:")
    for query in queries:
        result = enhancer.analyze_query(query)
        detected = result.language or '未检测'
        print(f"    '{query[:50]}...' → {detected}")


def main():
    print_header("🧪 Code RAG v12.0 - 语义搜索增强测试")
    
    try:
        test_query_analysis()
        test_query_expansion()
        test_code_pattern_matching()
        test_relevance_ranking()
        test_enhance_search()
        test_multilingual_detection()
        
        print_header("📋 测试总结")
        print("\n  ✅ 所有测试完成!")
        print("\n  新增功能:")
        print("    1. 查询类型分析 - 自动识别查询类型")
        print("    2. 查询扩展 - 生成多个搜索变体")
        print("    3. 代码模式匹配 - 识别代码结构模式")
        print("    4. 相关性排序 - 多维度智能排序")
        print("    5. 多语言检测 - 自动识别编程语言")
        print("    6. 意图识别 - 理解用户搜索意图")
        
        print("\n  核心优势:")
        print("    • 自然语言理解 - 支持 NL2Code 搜索")
        print("    • 语义扩展 - 自动扩展同义词和相关概念")
        print("    • 模式识别 - 识别代码结构模式")
        print("    • 智能排序 - 多维度相关性评分")
        print("    • 语言适配 - 自动检测并优化语言特定查询")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
