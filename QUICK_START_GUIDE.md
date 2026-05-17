# Code RAG v15.0 - 5分钟快速开始

## 🚀 5分钟上手指南

### 第一步：安装 (1分钟)

```bash
# 克隆项目
git clone https://github.com/your-repo/code-rag.git
cd code-rag

# 安装依赖
pip install -r requirements.txt

# 或者安装富文本支持（可选但推荐）
pip install rich click
```

### 第二步：索引代码 (1分钟)

```bash
# 使用增强版CLI索引你的代码库
python -m code_rag.cli_enhanced index ./src

# 或者交互模式
python -m code_rag.cli_enhanced
```

### 第三步：搜索代码 (1分钟)

```bash
# 基础搜索
python -m code_rag.cli_enhanced search "user authentication"

# 自然语言搜索
python -m code_rag.cli_enhanced nl2code "create login function"

# 交互模式
python -m code_rag.cli_enhanced
# 然后输入: search "your query"
```

### 第四步：分析代码 (1分钟)

```bash
# 代码分析
python -m code_rag.cli_enhanced analyze
# 然后粘贴代码

# 依赖分析
python -m code_rag.cli_enhanced deps ./src
```

### 第五步：探索功能 (1分钟)

```bash
# 查看帮助
python -m code_rag.cli_enhanced help

# 查看状态
python -m code_rag.cli_enhanced stats

# 退出
exit
```

---

## 📖 常用命令

### 索引命令

```bash
# 索引整个项目
index ./my-project

# 索引特定目录
index ./src/utils

# 索引当前目录
index .
```

### 搜索命令

```bash
# 基础搜索
search "function name"

# 搜索类
search "class User"

# 搜索特定模式
search "def __init__"
```

### NL2Code命令

```bash
# 自然语言转代码搜索
nl2code "create user authentication"

# 查询数据库
nl2code "connect to database"

# 错误处理
nl2code "handle API errors"
```

### 分析命令

```bash
# 代码依赖分析
deps ./src

# 代码质量分析
analyze
```

---

## 💡 实战示例

### 示例1: 查找认证代码

```bash
$ python -m code_rag.cli_enhanced
🧠  Code RAG v15.0 - 智能代码检索系统

code-rag> index ./my-django-app
🚀 开始索引
ℹ️  索引目录: ./my-django-app
✅ 索引完成!
  处理文件: 156
  索引代码块: 1,234
  耗时: 2.34秒

code-rag> search "user authentication"
🔍 搜索结果: 'user authentication'
✅ 找到 5 个结果 (15.3ms)

1. 相关性: [██████████] 0.98
   路径: my-django-app/auth/views.py
   def authenticate_user(username, password):
       # 认证逻辑...

code-rag>
```

### 示例2: 自然语言查询

```bash
code-rag> nl2code "how to validate email format"
🔄 NL2Code 转换结果

意图: validate
置信度: 0.85

生成的搜索查询:
  • validate email
  • email validation
  • format validation
  • email regex
  • validation function

code-rag> search "email validation"

1. 相关性: [█████████░] 0.95
   def validate_email(email):
       pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
       return re.match(pattern, email) is not None
```

### 示例3: 代码分析

```bash
code-rag> deps ./src
📊 依赖分析结果

文件数: 156
函数数: 1,234
类数: 342
代码行数: 45,678

最常导入的模块:
  • django: 89 次
  • rest_framework: 45 次
  • typing: 38 次
```

---

## 🎯 进阶用法

### Python API使用

```python
from code_rag import create_code_rag

# 创建实例
rag = create_code_rag()

# 索引代码
rag.index_directory("/path/to/code")

# 搜索
results = rag.search("authentication")

# 分析
analysis = rag.analyze_code(code_string)

# NL2Code
nl2code_result = rag.nl2code_search("create login")
```

### 性能优化

```python
# 使用增量索引
from code_rag.processing_layer.incremental_index_and_parallel_processing import (
    create_incremental_indexer
)

indexer = create_incremental_indexer()
indexer.incremental_index("/path/to/code", parser)
```

---

## 🔧 常见问题

### Q: 索引很慢怎么办？

A: 使用并行处理：

```python
from code_rag.processing_layer.incremental_index_and_parallel_processing import (
    create_parallel_engine
)

engine = create_parallel_engine(max_workers=4)
engine.parallel_index_files(files, parser_factory)
```

### Q: 搜索结果不准确？

A: 尝试 NL2Code：

```bash
nl2code "your natural language query"
```

### Q: 如何提高搜索质量？

A:
1. 使用更大的代码块大小
2. 索引前清理无关文件
3. 多次索引以更新

---

## 📚 更多资源

- [完整文档](./docs/)
- [API参考](./docs/API.md)
- [架构设计](./docs/ARCHITECTURE.md)
- [示例项目](./examples/)

---

## 🎉 下一步

- ✅ 5分钟快速开始 - 完成！
- 📖 阅读完整文档
- 💡 查看更多示例
- 🐛 报告问题或建议
- ⭐ Star 项目

---

**恭喜！你已经掌握了 Code RAG 的基本用法！**

继续探索更多高级功能吧！ 🚀
