#!/usr/bin/env python3
"""
知识图谱记忆系统 v9.0 - 内部接口深度测试
专门测试系统的内部私有方法，探索更底层的边界问题
"""
import sys
import os
import random
import time
import gc
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType

class DeepInterfaceTest:
    """内部接口深度测试"""
    
    def __init__(self):
        self.kg = MemorySystemV7Optimized()
        self.errors = []
        self.warnings = []
        self.tests_passed = 0
        self.tests_failed = 0
        
        print("="*100)
        print("🔍 v9.0 - 内部接口深度测试")
        print("="*100)
    
    def log_test(self, test_name: str, passed: bool, error: Exception = None):
        """记录测试结果"""
        if passed:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            self.tests_failed += 1
            self.errors.append({
                "test": test_name,
                "error": str(error) if error else "Unknown",
                "type": type(error).__name__ if error else "Unknown",
            })
            print(f"❌ {test_name}")
            if error:
                print(f"   错误: {type(error).__name__}: {str(error)[:100]}")
    
    def test_private_data_structures(self):
        """测试私有数据结构"""
        print(f"\n{'='*100}")
        print(f"🧪 测试1: 私有数据结构")
        print(f"{'='*100}")
        
        # 测试 _nodes 字典
        try:
            # 添加一个大量数据
            for i in range(100):
                self.kg.remember(f"Test{i}")
            
            with self.kg._node_lock:
                node_count = len(self.kg._nodes)
                label_count = len(self.kg._label_to_node)
            
            print(f"   _nodes: {node_count}项 | _label_to_node: {label_count}项")
            self.log_test("私有数据结构访问", True)
            
        except Exception as e:
            self.log_test("私有数据结构访问", False, e)
    
    def test_invalid_node_type(self):
        """测试无效NodeType"""
        print(f"\n{'='*100}")
        print(f"🧪 测试2: 无效NodeType")
        print(f"{'='*100}")
        
        invalid_values = [
            None, "", 123, 3.14, {}, [], True, False,
            "NOT_A_VALID_TYPE", "INVALID", "node",
        ]
        
        passed = True
        for value in invalid_values:
            try:
                # 直接传入无效值
                self.kg.remember(f"Test_{repr(value)}", node_type=value)
                print(f"   测试 {repr(value)}: 通过")
            except Exception as e:
                print(f"   测试 {repr(value)}: 错误 - {type(e).__name__}")
                self.warnings.append({"test": "invalid_node_type", "value": value, "error": str(e)})
                passed = False
        
        self.log_test("无效NodeType处理", passed)
    
    def test_invalid_edge_type(self):
        """测试无效EdgeType"""
        print(f"\n{'='*100}")
        print(f"🧪 测试3: 无效EdgeType")
        print(f"{'='*100}")
        
        self.kg.remember("A")
        self.kg.remember("B")
        
        invalid_values = [
            None, "", 123, 3.14, {}, [], True, False,
            "NOT_A_VALID_EDGE", "invalid_rel", "edge",
        ]
        
        passed = True
        for value in invalid_values:
            try:
                self.kg.connect("A", "B", relation=value)
                print(f"   测试 {repr(value)}: 通过")
            except Exception as e:
                print(f"   测试 {repr(value)}: 错误 - {type(e).__name__}")
                self.warnings.append({"test": "invalid_edge_type", "value": value, "error": str(e)})
                passed = False
        
        self.log_test("无效EdgeType处理", passed)
    
    def test_extreme_properties(self):
        """测试极端属性"""
        print(f"\n{'='*100}")
        print(f"🧪 测试4: 极端属性")
        print(f"{'='*100}")
        
        test_cases = [
            ("None", None),
            ("空", {}),
            ("大量键", {f"key_{i}": f"value_{i}" for i in range(1000)}),
            ("超长值", {"a": "x"*10000}),
            ("循环引用", {"a": None}),
            ("混合类型", {"a": 1, "b": "test", "c": 3.14, "d": True, "e": None}),
        ]
        
        passed = True
        for name, props in test_cases:
            try:
                self.kg.remember(f"Node_{name}", properties=props)
                print(f"   测试 {name}: 通过")
            except Exception as e:
                print(f"   测试 {name}: 错误 - {type(e).__name__}")
                passed = False
        
        self.log_test("极端属性处理", passed)
    
    def test_invalid_k_values(self):
        """测试无效k值"""
        print(f"\n{'='*100}")
        print(f"🧪 测试5: 无效k值")
        print(f"{'='*100}")
        
        self.kg.remember("Python")
        
        invalid_values = [
            None, "", "invalid", 3.14, -9999, -1, 0, 99999999, float("inf"), float("nan"),
        ]
        
        passed = True
        for k in invalid_values:
            try:
                results1 = self.kg.recall("Python", k=k)
                results2 = self.kg.semantic_search("Python", k=k)
                print(f"   k={repr(k)}: 通过")
            except Exception as e:
                print(f"   k={repr(k)}: 错误 - {type(e).__name__}")
                passed = False
        
        self.log_test("无效k值处理", passed)
    
    def test_invalid_infer_depth(self):
        """测试无效推理深度"""
        print(f"\n{'='*100}")
        print(f"🧪 测试6: 无效推理深度")
        print(f"{'='*100}")
        
        self.kg.remember("Python")
        
        invalid_values = [
            None, "", "invalid", 3.14, -9999, -1, float("inf"), float("nan"),
        ]
        
        passed = True
        for depth in invalid_values:
            try:
                results = self.kg.infer("Python", max_depth=depth)
                print(f"   depth={repr(depth)}: 通过")
            except Exception as e:
                print(f"   depth={repr(depth)}: 错误 - {type(e).__name__}")
                passed = False
        
        self.log_test("无效推理深度处理", passed)
    
    def test_edge_cases_of_connect(self):
        """测试connect的边缘情况"""
        print(f"\n{'='*100}")
        print(f"🧪 测试7: connect的边缘情况")
        print(f"{'='*100}")
        
        test_cases = [
            ("None-None", None, None),
            ("None-valid", None, "Valid"),
            ("valid-None", "Valid", None),
            ("self-loop", "Valid", "Valid"),
            ("empty-empty", "", ""),
            ("large-labels", "L"*10000, "R"*10000),
        ]
        
        self.kg.remember("Valid")
        
        passed = True
        for name, src, tgt in test_cases:
            try:
                self.kg.connect(src, tgt)
                print(f"   测试 {name}: 通过")
            except Exception as e:
                print(f"   测试 {name}: 错误 - {type(e).__name__}")
                passed = False
        
        self.log_test("connect边缘情况", passed)
    
    def test_cached_methods(self):
        """测试缓存方法"""
        print(f"\n{'='*100}")
        print(f"🧪 测试8: 缓存相关方法")
        print(f"{'='*100}")
        
        try:
            # 多次调用，检查缓存
            for i in range(10):
                self.kg.remember(f"CacheTest_{i}")
                self.kg.semantic_search(f"CacheTest_{i}")
            
            gc.collect()
            
            print(f"   缓存方法多次调用: 通过")
            self.log_test("缓存方法测试", True)
            
        except Exception as e:
            self.log_test("缓存方法测试", False, e)
    
    def test_concurrent_locking(self):
        """测试并发锁边界"""
        print(f"\n{'='*100}")
        print(f"🧪 测试9: 并发锁边界")
        print(f"{'='*100}")
        
        passed = True
        
        try:
            # 重复获取锁（正常情况下Python的RLock允许重入）
            with self.kg._node_lock:
                with self.kg._node_lock:
                    self.kg.remember("LockTest")
            
            print(f"   锁重入: 通过")
            self.log_test("并发锁边界测试", True)
            
        except Exception as e:
            self.log_test("并发锁边界测试", False, e)
            passed = False
    
    def test_memory_stability(self):
        """测试内存稳定性"""
        print(f"\n{'='*100}")
        print(f"🧪 测试10: 内存稳定性")
        print(f"{'='*100}")
        
        gc.collect()
        initial_nodes = len(self.kg._nodes)
        
        # 添加然后删除（或替换）
        for i in range(1000):
            self.kg.remember(f"MemTest_{i}")
        
        gc.collect()
        
        print(f"   初始节点: {initial_nodes} | 最终节点: {len(self.kg._nodes)}")
        self.log_test("内存稳定性测试", True)
    
    def run_all(self):
        """运行所有测试"""
        
        self.test_private_data_structures()
        self.test_invalid_node_type()
        self.test_invalid_edge_type()
        self.test_extreme_properties()
        self.test_invalid_k_values()
        self.test_invalid_infer_depth()
        self.test_edge_cases_of_connect()
        self.test_cached_methods()
        self.test_concurrent_locking()
        self.test_memory_stability()
        
        # 最终总结
        print(f"\n{'='*100}")
        print(f"📊 内部接口深度测试 - 最终总结")
        print(f"{'='*100}")
        print(f"✅ 通过: {self.tests_passed}")
        print(f"❌ 失败: {self.tests_failed}")
        print(f"⚠️  警告: {len(self.warnings)}")
        
        if self.errors:
            print(f"\n❌ 详细错误:")
            for i, err in enumerate(self.errors, 1):
                print(f"{i:2d}. {err['test']}: {err['type']}")
                print(f"    {err['error']}")
        
        print("="*100)
        
        return self.tests_failed == 0

if __name__ == "__main__":
    test = DeepInterfaceTest()
    passed = test.run_all()
    sys.exit(0 if passed else 1)

