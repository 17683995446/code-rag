#!/usr/bin/env python3
"""
Code RAG v20.0 - 扩展多语言解析器测试
Java / C++ / Go
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v20.0 - 扩展多语言解析器测试")
print("="*80)

from code_rag.processing_layer.multilang_parser import (
    Language,
    ParserRegistry,
    parse_code,
    JavaParser,
    CppParser,
    GoParser
)


def test_java_parser():
    """测试 Java 解析器"""
    print("\n" + "="*70)
    print("测试 1: Java 解析器")
    print("="*70)
    
    java_code = """
package com.example;

import java.util.List;
import java.util.ArrayList;

public class Calculator {
    private int result;
    
    public Calculator() {
        this.result = 0;
    }
    
    public int add(int a, int b) {
        return a + b;
    }
    
    public int multiply(int a, int b) {
        return a * b;
    }
    
    public static void main(String[] args) {
        Calculator calc = new Calculator();
        System.out.println(calc.add(1, 2));
    }
}
"""
    
    module = parse_code(java_code, Language.JAVA, "Calculator.java")
    
    assert module is not None
    assert module.language == Language.JAVA
    print(f"  ✅ Java 解析器初始化成功")
    print(f"  ✅ 提取到 {len(module.entities)} 个实体")
    print(f"  ✅ 提取到 {len(module.imports)} 个导入")
    
    # 检查类
    class_entity = None
    for entity in module.entities:
        if entity.entity_type == "class":
            class_entity = entity
            print(f"    - 类: {entity.name}")
        elif entity.entity_type == "function":
            print(f"    - 方法: {entity.name}")
    
    assert class_entity is not None
    assert len(module.entities) >= 1
    print(f"  ✅ Java 解析器工作正常")
    
    return True


def test_cpp_parser():
    """测试 C++ 解析器"""
    print("\n" + "="*70)
    print("测试 2: C++ 解析器")
    print("="*70)
    
    cpp_code = """
#include <iostream>
#include <vector>

using namespace std;

class Calculator {
private:
    int result;
public:
    Calculator() : result(0) {}
    
    int add(int a, int b) {
        return a + b;
    }
    
    int multiply(int a, int b) {
        return a * b;
    }
};

int main() {
    Calculator calc;
    cout << calc.add(1, 2) << endl;
    return 0;
}
"""
    
    module = parse_code(cpp_code, Language.CPP, "calculator.cpp")
    
    assert module is not None
    assert module.language == Language.CPP
    print(f"  ✅ C++ 解析器初始化成功")
    print(f"  ✅ 提取到 {len(module.entities)} 个实体")
    print(f"  ✅ 提取到 {len(module.imports)} 个导入")
    
    for entity in module.entities:
        if entity.entity_type == "class":
            print(f"    - 类/结构体: {entity.name}")
        elif entity.entity_type == "function":
            print(f"    - 函数/方法: {entity.name}")
    
    assert len(module.entities) >= 1
    print(f"  ✅ C++ 解析器工作正常")
    
    return True


def test_go_parser():
    """测试 Go 解析器"""
    print("\n" + "="*70)
    print("测试 3: Go 解析器")
    print("="*70)
    
    go_code = """
package main

import "fmt"

type Calculator struct {
    result int
}

func NewCalculator() *Calculator {
    return &Calculator{result: 0}
}

func (c *Calculator) Add(a, b int) int {
    return a + b
}

func (c *Calculator) Multiply(a, b int) int {
    return a * b
}

type Shape interface {
    Area() float64
}

func main() {
    calc := NewCalculator()
    fmt.Println(calc.Add(1, 2))
}
"""
    
    module = parse_code(go_code, Language.GO, "calculator.go")
    
    assert module is not None
    assert module.language == Language.GO
    print(f"  ✅ Go 解析器初始化成功")
    print(f"  ✅ 提取到 {len(module.entities)} 个实体")
    print(f"  ✅ 提取到 {len(module.imports)} 个导入")
    
    for entity in module.entities:
        if entity.entity_type == "class":
            print(f"    - 结构体: {entity.name}")
        elif entity.entity_type == "interface":
            print(f"    - 接口: {entity.name}")
        elif entity.entity_type == "function":
            print(f"    - 函数: {entity.name}")
    
    assert len(module.entities) >= 1
    print(f"  ✅ Go 解析器工作正常")
    
    return True


def test_auto_detection_by_extension():
    """测试通过文件扩展名自动检测"""
    print("\n" + "="*70)
    print("测试 4: 自动语言检测")
    print("="*70)
    
    test_files = [
        ("Test.java", Language.JAVA),
        ("test.cpp", Language.CPP),
        ("calc.go", Language.GO),
        ("test.hxx", Language.CPP),
    ]
    
    for file_path, expected_lang in test_files:
        parser = ParserRegistry.get_parser_for_file(file_path)
        assert parser is not None
        assert parser.language == expected_lang
        print(f"  ✅ {file_path} 正确检测为 {expected_lang.value}")
    
    return True


def test_all_languages_comparison():
    """测试所有语言的简单解析"""
    print("\n" + "="*70)
    print("测试 5: 所有语言解析")
    print("="*70)
    
    languages = [
        (Language.PYTHON, "def foo(): pass"),
        (Language.JAVASCRIPT, "function foo() {}"),
        (Language.JAVA, "public class Foo {}"),
        (Language.CPP, "class Foo {}"),
        (Language.GO, "type Foo struct {}"),
    ]
    
    for lang, code in languages:
        module = parse_code(code, lang)
        assert module is not None
        print(f"  ✅ {lang.value} 解析成功，实体数: {len(module.entities)}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("Java 解析器", test_java_parser),
        ("C++ 解析器", test_cpp_parser),
        ("Go 解析器", test_go_parser),
        ("自动语言检测", test_auto_detection_by_extension),
        ("所有语言解析", test_all_languages_comparison),
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
    print("📋 扩展多语言解析器测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有扩展多语言解析器测试通过！")
        return True
    else:
        print(f"\n⚠️ {failed}个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
