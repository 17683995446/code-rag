"""
增强的 RAG 评估器 - 使用真实的测试数据集
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import (
    CodeRAG,
    RAGEvaluator,
    SAMPLE_CODE_DATABASE,
    ADDITIONAL_KNOWLEDGE
)
from src.core.logger import get_logger

logger = get_logger(__name__)


def index_test_data(rag_system):
    """
    使用测试数据集索引 RAG 系统
    """
    logger.info("开始索引测试数据...")

    # 合并所有测试数据
    all_data = SAMPLE_CODE_DATABASE + ADDITIONAL_KNOWLEDGE

    # 提取文档内容
    documents = [item['content'] for item in all_data]
    metadatas = [item['metadata'] for item in all_data]

    # 索引文档
    rag_system.pipeline._index_documents(documents, metadatas)

    logger.info(f"索引完成，共 {len(documents)} 个文档")
    return len(documents)


def run_enhanced_evaluation():
    """
    运行增强的 RAG 评估
    """
    print("\n" + "="*70)
    print("  🚀 Code RAG 增强评估系统")
    print("="*70)

    try:
        # 1. 初始化 RAG 系统
        print("\n[1/4] 初始化 RAG 系统...")
        rag = CodeRAG()

        # 2. 索引测试数据
        print("\n[2/4] 索引测试数据...")
        num_docs = index_test_data(rag)
        print(f"  索引了 {num_docs} 个文档")

        # 3. 定义测试查询
        test_queries = [
            {
                'query': 'FAISS 向量数据库',
                'expected_keywords': ['FAISS', '向量数据库', '向量检索'],
                'category': 'knowledge'
            },
            {
                'query': 'LangChain RAG',
                'expected_keywords': ['LangChain', 'RAG', '检索增强生成'],
                'category': 'usage'
            },
            {
                'query': '快速排序算法',
                'expected_keywords': ['快速排序', '排序算法', '算法'],
                'category': 'code'
            },
            {
                'query': '向量检索性能优化',
                'expected_keywords': ['向量检索', '性能优化', 'FAISS', '索引'],
                'category': 'performance'
            },
            {
                'query': 'Sentence-Transformers embedding',
                'expected_keywords': ['Sentence-Transformers', 'embedding', '文本向量化'],
                'category': 'knowledge'
            },
            {
                'query': 'Python 异步编程',
                'expected_keywords': ['异步', 'async', 'Python', '并发'],
                'category': 'code'
            },
            {
                'query': '数据库索引优化',
                'expected_keywords': ['数据库', '索引', 'B-Tree', '向量数据库'],
                'category': 'knowledge'
            },
            {
                'query': 'RAG 系统架构',
                'expected_keywords': ['RAG', '架构', '检索', '生成'],
                'category': 'usage'
            }
        ]

        print(f"\n[3/4] 执行 {len(test_queries)} 个测试查询...")

        # 4. 执行评估
        results = []
        for i, test in enumerate(test_queries, 1):
            query = test['query']
            expected = test['expected_keywords']

            # 执行搜索
            search_results = rag.search(query, k=5)

            # 提取检索到的内容
            retrieved_docs = [r.text for r in search_results]

            # 计算评估指标
            metrics = evaluate_single_query(retrieved_docs, expected)

            # 判断是否通过
            passed = metrics['f1'] > 0.3 and metrics['recall'] > 0.2

            results.append({
                'query': query,
                'category': test['category'],
                'passed': passed,
                'metrics': metrics,
                'num_results': len(search_results)
            })

            status = "✅" if passed else "❌"
            print(f"  {status} [{i}/{len(test_queries)}] {query}")
            print(f"      精确率: {metrics['precision']:.2f}, "
                  f"召回率: {metrics['recall']:.2f}, "
                  f"F1: {metrics['f1']:.2f}")

        # 5. 计算总体指标
        print(f"\n[4/4] 计算评估结果...")

        total_precision = sum(r['metrics']['precision'] for r in results) / len(results)
        total_recall = sum(r['metrics']['recall'] for r in results) / len(results)
        total_f1 = sum(r['metrics']['f1'] for r in results) / len(results)
        passed_count = sum(1 for r in results if r['passed'])

        print("\n" + "="*70)
        print("  📊 增强评估结果")
        print("="*70)
        print(f"\n  总体指标:")
        print(f"    精确率 (Precision):  {total_precision:.2%}")
        print(f"    召回率 (Recall):     {total_recall:.2%}")
        print(f"    F1分数:              {total_f1:.2f}")
        print(f"\n  测试结果:")
        print(f"    总测试数:   {len(results)}")
        print(f"    通过:       {passed_count}")
        print(f"    失败:       {len(results) - passed_count}")
        print(f"    通过率:     {passed_count/len(results):.2%}")

        # 分类统计
        categories = {}
        for r in results:
            cat = r['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'passed': 0}
            categories[cat]['total'] += 1
            if r['passed']:
                categories[cat]['passed'] += 1

        print(f"\n  分类结果:")
        for cat, stats in categories.items():
            print(f"    {cat}: {stats['passed']}/{stats['total']}")

        # 综合得分
        overall_score = (total_precision * 30 + total_recall * 30 +
                       total_f1 * 25 + (passed_count/len(results)) * 15)

        print(f"\n  综合得分: {overall_score:.2f}/100")

        return {
            'precision': total_precision,
            'recall': total_recall,
            'f1': total_f1,
            'passed': passed_count,
            'total': len(results),
            'score': overall_score,
            'categories': categories
        }

    except Exception as e:
        logger.error(f"评估失败: {e}", exc_info=True)
        return None


def evaluate_single_query(retrieved_docs, expected_keywords):
    """
    评估单个查询
    """
    if not retrieved_docs or not expected_keywords:
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0
        }

    # 计算精确率
    matched = 0
    for doc in retrieved_docs:
        doc_lower = doc.lower()
        # 检查是否包含任何关键词
        if any(kw.lower() in doc_lower for kw in expected_keywords):
            matched += 1

    precision = matched / len(retrieved_docs)

    # 计算召回率
    matched_keywords = set()
    for doc in retrieved_docs:
        doc_lower = doc.lower()
        for kw in expected_keywords:
            if kw.lower() in doc_lower:
                matched_keywords.add(kw)

    recall = len(matched_keywords) / len(expected_keywords)

    # F1
    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0

    return {
        'precision': precision,
        'recall': recall,
        'f1': f1
    }


if __name__ == "__main__":
    result = run_enhanced_evaluation()
    if result:
        print("\n" + "="*70)
        print("  ✅ 增强评估完成！")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("  ❌ 评估失败")
        print("="*70)
