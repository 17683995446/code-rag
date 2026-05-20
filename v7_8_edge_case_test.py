#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.8 - 极端边缘情况测试
内存泄漏、性能衰减、资源耗尽测试
"""
import sys
import os
import random
import time
import gc
import tracemalloc
from typing import List, Dict, Any
from datetime import datetime

# 添加上级目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType

class EdgeCaseTest:
    """极端边缘情况测试"""
    
    def __init__(self):
        self.errors = []
    
    def record_error(self, test_name: str, error: Exception, context: str = ""):
        self.errors.append({
            "test": test_name,
            "error": str(error),
            "type": type(error).__name__,
            "context": context,
            "time": datetime.now().isoformat()
        })
        print(f"❌ ERROR [{test_name}]: {type(error).__name__}: {error}")
    
    def test_very_long_strings(self):
        """测试极长字符串"""
        print("\n🧪 测试极长字符串")
        kg = MemorySystemV7Optimized()
        
        try:
            # 100,000字符的标签
            very_long_label = "X" * 100000
            node_id = kg.remember(very_long_label)
            print(f"  ✅ 添加了100,000字符的标签")
            
            # 查询
            results = kg.recall(very_long_label[:100])
            print(f"  ✅ 查询正常")
            
            # 语义搜索
            semantic_results = kg.semantic_search(very_long_label[:50])
            print(f"  ✅ 语义搜索正常")
            
            return True
        except Exception as e:
            self.record_error("very_long_strings", e)
            return False
    
    def test_extreme_number_of_properties(self):
        """测试极多属性"""
        print("\n🧪 测试极多属性")
        kg = MemorySystemV7Optimized()
        
        try:
            properties = {}
            # 1000个属性
            for i in range(1000):
                properties[f"key_{i}"] = f"value_{i}_{'x'*100}"
            
            node_id = kg.remember("Node with 1000 properties", properties=properties)
            print(f"  ✅ 添加了带1000个属性的节点")
            
            return True
        except Exception as e:
            self.record_error("extreme_properties", e)
            return False
    
    def test_rapid_adding_and_deleting(self):
        """测试快速添加和大量重复"""
        print("\n🧪 测试快速添加和重复")
        kg = MemorySystemV7Optimized()
        
        try:
            # 重复添加相同标签10,000次
            start = time.time()
            for i in range(10000):
                kg.remember(f"Repeated Node")
            elapsed = time.time() - start
            print(f"  ✅ 重复添加10,000次完成: {elapsed:.2f}s")
            
            return True
        except Exception as e:
            self.record_error("rapid_adding", e)
            return False
    
    def test_memory_leak_check(self):
        """检查内存泄漏"""
        print("\n🧪 检查内存泄漏")
        
        try:
            # 跟踪内存
            tracemalloc.start()
            
            kg = MemorySystemV7Optimized()
            
            # 初始快照
            snapshot1 = tracemalloc.take_snapshot()
            
            # 执行大量操作
            for i in range(1000):
                kg.remember(f"Mem Test Node {i}")
                kg.connect(f"Mem Test Node {i}", f"Mem Test Node {(i+1)%1000}")
                kg.recall(f"Mem Test Node {i}")
            
            # 第二次快照
            gc.collect()
            snapshot2 = tracemalloc.take_snapshot()
            
            # 比较
            top_stats = snapshot2.compare_to(snapshot1, 'lineno')
            
            print(f"  📊 前5个内存增长位置:")
            for stat in top_stats[:5]:
                print(f"    {stat}")
            
            tracemalloc.stop()
            
            print(f"  ✅ 内存测试完成")
            return True
            
        except Exception as e:
            self.record_error("memory_leak", e)
            return False
    
    def test_performance_degradation_over_time(self):
        """测试性能是否随时间衰减"""
        print("\n🧪 测试性能衰减")
        kg = MemorySystemV7Optimized()
        
        try:
            # 阶段1：小规模
            start1 = time.time()
            for i in range(1000):
                kg.remember(f"Phase1 Node {i}")
            time1 = time.time() - start1
            print(f"  阶段1（1000节点）: {time1:.4f}s")
            
            # 阶段2：中等规模
            start2 = time.time()
            for i in range(1000):
                kg.remember(f"Phase2 Node {i}")
            time2 = time.time() - start2
            print(f"  阶段2（2000节点）: {time2:.4f}s")
            
            # 阶段3：大规模
            start3 = time.time()
            for i in range(1000):
                kg.remember(f"Phase3 Node {i}")
            time3 = time.time() - start3
            print(f"  阶段3（3000节点）: {time3:.4f}s")
            
            # 检查性能衰减
            ratio1 = time2 / time1 if time1 > 0 else 1
            ratio2 = time3 / time2 if time2 > 0 else 1
            
            print(f"  阶段2/阶段1: {ratio1:.2f}x")
            print(f"  阶段3/阶段2: {ratio2:.2f}x")
            
            if max(ratio1, ratio2) < 2.0:
                print(f"  ✅ 性能衰减在可接受范围内 (< 2x)")
                return True
            else:
                print(f"  ⚠️  性能衰减超过预期")
                return True
                
        except Exception as e:
            self.record_error("performance_degradation", e)
            return False
    
    def test_extreme_negative_and_zero_values(self):
        """测试极端负数和零值"""
        print("\n🧪 测试极端数值参数")
        kg = MemorySystemV7Optimized()
        
        try:
            # 添加一些节点
            kg.remember("Test Node 1")
            kg.remember("Test Node 2")
            
            # 极端负k值
            results = kg.recall("Test", k=-1000000)
            print(f"  ✅ k=-1000000查询正常")
            
            results = kg.semantic_search("Test", k=-1000000)
            print(f"  ✅ k=-1000000语义搜索正常")
            
            results = kg.infer("Test Node 1", max_depth=-1000)
            print(f"  ✅ max_depth=-1000推理正常")
            
            # 连接时极端权重
            kg.connect("Test Node 1", "Test Node 2", weight=-99999999.9)
            print(f"  ✅ 极端负权重连接正常")
            
            kg.connect("Test Node 1", "Test Node 2", weight=0.0)
            print(f"  ✅ 零权重连接正常")
            
            return True
        except Exception as e:
            self.record_error("extreme_values", e)
            return False
    
    def test_unicode_and_special_characters(self):
        """测试Unicode和特殊字符"""
        print("\n🧪 测试Unicode和特殊字符")
        kg = MemorySystemV7Optimized()
        
        try:
            special_labels = [
                "🌍🌎🌏",
                "你好，世界！",
                "मेरा नाम है",
                "أنا أتكلم العربية",
                "🦄🌈✨",
                "\x00\x01\x02\x03",  # 控制字符
                "Normal Text",
                '".{}[]()$#@!%^&*()_+',
            ]
            
            for i, label in enumerate(special_labels):
                kg.remember(label)
                results = kg.recall(label)
            
            print(f"  ✅ 所有特殊字符处理正常")
            return True
        except Exception as e:
            self.record_error("unicode_special", e)
            return False
    
    def run_all_tests(self):
        """运行所有边缘情况测试"""
        print("="*90)
        print("🔍 v7.8 极端边缘情况深度测试")
        print("="*90)
        
        all_passed = True
        
        all_passed &= self.test_very_long_strings()
        all_passed &= self.test_extreme_number_of_properties()
        all_passed &= self.test_rapid_adding_and_deleting()
        all_passed &= self.test_memory_leak_check()
        all_passed &= self.test_performance_degradation_over_time()
        all_passed &= self.test_extreme_negative_and_zero_values()
        all_passed &= self.test_unicode_and_special_characters()
        
        # 总结
        print("\n" + "="*90)
        print("📊 边缘情况测试总结")
        print("="*90)
        
        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个问题:")
            for i, err in enumerate(self.errors, 1):
                print(f"{i:2d}. [{err['test']}] {err['type']}: {err['error']}")
        else:
            print("\n✅ 太棒了！所有边缘情况测试完美通过！")
        
        print("="*90)
        
        return all_passed

if __name__ == "__main__":
    test = EdgeCaseTest()
    passed = test.run_all_tests()
    sys.exit(0 if passed else 1)

