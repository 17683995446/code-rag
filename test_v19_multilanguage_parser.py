#!/usr/bin/env python3
"""
Code RAG v19.0 - 多语言解析器测试
验证Python + JavaScript解析
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v19.0 - 多语言解析测试")
print("="*80)

from code_rag.processing_layer.multilang_parser import (
    Language,
    ParserRegistry,
    parse_code,
    PythonParser,
    JavaScriptParser,
    CodeModule,
    CodeEntity
)


def test_python_parser():
    """测试Python解析器"""
    print("\n" + "="*60)
    print("测试 1: Python解析器")
    print("="*60)
    
    code = '''
"""
这是一个测试模块
"""

import os
import sys

class Calculator:
    """计算器类"""
    
    def __init__(self):
        self.result = 0
    
    def add(self, a: int, b: int) -> int:
        """加法方法"""
        return a + b
    
    def multiply(self, a: int, b: int) -> int:
        """乘法方法"""
        return a * b

def main():
    """主函数"""
    calc = Calculator()
    print(calc.add(1, 2))

if __name__ == "__main__":
    main()
    '''
    
    parser = PythonParser()
    module = parser.parse(code, "test.py")
    
    print(f"✅ 解析成功")
    print(f"  语言: {module.language}")
    print(f"  实体数: {len(module.entities)}")
    print(f"  导入数: {len(module.imports)}")
    
    print(f"\n  提取的实体:")
    for entity in module.entities:
        print(f"    - [{entity.entity_type}] {entity.name}")
        if entity.entity_type == "class" and entity.children:
            for child in entity.children:
                print(f"      ↳ [{child.entity_type}] {child.name}")
    
    return True


def test_javascript_parser():
    """测试JavaScript解析器"""
    print("\n" + "="*60)
    print("测试 2: JavaScript解析器")
    print("="*60)
    
    code = '''
/**
 * 计算器模块
 */

class Calculator {
    constructor() {
        this.result = 0;
    }
    
    add(a, b) {
        /**加法*/
        return a + b;
    }
    
    multiply(a, b) {
        return a * b;
    }
}

function main() {
    const calc = new Calculator();
    console.log(calc.add(1, 2));
}

const subtract = (a, b) => a - b;

main();
    '''
    
    parser = JavaScriptParser()
    module = parser.parse(code, "test.js")
    
    print(f"✅ 解析成功")
    print(f"  语言: {module.language}")
    print(f"  实体数: {len(module.entities)}")
    print(f"  导入数: {len(module.imports)}")
    
    print(f"\n  提取的实体:")
    for entity in module.entities:
        print(f"    - [{entity.entity_type}] {entity.name}")
    
    return True


def test_parser_registry():
    """测试解析器注册表"""
    print("\n" + "="*60)
    print("测试 3: 解析器注册表")
    print("="*60)
    
    # 通过语言获取
    py_parser = ParserRegistry.get_parser(Language.PYTHON)
    assert py_parser is not None
    print(f"  ✅ Python解析器获取成功")
    
    js_parser = ParserRegistry.get_parser(Language.JAVASCRIPT)
    assert js_parser is not None
    print(f"  ✅ JavaScript解析器获取成功")
    
    # 通过文件扩展名获取
    file_parser = ParserRegistry.get_parser_for_file("app.py")
    assert file_parser is not None
    assert file_parser.language == Language.PYTHON
    print(f"  ✅ 文件扩展名解析: app.py")
    
    js_file_parser = ParserRegistry.get_parser_for_file("main.js")
    assert js_file_parser is not None
    print(f"  ✅ 文件扩展名解析: main.js")
    
    return True


def test_parse_code_unified():
    """测试统一解析接口"""
    print("\n" + "="*60)
    print("测试 4: 统一解析接口")
    print("="*60)
    
    # Python
    py_code = "def hello(): print('hello')"
    py_module = parse_code(py_code, Language.PYTHON, "test.py")
    assert py_module is not None
    assert len(py_module.entities) > 0
    print(f"  ✅ Python统一解析成功")
    
    # JavaScript
    js_code = "function hello() { console.log('hello'); }"
    js_module = parse_code(js_code, Language.JAVASCRIPT, "test.js")
    assert js_module is not None
    print(f"  ✅ JavaScript统一解析成功")
    
    # 自动检测
    auto_module = parse_code(py_code, file_path="test.py")
    assert auto_module is not None
    print(f"  ✅ 自动语言检测成功")
    
    return True


def test_cross_language_operations():
    """测试跨语言功能"""
    print("\n" + "="*60)
    print("测试 5: 跨语言操作")
    print("="*60)
    
    py_module = parse_code("class Test: pass", Language.PYTHON)
    js_module = parse_code("class Test {}", Language.JAVASCRIPT)
    
    print(f"  ✅ 解析两种语言")
    print(f"    Python实体数: {len(py_module.entities)}")
    print(f"    JavaScript实体数: {len(js_module.entities)}")
    
    # 统计所有实体
    all_entities = py_module.entities + js_module.entities
    print(f"  ✅ 跨语言实体合并: {len(all_entities)}个实体")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("Python解析器", test_python_parser),
        ("JavaScript解析器", test_javascript_parser),
        ("解析器注册表", test_parser_registry),
        ("统一解析接口", test_parse_code_unified),
        ("跨语言操作", test_cross_language_operations),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n[{passed+1+failed}/{len(tests)}] 执行: {name}")
            if test_func():
                passed += 1
                print(f"\n✅ {name} - 通过")
            else:
                failed += 1
                print(f"\n❌ {name} - 失败")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} - 异常: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("📋 多语言解析测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有多语言解析测试通过！")
        return True
    else:
        print(f"\n⚠️ {failed}个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
