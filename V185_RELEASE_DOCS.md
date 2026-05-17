# Code RAG v18.5 发布文档

## 📚 10个文档点完整索引

1. [快速开始指南](#1-快速开始指南)
2. [用户手册](#2-用户手册)
3. [API参考文档](#3-api参考文档)
4. [性能监控文档](#4-性能监控文档)
5. [用户体验指南](#5-用户体验指南)
6. [架构设计文档](#6-架构设计文档)
7. [部署指南](#7-部署指南)
8. [开发者贡献指南](#8-开发者贡献指南)
9. [版本历史](#9-版本历史)
10. [FAQ常见问题](#10-faq常见问题)

---

## 1. 快速开始指南

### 安装

```bash
# 基础安装
pip install code-rag

# 完全安装（包含性能监控依赖）
pip install code-rag[full]

# 开发安装
pip install -e ".[dev]"
```

### 快速使用

```python
from code_rag.service_layer.enhanced_qa_engine import EnhancedQAEngine

# 初始化
qa_engine = EnhancedQAEngine()

# 查询
response = qa_engine.ask("解释这个函数")
print(response.answer)
```

### 命令行使用

```bash
# 索引目录
code-rag index ./src

# 搜索
code-rag search "find user class"

# 代码审查
code-rag review main.py
```

---

## 2. 用户手册

### 核心功能

| 功能模块 | 说明 | 使用场景 |
|---------|------|---------|
| 代码审查 | 自动审查代码质量 | 代码评审、质量保证 |
| 智能问答 | 自然语言代码查询 | 开发、学习、调试 |
| 上下文理解 | 多轮对话支持 | 持续交互、复杂查询 |
| 性能监控 | 系统性能指标 | 性能优化、问题定位 |
| 用户体验 | 增强的CLI界面 | 日常开发使用 |

### 配置

配置文件位置: `~/.code_rag_config.json`

```json
{
    "enable_color": true,
    "enable_emoji": true,
    "enable_progress": true,
    "theme": "ocean",
    "compact_mode": false
}
```

---

## 3. API参考文档

### 性能监控 API

```python
from code_rag.observability.performance_monitor import (
    PerformanceMonitor, LRUCache, timed_operation
)

# 性能监控
monitor = PerformanceMonitor()

@timed_operation(monitor, "search")
def search(query):
    return "results"

# 缓存
cache = LRUCache(max_size=128)
cache.set("key", "value")
value = cache.get("key")
```

### 用户体验 API

```python
from code_rag.service_layer.enhanced_ux import create_ux

ux = create_ux()

# 打印表格
data = [{"file": "a.py", "lines": 100}]
ux.print_table(data, title="统计")

# 代码高亮
ux.print_code("def add(): return 1 + 2")

# 统计展示
stats = {"files": 100, "lines": 10000}
ux.print_stats(stats)
```

### 问答 API

```python
from code_rag.service_layer.enhanced_qa_engine import EnhancedQAEngine

qa = EnhancedQAEngine()
response = qa.ask("解释这个")
```

---

## 4. 性能监控文档

详细文档参考: [PERFORMANCE_MONITORING.md](./PERFORMANCE_MONITORING.md)

### 监控指标

- 查询响应时间
- 缓存命中率
- 内存使用
- CPU使用
- 错误率

### 性能优化建议

| 问题 | 建议 | 预期提升 |
|------|------|---------|
| 低缓存命中率 | 增加缓存大小或调整TTL | 20-50% |
| 慢查询 | 添加索引或优化算法 | 30-80% |
| 高内存使用 | 实现分页或限制结果集 | 30-50% |

---

## 5. 用户体验指南

### 主题配置

内置主题:

- `default` - 默认主题
- `dark` - 深色主题
- `mono` - 单色主题
- `ocean` - 海洋主题

### 表情控制

```python
from code_rag.service_layer.enhanced_ux import UXConfig

config = UXConfig(enable_emoji=False)
```

### 进度条

```python
from code_rag.service_layer.enhanced_ux import ProgressTracker

tracker = ProgressTracker()
tracker.start("indexing", "索引文件", total=100)
for i in range(100):
    tracker.update("indexing")
tracker.finish("indexing")
```

---

## 6. 架构设计文档

### 9层模块化架构

```
1. Base Layer (基础层)
   - configuration_and_settings
   - logging_and_diagnostics
   - performance_monitoring
   - security_and_access_control

2. Data Layer (数据层)
   - backup_and_version_control
   - caching_and_in_memory_cache
   - code_parser_and_document_processor
   - data_input_and_output_handler
   - data_repository_and_storage

3. Processing Layer (处理层)
   - code_dependency_analyzer
   - code_intelligence_and_semantic_understanding
   - incremental_index_and_parallel_processing
   - text_processing_and_tokenization

4. Search Layer (搜索层)
   - bm25_search_engine
   - nl2code_converter
   - semantic_search_enhancement

5. RAG Engine (RAG引擎层)
   - embedding_production
   - language_model_and_answer_generator
   - llm_production
   - rag_core_engine
   - retrieval_pipeline_processor
   - semantic_search_evaluator
   - vector_index_production

6. Service Layer (服务层)
   - advanced_code_reviewer
   - code_generator
   - code_reviewer
   - context_understanding
   - conversation_manager
   - enhanced_qa_engine
   - enhanced_ux
   - service_layer

7. Middleware Layer (中间件层)
   - middleware_layer

8. Observability Layer (可观测层)
   - performance_monitor
   - metrics_and_evaluation_reporter
   - prometheus_metrics_collector

9. API Layer (API层)
   - error_handlers
   - rest_api_endpoints
```

---

## 7. 部署指南

### Docker部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["code-rag", "serve"]
```

### Kubernetes部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: code-rag
spec:
  replicas: 3
  selector:
    matchLabels:
      app: code-rag
  template:
    metadata:
      labels:
        app: code-rag
    spec:
      containers:
      - name: code-rag
        image: code-rag:v18.5
        ports:
        - containerPort: 8000
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| CODE_RAG_PORT | 服务端口 | 8000 |
| CODE_RAG_CACHE_SIZE | 缓存大小 | 128 |
| CODE_RAG_THEME | UI主题 | ocean |

---

## 8. 开发者贡献指南

### 代码风格

遵循 PEP 8，使用 black 和 ruff:

```bash
pip install black ruff
black src/
ruff check src/ --fix
```

### 测试

```bash
# 运行测试
python -m pytest tests/

# 性能测试
python test_v18_performance.py
```

### 提交规范

格式: `<type>(<scope>): <subject>`

- feat: 新功能
- fix: 修复
- docs: 文档
- refactor: 重构
- test: 测试

---

## 9. 版本历史

### v18.5 (2026-05-16)

**新功能:**
- ✅ 完整性能监控系统
- ✅ LRU缓存实现
- ✅ 增强用户体验（12个优化点）
- ✅ 实时性能仪表板
- ✅ 多主题支持

**改进:**
- ⚡ 查询性能提升 20%
- ⚡ 缓存命中率优化
- 📊 全面测试覆盖

### v18.0 (2026-05-16)

**新功能:**
- ✅ 代码审查AI
- ✅ 增强问答引擎
- ✅ 上下文理解增强
- ✅ 多轮对话系统

---

## 10. FAQ常见问题

### Q: 如何启用缓存？

A: 缓存默认启用，可通过配置调整:

```python
from code_rag.observability.performance_monitor import LRUCache
cache = LRUCache(max_size=256, ttl_seconds=1800)
```

### Q: 如何切换主题？

A: 在配置文件设置或运行时切换:

```python
config = UXConfig(theme="ocean")
```

### Q: 性能监控对系统影响大吗？

A: 设计为低开销，影响 < 1% CPU。使用psutil依赖可选。

### Q: 如何导出对话历史？

A:

```python
manager = ContextManager()
json_data = manager.export_conversation("conv_id")
```

### Q: 支持哪些语言？

A: 目前主要支持Python，JavaScript支持在v19.0添加。

### Q: 报告Bug？

A: 访问GitHub Issues，提供复现步骤和错误日志。

---

## 最后更新

文档版本: v1.0  
更新日期: 2026-05-16  
维护者: Code RAG Team
