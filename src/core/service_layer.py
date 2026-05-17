"""
服务层模块（Service Layer）
提供业务逻辑封装和服务组合
"""

from typing import Dict, Any, Optional, List, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from src.core.logger import get_logger
from src.core.data_layer import DocumentDAO, MetadataDAO, create_data_repository
from src.core.processing_layer import TextProcessor, VectorProcessor, DocumentTransformer, DocumentValidator

logger = get_logger(__name__)


# ============================================================================
# 服务接口
# ============================================================================

class Service(ABC):
    """服务抽象接口"""

    @abstractmethod
    def initialize(self) -> bool:
        """初始化服务"""
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """关闭服务"""
        pass


class DocumentService(Service):
    """文档服务接口"""

    @abstractmethod
    def create_document(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """创建文档"""
        pass

    @abstractmethod
    def retrieve_document(self, doc_id: str) -> Optional[str]:
        """获取文档"""
        pass

    @abstractmethod
    def update_document(self, doc_id: str, content: str) -> bool:
        """更新文档"""
        pass

    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        pass

    @abstractmethod
    def list_documents(self) -> List[str]:
        """列出所有文档"""
        pass


class SearchService(Service):
    """搜索服务接口"""

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """搜索文档"""
        pass

    @abstractmethod
    def semantic_search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """语义搜索"""
        pass


class EmbeddingService(Service):
    """嵌入服务接口"""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """生成嵌入向量"""
        pass

    @abstractmethod
    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        pass


# ============================================================================
# 实现类
# ============================================================================

@dataclass
class DocumentRecord:
    """文档记录"""
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class DefaultDocumentService(DocumentService):
    """默认文档服务"""

    def __init__(self):
        self._document_dao = DocumentDAO(create_data_repository().file_store)
        self._metadata_dao = MetadataDAO(create_data_repository().json_store)
        self._validator = DocumentValidator()
        self._transformer = DocumentTransformer()
        self._initialized = False

    def initialize(self) -> bool:
        """初始化服务"""
        logger.info("Initializing DocumentService...")
        self._initialized = True
        logger.info("DocumentService initialized successfully")
        return True

    def shutdown(self) -> bool:
        """关闭服务"""
        logger.info("Shutting down DocumentService...")
        self._initialized = False
        return True

    def _generate_id(self, content: str) -> str:
        """生成文档ID"""
        import hashlib
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]

    def create_document(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """创建文档"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")

        # 验证
        if not self._validator.validate('non_empty', content):
            raise ValueError("Document content cannot be empty")
        
        # 转换
        content = self._transformer.transform('clean', content)
        
        # 生成ID
        doc_id = self._generate_id(content)
        
        # 保存
        self._document_dao.save_document(doc_id, content)
        if metadata:
            metadata['created_at'] = datetime.now().isoformat()
            self._metadata_dao.save_metadata(doc_id, metadata)
        
        logger.info(f"Document created: {doc_id}")
        return doc_id

    def retrieve_document(self, doc_id: str) -> Optional[str]:
        """获取文档"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")

        return self._document_dao.load_document(doc_id)

    def update_document(self, doc_id: str, content: str) -> bool:
        """更新文档"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")

        if not self._document_dao.load_document(doc_id):
            return False
        
        content = self._transformer.transform('clean', content)
        self._document_dao.save_document(doc_id, content)
        
        # 更新元数据
        self._metadata_dao.update_metadata(doc_id, {'updated_at': datetime.now().isoformat()})
        
        logger.info(f"Document updated: {doc_id}")
        return True

    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")

        if self._document_dao.delete_document(doc_id):
            self._metadata_dao.delete_document(doc_id)
            logger.info(f"Document deleted: {doc_id}")
            return True
        return False

    def list_documents(self) -> List[str]:
        """列出所有文档"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")

        return self._document_dao.list_documents()

    def get_metadata(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取文档元数据"""
        return self._metadata_dao.load_metadata(doc_id)


class DefaultSearchService(SearchService):
    """默认搜索服务"""

    def __init__(self):
        self._document_service = DefaultDocumentService()
        self._text_processor = TextProcessor.__subclasses__()[0]()
        self._initialized = False

    def initialize(self) -> bool:
        """初始化服务"""
        logger.info("Initializing SearchService...")
        self._document_service.initialize()
        self._initialized = True
        logger.info("SearchService initialized successfully")
        return True

    def shutdown(self) -> bool:
        """关闭服务"""
        logger.info("Shutting down SearchService...")
        self._document_service.shutdown()
        self._initialized = False
        return True

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """搜索文档（简单关键词匹配）"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")

        results = []
        query_tokens = set(self._text_processor.tokenize(query.lower()))
        
        for doc_id in self._document_service.list_documents():
            content = self._document_service.retrieve_document(doc_id)
            if content:
                content_tokens = set(self._text_processor.tokenize(content.lower()))
                intersection = query_tokens.intersection(content_tokens)
                score = len(intersection) / max(len(query_tokens), 1)
                if score > 0:
                    results.append((doc_id, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def semantic_search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """语义搜索（占位符）"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")

        logger.warning("Semantic search using simple keyword matching as fallback")
        return self.search(query, top_k)


class DefaultEmbeddingService(EmbeddingService):
    """默认嵌入服务"""

    def __init__(self):
        self._vector_processor = VectorProcessor.__subclasses__()[0]()
        self._text_processor = TextProcessor.__subclasses__()[0]()
        self._initialized = False

    def initialize(self) -> bool:
        """初始化服务"""
        logger.info("Initializing EmbeddingService...")
        self._initialized = True
        logger.info("EmbeddingService initialized successfully")
        return True

    def shutdown(self) -> bool:
        """关闭服务"""
        logger.info("Shutting down EmbeddingService...")
        self._initialized = False
        return True

    def embed(self, text: str) -> List[float]:
        """生成嵌入向量（简化实现）"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")

        # 简化的哈希嵌入
        tokens = self._text_processor.tokenize(text)
        vector = [hash(token) % 256 for token in tokens]
        
        # 确保向量长度一致（384维）
        while len(vector) < 384:
            vector.append(0)
        vector = vector[:384]
        
        # 归一化
        return self._vector_processor.normalize_vector(vector)

    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        return [self.embed(text) for text in texts]


# ============================================================================
# 服务组合器
# ============================================================================

class ServiceManager:
    """服务管理器"""

    def __init__(self):
        self._services: Dict[str, Service] = {}

    def register(self, name: str, service: Service):
        """注册服务"""
        self._services[name] = service

    def get(self, name: str) -> Service:
        """获取服务"""
        if name not in self._services:
            raise ValueError(f"Service '{name}' not found")
        return self._services[name]

    def initialize_all(self) -> bool:
        """初始化所有服务"""
        for name, service in self._services.items():
            if not service.initialize():
                logger.error(f"Failed to initialize service: {name}")
                return False
        return True

    def shutdown_all(self) -> bool:
        """关闭所有服务"""
        for name, service in self._services.items():
            if not service.shutdown():
                logger.error(f"Failed to shutdown service: {name}")
                return False
        return True

    def list_services(self) -> List[str]:
        """列出所有服务"""
        return list(self._services.keys())


# ============================================================================
# 业务服务
# ============================================================================

class RAGService(Service):
    """RAG业务服务"""

    def __init__(self):
        self._document_service = DefaultDocumentService()
        self._search_service = DefaultSearchService()
        self._embedding_service = DefaultEmbeddingService()
        self._initialized = False

    def initialize(self) -> bool:
        """初始化服务"""
        logger.info("Initializing RAGService...")
        self._document_service.initialize()
        self._search_service.initialize()
        self._embedding_service.initialize()
        self._initialized = True
        logger.info("RAGService initialized successfully")
        return True

    def shutdown(self) -> bool:
        """关闭服务"""
        logger.info("Shutting down RAGService...")
        self._document_service.shutdown()
        self._search_service.shutdown()
        self._embedding_service.shutdown()
        self._initialized = False
        return True

    def add_document(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """添加文档"""
        return self._document_service.create_document(content, metadata)

    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索文档"""
        results = self._search_service.search(query, top_k)
        docs = []
        for doc_id, score in results:
            content = self._document_service.retrieve_document(doc_id)
            metadata = self._document_service.get_metadata(doc_id) or {}
            docs.append({
                'doc_id': doc_id,
                'content': content,
                'score': score,
                'metadata': metadata
            })
        return docs

    def generate_answer(self, query: str) -> str:
        """生成回答（简化实现）"""
        documents = self.search_documents(query, top_k=3)
        if not documents:
            return "未找到相关文档。"
        
        context = "\n\n".join(doc['content'][:200] for doc in documents)
        return f"基于检索到的文档内容：\n\n{context}\n\n如需更详细的回答，请提供更多信息。"


# ============================================================================
# 工厂函数
# ============================================================================

def get_document_service() -> DocumentService:
    """获取文档服务"""
    service = DefaultDocumentService()
    service.initialize()
    return service


def get_search_service() -> SearchService:
    """获取搜索服务"""
    service = DefaultSearchService()
    service.initialize()
    return service


def get_embedding_service() -> EmbeddingService:
    """获取嵌入服务"""
    service = DefaultEmbeddingService()
    service.initialize()
    return service


def get_rag_service() -> RAGService:
    """获取RAG服务"""
    service = RAGService()
    service.initialize()
    return service


def create_service_manager() -> ServiceManager:
    """创建服务管理器"""
    manager = ServiceManager()
    manager.register('document', get_document_service())
    manager.register('search', get_search_service())
    manager.register('embedding', get_embedding_service())
    manager.register('rag', get_rag_service())
    return manager
