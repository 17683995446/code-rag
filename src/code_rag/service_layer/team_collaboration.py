"""
Code RAG v22.0 - 团队协作索引
支持团队共享代码知识库
"""

import time
import hashlib
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class AccessLevel(Enum):
    """访问级别"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class SyncStatus(Enum):
    """同步状态"""
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    FAILED = "failed"


@dataclass
class User:
    """用户"""
    user_id: str
    username: str
    email: str
    access_level: AccessLevel = AccessLevel.READ
    created_at: float = field(default_factory=time.time)
    active: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "access_level": self.access_level.value,
            "created_at": self.created_at,
            "active": self.active
        }


@dataclass
class Project:
    """项目"""
    project_id: str
    name: str
    description: str = ""
    owner_id: str = ""
    members: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "members": self.members,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }


@dataclass
class SharedIndex:
    """共享索引"""
    index_id: str
    project_id: str
    name: str
    content_hash: str = ""
    last_sync: float = field(default_factory=time.time)
    sync_status: SyncStatus = SyncStatus.PENDING
    index_data: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "index_id": self.index_id,
            "project_id": self.project_id,
            "name": self.name,
            "content_hash": self.content_hash,
            "last_sync": self.last_sync,
            "sync_status": self.sync_status.value,
            "index_data": self.index_data
        }


class UserManager:
    """用户管理器"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.email_to_user: Dict[str, str] = {}
    
    def create_user(self, username: str, email: str, 
                   access_level: AccessLevel = AccessLevel.READ) -> User:
        """创建用户"""
        user_id = f"user_{hashlib.md5(f'{username}_{email}'.encode()).hexdigest()[:8]}"
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            access_level=access_level
        )
        self.users[user_id] = user
        self.email_to_user[email] = user_id
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        return self.users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        user_id = self.email_to_user.get(email)
        return self.users.get(user_id) if user_id else None
    
    def update_access_level(self, user_id: str, 
                            access_level: AccessLevel) -> bool:
        """更新访问级别"""
        if user_id in self.users:
            self.users[user_id].access_level = access_level
            return True
        return False
    
    def list_users(self) -> List[User]:
        """列出所有用户"""
        return list(self.users.values())


class ProjectManager:
    """项目管理器"""
    
    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager
        self.projects: Dict[str, Project] = {}
        self.user_projects: Dict[str, Set[str]] = {}
    
    def create_project(self, name: str, owner_id: str, 
                      description: str = "") -> Project:
        """创建项目"""
        project_id = f"proj_{hashlib.md5(f'{name}_{time.time()}'.encode()).hexdigest()[:8]}"
        project = Project(
            project_id=project_id,
            name=name,
            description=description,
            owner_id=owner_id,
            members=[owner_id]
        )
        self.projects[project_id] = project
        
        if owner_id not in self.user_projects:
            self.user_projects[owner_id] = set()
        self.user_projects[owner_id].add(project_id)
        
        return project
    
    def add_member(self, project_id: str, user_id: str) -> bool:
        """添加项目成员"""
        if project_id in self.projects and user_id in self.user_manager.users:
            if user_id not in self.projects[project_id].members:
                self.projects[project_id].members.append(user_id)
                
                if user_id not in self.user_projects:
                    self.user_projects[user_id] = set()
                self.user_projects[user_id].add(project_id)
                
                self.projects[project_id].updated_at = time.time()
            return True
        return False
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目"""
        return self.projects.get(project_id)
    
    def get_user_projects(self, user_id: str) -> List[Project]:
        """获取用户的所有项目"""
        if user_id in self.user_projects:
            return [
                self.projects[pid] 
                for pid in self.user_projects[user_id] 
                if pid in self.projects
            ]
        return []
    
    def list_projects(self) -> List[Project]:
        """列出所有项目"""
        return list(self.projects.values())


class SharedIndexManager:
    """共享索引管理器"""
    
    def __init__(self, project_manager: ProjectManager):
        self.project_manager = project_manager
        self.shared_indexes: Dict[str, SharedIndex] = {}
        self.project_indexes: Dict[str, List[str]] = {}
    
    def create_index(self, project_id: str, name: str, 
                    index_data: Dict = None) -> SharedIndex:
        """创建共享索引"""
        index_id = f"idx_{hashlib.md5(f'{project_id}_{name}_{time.time()}'.encode()).hexdigest()[:8]}"
        index = SharedIndex(
            index_id=index_id,
            project_id=project_id,
            name=name,
            content_hash="",
            index_data=index_data or {},
            sync_status=SyncStatus.PENDING
        )
        
        content_str = str(index_data) if index_data else ""
        index.content_hash = hashlib.sha256(content_str.encode()).hexdigest()
        
        self.shared_indexes[index_id] = index
        
        if project_id not in self.project_indexes:
            self.project_indexes[project_id] = []
        self.project_indexes[project_id].append(index_id)
        
        return index
    
    def sync_index(self, index_id: str) -> bool:
        """同步索引"""
        if index_id in self.shared_indexes:
            self.shared_indexes[index_id].sync_status = SyncStatus.SYNCING
            time.sleep(0.1)  # 模拟同步
            self.shared_indexes[index_id].sync_status = SyncStatus.SYNCED
            self.shared_indexes[index_id].last_sync = time.time()
            return True
        return False
    
    def get_index(self, index_id: str) -> Optional[SharedIndex]:
        """获取索引"""
        return self.shared_indexes.get(index_id)
    
    def get_project_indexes(self, project_id: str) -> List[SharedIndex]:
        """获取项目的所有索引"""
        if project_id in self.project_indexes:
            return [
                self.shared_indexes[idx] 
                for idx in self.project_indexes[project_id] 
                if idx in self.shared_indexes
            ]
        return []


class TeamCollaboration:
    """团队协作服务"""
    
    def __init__(self):
        self.user_manager = UserManager()
        self.project_manager = ProjectManager(self.user_manager)
        self.index_manager = SharedIndexManager(self.project_manager)
    
    def setup_team(self, team_name: str, owner_email: str, 
                  owner_name: str = "owner") -> Dict:
        """设置团队（快速初始化）"""
        owner = self.user_manager.create_user(
            owner_name, 
            owner_email, 
            AccessLevel.ADMIN
        )
        project = self.project_manager.create_project(team_name, owner.user_id)
        
        return {
            "owner": owner.to_dict(),
            "project": project.to_dict()
        }
    
    def add_team_member(self, project_id: str, email: str, 
                       username: str, 
                       access_level: AccessLevel = AccessLevel.READ) -> bool:
        """添加团队成员"""
        user = self.user_manager.get_user_by_email(email)
        if not user:
            user = self.user_manager.create_user(username, email, access_level)
        
        return self.project_manager.add_member(project_id, user.user_id)
    
    def get_team_report(self, project_id: str) -> Dict:
        """获取团队报告"""
        project = self.project_manager.get_project(project_id)
        if not project:
            return {}
        
        indexes = self.index_manager.get_project_indexes(project_id)
        
        members = [
            self.user_manager.get_user(mid).to_dict() 
            for mid in project.members 
            if self.user_manager.get_user(mid)
        ]
        
        return {
            "project": project.to_dict(),
            "member_count": len(members),
            "index_count": len(indexes),
            "members": members,
            "indexes": [idx.to_dict() for idx in indexes]
        }


def create_team_collaboration() -> TeamCollaboration:
    """创建团队协作服务"""
    return TeamCollaboration()
