"""
快速问题暴露测试！
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.code_rag.kg_v2_enhanced import MemorySystem


def test_concurrent_write_read():
    """发现并发问题！"""
    print("=" * 70)
    print("🔍 并发读/写冲突测试")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./quick_concurrent")
    ms.store.clear_all()
    ms.start_session()
    
    # 初始化
    ms.remember("Init Node")
    
    import threading
    errors = []
    
    def writer():
        try:
            for i in range(50):
                ms.remember(f"Write-{i}")
        except Exception as e:
            errors.append(f"Write err: {e}")
    
    def reader():
        try:
            for i in range(50):
                ms.recall("Init Node", k=2)
        except Exception as e:
            errors.append(f"Read err: {e}")
    
    t1 = threading.Thread(target=writer)
    t2 = threading.Thread(target=reader)
    t3 = threading.Thread(target=reader)
    t4 = threading.Thread(target=writer)
    
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    
    t1.join()
    t2.join()
    t3.join()
    t4.join()
    
    print(f"错误数: {len(errors)}")
    if errors:
        print("\n错误:")
        for e in errors[:5]:
            print(f"  - {e}")
        return False
    else:
        print("✅ 无并发错误")
        return True


def test_rapid_deletion():
    """发现删除性能问题！"""
    print("\n" + "=" * 70)
    print("🔍 快速删除测试")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./quick_delete")
    ms.store.clear_all()
    ms.start_session()
    
    # 创建1000个节点并连接
    node_ids = []
    for i in range(1000):
        node_ids.append(ms.remember(f"DelTest-{i}"))
    
    for i in range(999):
        ms.connect_knowledge(f"DelTest-{i}", f"DelTest-{i+1}", "related_to")
    
    print(f"初始节点数: {len(ms.store.graph.nodes)}, 边数: {len(ms.store.graph.edges)}")
    
    import time
    start = time.time()
    
    # 逐个删除
    for i in range(100):
        try:
            ms.forget(node_ids[i])
        except:
            pass
    
    elapsed = time.time() - start
    print(f"删除100个节点耗时: {elapsed:.3f}s")
    
    if elapsed > 0.5:
        print("⚠️ 删除性能可能需要优化")
        return False
    else:
        print("✅ 删除性能可接受")
        return True


def test_keyword_index_stability():
    """测试关键词索引的稳定性！"""
    print("\n" + "=" * 70)
    print("🔍 关键词索引稳定性测试")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./keyword_test")
    ms.store.clear_all()
    ms.start_session()
    
    ms.remember("Python is great")
    ms.remember("Python is fast")
    ms.remember("Python is easy")
    
    print(f"初始关键词数: {len(ms.store.memory_index)}")
    
    # 多次查找应该稳定
    results1 = ms.recall("Python", k=10)
    results2 = ms.recall("Python", k=10)
    
    print(f"第1次查找: {len(results1)} 结果")
    print(f"第2次查找: {len(results2)} 结果")
    
    if len(results1) != len(results2):
        print("❌ 关键词索引查找不稳定！")
        return False
    
    # 测试删除后的索引
    if results1:
        node_id = results1[0]['id']
        ms.forget(node_id)
        
        results3 = ms.recall("Python", k=10)
        print(f"删除后查找: {len(results3)} 结果")
        
        if len(results3) >= len(results2):
            print("❌ 删除后索引未更新！")
            return False
    
    print("✅ 关键词索引工作正常")
    return True


def run_all_quick_tests():
    print("=" * 70)
    print("🧪 快速问题暴露测试")
    print("=" * 70)
    
    tests = [
        test_concurrent_write_read,
        test_rapid_deletion,
        test_keyword_index_stability
    ]
    
    all_ok = True
    for test in tests:
        try:
            if not test():
                all_ok = False
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            all_ok = False
    
    print("\n" + "=" * 70)
    if all_ok:
        print("✅ 快速检查通过")
    else:
        print("⚠️ 发现问题")
    print("=" * 70)


if __name__ == "__main__":
    run_all_quick_tests()
