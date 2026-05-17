#!/usr/bin/env python3
"""
Code RAG v23.0 - AI 辅助代码库迁移器测试
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v23.0 - AI 辅助代码库迁移器测试")
print("="*80)

from code_rag.processing_layer.code_migrator import (
    create_code_migrator,
    CodeMigrator,
    LanguageMapper,
    SyntaxTransformer,
    DependencyMapper
)


def test_language_mapper():
    """测试语言映射器"""
    print("\n" + "="*70)
    print("测试 1: 语言映射器")
    print("="*70)
    
    mapper = LanguageMapper()
    
    py_to_js_mappings = mapper.get_mappings("python", "javascript")
    
    assert len(py_to_js_mappings) > 0
    print(f"  ✅ Python → JavaScript 映射: {len(py_to_js_mappings)} 条规则")
    
    js_to_py_mappings = mapper.get_mappings("javascript", "python")
    assert len(js_to_py_mappings) > 0
    print(f"  ✅ JavaScript → Python 映射: {len(js_to_py_mappings)} 条规则")
    
    return True


def test_syntax_transformer():
    """测试语法转换器"""
    print("\n" + "="*70)
    print("测试 2: 语法转换器")
    print("="*70)
    
    transformer = SyntaxTransformer()
    
    py_code = """
def hello(name):
    print("Hello, " + name)
    return True
"""
    
    js_code = transformer.transform(py_code, "python", "javascript")
    
    assert js_code is not None
    print(f"  ✅ Python → JavaScript 转换成功")
    print(f"     原代码: {len(py_code)} 行")
    print(f"     转换后: {len(js_code)} 行")
    
    return True


def test_dependency_mapper():
    """测试依赖映射器"""
    print("\n" + "="*70)
    print("测试 3: 依赖映射器")
    print("="*70)
    
    mapper = DependencyMapper()
    
    flask_to_express = mapper.map_dependency("flask", "python", "javascript")
    print(f"  ✅ flask → {flask_to_express}")
    
    requests_to_axios = mapper.map_dependency("requests", "python", "javascript")
    print(f"  ✅ requests → {requests_to_axios}")
    
    return True


def test_code_migrator_basic():
    """测试代码迁移器基础"""
    print("\n" + "="*70)
    print("测试 4: 代码迁移器基础")
    print("="*70)
    
    migrator = create_code_migrator()
    
    py_code = """
def add(a, b):
    return a + b

result = add(1, 2)
print(result)
"""
    
    result = migrator.migrate(py_code, "python", "javascript")
    
    assert result is not None
    assert result.target_code is not None
    assert len(result.target_code) > 0
    
    print(f"  ✅ 基础代码迁移成功")
    print(f"     迁移率: {result.migration_percentage:.1f}%")
    print(f"     应用规则: {len(result.rules_applied)} 条")
    
    return True


def test_python_to_javascript():
    """测试 Python 到 JavaScript 迁移"""
    print("\n" + "="*70)
    print("测试 5: Python → JavaScript 迁移")
    print("="*70)
    
    migrator = create_code_migrator()
    
    py_code = """
def calculate(x, y):
    if x > 0 and y > 0:
        return x + y
    else:
        return 0

print(calculate(5, 3))
"""
    
    result = migrator.migrate(py_code, "python", "javascript")
    
    print(f"  ✅ Python → JavaScript 迁移完成")
    print(f"     迁移率: {result.migration_percentage:.1f}%")
    print(f"     目标代码预览: {result.target_code[:100]}...")
    
    return True


def test_python_to_java():
    """测试 Python 到 Java 迁移"""
    print("\n" + "="*70)
    print("测试 6: Python → Java 迁移")
    print("="*70)
    
    migrator = create_code_migrator()
    
    py_code = """
def main():
    print("Hello World")
    return True
"""
    
    result = migrator.migrate(py_code, "python", "java")
    
    print(f"  ✅ Python → Java 迁移完成")
    print(f"     迁移率: {result.migration_percentage:.1f}%")
    
    return True


def test_project_migration():
    """测试项目迁移"""
    print("\n" + "="*70)
    print("测试 7: 项目迁移")
    print("="*70)
    
    migrator = create_code_migrator()
    
    files = {
        "app.py": "def main(): pass",
        "utils.py": "def helper(): pass",
        "models.py": "class User: pass"
    }
    
    results = migrator.migrate_project(files, "python", "javascript")
    
    assert len(results) == len(files)
    print(f"  ✅ 项目迁移成功")
    print(f"     迁移文件: {len(results)} 个")
    
    for file_path, result in results.items():
        print(f"     - {file_path}: {result.migration_percentage:.1f}%")
    
    return True


def test_migration_report():
    """测试迁移报告"""
    print("\n" + "="*70)
    print("测试 8: 迁移报告")
    print("="*70)
    
    migrator = create_code_migrator()
    
    migrator.migrate("def test(): pass", "python", "javascript")
    migrator.migrate("function test() {}", "javascript", "python")
    
    report = migrator.get_migration_report()
    
    assert report is not None
    assert "total_migrations" in report
    
    print(f"  ✅ 迁移报告生成成功")
    print(f"     总迁移次数: {report['total_migrations']}")
    print(f"     平均迁移率: {report['average_migration_percentage']:.1f}%")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("语言映射器", test_language_mapper),
        ("语法转换器", test_syntax_transformer),
        ("依赖映射器", test_dependency_mapper),
        ("代码迁移器基础", test_code_migrator_basic),
        ("Python → JavaScript 迁移", test_python_to_javascript),
        ("Python → Java 迁移", test_python_to_java),
        ("项目迁移", test_project_migration),
        ("迁移报告", test_migration_report),
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
    print("📋 AI 辅助代码库迁移器测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有 AI 辅助代码库迁移器测试通过！")
        return True
    else:
        print(f"\n⚠️ {failed}个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
