#!/bin/bash

# Code RAG 文件系统重构脚本
# 将23个模块重命名为长命名，并按9层架构重组

set -e

echo "🚀 开始文件系统重构..."
echo "=========================================="

# 迁移 logger.py -> logging_and_diagnostics.py
echo "📦 迁移: logger.py -> logging_and_diagnostics.py"
cp src/core/logger.py src/code_rag/base_layer/logging_and_diagnostics.py
echo "✅ 完成"

# 迁移 settings.py 和 config.py -> configuration_and_settings.py
echo "📦 迁移: settings.py + config.py -> configuration_and_settings.py"
cat src/core/settings.py src/core/config.py > src/code_rag/base_layer/configuration_and_settings.py
echo "✅ 完成"

# 迁移 security.py -> security_and_access_control.py
echo "📦 迁移: security.py -> security_and_access_control.py"
cp src/core/security.py src/code_rag/base_layer/security_and_access_control.py
echo "✅ 完成"

# 迁移 monitor.py -> performance_monitoring.py
echo "📦 迁移: monitor.py -> performance_monitoring.py"
cp src/core/monitor.py src/code_rag/base_layer/performance_monitoring.py
echo "✅ 完成"

# 迁移 parser.py -> code_parser_and_document_processor.py
echo "📦 迁移: parser.py -> code_parser_and_document_processor.py"
cp src/core/parser.py src/code_rag/data_layer/code_parser_and_document_processor.py
echo "✅ 完成"

# 迁移 io.py -> data_input_and_output_handler.py
echo "📦 迁移: io.py -> data_input_and_output_handler.py"
cp src/core/io.py src/code_rag/data_layer/data_input_and_output_handler.py
echo "✅ 完成"

# 迁移 cache.py -> caching_and_in_memory_cache.py
echo "📦 迁移: cache.py -> caching_and_in_memory_cache.py"
cp src/core/cache.py src/code_rag/data_layer/caching_and_in_memory_cache.py
echo "✅ 完成"

# 迁移 backup.py -> backup_and_version_control.py
echo "📦 迁移: backup.py -> backup_and_version_control.py"
cp src/core/backup.py src/code_rag/data_layer/backup_and_version_control.py
echo "✅ 完成"

# 迁移 data_layer.py -> data_repository_and_storage.py
echo "📦 迁移: data_layer.py -> data_repository_and_storage.py"
cp src/core/data_layer.py src/code_rag/data_layer/data_repository_and_storage.py
echo "✅ 完成"

# 迁移 processing_layer.py -> processing modules
echo "📦 迁移: processing_layer.py -> text_processing_and_tokenization.py"
cp src/core/processing_layer.py src/code_rag/processing_layer/text_processing_and_tokenization.py
echo "✅ 完成"

# 迁移 bm25.py -> bm25_search_engine.py
echo "📦 迁移: bm25.py -> bm25_search_engine.py"
cp src/core/bm25.py src/code_rag/search_layer/bm25_search_engine.py
echo "✅ 完成"

# 迁移 rag.py -> rag_core_engine.py
echo "📦 迁移: rag.py -> rag_core_engine.py"
cp src/core/rag.py src/code_rag/rag_engine/rag_core_engine.py
echo "✅ 完成"

# 迁移 retrieval.py -> retrieval_pipeline_processor.py
echo "📦 迁移: retrieval.py -> retrieval_pipeline_processor.py"
cp src/core/retrieval.py src/code_rag/rag_engine/retrieval_pipeline_processor.py
echo "✅ 完成"

# 迁移 llm.py -> language_model_and_answer_generator.py
echo "📦 迁移: llm.py -> language_model_and_answer_generator.py"
cp src/core/llm.py src/code_rag/rag_engine/language_model_and_answer_generator.py
echo "✅ 完成"

# 迁移 semantic_evaluator.py -> semantic_search_evaluator.py
echo "📦 迁移: semantic_evaluator.py -> semantic_search_evaluator.py"
cp src/core/semantic_evaluator.py src/code_rag/rag_engine/semantic_search_evaluator.py
echo "✅ 完成"

# 迁移 test_data.py -> test_data_and_evaluation_pairs.py
echo "📦 迁移: test_data.py -> test_data_and_evaluation_pairs.py"
cp src/core/test_data.py src/code_rag/rag_engine/test_data_and_evaluation_pairs.py
echo "✅ 完成"

# 迁移 service_layer.py -> service modules
echo "📦 迁移: service_layer.py -> service modules"
cp src/core/service_layer.py src/code_rag/service_layer/service_layer.py
echo "✅ 完成"

# 迁移 middleware_layer.py -> middleware modules
echo "📦 迁移: middleware_layer.py -> middleware modules"
cp src/core/middleware_layer.py src/code_rag/middleware_layer/middleware_layer.py
echo "✅ 完成"

# 迁移 prometheus_metrics.py -> prometheus_metrics_collector.py
echo "📦 迁移: prometheus_metrics.py -> prometheus_metrics_collector.py"
cp src/core/prometheus_metrics.py src/code_rag/observability_layer/prometheus_metrics_collector.py
echo "✅ 完成"

# 迁移 evaluator.py -> metrics_and_evaluation_reporter.py
echo "📦 迁移: evaluator.py -> metrics_and_evaluation_reporter.py"
cp src/core/evaluator.py src/code_rag/observability_layer/metrics_and_evaluation_reporter.py
echo "✅ 完成"

echo "=========================================="
echo "✅ 文件迁移完成！"
echo ""
echo "📊 迁移统计："
echo "   - base_layer: 4个模块"
echo "   - data_layer: 5个模块"
echo "   - processing_layer: 1个模块"
echo "   - search_layer: 1个模块"
echo "   - rag_engine: 5个模块"
echo "   - service_layer: 1个模块"
echo "   - middleware_layer: 1个模块"
echo "   - observability_layer: 2个模块"
echo "   总计: 20个模块"
