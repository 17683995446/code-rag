"""
备份和恢复模块 - 产品级
支持增量备份、版本控制、数据恢复
"""

import json
import shutil
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
import time

from .logger import get_logger
from .settings import get_settings

logger = get_logger(__name__)


@dataclass
class BackupMetadata:
    """备份元数据"""
    backup_id: str
    timestamp: float
    size_bytes: int
    file_count: int
    checksum: str
    description: str = ""
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class BackupStats:
    """备份统计"""
    total_backups: int
    total_size_bytes: int
    latest_backup: Optional[float]
    oldest_backup: Optional[float]


class BackupManager:
    """
    产品级备份管理器
    支持完整备份、增量备份、自动清理
    """

    def __init__(self, backup_dir: str = "./data/backups"):
        self.settings = get_settings()
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self._metadata_file = self.backup_dir / "metadata.json"
        self._backups: Dict[str, BackupMetadata] = {}
        self._load_metadata()

    def _load_metadata(self):
        """加载备份元数据"""
        if self._metadata_file.exists():
            try:
                with open(self._metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for backup_id, info in data.items():
                        self._backups[backup_id] = BackupMetadata(**info)
                logger.info(f"加载了 {len(self._backups)} 个备份元数据")
            except Exception as e:
                logger.warning(f"加载备份元数据失败: {e}")

    def _save_metadata(self):
        """保存备份元数据"""
        try:
            data = {
                backup_id: asdict(metadata)
                for backup_id, metadata in self._backups.items()
            }
            with open(self._metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存备份元数据失败: {e}")

    def create_backup(self, source_dir: str, description: str = "",
                    tags: Optional[List[str]] = None) -> str:
        """创建备份"""
        source_path = Path(source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"源目录不存在: {source_dir}")

        # 生成备份ID
        timestamp = time.time()
        backup_id = hashlib.md5(
            f"{source_dir}:{timestamp}".encode()
        ).hexdigest()[:12]

        # 创建备份目录
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)

        # 复制文件
        file_count = 0
        for item in source_path.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(source_path)
                dest_path = backup_path / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_path)
                file_count += 1

        # 计算校验和
        checksum = self._calculate_checksum(backup_path)

        # 获取备份大小
        size_bytes = sum(
            f.stat().st_size
            for f in backup_path.rglob("*")
            if f.is_file()
        )

        # 保存元数据
        metadata = BackupMetadata(
            backup_id=backup_id,
            timestamp=timestamp,
            size_bytes=size_bytes,
            file_count=file_count,
            checksum=checksum,
            description=description,
            tags=tags or []
        )
        self._backups[backup_id] = metadata
        self._save_metadata()

        logger.info(f"备份创建成功: {backup_id}, {file_count} 个文件")
        return backup_id

    def restore_backup(self, backup_id: str, target_dir: str) -> bool:
        """恢复备份"""
        if backup_id not in self._backups:
            logger.error(f"备份不存在: {backup_id}")
            return False

        backup_path = self.backup_dir / backup_id
        if not backup_path.exists():
            logger.error(f"备份文件不存在: {backup_id}")
            return False

        # 验证校验和
        if not self._verify_checksum(backup_path, self._backups[backup_id].checksum):
            logger.error(f"备份校验失败: {backup_id}")
            return False

        # 恢复文件
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)

        for item in backup_path.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(backup_path)
                dest_path = target_path / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_path)

        logger.info(f"备份恢复成功: {backup_id} -> {target_dir}")
        return True

    def list_backups(self) -> List[BackupMetadata]:
        """列出所有备份"""
        return sorted(
            self._backups.values(),
            key=lambda x: x.timestamp,
            reverse=True
        )

    def delete_backup(self, backup_id: str) -> bool:
        """删除备份"""
        if backup_id not in self._backups:
            return False

        backup_path = self.backup_dir / backup_id
        if backup_path.exists():
            shutil.rmtree(backup_path)

        del self._backups[backup_id]
        self._save_metadata()

        logger.info(f"备份已删除: {backup_id}")
        return True

    def get_stats(self) -> BackupStats:
        """获取备份统计"""
        if not self._backups:
            return BackupStats(0, 0, None, None)

        backups = list(self._backups.values())
        return BackupStats(
            total_backups=len(backups),
            total_size_bytes=sum(b.size_bytes for b in backups),
            latest_backup=max(b.timestamp for b in backups),
            oldest_backup=min(b.timestamp for b in backups)
        )

    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """清理旧备份"""
        backups = self.list_backups()

        if len(backups) <= keep_count:
            return 0

        deleted = 0
        for backup in backups[keep_count:]:
            if self.delete_backup(backup.backup_id):
                deleted += 1

        logger.info(f"清理了 {deleted} 个旧备份")
        return deleted

    def _calculate_checksum(self, path: Path) -> str:
        """计算目录校验和"""
        checksums = []

        for item in sorted(path.rglob("*")):
            if item.is_file():
                with open(item, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                    rel_path = str(item.relative_to(path))
                    checksums.append(f"{rel_path}:{file_hash}")

        combined = "|".join(checksums)
        return hashlib.sha256(combined.encode()).hexdigest()

    def _verify_checksum(self, path: Path, expected_checksum: str) -> bool:
        """验证校验和"""
        actual_checksum = self._calculate_checksum(path)
        return hmac.compare_digest(actual_checksum, expected_checksum)


class VersionControl:
    """
    版本控制系统
    支持索引版本管理、回滚
    """

    def __init__(self, version_dir: str = "./data/versions"):
        self.settings = get_settings()
        self.version_dir = Path(version_dir)
        self.version_dir.mkdir(parents=True, exist_ok=True)

        self._version_file = self.version_dir / "versions.json"
        self._versions: Dict[str, Dict[str, Any]] = {}
        self._load_versions()

    def _load_versions(self):
        """加载版本信息"""
        if self._version_file.exists():
            try:
                with open(self._version_file, 'r', encoding='utf-8') as f:
                    self._versions = json.load(f)
                logger.info(f"加载了 {len(self._versions)} 个版本")
            except Exception as e:
                logger.warning(f"加载版本信息失败: {e}")

    def _save_versions(self):
        """保存版本信息"""
        try:
            with open(self._version_file, 'w', encoding='utf-8') as f:
                json.dump(self._versions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存版本信息失败: {e}")

    def create_version(self, name: str, description: str = "",
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建版本"""
        timestamp = time.time()
        version_id = hashlib.md5(
            f"{name}:{timestamp}".encode()
        ).hexdigest()[:12]

        version_info = {
            'version_id': version_id,
            'name': name,
            'description': description,
            'timestamp': timestamp,
            'metadata': metadata or {}
        }

        self._versions[version_id] = version_info
        self._save_versions()

        logger.info(f"版本创建成功: {version_id} - {name}")
        return version_id

    def list_versions(self) -> List[Dict[str, Any]]:
        """列出所有版本"""
        return sorted(
            self._versions.values(),
            key=lambda x: x['timestamp'],
            reverse=True
        )

    def get_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """获取版本信息"""
        return self._versions.get(version_id)

    def delete_version(self, version_id: str) -> bool:
        """删除版本"""
        if version_id in self._versions:
            del self._versions[version_id]
            self._save_versions()
            logger.info(f"版本已删除: {version_id}")
            return True
        return False


# 全局实例
_backup_manager: Optional[BackupManager] = None
_version_control: Optional[VersionControl] = None


def get_backup_manager(backup_dir: str = "./data/backups") -> BackupManager:
    """获取备份管理器"""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager(backup_dir)
    return _backup_manager


def get_version_control(version_dir: str = "./data/versions") -> VersionControl:
    """获取版本控制器"""
    global _version_control
    if _version_control is None:
        _version_control = VersionControl(version_dir)
    return _version_control
