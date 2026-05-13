#!/usr/bin/env python3
"""
备份和恢复模块

提供完整的数据备份、恢复和版本控制功能
"""

import os
import sys
import json
import time
import shutil
import hashlib
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class BackupStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RESTORING = "restoring"


class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


@dataclass
class BackupMetadata:
    backup_id: str
    backup_type: BackupType
    status: BackupStatus
    created_at: float
    completed_at: float = 0
    size_bytes: int = 0
    file_count: int = 0
    chunk_count: int = 0
    checksum: str = ""
    description: str = ""
    parent_backup_id: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class RestorePoint:
    restore_id: str
    backup_id: str
    created_at: float
    status: str
    completed_at: float = 0
    files_restored: int = 0


class BackupScheduler:
    def __init__(self):
        self._schedules: Dict[str, Dict] = {}
        self._last_backup: Dict[str, float] = {}

    def add_schedule(
        self,
        schedule_id: str,
        backup_type: BackupType,
        interval_hours: int,
        enabled: bool = True
    ):
        self._schedules[schedule_id] = {
            "type": backup_type,
            "interval_hours": interval_hours,
            "enabled": enabled,
            "created_at": time.time()
        }

    def should_run_backup(self, schedule_id: str) -> bool:
        if schedule_id not in self._schedules:
            return False

        schedule = self._schedules[schedule_id]
        if not schedule.get("enabled", False):
            return False

        last_run = self._last_backup.get(schedule_id, 0)
        interval_seconds = schedule["interval_hours"] * 3600

        return (time.time() - last_run) >= interval_seconds

    def mark_backup_run(self, schedule_id: str):
        self._last_backup[schedule_id] = time.time()

    def get_schedule_info(self, schedule_id: str) -> Optional[Dict]:
        return self._schedules.get(schedule_id)


class IncrementalBackupTracker:
    def __init__(self, state_file: str = "./data/backup_state.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state: Dict[str, Any] = {}
        self._load_state()

    def _load_state(self):
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    self._state = json.load(f)
            except Exception:
                self._state = {}

    def _save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self._state, f, indent=2)

    def get_file_hash(self, file_path: Path) -> str:
        if not file_path.exists():
            return ""

        hash_md5 = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""

    def should_backup_file(self, file_path: str, source_root: Path) -> bool:
        file_key = str(file_path)

        if file_key not in self._state:
            return True

        current_hash = self.get_file_hash(Path(file_path))
        stored_hash = self._state.get(file_key, {}).get("hash", "")

        return current_hash != stored_hash

    def update_file_state(self, file_path: str, hash_value: str):
        self._state[file_path] = {
            "hash": hash_value,
            "last_backup": time.time()
        }
        self._save_state()

    def get_changed_files(
        self,
        source_root: Path,
        extensions: set = None
    ) -> List[Path]:
        changed = []

        for file_path in source_root.rglob("*"):
            if not file_path.is_file():
                continue

            if extensions and file_path.suffix not in extensions:
                continue

            if self.should_backup_file(str(file_path), source_root):
                changed.append(file_path)

        return changed

    def clear_state(self):
        self._state = {}
        self._save_state()


class BackupManager:
    def __init__(
        self,
        backup_dir: str = "./data/backups",
        temp_dir: str = "./data/temp"
    ):
        self.backup_dir = Path(backup_dir)
        self.temp_dir = Path(temp_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self._backups: Dict[str, BackupMetadata] = {}
        self._incremental_tracker = IncrementalBackupTracker()
        self._scheduler = BackupScheduler()

        self._load_backup_index()

    def _get_backup_file(self, backup_id: str) -> Path:
        return self.backup_dir / f"backup_{backup_id}.zip"

    def _get_backup_index(self) -> Path:
        return self.backup_dir / "backup_index.json"

    def _load_backup_index(self):
        index_file = self._get_backup_index()
        if index_file.exists():
            try:
                with open(index_file) as f:
                    data = json.load(f)

                for backup_id, backup_data in data.items():
                    backup_data["backup_type"] = BackupType(backup_data["backup_type"])
                    backup_data["status"] = BackupStatus(backup_data["status"])
                    self._backups[backup_id] = BackupMetadata(**backup_data)
            except Exception:
                pass

    def _save_backup_index(self):
        index_file = self._get_backup_index()
        data = {}

        for backup_id, backup in self._backups.items():
            data[backup_id] = {
                "backup_id": backup.backup_id,
                "backup_type": backup.backup_type.value,
                "status": backup.status.value,
                "created_at": backup.created_at,
                "completed_at": backup.completed_at,
                "size_bytes": backup.size_bytes,
                "file_count": backup.file_count,
                "chunk_count": backup.chunk_count,
                "checksum": backup.checksum,
                "description": backup.description,
                "parent_backup_id": backup.parent_backup_id,
                "metadata": backup.metadata
            }

        with open(index_file, 'w') as f:
            json.dump(data, f, indent=2)

    def create_backup(
        self,
        source_path: Path,
        backup_type: BackupType = BackupType.FULL,
        description: str = "",
        exclude_patterns: List[str] = None
    ) -> Optional[BackupMetadata]:
        import uuid

        backup_id = str(uuid.uuid4())
        backup_file = self._get_backup_file(backup_id)

        exclude_patterns = exclude_patterns or [
            "*.pyc", "__pycache__", ".git", "node_modules",
            "*.log", ".DS_Store"
        ]

        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            status=BackupStatus.IN_PROGRESS,
            created_at=time.time(),
            description=description
        )

        if backup_type == BackupType.INCREMENTAL:
            parent_backup = self._get_latest_backup()
            if parent_backup:
                metadata.parent_backup_id = parent_backup.backup_id

        try:
            file_count = 0
            chunk_count = 0
            total_size = 0

            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                if backup_type == BackupType.INCREMENTAL:
                    files_to_backup = self._incremental_tracker.get_changed_files(source_path)
                else:
                    files_to_backup = []

                    for file_path in source_path.rglob("*"):
                        if not file_path.is_file():
                            continue

                        should_exclude = False
                        for pattern in exclude_patterns:
                            if pattern in str(file_path):
                                should_exclude = True
                                break

                        if not should_exclude:
                            files_to_backup.append(file_path)

                for file_path in files_to_backup:
                    try:
                        rel_path = file_path.relative_to(source_path)
                        zf.write(file_path, rel_path)

                        file_size = file_path.stat().st_size
                        total_size += file_size
                        file_count += 1

                        if file_path.suffix in ['.py', '.js', '.ts', '.java']:
                            chunk_count += 1

                        if backup_type == BackupType.INCREMENTAL:
                            file_hash = self._incremental_tracker.get_file_hash(file_path)
                            self._incremental_tracker.update_file_state(
                                str(file_path), file_hash
                            )

                    except Exception:
                        pass

            checksum = self._calculate_checksum(backup_file)

            metadata.status = BackupStatus.COMPLETED
            metadata.completed_at = time.time()
            metadata.size_bytes = total_size
            metadata.file_count = file_count
            metadata.chunk_count = chunk_count
            metadata.checksum = checksum

            self._backups[backup_id] = metadata
            self._save_backup_index()

            return metadata

        except Exception as e:
            metadata.status = BackupStatus.FAILED
            metadata.metadata["error"] = str(e)
            self._backups[backup_id] = metadata
            self._save_backup_index()
            return None

    def _calculate_checksum(self, file_path: Path) -> str:
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""

    def _get_latest_backup(self) -> Optional[BackupMetadata]:
        completed_backups = [
            b for b in self._backups.values()
            if b.status == BackupStatus.COMPLETED
        ]

        if not completed_backups:
            return None

        return max(completed_backups, key=lambda b: b.created_at)

    def get_backup(self, backup_id: str) -> Optional[BackupMetadata]:
        return self._backups.get(backup_id)

    def list_backups(
        self,
        status: BackupStatus = None,
        limit: int = 100
    ) -> List[BackupMetadata]:
        backups = list(self._backups.values())

        if status:
            backups = [b for b in backups if b.status == status]

        backups.sort(key=lambda b: b.created_at, reverse=True)
        return backups[:limit]

    def restore_backup(
        self,
        backup_id: str,
        target_path: Path,
        overwrite: bool = False
    ) -> Optional[RestorePoint]:
        import uuid

        backup = self._backups.get(backup_id)
        if not backup or backup.status != BackupStatus.COMPLETED:
            return None

        if target_path.exists() and not overwrite:
            return None

        backup_file = self._get_backup_file(backup_id)
        if not backup_file.exists():
            return None

        target_path.mkdir(parents=True, exist_ok=True)

        restore_id = str(uuid.uuid4())
        restore_point = RestorePoint(
            restore_id=restore_id,
            backup_id=backup_id,
            created_at=time.time(),
            status="in_progress"
        )

        try:
            files_restored = 0

            with zipfile.ZipFile(backup_file, 'r') as zf:
                zf.extractall(target_path)
                files_restored = len(zf.namelist())

            restore_point.status = "completed"
            restore_point.completed_at = time.time()
            restore_point.files_restored = files_restored

            return restore_point

        except Exception as e:
            restore_point.status = f"failed: {str(e)}"
            restore_point.completed_at = time.time()
            return restore_point

    def delete_backup(self, backup_id: str) -> bool:
        if backup_id not in self._backups:
            return False

        backup_file = self._get_backup_file(backup_id)
        if backup_file.exists():
            backup_file.unlink()

        del self._backups[backup_id]
        self._save_backup_index()

        return True

    def verify_backup(self, backup_id: str) -> bool:
        backup = self._backups.get(backup_id)
        if not backup or backup.status != BackupStatus.COMPLETED:
            return False

        backup_file = self._get_backup_file(backup_id)
        if not backup_file.exists():
            return False

        current_checksum = self._calculate_checksum(backup_file)
        return current_checksum == backup.checksum

    def schedule_backup(
        self,
        schedule_id: str,
        backup_type: BackupType,
        interval_hours: int,
        source_path: Path,
        description: str = ""
    ):
        self._scheduler.add_schedule(
            schedule_id,
            backup_type,
            interval_hours
        )

    def run_scheduled_backups(self, source_path: Path) -> List[BackupMetadata]:
        created_backups = []

        for schedule_id in self._scheduler._schedules.keys():
            if self._scheduler.should_run_backup(schedule_id):
                schedule = self._scheduler.get_schedule_info(schedule_id)
                if schedule:
                    backup = self.create_backup(
                        source_path,
                        BackupType(schedule["type"].value),
                        f"Scheduled backup: {schedule_id}"
                    )

                    if backup:
                        self._scheduler.mark_backup_run(schedule_id)
                        created_backups.append(backup)

        return created_backups


class BackupFacade:
    def __init__(
        self,
        backup_dir: str = "./data/backups",
        temp_dir: str = "./data/temp"
    ):
        self.manager = BackupManager(backup_dir, temp_dir)
        self.scheduler = BackupScheduler()

    def quick_backup(
        self,
        source_path: str,
        description: str = ""
    ) -> Dict:
        source = Path(source_path)

        if not source.exists():
            return {"error": f"Source path does not exist: {source_path}"}

        backup = self.manager.create_backup(
            source,
            BackupType.FULL,
            description or f"Backup of {source.name}"
        )

        if backup:
            return {
                "success": True,
                "backup_id": backup.backup_id,
                "size_mb": backup.size_bytes / (1024 * 1024),
                "file_count": backup.file_count,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(backup.created_at))
            }

        return {"error": "Backup creation failed"}

    def quick_restore(
        self,
        backup_id: str,
        target_path: str
    ) -> Dict:
        target = Path(target_path)

        restore_point = self.manager.restore_backup(backup_id, target)

        if restore_point:
            return {
                "success": True,
                "restore_id": restore_point.restore_id,
                "files_restored": restore_point.files_restored,
                "completed_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(restore_point.completed_at))
            }

        return {"error": f"Restore failed for backup: {backup_id}"}

    def list_available_backups(self) -> List[Dict]:
        backups = self.manager.list_backups(status=BackupStatus.COMPLETED)

        return [
            {
                "backup_id": b.backup_id,
                "type": b.backup_type.value,
                "size_mb": b.size_bytes / (1024 * 1024),
                "file_count": b.file_count,
                "checksum": b.checksum[:16] + "...",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(b.created_at)),
                "description": b.description
            }
            for b in backups
        ]

    def delete_old_backups(self, keep_count: int = 5) -> Dict:
        backups = self.manager.list_backups(status=BackupStatus.COMPLETED)

        deleted = 0
        for backup in backups[keep_count:]:
            if self.manager.delete_backup(backup.backup_id):
                deleted += 1

        return {
            "deleted_count": deleted,
            "remaining_count": len(backups) - deleted
        }

    def verify_all_backups(self) -> Dict:
        backups = self.manager.list_backups(status=BackupStatus.COMPLETED)

        valid = 0
        invalid = 0

        for backup in backups:
            if self.manager.verify_backup(backup.backup_id):
                valid += 1
            else:
                invalid += 1

        return {
            "total": len(backups),
            "valid": valid,
            "invalid": invalid
        }


def demo_backup_restore():
    print("\n" + "="*60)
    print("演示: 备份和恢复功能")
    print("="*60)

    facade = BackupFacade(
        backup_dir="/tmp/rag_backups",
        temp_dir="/tmp/rag_backups/temp"
    )

    source_path = Path("/tmp/demo_source")
    source_path.mkdir(exist_ok=True)

    print(f"\n📁 创建演示数据...")
    (source_path / "file1.py").write_text("print('Hello World')")
    (source_path / "file2.py").write_text("def test(): pass")
    (source_path / "data.json").write_text('{"key": "value"}')

    print(f"   ✅ 创建3个文件")

    print(f"\n💾 执行完整备份...")
    result = facade.quick_backup(str(source_path), "演示备份")

    if result.get("success"):
        print(f"   ✅ 备份成功!")
        print(f"   - 备份ID: {result['backup_id'][:16]}...")
        print(f"   - 大小: {result['size_mb']:.2f} MB")
        print(f"   - 文件数: {result['file_count']}")
    else:
        print(f"   ❌ 备份失败: {result.get('error')}")

    print(f"\n📋 列出所有备份...")
    backups = facade.list_available_backups()

    for backup in backups:
        print(f"   - {backup['backup_id'][:16]}... | {backup['size_mb']:.2f}MB | {backup['created_at']}")

    print(f"\n🔍 验证备份完整性...")
    verify_result = facade.verify_all_backups()
    print(f"   总数: {verify_result['total']}")
    print(f"   有效: {verify_result['valid']}")
    print(f"   无效: {verify_result['invalid']}")

    target_path = Path("/tmp/demo_restore")
    target_path.mkdir(exist_ok=True)

    if backups:
        print(f"\n🔄 恢复备份...")
        restore_result = facade.quick_restore(
            backups[0]['backup_id'],
            str(target_path)
        )

        if restore_result.get("success"):
            print(f"   ✅ 恢复成功!")
            print(f"   - 恢复ID: {restore_result['restore_id'][:16]}...")
            print(f"   - 恢复文件数: {restore_result['files_restored']}")

            print(f"\n📂 恢复的文件:")
            for f in target_path.rglob("*"):
                if f.is_file():
                    print(f"   - {f.name}: {f.read_text()[:50]}")
        else:
            print(f"   ❌ 恢复失败")

    print(f"\n🧹 清理旧备份（保留最新2个）...")
    cleanup_result = facade.delete_old_backups(keep_count=2)
    print(f"   删除: {cleanup_result['deleted_count']}")
    print(f"   保留: {cleanup_result['remaining_count']}")

    print(f"\n" + "="*60)
    print("备份和恢复演示完成！")
    print("="*60)


if __name__ == "__main__":
    demo_backup_restore()
