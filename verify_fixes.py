"""
验证系统修复！
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.code_rag.kg_v2_enhanced import MemorySystem


def verify_deletion_fix():
    print("=" * 70)
    print("✅ 验证 1：级联删除修复")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./verify_delete")
    ms.store.clear_all()
    ms.start_session()
    
    ms.connect_knowledge("A", "B", "related_to")
    ms.connect_knowledge("B", "C", "related_to")
    ms.connect_knowledge("C", "A", "related_to")
    
    init_nodes = len(ms.store.graph.nodes)
    init_edges = len(ms.store.graph.edges)
    
    print(f"初始: {init_nodes} 节点, {init_edges} 边")
    
    # 找节点 A 并删除
    a_nodes = ms.store.graph.find_nodes_by_label("A")
    if a_nodes:
        ms.forget(a_nodes[0].id)
        
        remaining_nodes = len(ms.store.graph.nodes)
        remaining_edges = len(ms.store.graph.edges)
        
        print(f"删除后: {remaining_nodes} 节点, {remaining_edges} 边")
        
        if remaining_nodes == 2 and remaining_edges == 0:
            print("✅ 级联删除正确！")
            return True
        else:
            print("❌ 删除级联有问题！")
            return False


def verify_inference_depth():
    print("\n" + "=" * 70)
    print("✅ 验证 2：深度推理功能")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./verify_inference")
    ms.store.clear_all()
    ms.start_session()
    
    ms.connect_knowledge("A", "B", "related_to")
    ms.connect_knowledge("B", "C", "related_to")
    ms.connect_knowledge("C", "D", "related_to")
    
    # 测试深度 3
    results = ms.infer("A", max_depth=3)
    print(f"深度推理结果: {len(results)} 步")
    
    for r in results:
        print(f"  {r}")
    
    if len(results) >= 3:
        print("✅ 深度推理正常！")
        return True
    return False


def verify_concurrent_access():
    print("\n" + "=" * 70)
    print("✅ 验证 3：线程安全访问")
    print("=" * 70)
    
    import threading
    ms = MemorySystem(data_dir="./verify_concurrent")
    ms.store.clear_all()
    ms.start_session()
    
    # 初始化一点数据
    ms.connect_knowledge("A", "B", "related_to")
    ms.connect_knowledge("B", "C", "related_to")
    
    errors = []
    
    def thread_worker(thread_id):
        try:
            for i in range(50):
                ms.recall("A", k=3)
                ms.get_context()
        except Exception as e:
            errors.append(f"线程 {thread_id}: {e}")
    
    threads = [threading.Thread(target=thread_worker, args=(i,)) for i in range(10)]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    print(f"线程错误数: {len(errors)}")
    
    if len(errors) == 0:
        print("✅ 并发安全正常！")
        return True
    return False


def verify_all_fixes():
    print("\n" + "=" * 70)
    print("🚀 完整验证测试")
    print("=" * 70)
    
    all_ok = True
    
    all_ok &= verify_deletion_fix()
    all_ok &= verify_inference_depth()
    all_ok &= verify_concurrent_access()
    
    print("\n" + "=" * 70)
    if all_ok:
        print("🎉 所有验证通过！系统增强成功！")
    else:
        print("❌ 还有问题需要解决")
    print("=" * 70)
    return all_ok


if __name__ == "__main__":
    verify_all_fixes()
