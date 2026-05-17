"""
数据层模块（Data Layer）
提供数据访问抽象和存储管理
"""

from typing import Dict, Any, Optional, List, Generic, TypeVar
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import json
import pickle

try:
    from ..base_layer import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)

# 类型变量
T = TypeVar('T')


# ============================================================================
# 数据访问接口
# ============================================================================

class DataStore(ABC, Generic[T]):
    """数据存储抽象接口"""

    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        """获取数据"""
        pass

    @abstractmethod
    def set(self, key: str, value: T) -> bool:
        """设置数据"""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除数据"""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass

    @abstractmethod
    def keys(self) -> List[str]:
        """获取所有键"""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """清空所有数据"""
        pass


class DocumentStore(DataStore[str]):
    """文档存储接口"""

    @abstractmethod
    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None):
        """添加文档"""
        pass

    @abstractmethod
    def get_document(self, doc_id: str) -> Optional[str]:
        """获取文档内容"""
        pass

    @abstractmethod
    def get_metadata(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取文档元数据"""
        pass

    @abstractmethod
    def search_by_metadata(self, query: Dict[str, Any]) -> List[str]:
        """按元数据搜索"""
        pass


class VectorStore(DataStore[List[float]]):
    """向量存储接口"""

    @abstractmethod
    def add_vector(self, key: str, vector: List[float], metadata: Dict[str, Any] = None):
        """添加向量"""
        pass

    @abstractmethod
    def search_similar(self, query_vector: List[float], top_k: int = 5) -> List[tuple]:
        """搜索相似向量"""
        pass


# ============================================================================
# 实现类
# ============================================================================

class MemoryDataStore(DataStore[T]):
    """内存数据存储"""

    def __init__(self):
        self._data: Dict[str, T] = {}

    def get(self, key: str) -> Optional[T]:
        return self._data.get(key)

    def set(self, key: str, value: T) -> bool:
        self._data[key] = value
        return True

    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        return key in self._data

    def keys(self) -> List[str]:
        return list(self._data.keys())

    def clear(self) -> bool:
        self._data.clear()
        return True


class FileDataStore(DataStore[T]):
    """文件数据存储"""

    def __init__(self, base_path: str = "./data"):
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        safe_key = key.replace('/', '_').replace('\\', '_')
        return self._base_path / f"{safe_key}.pkl"

    def get(self, key: str) -> Optional[T]:
        path = self._get_path(key)
        if path.exists():
            try:
                with open(path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.error(f"Failed to load {key}: {e}")
        return None

    def set(self, key: str, value: T) -> bool:
        try:
            path = self._get_path(key)
            with open(path, 'wb') as f:
                pickle.dump(value, f)
            return True
        except Exception as e:
            logger.error(f"Failed to save {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        path = self._get_path(key)
        if path.exists():
            try:
                path.unlink()
                return True
            except Exception as e:
                logger.error(f"Failed to delete {key}: {e}")
        return False

    def exists(self, key: str) -> bool:
        return self._get_path(key).exists()

    def keys(self) -> List[str]:
        return [f.stem for f in self._base_path.glob("*.pkl")]

    def clear(self) -> bool:
        try:
            for f in self._base_path.glob("*.pkl"):
                f.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to clear store: {e}")
            return False


class JSONDataStore(DataStore[Dict[str, Any]]):
    """JSON数据存储"""

    def __init__(self, file_path: str = "./data/store.json"):
        self._file_path = Path(file_path)
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        if self._file_path.exists():
            try:
                with open(self._file_path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load JSON: {e}")
                self._data = {}
        else:
            self._data = {}

    def _save(self):
        try:
            with open(self._file_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")
            return False

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return self._data.get(key)

    def set(self, key: str, value: Dict[str, Any]) -> bool:
        self._data[key] = value
        return self._save()

    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return self._save()
        return False

    def exists(self, key: str) -> bool:
        return key in self._data

    def keys(self) -> List[str]:
        return list(self._data.keys())

    def clear(self) -> bool:
        self._data = {}
        return self._save()


# ============================================================================
# 数据仓库
# ============================================================================

@dataclass
class DataRepository:
    """数据仓库 - 统一数据访问入口"""
    memory_store: DataStore
    file_store: DataStore
    json_store: DataStore


def create_data_repository() -> DataRepository:
    """创建数据仓库"""
    return DataRepository(
        memory_store=MemoryDataStore(),
        file_store=FileDataStore(),
        json_store=JSONDataStore()
    )


# ============================================================================
# 数据访问对象（DAO）
# ============================================================================

class DocumentDAO:
    """文档数据访问对象"""

    def __init__(self, store: DataStore):
        self._store = store

    def save_document(self, doc_id: str, content: str):
        """保存文档"""
        self._store.set(doc_id, content)

    def load_document(self, doc_id: str) -> Optional[str]:
        """加载文档"""
        return self._store.get(doc_id)

    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        return self._store.delete(doc_id)

    def list_documents(self) -> List[str]:
        """列出所有文档ID"""
        return self._store.keys()


class MetadataDAO:
    """元数据访问对象"""

    def __init__(self, store: DataStore):
        self._store = store

    def save_metadata(self, doc_id: str, metadata: Dict[str, Any]) -> bool:
        """保存元数据"""
        return self._store.set(f"meta_{doc_id}", metadata)

    def load_metadata(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """加载元数据"""
        return self._store.get(f"meta_{doc_id}")

    def update_metadata(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """更新元数据"""
        existing = self.load_metadata(doc_id) or {}
        existing.update(updates)
        return self.save_metadata(doc_id, existing)


# ============================================================================
# 工厂函数
# ============================================================================

def get_memory_store() -> DataStore:
    """获取内存存储"""
    return MemoryDataStore()


def get_file_store() -> DataStore:
    """获取文件存储"""
    return FileDataStore()


def get_json_store() -> DataStore:
    """获取JSON存储"""
    return JSONDataStore()


def get_document_dao() -> DocumentDAO:
    """获取文档DAO"""
    return DocumentDAO(get_file_store())


def get_metadata_dao() -> MetadataDAO:
    """获取元数据DAO"""
    return MetadataDAO(get_json_store())
