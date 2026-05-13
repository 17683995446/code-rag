"""
版本控制集成模块

支持Git仓库集成、变更历史追踪、代码版本对比等功能
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import re
import threading


class ChangeType(Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


@dataclass
class FileChange:
    change_type: ChangeType
    file_path: str
    old_path: str = ""
    diff: str = ""
    size_diff: int = 0


@dataclass
class Commit:
    commit_id: str
    message: str
    author: str
    author_email: str
    timestamp: float
    changes: List[FileChange] = field(default_factory=list)
    parent_id: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class Branch:
    name: str
    commit_id: str
    is_head: bool = False
    created_at: float = 0


@dataclass
class VersionSnapshot:
    snapshot_id: str
    commit_id: str
    file_hashes: Dict[str, str]
    created_at: float
    size_bytes: int


class GitMetadataExtractor:
    def __init__(self):
        self._cache: Dict[str, Any] = {}

    def extract_from_git_log(self, git_dir: Path) -> List[Dict]:
        commits = []

        try:
            import subprocess

            result = subprocess.run(
                ['git', 'log', '--format=%H|%s|%an|%ae|%at', '-n', '100'],
                cwd=git_dir,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('|')
                        if len(parts) >= 5:
                            commits.append({
                                'commit_id': parts[0],
                                'message': parts[1],
                                'author': parts[2],
                                'author_email': parts[3],
                                'timestamp': float(parts[4])
                            })

        except Exception:
            pass

        return commits

    def get_file_history(self, git_dir: Path, file_path: str) -> List[Dict]:
        history = []

        try:
            import subprocess

            result = subprocess.run(
                ['git', 'log', '--follow', '--format=%H|%s|%at', '--', file_path],
                cwd=git_dir,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            history.append({
                                'commit_id': parts[0],
                                'message': parts[1],
                                'timestamp': float(parts[2])
                            })

        except Exception:
            pass

        return history

    def get_diff(self, git_dir: Path, commit_id: str) -> List[Dict]:
        diffs = []

        try:
            import subprocess

            result = subprocess.run(
                ['git', 'show', '--format=', '--name-status', commit_id],
                cwd=git_dir,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line and '\t' in line:
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            status_char = parts[0]
                            file_path = parts[1]

                            if status_char == 'A':
                                change_type = ChangeType.ADDED
                            elif status_char == 'M':
                                change_type = ChangeType.MODIFIED
                            elif status_char == 'D':
                                change_type = ChangeType.DELETED
                            elif status_char == 'R':
                                change_type = ChangeType.RENAMED
                            else:
                                continue

                            diffs.append({
                                'type': change_type,
                                'path': file_path
                            })

        except Exception:
            pass

        return diffs


class VersionHistory:
    def __init__(self, storage_path: str = "./data/version_history"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._commits: Dict[str, Commit] = {}
        self._file_commits: Dict[str, List[str]] = defaultdict(list)
        self._branch_commits: Dict[str, str] = {}
        self._snapshots: Dict[str, VersionSnapshot] = {}

        self._lock = threading.Lock()
        self._load_history()

    def _get_commits_file(self) -> Path:
        return self.storage_path / "commits.json"

    def _get_snapshots_file(self) -> Path:
        return self.storage_path / "snapshots.json"

    def _load_history(self):
        commits_file = self._get_commits_file()
        if commits_file.exists():
            try:
                with open(commits_file) as f:
                    data = json.load(f)

                for commit_id, commit_data in data.items():
                    commit_data['change_type'] = ChangeType(commit_data['change_type']) if isinstance(commit_data.get('change_type'), str) else ChangeType.MODIFIED
                    self._commits[commit_id] = Commit(**commit_data)

                    for change in self._commits[commit_id].changes:
                        self._file_commits[change.file_path].append(commit_id)

            except Exception:
                pass

        snapshots_file = self._get_snapshots_file()
        if snapshots_file.exists():
            try:
                with open(snapshots_file) as f:
                    self._snapshots = json.load(f)
            except Exception:
                pass

    def _save_history(self):
        commits_file = self._get_commits_file()
        data = {}

        for commit_id, commit in self._commits.items():
            data[commit_id] = {
                'commit_id': commit.commit_id,
                'message': commit.message,
                'author': commit.author,
                'author_email': commit.author_email,
                'timestamp': commit.timestamp,
                'changes': [
                    {
                        'change_type': c.change_type.value,
                        'file_path': c.file_path,
                        'old_path': c.old_path,
                        'diff': c.diff,
                        'size_diff': c.size_diff
                    }
                    for c in commit.changes
                ],
                'parent_id': commit.parent_id,
                'metadata': commit.metadata
            }

        with open(commits_file, 'w') as f:
            json.dump(data, f, indent=2)

    def record_commit(self, commit: Commit):
        with self._lock:
            self._commits[commit.commit_id] = commit

            for change in commit.changes:
                self._file_commits[change.file_path].append(commit.commit_id)

            self._save_history()

    def get_commit(self, commit_id: str) -> Optional[Commit]:
        return self._commits.get(commit_id)

    def get_file_history(self, file_path: str, limit: int = 50) -> List[Commit]:
        commit_ids = self._file_commits.get(file_path, [])
        commits = []

        for commit_id in reversed(commit_ids[-limit:]):
            commit = self._commits.get(commit_id)
            if commit:
                commits.append(commit)

        return commits

    def get_commits_by_author(self, author: str, limit: int = 100) -> List[Commit]:
        commits = [
            c for c in self._commits.values()
            if c.author == author
        ]

        commits.sort(key=lambda c: c.timestamp, reverse=True)
        return commits[:limit]

    def search_commits(self, query: str, limit: int = 50) -> List[Commit]:
        query_lower = query.lower()
        results = []

        for commit in self._commits.values():
            if query_lower in commit.message.lower():
                results.append(commit)

            for change in commit.changes:
                if query_lower in change.file_path.lower():
                    if commit not in results:
                        results.append(commit)
                    break

        results.sort(key=lambda c: c.timestamp, reverse=True)
        return results[:limit]


class CodeVersionComparator:
    def __init__(self, version_history: VersionHistory):
        self.version_history = version_history

    def compare_versions(
        self,
        file_path: str,
        commit_a: str,
        commit_b: str
    ) -> Dict:
        commit_a_obj = self.version_history.get_commit(commit_a)
        commit_b_obj = self.version_history.get_commit(commit_b)

        if not commit_a_obj or not commit_b_obj:
            return {"error": "Commit not found"}

        file_a = None
        file_b = None

        for change in commit_a_obj.changes:
            if change.file_path == file_path:
                file_a = change
                break

        for change in commit_b_obj.changes:
            if change.file_path == file_path:
                file_b = change
                break

        if not file_a and not file_b:
            return {"error": "File not found in either commit"}

        return {
            "file": file_path,
            "commit_a": {
                "id": commit_a,
                "timestamp": commit_a_obj.timestamp,
                "author": commit_a_obj.author
            },
            "commit_b": {
                "id": commit_b,
                "timestamp": commit_b_obj.timestamp,
                "author": commit_b_obj.author
            },
            "change_a": file_a.change_type.value if file_a else None,
            "change_b": file_b.change_type.value if file_b else None,
            "size_change": (file_b.size_diff if file_b else 0) - (file_a.size_diff if file_a else 0)
        }

    def get_change_summary(self, commit_id: str) -> Dict:
        commit = self.version_history.get_commit(commit_id)

        if not commit:
            return {"error": "Commit not found"}

        summary = {
            "commit_id": commit_id,
            "message": commit.message,
            "author": commit.author,
            "timestamp": commit.timestamp,
            "changes": {
                "added": [],
                "modified": [],
                "deleted": [],
                "renamed": []
            },
            "stats": {
                "total": len(commit.changes),
                "added": 0,
                "modified": 0,
                "deleted": 0
            }
        }

        for change in commit.changes:
            if change.change_type == ChangeType.ADDED:
                summary["changes"]["added"].append(change.file_path)
                summary["stats"]["added"] += 1
            elif change.change_type == ChangeType.MODIFIED:
                summary["changes"]["modified"].append(change.file_path)
                summary["stats"]["modified"] += 1
            elif change.change_type == ChangeType.DELETED:
                summary["changes"]["deleted"].append(change.file_path)
                summary["stats"]["deleted"] += 1
            elif change.change_type == ChangeType.RENAMED:
                summary["changes"]["renamed"].append({
                    "from": change.old_path,
                    "to": change.file_path
                })

        return summary


class VersionTagManager:
    def __init__(self, storage_path: str = "./data/version_tags"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._tags: Dict[str, Dict] = {}
        self._load_tags()

    def _load_tags(self):
        tags_file = self.storage_path / "tags.json"
        if tags_file.exists():
            try:
                with open(tags_file) as f:
                    self._tags = json.load(f)
            except Exception:
                pass

    def _save_tags(self):
        tags_file = self.storage_path / "tags.json"
        with open(tags_file, 'w') as f:
            json.dump(self._tags, f, indent=2)

    def create_tag(
        self,
        tag_name: str,
        commit_id: str,
        message: str = "",
        author: str = "system"
    ) -> bool:
        self._tags[tag_name] = {
            "commit_id": commit_id,
            "message": message,
            "author": author,
            "created_at": time.time()
        }
        self._save_tags()
        return True

    def get_tag(self, tag_name: str) -> Optional[Dict]:
        return self._tags.get(tag_name)

    def list_tags(self, prefix: str = "") -> List[Dict]:
        tags = []
        for name, data in self._tags.items():
            if not prefix or name.startswith(prefix):
                tags.append({
                    "name": name,
                    **data
                })
        return sorted(tags, key=lambda t: t.get('created_at', 0), reverse=True)

    def delete_tag(self, tag_name: str) -> bool:
        if tag_name in self._tags:
            del self._tags[tag_name]
            self._save_tags()
            return True
        return False


class VersionControlIntegration:
    def __init__(self):
        self.version_history = VersionHistory()
        self.version_comparator = CodeVersionComparator(self.version_history)
        self.tag_manager = VersionTagManager()
        self.git_extractor = GitMetadataExtractor()

    def sync_from_git(self, git_dir: Path) -> Dict:
        commits = self.git_extractor.extract_from_git_log(git_dir)

        synced = 0
        for commit_data in commits:
            if commit_data['commit_id'] not in self.version_history._commits:
                diffs = self.git_extractor.get_diff(git_dir, commit_data['commit_id'])

                changes = []
                for diff in diffs:
                    changes.append(FileChange(
                        change_type=diff['type'],
                        file_path=diff['path']
                    ))

                commit = Commit(
                    commit_id=commit_data['commit_id'],
                    message=commit_data['message'],
                    author=commit_data['author'],
                    author_email=commit_data['author_email'],
                    timestamp=commit_data['timestamp'],
                    changes=changes
                )

                self.version_history.record_commit(commit)
                synced += 1

        return {
            "synced_commits": synced,
            "total_commits": len(commits)
        }

    def get_file_blame(
        self,
        file_path: str,
        start_line: int = None,
        end_line: int = None
    ) -> List[Dict]:
        history = self.version_history.get_file_history(file_path)

        blame_info = []

        for commit in history:
            for change in commit.changes:
                if change.file_path == file_path:
                    blame_info.append({
                        "commit_id": commit.commit_id,
                        "message": commit.message,
                        "author": commit.author,
                        "timestamp": commit.timestamp,
                        "change_type": change.change_type.value
                    })

        return blame_info

    def find_code_origin(
        self,
        code_snippet: str,
        max_results: int = 5
    ) -> List[Dict]:
        results = []

        for commit in self.version_history._commits.values():
            for change in commit.changes:
                if code_snippet in change.diff:
                    results.append({
                        "commit_id": commit.commit_id,
                        "message": commit.message,
                        "author": commit.author,
                        "timestamp": commit.timestamp,
                        "file_path": change.file_path,
                        "match_type": "diff"
                    })

                content_hash = hashlib.md5(code_snippet.encode()).hexdigest()
                if content_hash in commit.metadata.get('code_hashes', []):
                    results.append({
                        "commit_id": commit.commit_id,
                        "message": commit.message,
                        "author": commit.author,
                        "timestamp": commit.timestamp,
                        "file_path": change.file_path,
                        "match_type": "hash"
                    })

        results.sort(key=lambda r: r['timestamp'], reverse=True)
        return results[:max_results]


class BranchManager:
    def __init__(self):
        self._branches: Dict[str, Branch] = {}
        self._lock = threading.Lock()

    def create_branch(
        self,
        name: str,
        commit_id: str = None,
        from_head: bool = True
    ) -> Branch:
        with self._lock:
            branch = Branch(
                name=name,
                commit_id=commit_id or "HEAD",
                is_head=False,
                created_at=time.time()
            )
            self._branches[name] = branch
            return branch

    def set_head(self, branch_name: str) -> bool:
        with self._lock:
            for name, branch in self._branches.items():
                branch.is_head = (name == branch_name)
            return branch_name in self._branches

    def get_branch(self, name: str) -> Optional[Branch]:
        return self._branches.get(name)

    def get_head(self) -> Optional[Branch]:
        for branch in self._branches.values():
            if branch.is_head:
                return branch
        return None

    def list_branches(self) -> List[Branch]:
        return list(self._branches.values())


def demo_version_control():
    print("\n" + "="*60)
    print("演示: 版本控制集成")
    print("="*60)

    vc = VersionControlIntegration()

    print("\n📝 步骤1: 模拟代码版本历史")

    commits_data = [
        {
            "id": "abc123",
            "message": "Initial commit",
            "author": "Alice",
            "changes": [
                {"type": ChangeType.ADDED, "path": "main.py", "size": 500}
            ]
        },
        {
            "id": "def456",
            "message": "Add user authentication",
            "author": "Bob",
            "changes": [
                {"type": ChangeType.ADDED, "path": "auth.py", "size": 800},
                {"type": ChangeType.MODIFIED, "path": "main.py", "size": 200}
            ]
        },
        {
            "id": "ghi789",
            "message": "Refactor database layer",
            "author": "Alice",
            "changes": [
                {"type": ChangeType.ADDED, "path": "db.py", "size": 1000},
                {"type": ChangeType.DELETED, "path": "old_db.py", "size": -300}
            ]
        }
    ]

    for commit_data in commits_data:
        changes = [
            FileChange(
                change_type=cd['type'],
                file_path=cd['path'],
                size_diff=cd['size']
            )
            for cd in commit_data['changes']
        ]

        commit = Commit(
            commit_id=commit_data['id'],
            message=commit_data['message'],
            author=commit_data['author'],
            author_email=f"{commit_data['author']}@example.com",
            timestamp=time.time() - (len(commits_data) - commits_data.index(commit_data)) * 3600,
            changes=changes
        )

        vc.version_history.record_commit(commit)
        print(f"   ✅ 记录提交: {commit.commit_id} - {commit.message}")

    print("\n📊 步骤2: 获取文件历史")
    history = vc.version_history.get_file_history("main.py")

    print(f"\n   main.py 的提交历史 ({len(history)} 个提交):")
    for commit in history:
        print(f"   - {commit.commit_id[:6]}: {commit.message}")
        print(f"     作者: {commit.author} | 时间: {time.strftime('%Y-%m-%d %H:%M', time.localtime(commit.timestamp))}")

    print("\n🔍 步骤3: 搜索提交")
    results = vc.version_history.search_commits("authentication")

    print(f"\n   包含 'authentication' 的提交:")
    for result in results:
        print(f"   - {result.commit_id[:6]}: {result.message}")

    print("\n📈 步骤4: 版本对比")
    comparison = vc.version_comparator.compare_versions(
        "main.py",
        "abc123",
        "def456"
    )

    if "error" not in comparison:
        print(f"\n   文件: {comparison['file']}")
        print(f"   版本A: {comparison['commit_a']['id'][:6]} by {comparison['commit_a']['author']}")
        print(f"   版本B: {comparison['commit_b']['id'][:6]} by {comparison['commit_b']['author']}")
        print(f"   变更: {comparison['change_a']} -> {comparison['change_b']}")

    print("\n🏷️ 步骤5: 版本标签管理")
    tag_manager = vc.tag_manager

    tag_manager.create_tag(
        "v1.0.0",
        "abc123",
        "First stable release",
        "Alice"
    )
    print("   ✅ 创建标签: v1.0.0")

    tag_manager.create_tag(
        "v2.0.0",
        "ghi789",
        "Database refactor complete",
        "Bob"
    )
    print("   ✅ 创建标签: v2.0.0")

    tags = tag_manager.list_tags()
    print(f"\n   所有标签 ({len(tags)} 个):")
    for tag in tags:
        print(f"   - {tag['name']}: {tag['message']}")

    print("\n📋 步骤6: 获取变更摘要")
    summary = vc.version_comparator.get_change_summary("ghi789")

    print(f"\n   提交: {summary['commit_id'][:6]}")
    print(f"   消息: {summary['message']}")
    print(f"   作者: {summary['author']}")
    print(f"   统计:")
    print(f"     - 新增: {summary['stats']['added']} 个文件")
    print(f"     - 修改: {summary['stats']['modified']} 个文件")
    print(f"     - 删除: {summary['stats']['deleted']} 个文件")

    print("\n" + "="*60)
    print("版本控制集成演示完成！")
    print("="*60)


if __name__ == "__main__":
    demo_version_control()
