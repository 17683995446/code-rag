# Code RAG 文件系统重构方案

## 当前问题

### 1. 命名过短，不够描述性
```
当前: backup.py, bm25.py, cache.py, config.py, io.py, llm.py, rag.py...
问题: 无法从名称理解模块功能，需要打开文件查看
```

### 2. 目录结构混乱
```
当前: 所有23个模块都堆在 src/core/ 目录下
问题: 无法快速定位功能模块
```

### 3. 模块职责不够清晰
```
问题: 部分模块功能重叠，如 cache.py 和 memory 相关
```

---

## 重构方案

### 新目录结构（按功能分层）

```
src/code_rag/
├── __init__.py                      # 统一导出
│
├── base_layer/                      # 第一层：基础支撑
│   ├── __init__.py
│   ├── logging_and_diagnostics.py       # 日志记录与诊断
│   ├── configuration_and_settings.py     # 配置与设置管理
│   ├── security_and_access_control.py    # 安全与访问控制
│   └── performance_monitoring.py         # 性能监控
│
├── data_layer/                      # 第二层：数据管理
│   ├── __init__.py
│   ├── code_parser_and_document_processor.py    # 代码解析与文档处理
│   ├── data_input_and_output_handler.py        # 数据导入导出
│   ├── caching_and_in_memory_cache.py          # 缓存与内存存储
│   ├── backup_and_version_control.py            # 备份与版本控制
│   └── data_repository_and_storage.py          # 数据仓库与存储
│
├── processing_layer/                # 第三层：数据处理
│   ├── __init__.py
│   ├── text_processing_and_tokenization.py      # 文本处理与分词
│   ├── vector_processing_and_normalization.py   # 向量处理与归一化
│   ├── data_transformation_and_validation.py    # 数据转换与验证
│   └── encoding_and_decoding.py                # 编码与解码
│
├── search_layer/                    # 第四层：搜索引擎
│   ├── __init__.py
│   ├── bm25_search_engine.py               # BM25关键词搜索
│   ├── vector_search_and_similarity.py     # 向量搜索与相似度
│   ├── hybrid_search_and_fusion.py        # 混合搜索与融合
│   └── retrieval_pipeline_processor.py     # 检索流水线处理
│
├── rag_engine/                      # 第五层：RAG核心
│   ├── __init__.py
│   ├── rag_core_engine.py                   # RAG核心引擎
│   ├── embedding_and_vectorization.py       # 向量化与嵌入
│   ├── retrieval_augmented_generation.py   # 检索增强生成
│   ├── query_preprocessing_and_reranking.py # 查询预处理与重排序
│   └── semantic_search_evaluator.py         # 语义搜索评估
│
├── service_layer/                   # 第六层：业务服务
│   ├── __init__.py
│   ├── document_service.py                  # 文档服务
│   ├── search_service.py                   # 搜索服务
│   ├── embedding_service.py                 # 向量化服务
│   ├── rag_business_service.py              # RAG业务服务
│   └── service_manager_and_composer.py      # 服务管理与组合
│
├── middleware_layer/                # 第七层：中间件
│   ├── __init__.py
│   ├── request_logging_middleware.py       # 请求日志中间件
│   ├── timing_and_performance_middleware.py # 计时中间件
│   ├── validation_and_sanitization.py       # 验证与清洗
│   ├── rate_limiting_and_throttling.py       # 限流与节流
│   ├── authentication_and_authorization.py  # 认证与授权
│   ├── cors_and_cross_origin.py             # CORS跨域
│   ├── compression_and_encoding.py          # 压缩与编码
│   └── middleware_pipeline_composer.py       # 中间件管道组合
│
├── observability_layer/             # 第八层：可观测性
│   ├── __init__.py
│   ├── prometheus_metrics_collector.py     # Prometheus指标收集
│   ├── metrics_and_evaluation_reporter.py  # 指标与评估报告
│   └── health_check_and_uptime.py          # 健康检查
│
└── api_layer/                       # 第九层：API接口
    ├── __init__.py
    ├── rest_api_endpoints.py                # REST API端点
    ├── websocket_and_real_time.py           # WebSocket实时通信
    └── api_error_handlers.py                # API错误处理
```

---

## 命名规范对比

### 当前 vs 重构后

| 当前 | 重构后 | 描述 |
|------|--------|------|
| backup.py | backup_and_version_control.py | 备份与版本控制 |
| bm25.py | bm25_search_engine.py | BM25搜索引擎 |
| cache.py | caching_and_in_memory_cache.py | 缓存与内存存储 |
| config.py | configuration_and_settings.py | 配置与设置 |
| evaluator.py | metrics_and_evaluation_reporter.py | 指标与评估 |
| io.py | data_input_and_output_handler.py | 数据IO处理 |
| llm.py | language_model_and_answer_generator.py | LLM与答案生成 |
| logger.py | logging_and_diagnostics.py | 日志与诊断 |
| monitor.py | performance_monitoring.py | 性能监控 |
| parser.py | code_parser_and_document_processor.py | 代码解析 |
| rag.py | rag_core_engine.py | RAG核心引擎 |
| retrieval.py | retrieval_pipeline_processor.py | 检索流水线 |
| security.py | security_and_access_control.py | 安全与访问控制 |
| settings.py | configuration_and_settings.py | 配置（与config合并） |

---

## 模块数量统计

| 层级 | 模块数 | 功能 |
|------|--------|------|
| base_layer | 4 | 基础支撑 |
| data_layer | 5 | 数据管理 |
| processing_layer | 4 | 数据处理 |
| search_layer | 4 | 搜索引擎 |
| rag_engine | 5 | RAG核心 |
| service_layer | 5 | 业务服务 |
| middleware_layer | 8 | 中间件 |
| observability_layer | 3 | 可观测性 |
| api_layer | 3 | API接口 |
| **总计** | **41** | 41个模块 |

---

## 优点

### 1. **见名知意**
```
backup_and_version_control.py  -> 一眼就知道是备份和版本控制
performance_monitoring.py      -> 明确知道是性能监控
language_model_and_answer_generator.py -> 清楚知道是LLM和答案生成
```

### 2. **模块化清晰**
```
8个功能层级，从基础到业务
每层职责单一，边界清晰
方便定位和维护
```

### 3. **扩展性强**
```
新功能只需在对应层级添加模块
不会影响其他层级
```

### 4. **团队协作友好**
```
新成员可以快速定位功能位置
代码审查更高效
```

---

## 实施步骤

### Phase 1: 创建目录结构
```bash
mkdir -p src/code_rag/{base_layer,data_layer,processing_layer,search_layer,rag_engine,service_layer,middleware_layer,observability_layer,api_layer}
```

### Phase 2: 迁移模块
按层级逐个迁移模块文件

### Phase 3: 更新导入
- 更新所有 `__init__.py`
- 更新跨模块引用

### Phase 4: 测试验证
- 单元测试
- 集成测试
- API测试

---

## 是否需要立即执行重构？

请确认：
1. ✅ 同意上述重构方案？
2. ⚠️ 需要调整目录结构？
3. ⚠️ 需要调整命名？

确认后我将立即执行重构！
