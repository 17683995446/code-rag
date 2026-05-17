#!/usr/bin/env python3
"""
Code RAG v23.0 - 自然语言架构设计器测试
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v23.0 - 自然语言架构设计器测试")
print("="*80)

from code_rag.service_layer.architecture_designer import (
    create_architecture_designer,
    ArchitectureDesigner,
    NLParser,
    CodeStructureGenerator,
    DependencyAnalyzer
)


def test_nl_parser():
    """测试自然语言解析器"""
    print("\n" + "="*70)
    print("测试 1: 自然语言解析器")
    print("="*70)
    
    parser = NLParser()
    
    description = "I need a user service with authentication and a database to store user information"
    
    result = parser.parse(description)
    
    assert result is not None
    assert "components" in result
    assert "keywords" in result
    
    print(f"  ✅ 解析完成")
    print(f"     - 检测到组件: {len(result['components'])} 个")
    print(f"     - 关键词数: {len(result['keywords'])}")
    print(f"     - 复杂度: {result['complexity']}")
    
    return True


def test_code_structure_generator():
    """测试代码结构生成器"""
    print("\n" + "="*70)
    print("测试 2: 代码结构生成器")
    print("="*70)
    
    generator = CodeStructureGenerator()
    
    code = generator.generate_component("service", "User", "python")
    
    assert code is not None
    assert len(code) > 0
    
    print(f"  ✅ 代码生成成功")
    print(f"     - 生成的代码行数: {len(code.split(chr(10)))}")
    
    return True


def test_dependency_analyzer():
    """测试依赖分析器"""
    print("\n" + "="*70)
    print("测试 3: 依赖分析器")
    print("="*70)
    
    analyzer = DependencyAnalyzer()
    
    components = [
        {"type": "service"},
        {"type": "model"}
    ]
    
    deps = analyzer.analyze(components, "python")
    
    assert deps is not None
    assert isinstance(deps, list)
    
    print(f"  ✅ 依赖分析完成")
    print(f"     - 检测到的依赖: {deps}")
    
    return True


def test_architecture_designer():
    """测试架构设计器"""
    print("\n" + "="*70)
    print("测试 4: 架构设计器")
    print("="*70)
    
    designer = create_architecture_designer()
    
    description = "Create a service for managing products with a database"
    
    design = designer.design(description, "python")
    
    assert design is not None
    assert len(design.components) > 0
    
    print(f"  ✅ 架构设计生成成功")
    print(f"     - 组件数: {len(design.components)}")
    print(f"     - 文件结构: {len(design.file_structure)} 个文件")
    print(f"     - 依赖: {design.dependencies}")
    
    return True


def test_code_generation():
    """测试代码生成"""
    print("\n" + "="*70)
    print("测试 5: 代码生成")
    print("="*70)
    
    designer = create_architecture_designer()
    
    description = "Build an API with user authentication"
    design = designer.design(description, "python")
    
    generated = designer.generate_code(design)
    
    assert generated is not None
    assert isinstance(generated, dict)
    
    print(f"  ✅ 代码生成成功")
    print(f"     - 生成的组件: {list(generated.keys())}")
    
    return True


def test_full_project_generation():
    """测试完整项目生成"""
    print("\n" + "="*70)
    print("测试 6: 完整项目生成")
    print("="*70)
    
    designer = create_architecture_designer()
    
    description = "Create a user service with database and API endpoints"
    design = designer.design(description, "python")
    
    project = designer.generate_full_project(design)
    
    assert project is not None
    assert "files" in project
    assert "structure" in project
    
    print(f"  ✅ 完整项目生成成功")
    print(f"     - 生成文件数: {len(project['files'])}")
    print(f"     - 项目结构: {project['structure']}")
    
    return True


def test_multilanguage_support():
    """测试多语言支持"""
    print("\n" + "="*70)
    print("测试 7: 多语言支持")
    print("="*70)
    
    designer = create_architecture_designer()
    
    description = "Build a product management system"
    
    languages = ["python", "javascript"]
    
    for lang in languages:
        design = designer.design(description, lang)
        print(f"  ✅ {lang}: {len(design.components)} 个组件")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("自然语言解析器", test_nl_parser),
        ("代码结构生成器", test_code_structure_generator),
        ("依赖分析器", test_dependency_analyzer),
        ("架构设计器", test_architecture_designer),
        ("代码生成", test_code_generation),
        ("完整项目生成", test_full_project_generation),
        ("多语言支持", test_multilanguage_support),
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
    print("📋 自然语言架构设计器测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有自然语言架构设计器测试通过！")
        return True
    else:
        print(f"\n⚠️ {failed}个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
