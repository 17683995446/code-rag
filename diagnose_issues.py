"""
问题发现与诊断工具
主动发现系统缺陷！
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.code_rag.memory_system import MemorySystem


def find_keyword_indexing_bug():
    """发现关键词索引不工作的问题"""
    print("=" * 70)
    print("🔍 问题 1：关键词索引不工作？")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./debug_test1")
    ms.store.clear_all()
    ms.start_session()
    
    ms.remember("Python 是一种编程语言", {"source": "test"})
    ms.remember("Django 是 Python 的 Web 框架", {"source": "test"})
    
    print(f"节点数: {len(ms.store.graph.nodes)}")
    print(f"关键词索引: {dict(ms.store.memory_index)}")
    print(f"关键词数量: {len(ms.store.memory_index)}")
    
    bug_found = False
    if len(ms.store.memory_index) == 0:
        print("❌ 发现问题：关键词索引为空！")
        bug_found = True
    else:
        print("✅ 关键词索引正常")
    
    return bug_found


def test_delete_cascading():
    """测试删除节点时是否正确级联删除相关边和索引"""
    print("\n" + "=" * 70)
    print("🔍 问题 2：删除级联正确吗？")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./debug_test2")
    ms.store.clear_all()
    ms.start_session()
    
    ms.connect_knowledge("A", "B", "related_to")
    ms.connect_knowledge("B", "C", "related_to")
    
    initial_nodes = len(ms.store.graph.nodes)
    initial_edges = len(ms.store.graph.edges)
    
    print(f"初始状态: {initial_nodes} 节点, {initial_edges} 边")
    
    a_nodes = ms.store.graph.find_nodes_by_label("A")
    if a_nodes:
        node_id = a_nodes[0].id
        ms.forget(node_id)
        
        remaining_nodes = len(ms.store.graph.nodes)
        remaining_edges = len(ms.store.graph.edges)
        
        print(f"删除后: {remaining_nodes} 节点, {remaining_edges} 边")
        
        bugs = []
        
        if remaining_edges != 0:
            bugs.append("❌ 边没有完全删除！")
        
        if len(bugs) > 0:
            return True
    
    return False


def test_inference_completeness():
    """测试推理完整性"""
    print("\n" + "=" * 70)
    print("🔍 问题 3：推理完整吗？")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./debug_test3")
    ms.store.clear_all()
    ms.start_session()
    
    # 创建 A -> B -> C 的关系链
    ms.connect_knowledge("A", "B", "related_to")
    ms.connect_knowledge("B", "C", "related_to")
    
    results = ms.infer("A")
    
    print(f"推理结果: {len(results)} 个关系")
    
    bug_found = False
    if len(results) == 0:
        print("❌ 没有得到推理结果！")
        bug_found = True
    
    return bug_found


def test_large_labels_and_unicode():
    """测试大标签和 Unicode 处理"""
    print("\n" + "=" * 70)
    print("🔍 问题 4：大标签和 Unicode 处理？")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./debug_test4")
    ms.store.clear_all()
    ms.start_session()
    
    try:
        long_label = "X" * 1000
        ms.remember(long_label)
        
        unicode_labels = ["数学符号∑√π", "中文测试", "日本語テスト"]
        for label in unicode_labels:
            ms.remember(label)
        
        print("✅ 大标签和 Unicode 处理正常")
        return False
    except Exception as e:
        print(f"❌ 问题：{e}")
        return True


def test_empty_queries():
    """测试空查询边界情况"""
    print("\n" + "=" * 70)
    print("🔍 问题 5：边界情况处理？")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./debug_test5")
    ms.store.clear_all()
    ms.start_session()
    
    bugs = []
    
    # 空字符串查询
    try:
        result = ms.recall("", k=5)
        print(f"  空查询返回 {len(result)} 结果")
    except Exception as e:
        bugs.append(f"空查询崩溃: {e}")
    
    # 不存在的节点推理
    try:
        result = ms.infer("不存在的知识")
        print(f"  不存在知识推理返回 {len(result)} 结果")
    except Exception as e:
        bugs.append(f"不存在知识推理崩溃: {e}")
    
    # 重复记忆
    try:
        ms.remember("重复测试")
        ms.remember("重复测试")
        ms.remember("重复测试")
        print(f"  重复记忆正常")
    except Exception as e:
        bugs.append(f"重复记忆崩溃: {e}")
    
    if bugs:
        print("❌ 发现边界情况问题：")
        for b in bugs:
            print(f"  - {b}")
        return True
    else:
        print("✅ 边界情况处理正常")
        return False


def test_graph_export_integrity():
    """测试图导出完整性"""
    print("\n" + "=" * 70)
    print("🔍 问题 6：导出完整性？")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./debug_test6")
    ms.store.clear_all()
    ms.start_session()
    
    # 创建复杂图
    ms.connect_knowledge("A", "B", "is_a")
    ms.connect_knowledge("B", "C", "uses")
    ms.connect_knowledge("C", "A", "related_to")
    
    json_str = ms.store.graph.to_json()
    
    # 重新导入
    from src.code_rag.knowledge_graph import KnowledgeGraph
    new_graph = KnowledgeGraph.from_json(json_str)
    
    orig_nodes = len(ms.store.graph.nodes)
    orig_edges = len(ms.store.graph.edges)
    new_nodes = len(new_graph.nodes)
    new_edges = len(new_graph.edges)
    
    print(f"原始: {orig_nodes} 节点, {orig_edges} 边")
    print(f"重新导入: {new_nodes} 节点, {new_edges} 边")
    
    if orig_nodes != new_nodes or orig_edges != new_edges:
        print("❌ 导出/导入数据不一致！")
        return True
    
    print("✅ 导出完整性正常")
    return False


def run_all_diagnostics():
    """运行所有问题诊断"""
    print("=" * 70)
    print("🔧 全面系统诊断 - 问题发现！")
    print("=" * 70)
    
    all_bugs = []
    
    all_bugs.append(("关键词索引", find_keyword_indexing_bug()))
    all_bugs.append(("删除级联", test_delete_cascading()))
    all_bugs.append(("推理完整性", test_inference_completeness()))
    all_bugs.append(("大标签/Unicode", test_large_labels_and_unicode()))
    all_bugs.append(("边界情况", test_empty_queries()))
    all_bugs.append(("导出完整性", test_graph_export_integrity()))
    
    print("\n" + "=" * 70)
    print("📋 诊断报告")
    print("=" * 70)
    
    bug_count = 0
    for bug_name, found in all_bugs:
        status = "❌" if found else "✅"
        print(f"  {status} {bug_name}")
        if found:
            bug_count += 1
    
    print(f"\n发现 {bug_count} 个问题！")
    return [name for name, found in all_bugs if found]


if __name__ == "__main__":
    issues = run_all_diagnostics()
    print("\n准备修复问题！")
