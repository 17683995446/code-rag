# Code RAG - 产品级RAG系统

🚀 **基于开源生态的生产级代码检索增强生成系统**

---

## ✨ 核心特性

- **站在巨人肩膀上**: 基于 LangChain, FAISS, Sentence-Transformers 等工业标准开源组件
- **高度模块化**: 每个模块独立、可替换、可扩展
- **自动降级**: 无外部依赖也能正常工作，平滑降级
- **生产就绪**: 完整配置管理、日志系统、API服务、测试覆盖
- **零依赖**: 核心功能无需任何外部库即可运行

---

## 📁 项目结构

```
code-rag/
├── src/                     # 源码
│   ├── core/               # 核心模块
│   │   ├── __init__.py     # 模块导出
│   │   ├── rag.py          # RAG主逻辑
│   │   ├── settings.py     # 配置管理
│   │   └── logger.py       # 日志系统
│   └── api/                # API服务
│       ├── __init__.py
│       └── app.py          # FastAPI服务
├── tests/                  # 测试
│   └── test_core.py        # 核心测试
├── docs/                   # 文档
├── data/                   # 数据目录
├── archive/                # 归档文件（旧版本）
├── requirements.txt        # 依赖
├── main.py                # 主入口
└── README.md              # 本文
```

---

## 🚀 快速开始

### 安装依赖（可选但推荐）

```bash
pip install -r requirements.txt
```

### 运行演示

```bash
python main.py demo
```

### 基本使用

```python
from src.core import CodeRAG

# 初始化
rag = CodeRAG()

# 索引代码
rag.index("/path/to/your/codebase")

# 搜索
results = rag.search("如何实现并发控制？")

# 问答
answer = rag.ask("解释这个项目的架构")
```

### 命令行使用

```bash
# 索引
python main.py index /path/to/code

# 搜索
python main.py search "FAISS向量数据库"

# 问答
python main.py ask "什么是RAG?"

# 启动API服务
python main.py api

# 运行测试
python main.py test
```

### API使用

启动服务：

```bash
python main.py api
```

访问API文档：`http://localhost:8000/docs`

---

## 🧩 核心模块

### 1. RAG模块 (`src.core`)

| 类 | 说明 |
|---|---|
| `CodeRAG` | 统一入口，简单易用 |
| `RAGPipeline` | RAG处理管道 |
| `EmbeddingEngine` | 文本嵌入，支持多种实现 |
| `VectorStore` | 向量存储，支持FAISS等 |

### 2. 配置系统 (`src.core.settings`)

基于 `pydantic-settings`，支持环境变量和配置文件：

```python
from src.core import get_settings

settings = get_settings()
print(settings.embedding.model_name)
```

### 3. 日志系统 (`src.core.logger`)

产品级日志：

```python
from src.core import get_logger

logger = get_logger(__name__)
logger.info("处理中...")
```

### 4. API服务 (`src.api`)

FastAPI服务，完整文档和类型提示。

---

## 🔧 配置说明

### 环境变量

```bash
# 嵌入模型
export RAG_EMBEDDING_MODEL_NAME="all-MiniLM-L6-v2"

# 向量数据库
export RAG_VECTOR_DB_PROVIDER="faiss"

# 日志
export RAG_LOGGING_LEVEL="INFO"

# API
export RAG_API_HOST="0.0.0.0"
export RAG_API_PORT=8000
```

### 配置文件 (`.env`)

```env
RAG_EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
RAG_VECTOR_DB_PROVIDER=faiss
RAG_LOGGING_LEVEL=INFO
RAG_API_PORT=8000
```

---

## 🎯 四大原则实践

### ✅ 1. 站在巨人肩膀上

- 使用 **LangChain** 作为RAG框架
- 使用 **FAISS** 作为向量数据库
- 使用 **Sentence-Transformers** 进行嵌入
- 使用 **FastAPI** 作为Web框架

### ✅ 2. 尽量使用开源工具集

所有核心功能都依赖业界标准的开源项目，不重复造轮子。

### ✅ 3. 不重复造轮子

- 向量索引：FAISS
- 文本切分：LangChain
- 嵌入：Sentence-Transformers
- Web服务：FastAPI

### ✅ 4. 高度模块化

```python
# 每个模块独立，可替换
from src.core import EmbeddingEngine, VectorStore, RAGPipeline

# 独立使用
engine = EmbeddingEngine()
store = VectorStore()
pipeline = RAGPipeline()
```

---

## 🧪 测试

```bash
# 运行所有测试
python main.py test

# 或直接运行
python tests/test_core.py
```

测试覆盖：
- ✅ EmbeddingEngine
- ✅ VectorStore
- ✅ CodeRAG完整流程

---

## 📦 可选依赖

| 功能 | 依赖 | 用途 |
|---|---|---|
| 高质量嵌入 | `sentence-transformers` | 生产级嵌入 |
| 高性能向量检索 | `faiss-cpu` | Meta的向量库 |
| RAG框架 | `langchain` / `llama-index` | 完整RAG能力 |
| API服务 | `fastapi` + `uvicorn` | REST API |

安装所有：

```bash
pip install -r requirements.txt
```

---

## 🎉 项目演进

这个项目从混乱的多个版本，重构为清晰的产品级系统：

**之前**：60+ 混乱文件，4个不同版本，重复代码

**现在**：
- 📦 10+ 核心文件
- 🧩 清晰模块化结构
- ✅ 完整测试覆盖
- 📚 产品级日志和配置
- 🔌 统一API入口

---

## 📚 更多文档

见 `docs/` 目录下的详细文档。

---

## 📄 许可证

MIT

---

**使用愉快！** 🚀
