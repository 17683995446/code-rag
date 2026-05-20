#!/usr/bin/env python3
"""
v7.6 深度问题分析器
基于第一性原理，深度分析现有系统问题
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


class DeepIssueAnalyzer:
    """深度问题分析器"""
    
    def __init__(self):
        self.issues_found = []
        self.performance_data = {}
    
    def log_issue(self, category: str, severity: str, description: str, impact: str = ""):
        """记录发现的问题"""
        self.issues_found.append({
            "category": category,
            "severity": severity,
            "description": description,
            "impact": impact,
            "timestamp": datetime.now().isoformat()
        })
        print(f"  [{category}:{severity}] {description}")
    
    def test_1_cache_invalidation_strategy(self):
        """测试1: 缓存失效策略"""
        print("\n📋 测试1: 缓存失效策略分析")
        
        memory = MemorySystemV7Optimized()
        
        # 添加一些初始数据
        for i in range(10):
            memory.remember(f"cache_test_{i}", properties={"test": 1})
        
        # 第一次查询
        result1 = memory.recall("cache_test_1", k=3)
        
        # 添加新的不相关数据
        memory.remember("unrelated_node", properties={"test": 2})
        
        # 第二次查询相同内容
        result2 = memory.recall("cache_test_1", k=3)
        
        stats = memory.get_statistics()
        print(f"  缓存命中: {stats['cache_hits']}, 未命中: {stats['cache_misses']}")
        
        if stats['cache_hits'] < 1:
            self.log_issue(
                "缓存策略", "Medium",
                "缓存命中率较低，添加新节点后相同查询可能无法命中",
                "影响查询性能，造成不必要的重复计算"
            )
        else:
            print("  ✅ 缓存命中正常")
    
    def test_2_race_condition_risks(self):
        """测试2: 竞态条件风险"""
        print("\n📋 测试2: 并发竞态条件风险")
        
        memory = MemorySystemV7Optimized()
        errors = []
        completed = []
        lock = threading.RLock()
        
        def add_node(wid):
            try:
                node_id = memory.remember(f"race_node_{wid}", compute_embedding=True)
                with lock:
                    completed.append(node_id)
            except Exception as e:
                with lock:
                    errors.append(str(e))
        
        threads = []
        for i in range(100):
            t = threading.Thread(target=add_node, args=(i,))
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()
        
        stats = memory.get_statistics()
        
        if len(errors) > 0:
            self.log_issue(
                "并发安全", "High",
                f"发现 {len(errors)} 个并发错误",
                "可能导致数据不一致或系统崩溃"
            )
        else:
            print(f"  ✅ 并发运行正常，节点数: {stats['nodes']}")
    
    def test_3_memory_usage_patterns(self):
        """测试3: 内存使用模式"""
        print("\n📋 测试3: 内存使用模式分析")
        
        memory = MemorySystemV7Optimized()
        
        # 测试不同规模的数据
        sizes = [100, 1000, 5000]
        add_times = []
        
        for size in sizes:
            start = time.time()
            for i in range(size):
                memory.remember(f"mem_node_{len(add_times)}_{i}", compute_embedding=True)
            duration = time.time() - start
            add_times.append((size, duration))
            print(f"  添加 {size} 节点: {duration:.3f}秒")
        
        # 分析添加性能
        if len(add_times) >= 2:
            scale1, time1 = add_times[0]
            scale2, time2 = add_times[-1]
            scale_ratio = scale2 / scale1
            time_ratio = time2 / time1
            
            if time_ratio > scale_ratio * 2:
                self.log_issue(
                    "性能", "Medium",
                    f"节点添加性能随规模下降较快 (规模x{scale_ratio:.1f}, 时间x{time_ratio:.1f})",
                    "大规模数据场景性能下降明显"
                )
        
        # 清理并强制GC
        memory.clear()
        gc.collect()
    
    def test_4_query_optimization_opportunities(self):
        """测试4: 查询优化机会"""
        print("\n📋 测试4: 查询性能深度分析")
        
        memory = MemorySystemV7Optimized()
        
        # 准备测试数据
        print("  准备10,000节点...")
        for i in range(10000):
            memory.remember(f"query_node_{i}", compute_embedding=True)
        
        # 精确匹配查询性能
        print("  精确匹配查询测试...")
        start = time.time()
        for i in range(100):
            memory.recall(f"query_node_{i}", k=3)
        exact_time = time.time() - start
        
        # 模糊匹配查询性能
        print("  模糊匹配查询测试...")
        start = time.time()
        for i in range(100):
            memory.recall("query_node", k=3)
        fuzzy_time = time.time() - start
        
        print(f"  精确查询: {exact_time:.3f}s, 模糊查询: {fuzzy_time:.3f}s")
        
        if fuzzy_time > exact_time * 10:
            self.log_issue(
                "查询优化", "Medium",
                "模糊查询性能显著低于精确查询",
                "可能影响用户体验"
            )
    
    def test_5_vector_index_scalability(self):
        """测试5: 向量索引可扩展性"""
        print("\n📋 测试5: 向量索引性能分析")
        
        memory = MemorySystemV7Optimized()
        
        # 测试不同规模
        sizes = [500, 2000, 5000]
        search_times = []
        
        for size in sizes:
            print(f"  准备 {size} 向量...")
            start = time.time()
            for i in range(size):
                memory.remember(f"vec_node_{len(search_times)}_{i}", compute_embedding=True)
            add_time = time.time() - start
            
            # 测试语义搜索
            print(f"  语义搜索测试...")
            start = time.time()
            for i in range(20):
                memory.semantic_search(f"vec_node_{len(search_times)}_{i}", k=5)
            search_time = time.time() - start
            search_times.append((size, search_time))
            print(f"  规模 {size}: 添加 {add_time:.2f}s, 搜索 {search_time:.3f}s")
        
        # 分析
        if len(search_times) >= 2:
            size1, time1 = search_times[0]
            size2, time2 = search_times[-1]
            scale_ratio = size2 / size1
            search_ratio = time2 / time1
            
            if search_ratio > scale_ratio * 1.5:
                self.log_issue(
                    "向量索引", "High",
                    f"语义搜索性能随规模下降明显 (规模x{scale_ratio:.1f}, 搜索x{search_ratio:.1f})",
                    "大规模数据下语义搜索可能非常慢"
                )
    
    def test_6_lock_contention_analysis(self):
        """测试6: 锁竞争分析"""
        print("\n📋 测试6: 锁竞争分析")
        
        memory = MemorySystemV7Optimized()
        stats = {}
        
        # 预热
        for i in range(100):
            memory.remember(f"lock_test_{i}", compute_embedding=True)
        
        # 不同线程数的性能测试
        thread_counts = [1, 10, 30]
        results = {}
        
        for num_threads in thread_counts:
            errors = []
            start_time = time.time()
            ops_per_thread = 100
            total_ops = num_threads * ops_per_thread
            
            def worker(wid):
                for i in range(ops_per_thread):
                    try:
                        memory.remember(f"lock_test_{num_threads}_{wid}_{i}")
                    except Exception as e:
                        with threading.RLock():
                            errors.append(str(e))
            
            threads = []
            for i in range(num_threads):
                t = threading.Thread(target=worker, args=(i,))
                t.start()
                threads.append(t)
            
            for t in threads:
                t.join()
            
            duration = time.time() - start_time
            results[num_threads] = {
                "duration": duration,
                "ops_per_sec": total_ops / duration if duration > 0 else 0,
                "errors": len(errors)
            }
            print(f"  {num_threads} 线程: {duration:.2f}s, {total_ops/duration:.0f} ops/s")
        
        if len(results) >= 2:
            single_perf = results[1]['ops_per_sec']
            multi_perf = results[thread_counts[-1]]['ops_per_sec']
            scalability = multi_perf / single_perf if single_perf > 0 else 0
            
            if scalability < 0.5:
                self.log_issue(
                    "锁竞争", "High",
                    f"并发扩展性较差 (线程数x{thread_counts[-1]}, 性能x{scalability:.2f})",
                    "高并发场景性能受限"
                )
    
    def run_full_analysis(self):
        """运行完整分析"""
        print("\n" + "=" * 80)
        print("🔍 v7.6 深度问题分析器 - 第一性原理分析")
        print("=" * 80)
        
        # 运行所有测试
        self.test_1_cache_invalidation_strategy()
        self.test_2_race_condition_risks()
        self.test_3_memory_usage_patterns()
        self.test_4_query_optimization_opportunities()
        self.test_5_vector_index_scalability()
        self.test_6_lock_contention_analysis()
        
        # 总结报告
        print("\n" + "=" * 80)
        print("📊 分析报告")
        print("=" * 80)
        
        if not self.issues_found:
            print("✅ 未发现严重问题！系统表现良好")
        else:
            print(f"⚠️ 发现 {len(self.issues_found)} 个问题:")
            
            by_severity = {}
            for issue in self.issues_found:
                sev = issue['severity']
                if sev not in by_severity:
                    by_severity[sev] = []
                by_severity[sev].append(issue)
            
            for severity in ["Critical", "High", "Medium", "Low"]:
                if severity in by_severity:
                    print(f"\n{severity} 级别问题 ({len(by_severity[severity])} 个):")
                    for issue in by_severity[severity]:
                        print(f"  - [{issue['category']}] {issue['description']}")
                        if issue['impact']:
                            print(f"    影响: {issue['impact']}")
        
        print("\n" + "=" * 80)
        return self.issues_found


def main():
    analyzer = DeepIssueAnalyzer()
    issues = analyzer.run_full_analysis()
    
    if issues:
        print("\n💡 基于发现的问题，接下来将实现v7.6深度优化！")
        return 0 if len(issues) == 0 else 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
