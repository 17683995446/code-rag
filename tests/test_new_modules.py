"""
新增模块测试 - 检索算法和数据IO
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import (
    QueryPreprocessor,
    Reranker,
    MultiRetrieval,
    RetrievalPipeline,
    DataExporter,
    DataImporter,
    BatchProcessor,
    DataPipeline,
    export_data,
    import_data
)


def test_query_preprocessor():
    """测试查询预处理器"""
    print("🧪 测试: QueryPreprocessor")

    preprocessor = QueryPreprocessor()

    # 测试基本预处理
    result = preprocessor.preprocess("FAISS vector database")

    assert result is not None
    assert 'tokens' in result
    assert len(result['tokens']) > 0

    print(f"  - 原始查询: {result['original']}")
    print(f"  - 分词结果: {result['tokens']}")
    print(f"  - 扩展词: {result['expanded_tokens']}")

    # 测试同义词扩展
    assert len(result['expanded_tokens']) >= len(result['tokens'])

    print("  ✅ QueryPreprocessor测试通过")
    return True


def test_reranker():
    """测试重排序器"""
    print("🧪 测试: Reranker")

    reranker = Reranker()

    # 创建模拟结果
    class MockResult:
        def __init__(self, text, score):
            self.text = text
            self.score = score

    results = [
        MockResult("FAISS is a vector database", 0.9),
        MockResult("Python tutorial", 0.8),
        MockResult("FAISS implementation guide", 0.7),
    ]

    # 测试重排序
    reranked = reranker.rerank("FAISS database", results, top_k=3)

    assert len(reranked) == 3
    assert reranked[0].text == "FAISS is a vector database"

    print(f"  - 重排序后第一: {reranked[0].text[:30]}")

    print("  ✅ Reranker测试通过")
    return True


def test_multi_retrieval():
    """测试多路召回"""
    print("🧪 测试: MultiRetrieval")

    retriever = MultiRetrieval()

    class MockResult:
        def __init__(self, doc_id, text, score):
            self.doc_id = doc_id
            self.text = text
            self.score = score

    vector_results = [
        MockResult(1, "FAISS database", 0.9),
        MockResult(2, "Vector search", 0.8),
    ]

    keyword_results = [
        MockResult(1, "FAISS database", 0.85),
        MockResult(3, "Database system", 0.75),
    ]

    # 测试多路召回
    combined = retriever.retrieve("FAISS", vector_results, keyword_results, top_k=3)

    assert len(combined) > 0
    print(f"  - 多路召回结果: {len(combined)} 个")

    print("  ✅ MultiRetrieval测试通过")
    return True


def test_retrieval_pipeline():
    """测试检索流水线"""
    print("🧪 测试: RetrievalPipeline")

    pipeline = RetrievalPipeline()

    assert pipeline.query_preprocessor is not None
    assert pipeline.reranker is not None
    assert pipeline.multi_retrieval is not None

    print("  ✅ RetrievalPipeline测试通过")
    return True


def test_data_exporter():
    """测试数据导出器"""
    print("🧪 测试: DataExporter")

    exporter = DataExporter()

    # 测试JSON导出
    data = [
        {"id": 1, "name": "test1", "content": "Hello"},
        {"id": 2, "name": "test2", "content": "World"}
    ]

    output_file = "/tmp/test_export.json"
    success = exporter.export_json(data, output_file)

    assert success == True
    assert Path(output_file).exists()

    # 验证导出内容
    with open(output_file, 'r') as f:
        loaded = json.load(f)
        assert len(loaded) == 2

    print(f"  - JSON导出成功: {output_file}")

    # 测试YAML导出（支持降级）
    yaml_file = "/tmp/test_export.yaml"
    success = exporter.export_yaml(data, yaml_file)
    assert success == True
    # 检查是否是YAML或降级的JSON
    assert Path(yaml_file).exists() or Path(yaml_file.replace('.yaml', '.json')).exists()
    print(f"  - YAML导出成功（支持降级）: {yaml_file}")

    print("  ✅ DataExporter测试通过")
    return True


def test_data_importer():
    """测试数据导入器"""
    print("🧪 测试: DataImporter")

    importer = DataImporter()

    # 测试JSON导入
    data = importer.import_json("/tmp/test_export.json")

    assert data is not None
    assert len(data) == 2
    assert data[0]['name'] == "test1"

    print(f"  - JSON导入成功: {len(data)} 条数据")

    print("  ✅ DataImporter测试通过")
    return True


def test_batch_processor():
    """测试批量处理器"""
    print("🧪 测试: BatchProcessor")

    processor = BatchProcessor(batch_size=2)

    items = list(range(5))
    batches = processor.create_batches(items)

    assert len(batches) == 3
    assert len(batches[0]) == 2
    assert len(batches[1]) == 2
    assert len(batches[2]) == 1

    print(f"  - 创建批次: {len(batches)} 个")
    for i, batch in enumerate(batches):
        print(f"    批次 {i+1}: {batch}")

    # 测试处理函数
    def process_func(batch):
        return [x * 2 for x in batch]

    results = processor.process_in_batches(items, process_func)

    assert len(results) == 5
    assert results == [0, 2, 4, 6, 8]

    print("  ✅ BatchProcessor测试通过")
    return True


def test_data_pipeline():
    """测试数据流水线"""
    print("🧪 测试: DataPipeline")

    pipeline = DataPipeline()

    # 测试格式转换（支持降级）
    success = pipeline.convert_format(
        "/tmp/test_export.json",
        "/tmp/test_export_converted.yaml",
        input_format='json',
        output_format='yaml'
    )

    assert success == True
    # 检查是否是YAML或降级的JSON
    assert (Path("/tmp/test_export_converted.yaml").exists() or 
            Path("/tmp/test_export_converted.json").exists())

    print("  ✅ DataPipeline测试通过")
    return True


def test_convenience_functions():
    """测试便捷函数"""
    print("🧪 测试: 便捷函数")

    # 测试导入
    data = import_data("/tmp/test_export.json", format='json')
    assert data is not None
    print(f"  - import_data: {len(data)} 条")

    # 测试导出
    success = export_data(data, "/tmp/test_export2.json", format='json')
    assert success == True
    print("  ✅ export_data: 成功")

    print("  ✅ 便捷函数测试通过")
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("  🆕 新增模块测试 - 检索算法 & 数据IO")
    print("=" * 70)

    all_passed = True
    tests = [
        ("QueryPreprocessor", test_query_preprocessor),
        ("Reranker", test_reranker),
        ("MultiRetrieval", test_multi_retrieval),
        ("RetrievalPipeline", test_retrieval_pipeline),
        ("DataExporter", test_data_exporter),
        ("DataImporter", test_data_importer),
        ("BatchProcessor", test_batch_processor),
        ("DataPipeline", test_data_pipeline),
        ("便捷函数", test_convenience_functions),
    ]

    for test_name, test_func in tests:
        try:
            print()
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"  ❌ {test_name}测试失败: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("  ✅ 所有新模块测试通过！")
    else:
        print("  ❌ 部分测试失败")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
