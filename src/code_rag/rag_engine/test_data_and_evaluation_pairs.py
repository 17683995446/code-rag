"""
Code RAG 测试数据集
包含丰富的代码和知识内容
"""

SAMPLE_CODE_DATABASE = [
    {
        "content": """
        # FAISS 向量数据库教程

        FAISS (Facebook AI Similarity Search) 是 Meta (原 Facebook) 开源的高性能向量数据库。

        ## 主要特性

        1. **高性能**: 支持十亿级向量检索
        2. **多种索引**: IndexFlatL2, IndexIVFFlat, IndexIVFPQ 等
        3. **GPU 支持**: 可在 GPU 上加速计算
        4. **易用性**: 简洁的 Python API

        ## 基本使用

        ```python
        import faiss
        import numpy as np

        # 创建索引
        dimension = 128
        index = faiss.IndexFlatL2(dimension)

        # 添加向量
        vectors = np.random.rand(1000, dimension).astype('float32')
        index.add(vectors)

        # 搜索
        query = np.random.rand(1, dimension).astype('float32')
        distances, indices = index.search(query, k=5)
        ```

        ## 应用场景

        - 图像相似度搜索
        - 文档检索
        - 推荐系统
        - RAG (Retrieval Augmented Generation)
        """,
        "metadata": {
            "file": "faiss_tutorial.py",
            "topic": "FAISS",
            "category": "knowledge"
        }
    },
    {
        "content": """
        # LangChain RAG 实现指南

        LangChain 是一个用于构建 LLM 应用的框架，支持 RAG 模式。

        ## 核心组件

        1. **Document Loader**: 加载各种格式的文档
        2. **Text Splitter**: 文本分块
        3. **Embeddings**: 文本向量化
        4. **Vector Store**: 向量存储
        5. **Retrieval**: 检索组件
        6. **Chain**: 组合形成完整流程

        ## 完整示例

        ```python
        from langchain.document_loaders import TextLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain.embeddings import OpenAIEmbeddings
        from langchain.vectorstores import FAISS
        from langchain.chains import RetrievalQA
        from langchain.llms import OpenAI

        # 加载文档
        loader = TextLoader("document.txt")
        documents = loader.load()

        # 分块
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = text_splitter.split_documents(documents)

        # 创建向量存储
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(texts, embeddings)

        # 创建检索链
        qa_chain = RetrievalQA.from_chain_type(
            llm=OpenAI(),
            chain_type="stuff",
            retriever=vectorstore.as_retriever()
        )

        # 问答
        result = qa_chain({"query": "问题"})
        ```

        ## 最佳实践

        - 选择合适的 chunk_size
        - 使用重叠保持上下文
        - 考虑元数据过滤
        """,
        "metadata": {
            "file": "langchain_rag.py",
            "topic": "LangChain",
            "category": "usage"
        }
    },
    {
        "content": """
        # 快速排序算法实现

        快速排序是一种高效的排序算法，平均时间复杂度 O(n log n)。

        ## Python 实现

        ```python
        def quick_sort(arr):
            if len(arr) <= 1:
                return arr

            pivot = arr[len(arr) // 2]
            left = [x for x in arr if x < pivot]
            middle = [x for x in arr if x == pivot]
            right = [x for x in arr if x > pivot]

            return quick_sort(left) + middle + quick_sort(right)

        # 使用示例
        data = [64, 34, 25, 12, 22, 11, 90]
        sorted_data = quick_sort(data)
        print(sorted_data)  # [11, 12, 22, 25, 34, 64, 90]
        ```

        ## 算法步骤

        1. 选择基准元素 (pivot)
        2. 分区：将小于 pivot 的放左边，大于的放右边
        3. 递归：对左右两部分分别排序

        ## 性能优化

        - 三数取中选择 pivot
        - 随机化避免最坏情况
        - 小数组使用插入排序
        - 尾递归优化
        """,
        "metadata": {
            "file": "quick_sort.py",
            "topic": "算法",
            "category": "code"
        }
    },
    {
        "content": """
        # 向量检索性能优化技巧

        优化向量检索性能是构建高效 RAG 系统的关键。

        ## 索引优化

        ### 1. 量化 (Quantization)

        - **PQ (Product Quantization)**: 将高维向量压缩
        - **SQ (Scalar Quantization)**: 标量量化

        ```python
        # FAISS 量化索引
        import faiss

        dimension = 128
        nlist = 100  # 聚类数量

        quantizer = faiss.IndexFlatL2(dimension)
        index = faiss.IndexIVFPQ(quantizer, dimension, nlist, 16, 8)
        ```

        ### 2. 分层索引 (HNSW)

        - 构建多层图结构
        - 从高层快速定位
        - 近似最近邻搜索

        ```python
        # 使用 HNSW
        index = faiss.IndexHNSWFlat(dimension, 32)
        index.hnsw.efConstruction = 40
        ```

        ## 查询优化

        1. **批量查询**: 一次处理多个查询
        2. **预过滤**: 先过滤再检索
        3. **缓存**: 缓存热门查询结果
        4. **异步**: 异步执行多个检索

        ## 混合检索

        结合向量检索和关键词检索：

        ```python
        # BM25 + 向量检索
        bm25_scores = bm25_search(query, k=100)
        vector_scores = vector_search(query, k=100)

        # RRF 融合
        def rrf_fusion(results, k=60):
            scores = {}
            for result in results:
                for rank, doc in enumerate(result):
                    scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank + 1)
            return sorted(scores.items(), key=lambda x: x[1], reverse=True)
        ```

        ## 监控指标

        - 检索延迟 (P50, P95, P99)
        - 吞吐量 (QPS)
        - 命中率
        - 召回率
        """,
        "metadata": {
            "file": "vector_optimization.py",
            "topic": "性能优化",
            "category": "performance"
        }
    },
    {
        "content": """
        # Sentence-Transformers 使用指南

        Sentence-Transformers 提供高质量的文本 embedding 模型。

        ## 基础使用

        ```python
        from sentence_transformers import SentenceTransformer

        # 加载模型
        model = SentenceTransformer('all-MiniLM-L6-v2')

        # 单文本编码
        embedding = model.encode("Hello world")

        # 批量编码
        sentences = ["First sentence", "Second sentence"]
        embeddings = model.encode(sentences)

        # 计算相似度
        from sklearn.metrics.pairwise import cosine_similarity
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])
        ```

        ## 常用模型

        1. **all-MiniLM-L6-v2**: 速度快，效果好
        2. **all-mpnet-base-v2**: 最高质量
        3. **multi-qa-MiniLM-L6**: 问答任务优化

        ## 应用场景

        - 语义搜索
        - 文本聚类
        - 相似度计算
        - 重排序 (Re-ranking)

        ## 在 RAG 中使用

        ```python
        # 创建向量存储
        from langchain.vectorstores import Chroma
        from langchain.embeddings import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )

        vectorstore = Chroma.from_documents(
            documents=texts,
            embedding=embeddings
        )

        # 检索
        results = vectorstore.similarity_search(query, k=5)
        ```
        """,
        "metadata": {
            "file": "sentence_transformers.py",
            "topic": "Embedding",
            "category": "knowledge"
        }
    }
]

# 添加更多测试内容
ADDITIONAL_KNOWLEDGE = [
    {
        "content": """
        # 数据库索引优化

        数据库索引是提高查询性能的关键。

        ## 常见索引类型

        1. B-Tree 索引
        2. Hash 索引
        3. GiST 索引
        4. GIN 索引

        ## SQL 示例

        ```sql
        CREATE INDEX idx_user_email ON users(email);
        CREATE INDEX idx_order_date ON orders(order_date);

        -- 复合索引
        CREATE INDEX idx_sales ON sales(product_id, order_date);
        ```

        ## 向量数据库

        现代 AI 应用使用向量索引：
        - FAISS
        - Chroma
        - Milvus
        - Qdrant
        """,
        "metadata": {
            "file": "database_indexes.py",
            "topic": "数据库",
            "category": "knowledge"
        }
    },
    {
        "content": """
        # Python 异步编程

        异步编程提高 I/O 密集型应用的性能。

        ## async/await 语法

        ```python
        import asyncio

        async def fetch_data(url):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()

        async def main():
            tasks = [fetch_data(url) for url in urls]
            results = await asyncio.gather(*tasks)
            return results
        ```

        ## 异步向量检索

        ```python
        async def async_vector_search(query, k=10):
            # 异步获取 embedding
            query_embedding = await get_embedding_async(query)

            # 异步检索
            results = await vector_index.search_async(
                query_embedding,
                k=k
            )
            return results
        ```
        """,
        "metadata": {
            "file": "async_python.py",
            "topic": "异步编程",
            "category": "code"
        }
    },
    {
        "content": """
        # RAG 系统架构设计

        完整的 RAG 系统包含多个组件。

        ## 核心架构

        1. **数据摄入管道**
           - 文档加载
           - 文本分块
           - 向量化
           - 索引存储

        2. **检索管道**
           - 查询理解
           - 向量检索
           - 重排序
           - 上下文组装

        3. **生成管道**
           - Prompt 构建
           - LLM 调用
           - 响应后处理

        ## 关键优化

        - Chunk size 优化
        - 重叠大小调整
        - 元数据过滤
        - 混合检索
        - 结果缓存
        """,
        "metadata": {
            "file": "rag_architecture.py",
            "topic": "RAG架构",
            "category": "usage"
        }
    }
]


# ============================================================================
# 测试数据访问函数
# ============================================================================

def get_test_documents() -> list:
    """获取所有测试文档"""
    return SAMPLE_CODE_DATABASE + ADDITIONAL_KNOWLEDGE


def get_test_queries() -> list:
    """获取测试查询列表"""
    return [
        "FAISS向量数据库",
        "LangChain RAG实现",
        "快速排序算法",
        "向量检索性能优化",
        "Sentence-Transformers embedding",
        "Python异步编程",
        "数据库索引优化",
        "RAG系统架构"
    ]


def get_evaluation_pairs() -> list:
    """获取评估对（查询-答案对）"""
    return [
        {
            "query": "什么是FAISS?",
            "expected_keywords": ["FAISS", "向量数据库", "Facebook", "Meta", "向量检索"],
            "topic": "FAISS"
        },
        {
            "query": "LangChain RAG如何实现?",
            "expected_keywords": ["LangChain", "RAG", "文档加载", "向量存储", "检索"],
            "topic": "LangChain"
        },
        {
            "query": "快速排序算法实现",
            "expected_keywords": ["快速排序", "算法", "排序", "递归"],
            "topic": "算法"
        },
        {
            "query": "向量检索性能优化技巧",
            "expected_keywords": ["性能优化", "量化", "索引", "HNSW", "RRF"],
            "topic": "性能优化"
        },
        {
            "query": "Sentence-Transformers使用",
            "expected_keywords": ["Sentence-Transformers", "embedding", "向量", "模型"],
            "topic": "Embedding"
        },
        {
            "query": "Python异步编程",
            "expected_keywords": ["async", "异步", "await", "并发"],
            "topic": "异步编程"
        },
        {
            "query": "数据库索引优化",
            "expected_keywords": ["索引", "数据库", "性能", "SQL"],
            "topic": "数据库"
        },
        {
            "query": "RAG系统架构设计",
            "expected_keywords": ["RAG", "架构", "检索", "生成", "管道"],
            "topic": "RAG架构"
        }
    ]
