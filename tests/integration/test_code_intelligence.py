#!/usr/bin/env python3
"""
Code RAG v12.0 - 代码智能理解测试
测试新添加的代码智能分析功能
"""

import sys
from pathlib import Path

# Add project path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from code_rag.processing_layer.code_intelligence_and_semantic_understanding import (
    CodeIntelligenceAnalyzer,
    CodeSimilarityAnalyzer,
    analyze_code_intelligence
)


def print_header(title):
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def test_intent_recognition():
    """测试代码意图识别"""
    print_header("🎯 测试 1: 代码意图识别")
    
    test_cases = [
        {
            "name": "Flask路由",
            "code": """
@app.route('/users/<int:user_id>')
def get_user(user_id):
    user = User.query.get(user_id)
    return jsonify(user.to_dict())
            """,
            "expected_intent": "network_operation or user_interface"
        },
        {
            "name": "数据处理函数",
            "code": """
def transform_data(raw_data):
    parsed = json.loads(raw_data)
    filtered = [item for item in parsed if item['active']]
    return [transform(item) for item in filtered]
            """,
            "expected_intent": "data_processing"
        },
        {
            "name": "数据库操作",
            "code": """
def save_to_db(data):
    session = get_session()
    obj = Model(**data)
    session.add(obj)
    session.commit()
    return obj.id
            """,
            "expected_intent": "database_operation"
        },
        {
            "name": "认证授权",
            "code": """
def authenticate(token):
    payload = jwt.decode(token, SECRET_KEY)
    if not payload.get('verified'):
        raise AuthError()
    return User.query.get(payload['user_id'])
            """,
            "expected_intent": "security"
        }
    ]
    
    analyzer = CodeIntelligenceAnalyzer()
    
    for test in test_cases:
        print(f"\n  测试: {test['name']}")
        result = analyzer.analyze_intent(test['code'])
        print(f"    主要意图: {result.primary_intent.value}")
        print(f"    置信度: {result.confidence:.2f}")
        print(f"    次要意图: {[i.value for i in result.secondary_intents]}")
        print(f"    推理: {result.reasoning}")


def test_tag_generation():
    """测试标签生成"""
    print_header("🏷️ 测试 2: 代码标签生成")
    
    code = """
import os
from pathlib import Path
from typing import List

def analyze_files(directory: str) -> List[Path]:
    path = Path(directory)
    py_files = list(path.rglob('*.py'))
    
    results = []
    for file in py_files:
        if file.stat().st_size > 1000:
            results.append(file)
    
    return results
    """
    
    analyzer = CodeIntelligenceAnalyzer()
    tags = analyzer.generate_tags(code)
    
    print(f"\n  生成的标签 ({len(tags)} 个):")
    for tag in tags[:10]:
        print(f"    - {tag.name} [{tag.category}] (置信度: {tag.confidence:.2f})")


def test_language_detection():
    """测试编程语言检测"""
    print_header("🔍 测试 3: 编程语言检测")
    
    code_samples = {
        'Python': """
def hello_world():
    print("Hello, World!")
    return True
        """,
        'JavaScript': """
function helloWorld() {
    console.log("Hello, World!");
    return true;
}
        """,
        'Java': """
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
        """
    }
    
    analyzer = CodeIntelligenceAnalyzer()
    
    for lang, code in code_samples.items():
        detected = analyzer.detect_language(code)
        status = "✅" if detected.lower() in lang.lower() else "❌"
        print(f"  {status} {lang}: 检测为 '{detected}'")


def test_code_structure_extraction():
    """测试代码结构提取"""
    print_header("📊 测试 4: 代码结构提取")
    
    code = """
from flask import Flask, jsonify
from sqlalchemy import create_engine
import logging

class API:
    def __init__(self, config):
        self.app = Flask(__name__)
        self.engine = create_engine(config['db_url'])
    
    def setup_routes(self):
        @self.app.route('/api/data')
        def get_data():
            return jsonify({'status': 'ok'})
    
    def run(self):
        self.app.run()

def create_app(config_path):
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return API(config)
    """
    
    analyzer = CodeIntelligenceAnalyzer()
    structure = analyzer.extract_code_structure(code)
    
    print(f"\n  代码结构:")
    print(f"    函数: {structure['functions']}")
    print(f"    类: {structure['classes']}")
    print(f"    导入: {structure['imports']}")
    print(f"    复杂度: {structure['complexity']}")
    print(f"    代码行数: {structure['lines_of_code']}")


def test_similarity_analysis():
    """测试代码相似度分析"""
    print_header("🔗 测试 5: 代码相似度分析")
    
    code1 = """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
    """
    
    code2 = """
def calculate_product(items):
    result = 1
    for item in items:
        result *= item
    return result
    """
    
    code3 = """
def parse_data(data):
    parsed = []
    for item in data:
        parsed.append(process(item))
    return parsed
    """
    
    analyzer = CodeSimilarityAnalyzer()
    
    print(f"\n  相似度分析:")
    similarity_1_2 = analyzer.calculate_overall_similarity(code1, code2)
    print(f"\n  代码1 vs 代码2 (循环累加 vs 累乘):")
    print(f"    结构相似度: {similarity_1_2['structural']:.2f}")
    print(f"    语义相似度: {similarity_1_2['semantic']:.2f}")
    print(f"    词汇相似度: {similarity_1_2['lexical']:.2f}")
    print(f"    综合相似度: {similarity_1_2['overall']:.2f}")
    
    similarity_1_3 = analyzer.calculate_overall_similarity(code1, code3)
    print(f"\n  代码1 vs 代码3 (累加 vs 数据处理):")
    print(f"    综合相似度: {similarity_1_3['overall']:.2f}")


def test_comprehensive_analysis():
    """测试综合分析"""
    print_header("🚀 测试 6: 综合分析")
    
    code = """
import asyncio
from typing import List, Dict
import json

async def fetch_and_process(urls: List[str]) -> Dict:
    async def fetch(url):
        async with aiohttp.ClientSession() as session:
            response = await session.get(url)
            return await response.json()
    
    results = await asyncio.gather(*[fetch(url) for url in urls])
    
    processed = []
    for data in results:
        if data.get('valid'):
            processed.append({
                'id': data['id'],
                'value': transform(data['value'])
            })
    
    return {'items': processed, 'count': len(processed)}
    """
    
    print(f"\n  综合分析结果:")
    result = analyze_code_intelligence(code)
    
    print(f"  检测语言: {result['detected_language']}")
    print(f"\n  意图分析:")
    print(f"    主要意图: {result['intent']['primary']}")
    print(f"    置信度: {result['intent']['confidence']:.2f}")
    print(f"    推理: {result['intent']['reasoning']}")
    
    print(f"\n  结构信息:")
    print(f"    函数: {result['structure']['functions']}")
    print(f"    类: {result['structure']['classes']}")
    print(f"    复杂度: {result['structure']['complexity']}")
    
    print(f"\n  摘要:")
    print(f"    {result['summary']['short']}")
    print(f"    {result['summary']['long']}")
    
    print(f"\n  标签 (前10个):")
    for tag in result['tags'][:10]:
        print(f"    - {tag['name']}")


def main():
    print_header("🧪 Code RAG v12.0 - 代码智能理解测试")
    
    try:
        test_intent_recognition()
        test_tag_generation()
        test_language_detection()
        test_code_structure_extraction()
        test_similarity_analysis()
        test_comprehensive_analysis()
        
        print_header("📋 测试总结")
        print("\n  ✅ 所有测试完成!")
        print("\n  新增功能:")
        print("    1. 代码意图识别 - 识别代码的主要目的")
        print("    2. 自动标签生成 - 为代码打上相关标签")
        print("    3. 多语言检测 - 自动识别编程语言")
        print("    4. 结构提取 - 提取函数、类、依赖等信息")
        print("    5. 相似度分析 - 计算代码间的相似度")
        print("    6. 综合分析 - 一站式代码智能理解")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
