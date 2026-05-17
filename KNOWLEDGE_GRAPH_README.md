# 知识图谱记忆系统 - Knowledge Graph Memory System

## 系统概述

已将 **Code RAG v24.0 云原生配置生成器** 成功改造成 **知识图谱记忆系统**！

## 核心功能

### 1. 知识图谱数据模型
- **KnowledgeNode** - 知识节点（实体/概念/事实/文档）
- **KnowledgeEdge** - 知识边（关系连接）
- **MemorySession** - 记忆会话
- 支持多种知识类型和关系类型

### 2. 存储引擎与记忆管理
- **KnowledgeStore** - 知识持久化存储
  - JSON 格式存储图谱数据
  - Pickle 存储会话数据
  - 关键词倒排索引
  
- **MemorySystem** - 智能记忆系统
  - `remember()` - 记忆新知识
  - `recall()` - 回忆相关知识
  - `connect_knowledge()` - 连接知识
  - `infer()` - 知识推理
  - `forget()` - 遗忘知识

### 3. 可视化界面
- 使用 Vis.js 实现知识图谱可视化
- 友好的 Web UI（Tailwind CSS）
- 支持节点/边动态管理
- 实时统计展示

## 文件结构

```
/workspace/code-rag/
├── src/code_rag/
│   ├── knowledge_graph.py    # 知识图谱核心模型
│   ├── memory_system.py      # 记忆系统与存储
├── kg_memory_system.html     # 可视化界面
├── test_knowledge_memory.py  # 测试代码
└── 原有的其他文件（云原生配置生成器）
```

## 快速开始

### 1. Python API 使用

```python
from src.code_rag.memory_system import MemorySystem

# 初始化系统
ms = MemorySystem(data_dir="./my_knowledge")

# 开始会话
ms.start_session(user_id="user1")

# 记忆知识
ms.remember("Python 是一种编程语言", {"source": "wiki"})
ms.remember("Django 是 Python 的 Web 框架", {"category": "web"})

# 连接知识
ms.connect_knowledge("Django", "Python", "uses")

# 回忆知识
results = ms.recall("Python", k=10)
for item in results:
    print(f"- {item['label']}")

# 推理
inferences = ms.infer("Python")
print(inferences)
```

### 2. Web 可视化界面

访问：`http://localhost:8000/kg_memory_system.html`

功能：
- 记忆新知识
- 回忆知识搜索
- 知识连接
- 知识图谱可视化
- 推理查询
- 系统统计

### 3. 运行测试

```bash
cd /workspace/code-rag
python test_knowledge_memory.py
```

## 测试结果

✅ 所有 20+ 测试通过：
- 知识图谱核心功能
- 记忆与检索
- 知识连接与推理
- 数据持久化
- 完整工作流

## 核心特性

| 特性 | 描述 |
|------|------|
| 知识类型 | 实体/概念/事实/文档/会话 |
| 关系类型 | is_a/has_a/uses/related_to/part_of 等 |
| 存储格式 | JSON/Pickle 混合 |
| 检索策略 | 标签匹配 + 关键词索引 + 最近优先 |
| 可视化 | Vis.js 交互式图谱 |
| API | Python + Web UI |

## 统计数据（演示）

- **知识节点**：10+
- **知识连接**：8+
- **关键词索引**：15+
- **活动会话**：1

## 下一步建议

1. **增强推理能力** - 加入简单的规则推理
2. **导入导出** - 支持 RDF/OWL 等语义格式
3. **NLP 增强** - 集成实体抽取、关系抽取
4. **向量检索** - 结合嵌入进行语义搜索
5. **多用户支持** - 用户级别的知识隔离

---

系统已改造完成并正常运行！🎉
