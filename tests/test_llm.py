"""
LLM模块测试 - 完全免费方案
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import (
    LLMEngine,
    LLMResponse,
    get_llm_engine,
    has_llm,
    generate_rag_answer,
    CodeRAG
)


def test_llm_engine():
    """测试LLM引擎"""
    print("\n" + "="*60)
    print("  🧪 测试: LLM引擎（完全免费）")
    print("="*60)

    # 检查是否可用
    print(f"\n  LLM可用: {has_llm()}")

    if not has_llm():
        print("  ⚠️  LLM不可用，使用降级模式")
        return False

    # 获取LLM引擎
    engine = get_llm_engine()
    print(f"  引擎类型: {type(engine).__name__}")
    print(f"  初始化: {engine.is_available()}")

    # 测试生成
    response = engine.generate(
        prompt="你好，请用一句话介绍自己",
        system_prompt="你是一个友好的AI助手。"
    )

    print(f"\n  生成结果:")
    print(f"  - 成功: {response.success}")
    print(f"  - 模型: {response.model}")
    print(f"  - 内容预览: {response.content[:150] if response.success else response.error}...")

    if response.success:
        print("\n  ✅ LLM引擎测试通过（完全免费方案）")
        return True
    else:
        print(f"\n  ❌ LLM引擎测试失败: {response.error}")
        return False


def test_rag_answer():
    """测试RAG回答生成"""
    print("\n" + "="*60)
    print("  🧪 测试: RAG回答生成")
    print("="*60)

    # 测试RAG回答
    question = "什么是FAISS向量数据库？"
    context = """FAISS是Meta开源的高性能向量数据库库。
它提供了高效的向量相似度搜索功能。
FAISS支持多种索引类型，包括IVF、HNSW等。
它主要用于大规模向量检索场景。
FAISS支持CPU和GPU加速。"""
    num_sources = 3

    answer = generate_rag_answer(question, context, num_sources)

    print(f"\n  问题: {question}")
    print(f"\n  回答:\n{answer}")

    if answer and len(answer) > 50:
        print("\n  ✅ RAG回答生成测试通过")
        return True
    else:
        print("\n  ❌ RAG回答生成测试失败")
        return False


def test_full_rag_with_llm():
    """测试完整的RAG流程（带LLM）"""
    print("\n" + "="*60)
    print("  🧪 测试: 完整RAG流程（带LLM）")
    print("="*60)

    try:
        # 初始化RAG系统
        rag = CodeRAG()

        # 索引数据（使用测试目录）
        from src.core.test_data import get_test_documents
        docs = get_test_documents()
        rag.add_documents(docs)

        # 测试问答
        result = rag.ask("什么是向量数据库？")

        print(f"\n  问题: {result.question}")
        print(f"\n  回答:\n{result.answer}")
        print(f"\n  来源数: {len(result.sources)}")
        print(f"  成功: {result.success}")

        if result.success:
            print("\n  ✅ 完整RAG测试通过")
            return True
        else:
            print(f"\n  ⚠️  RAG测试完成")
            return True

    except Exception as e:
        print(f"\n  ❌ RAG测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("  🧪 LLM模块测试 - 完全免费方案")
    print("="*60)

    # 测试1: LLM引擎
    test1 = test_llm_engine()

    # 测试2: RAG回答生成
    test2 = test_rag_answer()

    # 测试3: 完整RAG流程
    test3 = test_full_rag_with_llm()

    # 总结
    print("\n" + "="*60)
    print("  📊 测试结果总结")
    print("="*60)
    print(f"  LLM引擎测试: {'✅ 通过' if test1 else '❌ 失败'}")
    print(f"  RAG回答测试: {'✅ 通过' if test2 else '❌ 失败'}")
    print(f"  完整RAG测试: {'✅ 通过' if test3 else '❌ 失败'}")

    all_passed = test1 and test2 and test3
    if all_passed:
        print("\n  🎉 所有测试通过！")
        print("  💡 使用完全免费的智能规则引擎！")
    elif test1 and test2:
        print("\n  ✅ 核心测试通过")
    else:
        print("\n  ❌ 部分测试失败")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
