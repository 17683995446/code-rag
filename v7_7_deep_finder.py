#!/usr/bin/env python3
"""
v7.7 深度问题发现器
在极端边缘情况下发现真实运行时bug
"""

import sys
import os
import time
import threading
import random
import gc
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType


class DeepIssueDiscover:
    """深度问题发现器"""
    
    def __init__(self):
        self.issues = []
        self.memory = None
    
    def log_issue(self, severity: str, category: str, description: str,
                   impact: str = "", test_case: str = ""):
        """记录发现的问题"""
        issue = {
            "severity": severity,
            "category": category,
            "description": description,
            "impact": impact,
            "test_case": test_case,
            "timestamp": datetime.now().isoformat()
        }
        self.issues.append(issue)
        print(f"[{severity}] {category}: {description}")
    
    def test_null_edge_cases(self):
        """测试空值和边界情况"""
        print("\n🧪 测试1: 极端边界情况")
        
        self.memory = MemorySystemV7Optimized()
        
        try:
            # 测试1a: 空字符串操作
            self.memory.remember("", properties={})
            self.memory.remember(None)
        except Exception as e:
            self.log_issue("Medium", "NullHandling", "空/None标签处理异常", str(e))
        
        try:
            # 测试1b: 空标签查询
            self.memory.recall("", k=10)
            self.memory.semantic_search("")
        except Exception as e:
            self.log_issue("Medium", "Query", "空查询处理异常", str(e))
        
        try:
            # 测试1c: 无效k值
            self.memory.recall("test", k=0)
            self.memory.recall("test", k=-5)
        except Exception as e:
            self.log_issue("Medium", "Query", "k=0/k负数处理异常", str(e))
        
        # 清理
        self.memory.clear()
        gc.collect()
        
        print("✅ 边界情况测试完成")
    
    def test_extreme_concurrency(self):
        """测试极端并发"""
        print("\n🧪 测试2: 极端并发条件")
        
        self.memory = MemorySystemV7Optimized()
        
        errors = []
        num_threads = 100
        ops_per_thread = 50
        
        def worker(wid):
            for _ in range(ops_per_thread):
                try:
                    if random.random() < 0.5:
                        self.memory.remember(f"ec_{wid}_{_}")
                    else:
                        self.memory.recall(f"ec_{random.randint(0, 100)}_test")
                except Exception as e:
                    errors.append(str(e))
        
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        if len(errors) > 0:
            unique_errors = list(set(errors))
            self.log_issue("High", "Concurrency", 
                        f"极端并发下发现 {len(unique_errors)} 种错误",
                        str(unique_errors[:3]))
        
        stats = self.memory.get_statistics()
        print(f"✅ 极端并发测试完成: {stats['nodes']}节点, 错误数: {len(errors)}")
        
        self.memory.clear()
        gc.collect()
    
    def test_rapid_add_remove(self):
        """测试快速添加和大量节点"""
        print("\n🧪 测试3: 大数据量压力")
        
        self.memory = MemorySystemV7Optimized()
        
        num_nodes = 20000
        
        try:
            start = time.time()
            for i in range(num_nodes):
                self.memory.remember(f"rapid_{i}")
            add_time = time.time() - start
            print(f"   添加{num_nodes}节点: {add_time:.2f}秒")
        except Exception as e:
            self.log_issue("Medium", "Performance", "大数据量添加问题", str(e))
        
        try:
            start = time.time()
            for i in range(10000):
                self.memory.recall(f"rapid_{random.randint(0, num_nodes-1)}")
            query_time = time.time() - start
            print(f"   查询10000次: {query_time:.2f}秒")
        except Exception as e:
            self.log_issue("Medium", "Performance", "大数据量查询问题", str(e))
        
        self.memory.clear()
        gc.collect()
        print("✅ 大数据量测试完成")
    
    def test_repeated_same_node(self):
        """测试重复添加相同节点"""
        print("\n🧪 测试4: 重复操作")
        
        self.memory = MemorySystemV7Optimized()
        same_label = "repeated_test_node"
        
        try:
            for i in range(1000):
                self.memory.remember(same_label)
            
            stats = self.memory.get_statistics()
            if stats['nodes'] > 1:
                self.log_issue("Low", "DataIntegrity", 
                            "重复添加相同标签时创建了多个节点",
                            f"期望1个节点，但实际: {stats['nodes']}")
        except Exception as e:
            self.log_issue("Medium", "DataIntegrity", "重复添加异常", str(e))
        
        try:
            for i in range(1000):
                self.memory.recall(same_label, k=1)
        except Exception as e:
            self.log_issue("Low", "Performance", "重复查询问题", str(e))
        
        self.memory.clear()
        gc.collect()
        print("✅ 重复操作测试完成")
    
    def test_stress_cache(self):
        """测试缓存压力"""
        print("\n🧪 测试5: 缓存压力")
        
        self.memory = MemorySystemV7Optimized()
        
        try:
            for i in range(10000):
                self.memory.remember(f"cache_{i}")
            
            for round in range(5):
                for i in range(10000):
                    query_idx = random.randint(0, 9999)
                    self.memory.recall(f"cache_{query_idx}")
            
            stats = self.memory.get_statistics()
            print(f"   缓存统计: {stats['cache_hits']}/{stats['cache_misses']}")
            
            if (stats['cache_hits'] + stats['cache_misses']) > 0:
                hit_rate = stats['cache_hits']/(stats['cache_hits'] + stats['cache_misses'])
                if hit_rate > 0 and hit_rate < 0.3:
                    self.log_issue("Medium", "Cache", "缓存命中率过低", f"{hit_rate*100:.1f}%")
        
        except Exception as e:
            self.log_issue("Medium", "Cache", "缓存系统异常", str(e))
        
        self.memory.clear()
        gc.collect()
        print("✅ 缓存压力测试完成")
    
    def test_rapid_semantic_stress(self):
        """测试语义搜索压力"""
        print("\n🧪 测试6: 语义搜索压力")
        
        self.memory = MemorySystemV7Optimized()
        
        try:
            num_nodes = 5000
            
            for i in range(num_nodes):
                self.memory.remember(f"semantic_stress_{i}", compute_embedding=True)
            
            start = time.time()
            
            for i in range(500):
                self.memory.semantic_search(f"semantic_stress_{i}", k=20)
            
            search_time = time.time() - start
            print(f"   500次语义搜索: {search_time:.2f}秒")
        
        except Exception as e:
            self.log_issue("High", "SemanticSearch", "语义搜索压力问题", str(e))
        
        self.memory.clear()
        gc.collect()
        print("✅ 语义搜索压力测试完成")
    
    def test_edge_case_connect(self):
        """测试边连接的各种边缘情况"""
        print("\n🧪 测试7: 边连接边缘情况")
        
        self.memory = MemorySystemV7Optimized()
        
        try:
            self.memory.remember("edge_test_1")
            self.memory.remember("edge_test_2")
            
            self.memory.connect("edge_test_1", "edge_test_2")
            self.memory.connect("edge_test_1", "edge_test_1")
            self.memory.connect("nonexistent_1", "nonexistent_2")
        
        except Exception as e:
            self.log_issue("Medium", "EdgeHandling", "边连接处理异常", str(e))
        
        self.memory.clear()
        gc.collect()
        print("✅ 边连接边缘情况测试完成")
    
    def test_chaos_mixed(self):
        """测试最混乱的混合操作"""
        print("\n🧪 测试8: 最混乱混合测试")
        
        self.memory = MemorySystemV7Optimized()
        
        try:
            chaos_ops = 2000
            operations = ["remember", "connect", "recall", "infer", "semantic_search"]
            errors = []
            
            for i in range(chaos_ops):
                try:
                    op = random.choice(operations)
                    if op == "remember":
                        self.memory.remember(f"chaos_mixed_{i}")
                    elif op == "connect":
                        src = max(0, i - 1)
                        self.memory.connect(f"chaos_mixed_{src}", f"chaos_mixed_{i}")
                    elif op == "recall":
                        self.memory.recall(f"chaos_mixed_{random.randint(0, i)}")
                    elif op == "infer":
                        self.memory.infer(f"chaos_mixed_{random.randint(0, i)}")
                    elif op == "semantic_search":
                        self.memory.semantic_search(f"chaos_mixed_{random.randint(0, i)}")
                except Exception as e:
                    errors.append(str(e))
            
            if errors:
                unique_errors = list(set(errors))
                self.log_issue("Medium", "ChaosTesting", 
                            f"混乱测试中发现 {len(unique_errors)}种错误",
                            str(unique_errors[:5]))
        
        except Exception as e:
            self.log_issue("High", "ChaosTesting", "整体系统异常", str(e))
        
        self.memory.clear()
        gc.collect()
        print("✅ 混乱混合测试完成")
    
    def run_all(self):
        """运行所有发现测试"""
        print("\n" + "="*80)
        print("🔍 v7.7 深度问题发现 - 极端边缘情况测试")
        print("="*80)
        
        self.test_null_edge_cases()
        self.test_extreme_concurrency()
        self.test_rapid_add_remove()
        self.test_repeated_same_node()
        self.test_stress_cache()
        self.test_rapid_semantic_stress()
        self.test_edge_case_connect()
        self.test_chaos_mixed()
        
        print("\n" + "="*80)
        print("📊 问题发现总结")
        print("="*80)
        
        if not self.issues:
            print("✅ 太棒了！没有发现严重问题！系统非常稳定！")
        else:
            print(f"⚠️ 发现 {len(self.issues)} 个问题:")
            
            by_severity = {}
            for issue in self.issues:
                sev = issue['severity']
                if sev not in by_severity:
                    by_severity[sev] = []
                by_severity[sev].append(issue)
            
            for severity in ["Critical", "High", "Medium", "Low"]:
                if severity in by_severity:
                    print(f"\n{severity} ({len(by_severity[severity])}个):")
                    for issue in by_severity[severity]:
                        print(f"  - [{issue['category']}] {issue['description']}")
        
        print("\n" + "="*80)
        
        return self.issues


def main():
    discoverer = DeepIssueDiscover()
    issues = discoverer.run_all()
    
    if issues:
        print("\n💡 发现了问题！将进行v7.7深度优化！")
    else:
        print("\n✅ 系统非常稳定！")
    
    return issues


if __name__ == "__main__":
    main()
