#!/usr/bin/env python3
"""
Data Layer 验证测试
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

print("=" * 80)
print("  Data Layer 模块验证测试")
print("=" * 80)

try:
    print("\n1. 测试导入 code_parser_and_document_processor ...")
    from code_rag.data_layer import CodeParser, CodeLanguage, CodeChunk, ParsedDocument
    print("   ✅ 成功导入")

    # 测试 CodeParser
    parser = CodeParser()
    test_file = project_root / "src" / "code_rag" / "base_layer" / "logging_and_diagnostics.py"
    doc = parser.parse_file(str(test_file))
    print(f"   ✅ 解析文件成功: {len(doc.chunks)} 个代码块")

    for i, chunk in enumerate(doc.chunks[:3]):
        print(f"     - Chunk {i+1}: {chunk.chunk_type}")

except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n2. 测试导入 caching_and_in_memory_cache ...")
    from code_rag.data_layer import LRUCache, TTLCache
    print("   ✅ 成功导入")

    # 测试 LRUCache
    cache = LRUCache(max_size=10)
    cache.set("test1", "value1")
    cache.set("test2", "value2")
    assert cache.get("test1") == "value1"
    print(f"   ✅ LRUCache 正常工作")

    stats = cache.stats()
    print(f"   - 缓存统计: {stats}")

except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n3. 测试导入 data_input_and_output_handler ...")
    from code_rag.data_layer import DataExporter, DataImporter
    print("   ✅ 成功导入")

    # 测试简单导出
    exporter = DataExporter()
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        test_data = {"name": "Test", "data": [1, 2, 3]}
        result = exporter.export_json(test_data, f.name)
        print(f"   ✅ 导出功能正常: {result}")
    import os
    os.unlink(f.name)

except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n4. 测试导入 backup_and_version_control ...")
    from code_rag.data_layer import BackupManager, VersionControl
    print("   ✅ 成功导入")

    # 初始化备份管理器
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        backup_manager = BackupManager(backup_dir=str(Path(tmp_dir) / "backups"))
        print(f"   ✅ 备份管理器初始化成功")

    with tempfile.TemporaryDirectory() as tmp_dir:
        version_control = VersionControl(version_dir=str(Path(tmp_dir) / "versions"))
        print(f"   ✅ 版本控制器初始化成功")

except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n5. 测试导入 data_repository_and_storage ...")
    from code_rag.data_layer import DataStore, DocumentStore, VectorStore
    from code_rag.data_layer import MemoryDataStore, FileDataStore, JSONDataStore
    from code_rag.data_layer import DataRepository, create_data_repository
    from code_rag.data_layer import DocumentDAO, MetadataDAO
    print("   ✅ 成功导入所有存储类")

    # 测试内存存储
    memory_store = MemoryDataStore()
    memory_store.set("key1", "value1")
    assert memory_store.get("key1") == "value1"
    print(f"   ✅ MemoryDataStore 正常工作")

    # 测试数据仓库
    repo = create_data_repository()
    print(f"   ✅ DataRepository 创建成功")

    # 测试 DAO
    doc_dao = DocumentDAO(repo.memory_store)
    doc_dao.save_document("doc1", "This is a test document")
    assert doc_dao.load_document("doc1") == "This is a test document"
    print(f"   ✅ DocumentDAO 正常工作")

except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("  所有 Data Layer 模块验证完成")
print("=" * 80)
