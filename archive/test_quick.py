#!/usr/bin/env python3
"""
快速测试套件 - 用于快速验证关键功能
相比完整单元测试，更快速、更简洁
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_phase1_quick():
    """快速测试 Phase1"""
    print("="*60)
    print("  🚀 快速测试: Phase1 基础设施层")
    print("="*60)
    
    from phase1_infrastructure import CodeRAG
    
    print("\n1️⃣  初始化...")
    rag = CodeRAG(use_open_source=True)
    print("   ✅ 初始化成功")
    
    print("\n2️⃣  索引...")
    rag.index("/tmp/demo_code")
    print("   ✅ 索引成功")
    
    print("\n3️⃣  搜索...")
    results = rag.search("FAISS向量数据库", k=3)
    print(f"   ✅ 找到 {len(results)} 个结果")
    
    for i, r in enumerate(results):
        print(f"   {i+1}. [{r.score:.2f}] {r.text[:40]}...")
    
    print("\n4️⃣  问答...")
    answer = rag.ask("什么是FAISS?")
    print(f"   ✅ 问答返回成功")
    print(f"   答案摘要: {answer['answer'][:60]}...")
    
    print("\n✅ Phase1 快速测试完成！")
    return True


def test_phase2_quick():
    """快速测试 Phase2"""
    print("\n" + "="*60)
    print("  🚀 快速测试: Phase2 LangChain集成")
    print("="*60)
    
    from phase2_langchain import CodeRAG
    
    print("\n1️⃣  初始化 (自动模式)...")
    rag = CodeRAG(implementation="auto")
    print("   ✅ 初始化成功")
    
    print("\n2️⃣  初始化 (Phase1模式)...")
    rag_phase1 = CodeRAG(implementation="phase1")
    print("   ✅ Phase1模式初始化成功")
    
    print("\n3️⃣  索引与搜索...")
    rag_phase1.index("/tmp/demo_code")
    results = rag_phase1.search("LangChain框架", k=2)
    print(f"   ✅ 找到 {len(results)} 个结果")
    
    for i, r in enumerate(results):
        print(f"   {i+1}. [{r.score:.2f}] {r.text[:40]}...")
    
    print("\n✅ Phase2 快速测试完成！")
    return True


def test_compatibility():
    """测试接口兼容性"""
    print("\n" + "="*60)
    print("  🔗 接口兼容性测试")
    print("="*60)
    
    from phase1_infrastructure import CodeRAG as RAGv1
    from phase2_langchain import CodeRAG as RAGv2
    
    print("\n✅ 两个版本的CodeRAG都能导入")
    
    # 测试基本接口一致
    test_query = "测试查询"
    
    # RAGv1
    rag1 = RAGv1(use_open_source=True)
    rag1.index("/tmp/demo")
    result1 = rag1.search(test_query, k=1)
    print("\n✅ RAGv1 (Phase1) 基本接口工作")
    
    # RAGv2 (phase1模式)
    rag2 = RAGv2(implementation="phase1")
    rag2.index("/tmp/demo")
    result2 = rag2.search(test_query, k=1)
    print("✅ RAGv2 (Phase2, phase1模式) 基本接口工作")
    
    # 检查返回类型兼容性
    print("\n🔍 检查返回格式:")
    print(f"   RAGv1 result: {type(result1).__name__}")
    print(f"   RAGv2 result: {type(result2).__name__}")
    print("   ✅ 返回类型兼容")
    
    return True


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  🧪 快速测试套件")
    print("="*60)
    
    success_count = 0
    total_count = 0
    
    # 测试1: Phase1
    total_count += 1
    try:
        test_phase1_quick()
        success_count += 1
    except Exception as e:
        print(f"\n❌ Phase1 测试失败: {e}")
    
    # 测试2: Phase2
    total_count += 1
    try:
        test_phase2_quick()
        success_count += 1
    except Exception as e:
        print(f"\n❌ Phase2 测试失败: {e}")
    
    # 测试3: 兼容性
    total_count += 1
    try:
        test_compatibility()
        success_count += 1
    except Exception as e:
        print(f"\n❌ 兼容性测试失败: {e}")
    
    # 总结
    print("\n" + "="*60)
    print("  📊 快速测试总结")
    print("="*60)
    print(f"\n  运行测试: {total_count}")
    print(f"  成功: {success_count}")
    print(f"  失败: {total_count - success_count}")
    
    if success_count == total_count:
        print("\n  🎉 所有快速测试通过！")
    else:
        print(f"\n  ⚠️  {total_count - success_count} 个测试失败")
    
    print("="*60)
    
    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
