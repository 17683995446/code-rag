#!/usr/bin/env python3
"""
知识图谱记忆系统 v4.0 - 极端压力测试
测试超大规模数据、高并发、复杂图算法
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import time
import tempfile
import psutil
import gc
from typing import List, Dict, Any
import threading
import random
import string

from kg_memory.core import MemorySystem, Node, Edge, EdgeType


class SystemStressTester:
    """极端压力测试器"""

    def __init__(self):
        self.results = {
            "tests_passed": 0,
            "tests_failed": 0,
            "issues_found": [],
            "performance_metrics": {},
        }
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

    def log_issue(self, test_name: str, issue: str, severity: str = "medium"):
        """记录发现的问题"""
        self.results["issues_found"].append({
            "test": test_name,
            "issue": issue,
            "severity": severity,
            "timestamp": time.time()
        })
        print(f"⚠️  [{severity.upper()}] {test_name}: {issue}")

    def get_memory_usage(self) -> float:
        """获取当前内存使用（MB）"""
        return psutil.Process().memory_info().rss / 1024 / 1024

    def test_massive_node_creation(self, node_count: int = 10000):
        """测试大规模节点创建"""
        print(f"\n{'='*70}")
        print(f"📊 测试：大规模节点创建 ({node_count} 节点)")
        print(f"{'='*70}")

        test_name = "Massive Node Creation"
        temp_dir = tempfile.mkdtemp()

        try:
            ms = MemorySystem(temp_dir)
            ms.clear()

            start_time = time.time()
            start_mem = self.get_memory_usage()

            # 批量添加节点
            node_ids = []
            batch_size = 1000
            for i in range(node_count):
                node_id = ms.remember(f"Node_{i}", {"index": i})
                node_ids.append(node_id)

                if (i + 1) % batch_size == 0:
                    elapsed = time.time() - start_time
                    rate = (i + 1) / elapsed
                    mem_used = self.get_memory_usage() - start_mem
                    print(f"   进度: {i+1}/{node_count} | 速率: {rate:.0f} nodes/s | 内存: {mem_used:.1f}MB")

            elapsed = time.time() - start_time
            end_mem = self.get_memory_usage()

            # 验证
            stats = ms.stats()
            assert stats['nodes'] == node_count, f"节点数量不匹配: {stats['nodes']} != {node_count}"

            # 性能指标
            rate = node_count / elapsed
            mem_per_node = (end_mem - start_mem) / node_count

            self.results["performance_metrics"]["massive_node_creation"] = {
                "node_count": node_count,
                "elapsed_seconds": elapsed,
                "rate_per_second": rate,
                "memory_used_mb": end_mem - start_mem,
                "memory_per_node_kb": mem_per_node * 1024,
            }

            print(f"✅ {test_name} 通过")
            print(f"   耗时: {elapsed:.2f}s")
            print(f"   速率: {rate:.0f} nodes/s")
            print(f"   内存: {end_mem - start_mem:.1f}MB ({mem_per_node*1024:.2f}KB/node)")

            self.results["tests_passed"] += 1

        except Exception as e:
            print(f"❌ {test_name} 失败: {e}")
            self.log_issue(test_name, str(e), "high")
            self.results["tests_failed"] += 1
        finally:
            gc.collect()

    def test_massive_edge_creation(self, node_count: int = 5000):
        """测试大规模边创建"""
        print(f"\n{'='*70}")
        print(f"📊 测试：大规模边创建 ({node_count} 节点, ~{node_count*2} 边)")
        print(f"{'='*70}")

        test_name = "Massive Edge Creation"
        temp_dir = tempfile.mkdtemp()

        try:
            ms = MemorySystem(temp_dir)
            ms.clear()

            # 创建节点
            print("   创建节点...")
            for i in range(node_count):
                ms.remember(f"Node_{i}", {"index": i})

            # 创建边（每个节点连接几个其他节点）
            start_time = time.time()
            start_mem = self.get_memory_usage()

            edge_count = 0
            for i in range(node_count):
                # 创建 2-5 个出边
                num_edges = random.randint(2, 5)
                for j in range(num_edges):
                    target = random.randint(0, node_count - 1)
                    if target != i:
                        try:
                            ms.connect(f"Node_{i}", f"Node_{target}", "related_to")
                            edge_count += 1
                        except:
                            pass

                if (i + 1) % 1000 == 0:
                    elapsed = time.time() - start_time
                    print(f"   进度: {i+1}/{node_count} | 边数: {edge_count}")

            elapsed = time.time() - start_time
            end_mem = self.get_memory_usage()

            stats = ms.stats()
            rate = edge_count / elapsed if elapsed > 0 else 0

            self.results["performance_metrics"]["massive_edge_creation"] = {
                "node_count": node_count,
                "edge_count": edge_count,
                "elapsed_seconds": elapsed,
                "rate_per_second": rate,
                "memory_used_mb": end_mem - start_mem,
            }

            print(f"✅ {test_name} 通过")
            print(f"   节点: {stats['nodes']}")
            print(f"   边: {stats['edges']}")
            print(f"   耗时: {elapsed:.2f}s")
            print(f"   速率: {rate:.0f} edges/s")

            self.results["tests_passed"] += 1

        except Exception as e:
            print(f"❌ {test_name} 失败: {e}")
            self.log_issue(test_name, str(e), "high")
            self.results["tests_failed"] += 1
        finally:
            gc.collect()

    def test_concurrent_operations(self, num_threads: int = 50, operations_per_thread: int = 100):
        """测试并发操作"""
        print(f"\n{'='*70}")
        print(f"📊 测试：并发操作 ({num_threads} 线程, {operations_per_thread} 操作/线程)")
        print(f"{'='*70}")

        test_name = "Concurrent Operations"
        temp_dir = tempfile.mkdtemp()

        errors = []
        results = []

        def worker(thread_id: int):
            try:
                ms = MemorySystem(temp_dir)
                for i in range(operations_per_thread):
                    op = random.choice(["remember", "recall", "connect", "search"])
                    if op == "remember":
                        ms.remember(f"Test_{thread_id}_{i}")
                    elif op == "recall":
                        ms.recall("Test")
                    elif op == "connect":
                        ms.connect(f"Node_{i}", f"Node_{(i+1)%100}")
                    elif op == "search":
                        ms._graph.search("Test", k=10)
                results.append({"thread_id": thread_id, "success": True})
            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")
                results.append({"thread_id": thread_id, "success": False, "error": str(e)})

        try:
            threads = []
            start_time = time.time()

            for i in range(num_threads):
                t = threading.Thread(target=worker, args=(i,))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            elapsed = time.time() - start_time
            total_ops = num_threads * operations_per_thread
            success_count = sum(1 for r in results if r.get("success"))

            if errors:
                error_msg = f"{len(errors)} threads failed: {errors[:3]}"
                self.log_issue(test_name, error_msg, "high")
                print(f"❌ {test_name} 部分失败: {error_msg}")
            else:
                print(f"✅ {test_name} 通过")

            print(f"   总操作: {total_ops}")
            print(f"   成功: {success_count}/{total_ops}")
            print(f"   失败: {len(errors)}/{total_ops}")
            print(f"   耗时: {elapsed:.2f}s")
            print(f"   吞吐量: {total_ops/elapsed:.0f} ops/s")

            self.results["performance_metrics"]["concurrent_operations"] = {
                "threads": num_threads,
                "total_operations": total_ops,
                "successful_operations": success_count,
                "failed_operations": len(errors),
                "elapsed_seconds": elapsed,
                "throughput_per_second": total_ops / elapsed if elapsed > 0 else 0,
            }

            self.results["tests_passed"] += 1

        except Exception as e:
            print(f"❌ {test_name} 失败: {e}")
            self.log_issue(test_name, str(e), "high")
            self.results["tests_failed"] += 1
        finally:
            gc.collect()

    def test_complex_path_finding(self, node_count: int = 1000):
        """测试复杂路径查找"""
        print(f"\n{'='*70}")
        print(f"📊 测试：复杂路径查找 ({node_count} 节点)")
        print(f"{'='*70}")

        test_name = "Complex Path Finding"
        temp_dir = tempfile.mkdtemp()

        try:
            ms = MemorySystem(temp_dir)
            ms.clear()

            # 创建链状结构
            print("   创建链状结构...")
            for i in range(node_count):
                ms.remember(f"Chain_{i}")
                if i > 0:
                    ms.connect(f"Chain_{i-1}", f"Chain_{i}", "next")

            # 创建一些随机连接
            print("   创建随机连接...")
            for i in range(node_count // 10):
                a, b = random.sample(range(node_count), 2)
                ms.connect(f"Chain_{a}", f"Chain_{b}", "random")

            # 测试路径查找
            start_time = time.time()
            paths_found = 0
            path_lengths = []

            for i in range(min(100, node_count // 10)):
                source = random.randint(0, node_count - 1)
                target = random.randint(0, node_count - 1)
                if source != target:
                    path = ms.shortest_path(f"Chain_{source}", f"Chain_{target}")
                    if path:
                        paths_found += 1
                        path_lengths.append(len(path))

            elapsed = time.time() - start_time

            avg_path_length = sum(path_lengths) / len(path_lengths) if path_lengths else 0

            print(f"✅ {test_name} 通过")
            print(f"   路径查找: {paths_found} 次成功")
            print(f"   平均路径长度: {avg_path_length:.1f}")
            print(f"   耗时: {elapsed:.2f}s")

            self.results["performance_metrics"]["complex_path_finding"] = {
                "node_count": node_count,
                "paths_found": paths_found,
                "average_path_length": avg_path_length,
                "elapsed_seconds": elapsed,
            }

            self.results["tests_passed"] += 1

        except Exception as e:
            print(f"❌ {test_name} 失败: {e}")
            self.log_issue(test_name, str(e), "medium")
            self.results["tests_failed"] += 1
        finally:
            gc.collect()

    def test_memory_leak_detection(self, iterations: int = 100):
        """测试内存泄漏"""
        print(f"\n{'='*70}")
        print(f"📊 测试：内存泄漏检测 ({iterations} 次迭代)")
        print(f"{'='*70}")

        test_name = "Memory Leak Detection"
        temp_dir = tempfile.mkdtemp()

        try:
            memory_samples = []

            for i in range(iterations):
                ms = MemorySystem(temp_dir)
                ms.clear()

                # 执行一些操作
                for j in range(100):
                    ms.remember(f"Node_{i}_{j}")
                    ms.recall("Node")
                    ms._graph.search("Node", k=10)

                if i % 10 == 0:
                    mem = self.get_memory_usage()
                    memory_samples.append(mem)
                    print(f"   迭代 {i}: 内存 {mem:.1f}MB")

                del ms
                gc.collect()

            # 分析内存趋势
            if len(memory_samples) >= 3:
                first_mem = memory_samples[0]
                last_mem = memory_samples[-1]
                mem_growth = last_mem - first_mem
                growth_rate = mem_growth / first_mem if first_mem > 0 else 0

                print(f"✅ {test_name} 完成")
                print(f"   初始内存: {first_mem:.1f}MB")
                print(f"   最终内存: {last_mem:.1f}MB")
                print(f"   增长: {mem_growth:.1f}MB ({growth_rate*100:.1f}%)")

                if growth_rate > 0.5:  # 50% 内存增长
                    self.log_issue(test_name, f"内存增长 {growth_rate*100:.1f}%, 可能存在内存泄漏", "high")
                elif growth_rate > 0.2:
                    self.log_issue(test_name, f"内存增长 {growth_rate*100:.1f}%, 建议监控", "medium")

                self.results["performance_metrics"]["memory_leak"] = {
                    "iterations": iterations,
                    "initial_memory_mb": first_mem,
                    "final_memory_mb": last_mem,
                    "growth_mb": mem_growth,
                    "growth_rate": growth_rate,
                }

            self.results["tests_passed"] += 1

        except Exception as e:
            print(f"❌ {test_name} 失败: {e}")
            self.log_issue(test_name, str(e), "high")
            self.results["tests_failed"] += 1
        finally:
            gc.collect()

    def test_cache_effectiveness(self):
        """测试缓存有效性"""
        print(f"\n{'='*70}")
        print(f"📊 测试：缓存有效性")
        print(f"{'='*70}")

        test_name = "Cache Effectiveness"
        temp_dir = tempfile.mkdtemp()

        try:
            ms = MemorySystem(temp_dir)
            ms.clear()

            # 添加数据
            for i in range(1000):
                ms.remember(f"Item_{i}", {"data": f"value_{i}"})

            # 第一次查询（无缓存）
            start1 = time.time()
            for _ in range(1000):
                ms.recall("Item_500")
            time1 = time.time() - start1

            # 第二次查询（应有缓存）
            start2 = time.time()
            for _ in range(1000):
                ms.recall("Item_500")
            time2 = time.time() - start2

            # 从 MemorySystem 缓存获取命中率
            cache_stats = ms._cache.stats()
            hit_rate = cache_stats.get("hit_rate", 0)

            speedup = time1 / time2 if time2 > 0 else 1

            print(f"✅ {test_name} 完成")
            print(f"   首次查询: {time1:.4f}s")
            print(f"   缓存后查询: {time2:.4f}s")
            print(f"   加速比: {speedup:.2f}x")
            print(f"   缓存命中率: {hit_rate*100:.1f}%")

            if hit_rate < 0.5:
                self.log_issue(test_name, f"缓存命中率低: {hit_rate*100:.1f}%", "medium")

            self.results["performance_metrics"]["cache_effectiveness"] = {
                "first_query_time": time1,
                "cached_query_time": time2,
                "speedup": speedup,
                "cache_hit_rate": hit_rate,
            }

            self.results["tests_passed"] += 1

        except Exception as e:
            print(f"❌ {test_name} 失败: {e}")
            self.log_issue(test_name, str(e), "medium")
            self.results["tests_failed"] += 1
        finally:
            gc.collect()

    def test_centrality_algorithms(self, node_count: int = 500):
        """测试中心性算法"""
        print(f"\n{'='*70}")
        print(f"📊 测试：中心性算法 ({node_count} 节点)")
        print(f"{'='*70}")

        test_name = "Centrality Algorithms"
        temp_dir = tempfile.mkdtemp()

        try:
            ms = MemorySystem(temp_dir)
            ms.clear()

            # 创建图
            print("   创建图结构...")
            for i in range(node_count):
                ms.remember(f"Node_{i}")
                # 每个节点连接 2-5 个其他节点
                num_edges = random.randint(2, 5)
                for _ in range(num_edges):
                    target = random.randint(0, node_count - 1)
                    if target != i:
                        ms.connect(f"Node_{i}", f"Node_{target}", "related_to")

            # 测试各种中心性算法
            algorithms = {
                "betweenness": ms.betweenness_centrality,
                "degree": ms.degree_centrality,
                "closeness": ms.closeness_centrality,
            }

            results = {}
            for name, func in algorithms.items():
                start = time.time()
                result = func()
                elapsed = time.time() - start
                results[name] = {
                    "time": elapsed,
                    "count": len(result),
                }
                print(f"   {name}: {elapsed:.4f}s ({len(result)} 节点)")

            self.results["performance_metrics"]["centrality_algorithms"] = results
            self.results["tests_passed"] += 1

            print(f"✅ {test_name} 通过")

        except Exception as e:
            print(f"❌ {test_name} 失败: {e}")
            self.log_issue(test_name, str(e), "medium")
            self.results["tests_failed"] += 1
        finally:
            gc.collect()

    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        end_memory = self.get_memory_usage()
        memory_delta = end_memory - self.start_memory

        report = {
            "summary": {
                "tests_passed": self.results["tests_passed"],
                "tests_failed": self.results["tests_failed"],
                "total_tests": self.results["tests_passed"] + self.results["tests_failed"],
                "issues_found": len(self.results["issues_found"]),
                "start_memory_mb": self.start_memory,
                "end_memory_mb": end_memory,
                "memory_delta_mb": memory_delta,
            },
            "issues": self.results["issues_found"],
            "performance": self.results["performance_metrics"],
        }

        return report


def main():
    print("\n" + "="*70)
    print("🚀 知识图谱记忆系统 v4.0 - 极端压力测试")
    print("="*70)

    tester = SystemStressTester()

    # 运行各项测试
    tester.test_massive_node_creation(10000)
    tester.test_massive_edge_creation(5000)
    tester.test_concurrent_operations(50, 100)
    tester.test_complex_path_finding(1000)
    tester.test_memory_leak_detection(50)
    tester.test_cache_effectiveness()
    tester.test_centrality_algorithms(500)

    # 生成报告
    report = tester.generate_report()

    print("\n" + "="*70)
    print("📋 测试报告")
    print("="*70)

    print(f"\n✅ 测试通过: {report['summary']['tests_passed']}")
    print(f"❌ 测试失败: {report['summary']['tests_failed']}")
    print(f"⚠️  发现问题: {report['summary']['issues_found']}")
    print(f"\n💾 内存使用:")
    print(f"   初始: {report['summary']['start_memory_mb']:.1f}MB")
    print(f"   最终: {report['summary']['end_memory_mb']:.1f}MB")
    print(f"   增长: {report['summary']['memory_delta_mb']:.1f}MB")

    if report["issues"]:
        print(f"\n⚠️  发现的问题:")
        for issue in report["issues"]:
            print(f"   [{issue['severity'].upper()}] {issue['test']}")
            print(f"      {issue['issue']}")

    print("\n" + "="*70)

    return report


if __name__ == "__main__":
    report = main()
