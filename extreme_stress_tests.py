"""
极端压力测试 - 揭露深层缺陷！
"""

import sys
import os
import time
import threading
import random
import gc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.code_rag.kg_v2_enhanced import MemorySystem


def test_memory_leaks():
    """测试1：内存泄漏测试"""
    print("=" * 70)
    print("🔥 测试1：极端内存压力与泄漏检测")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./leak_test")
    ms.store.clear_all()
    ms.start_session()
    
    # 记录初始内存
    import tracemalloc
    tracemalloc.start()
    
    start_time = time.time()
    operations = 10000
    
    # 疯狂操作：创建节点、连接、查询、删除...
    print(f"开始 {operations} 次混合操作...")
    node_ids = []
    
    for i in range(operations):
        # 随机操作
        op_type = random.choice([
            "add", "connect", "query", "delete"
        ])
        
        if op_type == "add":
            label = f"Node-{random.randint(0, 100000)}"
            nid = ms.remember(label)
            node_ids.append(nid)
        
        elif op_type == "connect":
            if len(node_ids) >= 2:
                try:
                    idx1 = random.randint(0, len(node_ids) - 1)
                    idx2 = random.randint(0, len(node_ids) - 1)
                    ms.connect_knowledge(f"Node-{idx1}", f"Node-{idx2}")
                except:
                    pass
        
        elif op_type == "query":
            ms.recall(f"Node-{random.randint(0, 1000)}", k=3)
        
        elif op_type == "delete" and len(node_ids) > 0:
            idx = random.randint(0, len(node_ids) - 1)
            try:
                ms.forget(node_ids[idx])
                node_ids.pop(idx)
            except:
                pass
        
        if (i + 1) % 2000 == 0:
            print(f"   已完成 {i+1} 操作")
    
    elapsed = time.time() - start_time
    
    # 检查内存
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    
    print(f"\n操作完成：{operations} 次, {elapsed:.2f}s")
    print(f"当前节点数：{len(ms.store.graph.nodes)}")
    print(f"当前边数：{len(ms.store.graph.edges)}")
    
    # 内存泄漏检查
    print("\n内存使用最高的3个位置：")
    for stat in top_stats[:3]:
        print(f"  {stat}")
    
    tracemalloc.stop()
    return True


def test_concurrent_storm():
    """测试2：并发风暴测试 - 查找竞态条件"""
    print("\n" + "=" * 70)
    print("⚡ 测试2：并发风暴 - 竞态条件检查")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./storm_test")
    ms.store.clear_all()
    ms.start_session()
    
    # 先初始化一些节点
    for i in range(100):
        ms.remember(f"Init-{i}")
    
    errors = []
    final_node_count = None
    final_edge_count = None
    
    def writer_thread(tid):
        """疯狂写入线程"""
        try:
            for i in range(500):
                ms.remember(f"Thread-{tid}-Node-{i}")
                ms.connect_knowledge(
                    f"Thread-{tid}-Node-{i}",
                    f"Init-{i % 100}",
                    "related_to"
                )
        except Exception as e:
            errors.append(f"Writer {tid}: {str(e)}")
    
    def reader_thread(tid):
        """疯狂读取线程"""
        try:
            for i in range(1000):
                ms.recall(f"Init-{random.randint(0, 99)}", k=5)
                ms.get_context()
                ms.infer(f"Init-{random.randint(0, 99)}", max_depth=1)
        except Exception as e:
            errors.append(f"Reader {tid}: {str(e)}")
    
    def deleter_thread(tid):
        """疯狂删除线程"""
        try:
            for i in range(300):
                candidates = list(ms.store.graph.nodes.keys())
                if candidates:
                    ms.forget(random.choice(candidates))
        except Exception as e:
            errors.append(f"Deleter {tid}: {str(e)}")
    
    print("启动并发风暴 - 20线程同时访问...")
    start_time = time.time()
    
    all_threads = []
    for i in range(5):
        t = threading.Thread(target=writer_thread, args=(i,))
        all_threads.append(t)
    
    for i in range(10):
        t = threading.Thread(target=reader_thread, args=(i,))
        all_threads.append(t)
    
    for i in range(5):
        t = threading.Thread(target=deleter_thread, args=(i,))
        all_threads.append(t)
    
    for t in all_threads:
        t.start()
    for t in all_threads:
        t.join()
    
    elapsed = time.time() - start_time
    
    print(f"并发风暴耗时：{elapsed:.2f}s")
    print(f"发生错误数：{len(errors)}")
    
    if errors:
        print("\n错误示例：")
        for e in errors[:5]:
            print(f"  {e}")
    
    final_node_count = len(ms.store.graph.nodes)
    final_edge_count = len(ms.store.graph.edges)
    print(f"\n最终状态 - 节点：{final_node_count}, 边：{final_edge_count}")
    
    return len(errors) == 0


def test_data_corruption():
    """测试3：数据完整性与损坏恢复"""
    print("\n" + "=" * 70)
    print("💾 测试3：数据完整性与损坏恢复")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./corrupt_test")
    ms.store.clear_all()
    ms.start_session()
    
    # 创建数据
    ms.connect_knowledge("A", "B", "related_to")
    ms.connect_knowledge("B", "C", "related_to")
    ms.connect_knowledge("C", "A", "related_to")
    
    # 保存原始
    ms.store.save()
    
    # 故意损坏
    graph_file = ms.store.graph_file
    
    print(f"原始文件：{graph_file}")
    
    # 测试1：完整保存/加载
    ms2 = MemorySystem(data_dir="./corrupt_test")
    print(f"正常加载：{len(ms2.store.graph.nodes)} 节点, {len(ms2.store.graph.edges)} 边")
    
    # 测试2：模拟损坏场景 - 创建损坏的JSON
    if graph_file.exists():
        os.unlink(graph_file)
    
    # 尝试加载损坏的（不存在的）
    ms3 = MemorySystem(data_dir="./corrupt_test")
    print(f"损坏后加载：{len(ms3.store.graph.nodes)} 节点, {len(ms3.store.graph.edges)} 边")
    
    return True


def test_extreme_queries():
    """测试4：极端查询负载"""
    print("\n" + "=" * 70)
    print("🔍 测试4：极端查询负载")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./query_test")
    ms.store.clear_all()
    ms.start_session()
    
    # 创建大量节点
    print("创建5000个节点...")
    node_labels = []
    for i in range(5000):
        label = f"Node-{i}"
        ms.remember(label)
        node_labels.append(label)
    
    # 创建链状连接
    print("创建链状连接...")
    for i in range(4999):
        ms.connect_knowledge(f"Node-{i}", f"Node-{i+1}", "next")
    
    # 极端深度推理
    print("执行极端深度推理...")
    start_time = time.time()
    
    results = ms.infer("Node-0", max_depth=500)
    
    elapsed = time.time() - start_time
    print(f"推理结果：{len(results)} 步, 耗时 {elapsed:.2f}s")
    
    if elapsed > 5.0:
        print("⚠️ 警告：推理过慢，可能需要优化！")
    else:
        print("✅ 推理性能可接受")
    
    return elapsed < 5.0


def run_all_extreme_tests():
    """运行所有极端测试"""
    print("\n" + "=" * 70)
    print("🚀 开始第2轮极端压力测试 - 深度缺陷检测")
    print("=" * 70)
    
    tests = [
        ("内存泄漏检测", test_memory_leaks),
        ("并发风暴", test_concurrent_storm),
        ("数据完整性", test_data_corruption),
        ("极端查询", test_extreme_queries)
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = "✅ 成功" if result else "❌ 失败"
        except Exception as e:
            results[name] = f"❌ 异常：{str(e)}"
            import traceback
            traceback.print_exc()
    
    # 最终报告
    print("\n" + "=" * 70)
    print("📊 极端测试报告")
    print("=" * 70)
    for name, status in results.items():
        print(f"  {name}：{status}")
    
    all_ok = all("✅" in v for v in results.values())
    
    print("\n" + "=" * 70)
    if all_ok:
        print("🎉 所有极端测试通过！")
    else:
        print("⚠️ 发现问题，需要修复！")
    print("=" * 70)
    
    return all_ok


if __name__ == "__main__":
    run_all_extreme_tests()
