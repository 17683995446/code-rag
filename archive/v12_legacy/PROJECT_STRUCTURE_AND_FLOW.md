# Code RAG v11.0 - 项目结构和全流程说明

## 📁 目录结构

```
code-rag/
├── src/
│   └── code_rag/                              # 主源码目录
│       ├── __init__.py
│       │
│       ├── base_layer/                         # 第1层：基础层（基础设施）
│       │   ├── __init__.py
│       │   ├── logging_and_diagnostics.py     # 日志和诊断系统
│       │   ├── configuration_and_settings.py   # 配置和设置管理
│       │   ├── security_and_access_control.py  # 安全和访问控制
│       │   └── performance_monitoring.py       # 性能监控
│       │
│       ├── data_layer/                         # 第2层：数据层（数据处理）
│       │   ├── __init__.py
│       │   ├── code_parser_and_document_processor.py  # 代码解析和文档处理
│       │   ├── data_input_and_output_handler.py       # 数据输入输出
│       │   ├── data_repository_and_storage.py         # 数据存储和仓库
│       │   ├── caching_and_in_memory_cache.py         # 缓存系统
│       │   └── backup_and_version_control.py          # 备份和版本控制
│       │
│       ├── processing_layer/                   # 第3层：处理层（文本处理）
│       │   ├── __init__.py
│       │   └── text_processing_and_tokenization.py   # 文本处理和分词
│       │
│       ├── search_layer/                       # 第4层：搜索层（检索引擎）
│       │   ├── __init__.py
│       │   └── bm25_search_engine.py           # BM25 搜索引擎
│       │
│       ├── rag_engine/                         # 第5层：RAG引擎层（核心业务）
│       │   ├── __init__.py
│       │   ├── embedding_production.py         # 生产级 Embedding 引擎
│       │   ├── vector_index_production.py      # 生产级向量索引
│       │   ├── llm_production.py               # 多后端 LLM 引擎
│       │   ├── rag_core_engine.py              # RAG 核心引擎
│       │   ├── retrieval_pipeline_processor.py # 检索管道处理器
│       │   ├── semantic_search_evaluator.py    # 语义搜索评估器
│       │   ├── test_data_and_evaluation_pairs.py  # 测试数据和评估对
│       │   └── language_model_and_answer_generator.py  # 语言模型和答案生成
│       │
│       ├── service_layer/                      # 第6层：服务层（业务服务）
│       │   ├── __init__.py
│       │   └── service_layer.py                # 服务层实现
│       │
│       ├── middleware_layer/                   # 第7层：中间件层（横切关注点）
│       │   ├── __init__.py
│       │   └── middleware_layer.py             # 中间件实现
│       │
│       ├── observability_layer/                # 第8层：可观测性层（监控）
│       │   ├── __init__.py
│       │   ├── metrics_and_evaluation_reporter.py  # 指标和评估报告
│       │   └── prometheus_metrics_collector.py      # Prometheus 指标收集
│       │
│       └── api_layer/                          # 第9层：API层（对外接口）
│           ├── __init__.py
│           ├── rest_api_endpoints.py           # REST API 端点
│           └── error_handlers.py               # 错误处理器
│
├── tests/                                      # 测试目录
│   ├── test_complete_v11.py                    # v11 完整测试套件
│   └── ... (其他测试文件)
│
├── data/                                       # 数据目录
│   ├── auth/
│   ├── keys/
│   ├── version_history/
│   └── version_tags/
│
├── test_data/                                  # 测试数据
├── test_data_index/                           # 测试索引数据
├── test_prod_index/                           # 生产测试索引
│
├── archive/                                    # 归档（旧版本）
│
├── demo_end_to_end.py                          # 端到端演示
├── demo_github_project.py                      # GitHub 项目演示
├── test_large_github_project.py                # 大型 GitHub 项目测试
├── test_complete_v11.py                        # 完整测试
├── v11_final_evaluation.py                     # 最终评估
├── fix_imports.py                              # 导入修复脚本
├── main.py                                     # 主入口
├── requirements.txt                            # 依赖
├── README.md
└── (其他文档文件)
```

---

## ⏱️ 全流程时序说明

### 流程一：项目索引流程

```
用户输入 → [1] 数据层 → [2] 处理层 → [3] 搜索层/RAG引擎 → 索引存储
     |         |            |             |
     |         |            |             └─ 向量化
     |         |            └─ 文本分块
     |         └─ 代码解析
     └─ 文件扫描/API调用
```

#### 详细步骤：

**步骤 1：数据输入（data_layer）**
- 扫描代码库：[data_input_and_output_handler.py](file:///workspace/code-rag/src/code_rag/data_layer/data_input_and_output_handler.py)
- 解析代码文件：[code_parser_and_document_processor.py](file:///workspace/code-rag/src/code_rag/data_layer/code_parser_and_document_processor.py)
  - 识别编程语言（Python/JavaScript/Java等）
  - 解析函数、类、模块
  - 生成代码块

**步骤 2：文本处理（processing_layer）**
- 代码分块：[text_processing_and_tokenization.py](file:///workspace/code-rag/src/code_rag/processing_layer/text_processing_and_tokenization.py)
- 文本清洗和预处理
- 可选：缓存中间结果

**步骤 3：索引构建**
- BM25 索引：[bm25_search_engine.py](file:///workspace/code-rag/src/code_rag/search_layer/bm25_search_engine.py)
- Embedding 向量化：[embedding_production.py](file:///workspace/code-rag/src/code_rag/rag_engine/embedding_production.py)
- 向量索引：[vector_index_production.py](file:///workspace/code-rag/src/code_rag/rag_engine/vector_index_production.py)

**步骤 4：存储**
- 元数据和索引持久化：[data_repository_and_storage.py](file:///workspace/code-rag/src/code_rag/data_layer/data_repository_and_storage.py)
- 可选：备份和版本控制

---

### 流程二：查询检索流程

```
用户查询 → [1] 安全验证 → [2] 查询处理 → [3] 检索 → [4] 排序 → [5] LLM → 回答
     |           |              |           |        |       |
     |           |              |           |        |       └─ 生成答案
     |           |              |           |        └─ 结果融合
     |           |              |           └─ 向量搜索 + BM25
     |           |              └─ 向量化
     |           └─ 输入验证
     └─ 速率限制
```

#### 详细步骤：

**步骤 1：安全检查（base_layer）**
- 速率限制：[security_and_access_control.py](file:///workspace/code-rag/src/code_rag/base_layer/security_and_access_control.py)
- 输入验证：[InputValidator](file:///workspace/code-rag/src/code_rag/base_layer/security_and_access_control.py)
- 访问控制

**步骤 2：查询处理**
- 查询预处理：[text_processing_and_tokenization.py](file:///workspace/code-rag/src/code_rag/processing_layer/text_processing_and_tokenization.py)
- 向量化：[ProductionEmbeddingEngine](file:///workspace/code-rag/src/code_rag/rag_engine/embedding_production.py)

**步骤 3：检索**
- 混合搜索：[HybridSearch](file:///workspace/code-rag/src/code_rag/search_layer/bm25_search_engine.py)
  - BM25 关键词搜索
  - 向量语义搜索
- 检索管道：[retrieval_pipeline_processor.py](file:///workspace/code-rag/src/code_rag/rag_engine/retrieval_pipeline_processor.py)

**步骤 4：结果排序和过滤**
- 相关性重排
- 结果合并和去重
- 阈值过滤

**步骤 5：LLM 答案生成**
- 上下文构建
- LLM 调用：[MultiLLMEngine](file:///workspace/code-rag/src/code_rag/rag_engine/llm_production.py)
- 答案生成和格式化

---

### 流程三：完整端到端流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Phase 1: Setup & Initialization                                          │
│  ──────────────────────────────────────────────────────────────────────  │
│  1. Load Configuration [get_settings()]                                   │
│  2. Initialize Logging [DiagnosticLogger]                                 │
│  3. Initialize Components (Embedding, Vector, LLM)                        │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  Phase 2: Project Indexing (One-time)                                     │
│  ──────────────────────────────────────────────────────────────────────  │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │ Step 2.1: Scan Project Files                                      │   │
│  │   - DataImporter.scan_directory()                                 │   │
│  │   - Collect .py/.js/.ts/.java/.md files                          │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                              ↓                                          │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │ Step 2.2: Parse and Chunk Code                                    │   │
│  │   - CodeParser.parse_file()                                       │   │
│  │   - Identify functions, classes, modules                          │   │
│  │   - Split into chunks (1000 chars with 200 overlap)               │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                              ↓                                          │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │ Step 2.3: Build Indexes                                           │   │
│  │   - BM25Index.add_documents()                                     │   │
│  │   - ProductionEmbeddingEngine.encode_batch()                      │   │
│  │   - ProductionVectorIndex.add()                                   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  Phase 3: Query Processing (Per Query)                                    │
│  ──────────────────────────────────────────────────────────────────────  │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │ Step 3.1: Security & Validation                                   │   │
│  │   - InputValidator.validate_query()                              │   │
│  │   - RateLimiter.is_allowed()                                      │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                              ↓                                          │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │ Step 3.2: Query Encoding                                          │   │
│  │   - ProductionEmbeddingEngine.encode(query)                       │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                              ↓                                          │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │ Step 3.3: Hybrid Search                                           │   │
│  │   - BM25Search + VectorSearch                                     │   │
│  │   - Score fusion (weighted combination)                           │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                              ↓                                          │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │ Step 3.4: Generate Answer                                         │   │
│  │   - Build context from top results                                │   │
│  │   - MultiLLMEngine.generate()                                     │   │
│  │   - Format final answer with sources                              │   │
│  └───────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  Phase 4: Observability & Metrics                                         │
│  ──────────────────────────────────────────────────────────────────────  │
│  1. Record query latency [PerformanceMonitor]                            │
│  2. Log results [DiagnosticLogger]                                       │
│  3. Collect metrics [MetricsCollector]                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 各层职责说明

### 第1层：Base Layer（基础设施）
- **职责**：提供基础服务，支撑上层
- **包含**：
  - 日志系统：结构化日志、诊断追踪
  - 配置管理：多源配置加载
  - 安全：认证、授权、输入验证
  - 监控：性能指标、系统健康

### 第2层：Data Layer（数据）
- **职责**：数据获取、处理、存储
- **包含**：
  - 代码解析器
  - 数据导入/导出
  - 存储仓库
  - 缓存系统
  - 备份和版本控制

### 第3层：Processing Layer（处理）
- **职责**：文本处理、分块、转换
- **包含**：
  - 文本分块
  - Tokenization
  - 预处理

### 第4层：Search Layer（搜索）
- **职责**：关键词检索
- **包含**：
  - BM25 引擎
  - 混合搜索
  - 结果排序

### 第5层：RAG Engine（核心）
- **职责**：Embedding、向量检索、LLM集成
- **包含**：
  - Embedding 引擎
  - 向量索引
  - LLM 多后端
  - RAG 核心逻辑
  - 检索管道

### 第6层：Service Layer（服务）
- **职责**：业务逻辑封装
- **包含**：服务层接口

### 第7层：Middleware Layer（中间件）
- **职责**：横切关注点
- **包含**：中间件、拦截器

### 第8层：Observability Layer（可观测性）
- **职责**：监控、评估、报告
- **包含**：
  - 指标收集
  - Prometheus 集成
  - 评估报告

### 第9层：API Layer（接口）
- **职责**：对外暴露服务
- **包含**：
  - REST API
  - 错误处理
  - 请求验证

---

## 📋 核心组件文件索引

| 功能 | 文件路径 | 说明 |
|------|---------|------|
| 代码解析 | [code_parser_and_document_processor.py](file:///workspace/code-rag/src/code_rag/data_layer/code_parser_and_document_processor.py) | 解析各种编程语言 |
| Embedding | [embedding_production.py](file:///workspace/code-rag/src/code_rag/rag_engine/embedding_production.py) | 真实 sentence-transformers |
| 向量索引 | [vector_index_production.py](file:///workspace/code-rag/src/code_rag/rag_engine/vector_index_production.py) | FAISS 支持 |
| LLM | [llm_production.py](file:///workspace/code-rag/src/code_rag/rag_engine/llm_production.py) | 多后端支持 |
| BM25 | [bm25_search_engine.py](file:///workspace/code-rag/src/code_rag/search_layer/bm25_search_engine.py) | 关键词搜索 |
| 日志 | [logging_and_diagnostics.py](file:///workspace/code-rag/src/code_rag/base_layer/logging_and_diagnostics.py) | 诊断日志系统 |
| 配置 | [configuration_and_settings.py](file:///workspace/code-rag/src/code_rag/base_layer/configuration_and_settings.py) | 配置管理 |
| API | [rest_api_endpoints.py](file:///workspace/code-rag/src/code_rag/api_layer/rest_api_endpoints.py) | REST 接口 |
| 测试 | [test_complete_v11.py](file:///workspace/code-rag/test_complete_v11.py) | 完整测试套件 |
| 演示 | [demo_end_to_end.py](file:///workspace/code-rag/demo_end_to_end.py) | 端到端演示 |

---

## 🔄 优雅降级机制

当依赖缺失时的降级顺序：

```
1. sentence-transformers 可用 → ProductionEmbeddingEngine
   ↓ (缺失)
2. numpy 可用 → 简单随机向量
   ↓ (缺失)
3. Python 内置 → 纯文本 BM25 搜索

1. FAISS 可用 → ProductionVectorIndex (FAISS)
   ↓ (缺失)
2. numpy 可用 → 内存向量索引
   ↓ (缺失)
3. 无向量搜索 → 只 BM25

1. OpenAI/Anthropic 可用 → LLM API
   ↓ (缺失/无Key)
2. Local LLM 可用 → 本地模型
   ↓ (缺失)
3. SmartRuleEngine → 规则引擎
```

---

## 📊 数据流向图

```
代码文件 (.py/.js/.ts)
    ↓
┌─────────────────────────────┐
│  CodeParser                 │
│  - Detect language          │
│  - Extract functions/classes│
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│  TextChunker                │
│  - Split into chunks        │
│  - Overlap windows          │
└──────────────┬──────────────┘
               ↓
        ┌──────┴──────┐
        ↓             ↓
┌─────────────┐  ┌──────────────────┐
│   BM25 Index│  │ Embedding Engine │
└─────────────┘  └────────┬─────────┘
                          ↓
                  ┌──────────────┐
                  │ Vector Index │
                  └──────────────┘

查询流程:
用户查询 → 安全检查 → 向量化 → 混合搜索 → 结果融合 → LLM → 回答
```

---

## 🎉 运行演示

### 端到端演示
```bash
cd /workspace/code-rag
python demo_end_to_end.py
```

### GitHub 项目测试
```bash
python test_large_github_project.py
```

### 完整测试套件
```bash
python test_complete_v11.py
```

### 最终评估
```bash
python v11_final_evaluation.py
```
