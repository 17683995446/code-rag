import os
import json
import time
import uuid
import hashlib
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class TenantStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class ProjectStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class Tenant:
    tenant_id: str
    name: str
    status: TenantStatus = TenantStatus.ACTIVE
    created_at: float = 0
    updated_at: float = 0
    metadata: Dict = field(default_factory=dict)
    quotas: Dict = field(default_factory=dict)
    settings: Dict = field(default_factory=dict)


@dataclass
class Project:
    project_id: str
    tenant_id: str
    name: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.ACTIVE
    created_at: float = 0
    updated_at: float = 0
    metadata: Dict = field(default_factory=dict)
    index_stats: Dict = field(default_factory=lambda: {
        "total_files": 0,
        "total_chunks": 0,
        "total_size_bytes": 0,
        "last_indexed": 0
    })


@dataclass
class User:
    user_id: str
    tenant_id: str
    username: str
    email: str
    role: str = "user"
    created_at: float = 0
    last_login: float = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class ResourceQuota:
    max_projects: int = 10
    max_storage_mb: int = 1024
    max_files: int = 100000
    max_chunks: int = 1000000
    max_api_calls_per_day: int = 10000
    max_concurrent_requests: int = 10


class TenantManager:
    def __init__(self, storage_path: str = "./data/tenants"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._tenants: Dict[str, Tenant] = {}
        self._projects: Dict[str, Project] = {}
        self._users: Dict[str, User] = {}
        self._tenant_projects: Dict[str, set] = defaultdict(set)
        self._user_tenants: Dict[str, str] = {}

        self._lock = threading.Lock()
        self._load_data()

    def _get_tenant_file(self, tenant_id: str) -> Path:
        return self.storage_path / f"tenant_{tenant_id}.json"

    def _get_project_file(self, project_id: str) -> Path:
        return self.storage_path / f"project_{project_id}.json"

    def _load_data(self):
        for file in self.storage_path.glob("tenant_*.json"):
            try:
                with open(file) as f:
                    data = json.load(f)
                tenant = Tenant(**data)
                tenant.status = TenantStatus(tenant.status.value)
                self._tenants[tenant.tenant_id] = tenant
            except Exception:
                pass

        for file in self.storage_path.glob("project_*.json"):
            try:
                with open(file) as f:
                    data = json.load(f)
                project = Project(**data)
                project.status = ProjectStatus(project.status.value)
                self._projects[project.project_id] = project
                self._tenant_projects[project.tenant_id].add(project.project_id)
            except Exception:
                pass

    def _save_tenant(self, tenant: Tenant):
        file = self._get_tenant_file(tenant.tenant_id)
        with open(file, 'w') as f:
            json.dump({
                **tenant.__dict__,
                'status': tenant.status.value
            }, f, indent=2)

    def _save_project(self, project: Project):
        file = self._get_project_file(project.project_id)
        with open(file, 'w') as f:
            json.dump({
                **project.__dict__,
                'status': project.status.value
            }, f, indent=2)

    def create_tenant(
        self,
        name: str,
        metadata: Dict = None,
        quotas: ResourceQuota = None
    ) -> Tenant:
        with self._lock:
            tenant_id = str(uuid.uuid4())

            default_quotas = quotas or ResourceQuota()

            tenant = Tenant(
                tenant_id=tenant_id,
                name=name,
                status=TenantStatus.ACTIVE,
                created_at=time.time(),
                updated_at=time.time(),
                metadata=metadata or {},
                quotas={
                    "max_projects": default_quotas.max_projects,
                    "max_storage_mb": default_quotas.max_storage_mb,
                    "max_files": default_quotas.max_files,
                    "max_chunks": default_quotas.max_chunks,
                    "max_api_calls_per_day": default_quotas.max_api_calls_per_day,
                    "max_concurrent_requests": default_quotas.max_concurrent_requests
                }
            )

            self._tenants[tenant_id] = tenant
            self._save_tenant(tenant)

            return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)

    def update_tenant(self, tenant_id: str, updates: Dict) -> Optional[Tenant]:
        with self._lock:
            tenant = self._tenants.get(tenant_id)
            if not tenant:
                return None

            for key, value in updates.items():
                if hasattr(tenant, key):
                    setattr(tenant, key, value)

            tenant.updated_at = time.time()
            self._save_tenant(tenant)
            return tenant

    def suspend_tenant(self, tenant_id: str) -> bool:
        return self.update_tenant(tenant_id, {"status": TenantStatus.SUSPENDED}) is not None

    def delete_tenant(self, tenant_id: str) -> bool:
        with self._lock:
            if tenant_id in self._tenants:
                tenant = self._tenants[tenant_id]
                tenant.status = TenantStatus.DELETED
                self._save_tenant(tenant)
                return True
            return False

    def list_tenants(self, status: TenantStatus = None) -> List[Tenant]:
        tenants = list(self._tenants.values())
        if status:
            tenants = [t for t in tenants if t.status == status]
        return sorted(tenants, key=lambda t: t.created_at, reverse=True)

    def create_project(
        self,
        tenant_id: str,
        name: str,
        description: str = "",
        metadata: Dict = None
    ) -> Optional[Project]:
        with self._lock:
            tenant = self._tenants.get(tenant_id)
            if not tenant or tenant.status != TenantStatus.ACTIVE:
                return None

            if len(self._tenant_projects[tenant_id]) >= tenant.quotas.get("max_projects", 10):
                return None

            project_id = str(uuid.uuid4())

            project = Project(
                project_id=project_id,
                tenant_id=tenant_id,
                name=name,
                description=description,
                status=ProjectStatus.ACTIVE,
                created_at=time.time(),
                updated_at=time.time(),
                metadata=metadata or {}
            )

            self._projects[project_id] = project
            self._tenant_projects[tenant_id].add(project_id)
            self._save_project(project)

            return project

    def get_project(self, project_id: str) -> Optional[Project]:
        return self._projects.get(project_id)

    def get_project_by_name(self, tenant_id: str, name: str) -> Optional[Project]:
        for project in self._projects.values():
            if project.tenant_id == tenant_id and project.name == name:
                return project
        return None

    def list_projects(self, tenant_id: str, status: ProjectStatus = None) -> List[Project]:
        projects = [
            self._projects[pid]
            for pid in self._tenant_projects.get(tenant_id, set())
        ]
        if status:
            projects = [p for p in projects if p.status == status]
        return sorted(projects, key=lambda p: p.created_at, reverse=True)

    def update_project(self, project_id: str, updates: Dict) -> Optional[Project]:
        with self._lock:
            project = self._projects.get(project_id)
            if not project:
                return None

            for key, value in updates.items():
                if hasattr(project, key):
                    setattr(project, key, value)

            project.updated_at = time.time()
            self._save_project(project)
            return project

    def archive_project(self, project_id: str) -> bool:
        return self.update_project(project_id, {"status": ProjectStatus.ARCHIVED}) is not None

    def delete_project(self, project_id: str) -> bool:
        with self._lock:
            project = self._projects.get(project_id)
            if not project:
                return False

            project.status = ProjectStatus.DELETED
            self._save_project(project)
            return True

    def update_project_stats(self, project_id: str, stats: Dict) -> bool:
        with self._lock:
            project = self._projects.get(project_id)
            if not project:
                return False

            project.index_stats.update(stats)
            project.index_stats["last_indexed"] = time.time()
            self._save_project(project)
            return True

    def get_tenant_usage(self, tenant_id: str) -> Dict:
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return {}

        projects = self.list_projects(tenant_id)
        total_storage = sum(p.index_stats.get("total_size_bytes", 0) for p in projects)
        total_chunks = sum(p.index_stats.get("total_chunks", 0) for p in projects)
        total_files = sum(p.index_stats.get("total_files", 0) for p in projects)

        return {
            "project_count": len(projects),
            "max_projects": tenant.quotas.get("max_projects", 10),
            "storage_used_mb": total_storage / (1024 * 1024),
            "max_storage_mb": tenant.quotas.get("max_storage_mb", 1024),
            "total_chunks": total_chunks,
            "max_chunks": tenant.quotas.get("max_chunks", 1000000),
            "total_files": total_files,
            "max_files": tenant.quotas.get("max_files", 100000)
        }


class AccessControl:
    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager

        self._permissions: Dict[str, set] = defaultdict(set)
        self._user_roles: Dict[str, Dict[str, str]] = {}

        self._register_default_permissions()

    def _register_default_permissions(self):
        self._permissions["admin"] = {
            "tenant:read", "tenant:write", "tenant:delete",
            "project:read", "project:write", "project:delete",
            "user:read", "user:write", "user:delete",
            "index:read", "index:write", "index:delete",
            "api:admin"
        }

        self._permissions["manager"] = {
            "tenant:read",
            "project:read", "project:write",
            "user:read", "user:write",
            "index:read", "index:write"
        }

        self._permissions["user"] = {
            "tenant:read",
            "project:read",
            "user:read:own",
            "index:read",
            "api:standard"
        }

        self._permissions["viewer"] = {
            "tenant:read",
            "project:read",
            "index:read"
        }

    def assign_role(self, user_id: str, tenant_id: str, role: str):
        if role not in self._permissions:
            raise ValueError(f"Unknown role: {role}")

        with threading.Lock():
            if user_id not in self._user_roles:
                self._user_roles[user_id] = {}

            self._user_roles[user_id][tenant_id] = role

    def get_role(self, user_id: str, tenant_id: str) -> Optional[str]:
        return self._user_roles.get(user_id, {}).get(tenant_id)

    def has_permission(self, user_id: str, tenant_id: str, permission: str) -> bool:
        role = self.get_role(user_id, tenant_id)
        if not role:
            return False

        perms = self._permissions.get(role, set())

        if permission in perms:
            return True

        if permission.endswith(":own"):
            base_perm = permission.replace(":own", "")
            if base_perm in perms:
                return True

        return False

    def check_access(self, user_id: str, project_id: str, permission: str) -> bool:
        project = self.tenant_manager.get_project(project_id)
        if not project:
            return False

        return self.has_permission(user_id, project.tenant_id, permission)

    def list_user_permissions(self, user_id: str, tenant_id: str) -> List[str]:
        role = self.get_role(user_id, tenant_id)
        if not role:
            return []
        return list(self._permissions.get(role, set()))


class ProjectIsolation:
    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager
        self._index_paths: Dict[str, Path] = {}
        self._cache_paths: Dict[str, Path] = {}
        self._log_paths: Dict[str, Path] = {}

    def get_project_path(self, project_id: str, subdir: str = "") -> Path:
        project = self.tenant_manager.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        base_path = Path(f"./data/projects/{project.tenant_id}/{project_id}")

        if subdir:
            base_path = base_path / subdir

        base_path.mkdir(parents=True, exist_ok=True)
        return base_path

    def get_index_path(self, project_id: str) -> Path:
        if project_id not in self._index_paths:
            self._index_paths[project_id] = self.get_project_path(project_id, "index")
        return self._index_paths[project_id]

    def get_cache_path(self, project_id: str) -> Path:
        if project_id not in self._cache_paths:
            self._cache_paths[project_id] = self.get_project_path(project_id, "cache")
        return self._cache_paths[project_id]

    def get_log_path(self, project_id: str) -> Path:
        if project_id not in self._log_paths:
            self._log_paths[project_id] = self.get_project_path(project_id, "logs")
        return self._log_paths[project_id]

    def list_project_files(self, project_id: str, subdir: str = "") -> List[Path]:
        path = self.get_project_path(project_id, subdir)
        if not path.exists():
            return []

        return list(path.rglob("*"))

    def delete_project_data(self, project_id: str):
        import shutil

        project = self.tenant_manager.get_project(project_id)
        if not project:
            return

        base_path = Path(f"./data/projects/{project.tenant_id}/{project_id}")
        if base_path.exists():
            shutil.rmtree(base_path)

        self._index_paths.pop(project_id, None)
        self._cache_paths.pop(project_id, None)
        self._log_paths.pop(project_id, None)

    def get_project_size(self, project_id: str) -> int:
        total_size = 0
        for file_path in self.list_project_files(project_id):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except Exception:
                    pass
        return total_size


class RateLimiter:
    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager
        self._daily_usage: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._concurrent_requests: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    def check_rate_limit(
        self,
        tenant_id: str,
        operation: str = "api_call"
    ) -> Tuple[bool, str]:
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return False, "Tenant not found"

        if tenant.status != TenantStatus.ACTIVE:
            return False, "Tenant is not active"

        max_concurrent = tenant.quotas.get("max_concurrent_requests", 10)

        with self._lock:
            if self._concurrent_requests[tenant_id] >= max_concurrent:
                return False, f"Too many concurrent requests (max: {max_concurrent})"

            today = time.strftime("%Y-%m-%d")
            daily_usage = self._daily_usage[tenant_id].get(today, 0)
            max_daily = tenant.quotas.get("max_api_calls_per_day", 10000)

            if daily_usage >= max_daily:
                return False, f"Daily API limit reached (max: {max_daily})"

            self._concurrent_requests[tenant_id] += 1
            self._daily_usage[tenant_id][today] = daily_usage + 1

        return True, "OK"

    def release_request(self, tenant_id: str):
        with self._lock:
            if self._concurrent_requests[tenant_id] > 0:
                self._concurrent_requests[tenant_id] -= 1

    def get_usage_stats(self, tenant_id: str) -> Dict:
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return {}

        today = time.strftime("%Y-%m-%d")
        daily_usage = self._daily_usage[tenant_id].get(today, 0)
        max_daily = tenant.quotas.get("max_api_calls_per_day", 10000)

        return {
            "daily_usage": daily_usage,
            "daily_limit": max_daily,
            "remaining": max(0, max_daily - daily_usage),
            "concurrent_requests": self._concurrent_requests[tenant_id],
            "max_concurrent": tenant.quotas.get("max_concurrent_requests", 10)
        }


class TenantFacade:
    def __init__(self, storage_path: str = "./data/tenants"):
        self.tenant_manager = TenantManager(storage_path)
        self.access_control = AccessControl(self.tenant_manager)
        self.isolation = ProjectIsolation(self.tenant_manager)
        self.rate_limiter = RateLimiter(self.tenant_manager)

    def setup_tenant(
        self,
        tenant_name: str,
        admin_email: str,
        quotas: ResourceQuota = None
    ) -> Dict:
        tenant = self.tenant_manager.create_tenant(tenant_name, quotas=quotas)

        default_project = self.tenant_manager.create_project(
            tenant.tenant_id,
            "default",
            "Default project for the tenant"
        )

        return {
            "tenant": tenant,
            "default_project": default_project
        }

    def verify_access(
        self,
        user_id: str,
        project_id: str,
        permission: str
    ) -> Tuple[bool, Optional[str]]:
        if not self.access_control.check_access(user_id, project_id, permission):
            project = self.tenant_manager.get_project(project_id)
            if project:
                return False, f"Access denied: {permission} on project {project_id}"
            return False, "Project not found"

        allowed, message = self.rate_limiter.check_rate_limit(
            project.tenant_id if project else "",
            "api_call"
        )

        if not allowed:
            return False, message

        return True, None

    def release_access(self, tenant_id: str):
        self.rate_limiter.release_request(tenant_id)

    def create_isolated_project(
        self,
        tenant_id: str,
        project_name: str,
        description: str = ""
    ) -> Optional[Project]:
        project = self.tenant_manager.create_project(
            tenant_id, project_name, description
        )

        if project:
            self.isolation.get_index_path(project.project_id)
            self.isolation.get_cache_path(project.project_id)
            self.isolation.get_log_path(project.project_id)

        return project

    def delete_tenant_with_data(self, tenant_id: str):
        projects = self.tenant_manager.list_projects(tenant_id)
        for project in projects:
            self.isolation.delete_project_data(project.project_id)
            self.tenant_manager.delete_project(project.project_id)

        self.tenant_manager.delete_tenant(tenant_id)

    def get_full_usage_report(self, tenant_id: str) -> Dict:
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return {}

        usage = self.tenant_manager.get_tenant_usage(tenant_id)
        rate_stats = self.rate_limiter.get_usage_stats(tenant_id)
        projects = self.tenant_manager.list_projects(tenant_id)

        project_stats = []
        for project in projects:
            size = self.isolation.get_project_size(project.project_id)
            project_stats.append({
                "project_id": project.project_id,
                "name": project.name,
                "status": project.status.value,
                "size_mb": size / (1024 * 1024),
                "index_stats": project.index_stats
            })

        return {
            "tenant": {
                "tenant_id": tenant.tenant_id,
                "name": tenant.name,
                "status": tenant.status.value,
                "quotas": tenant.quotas
            },
            "usage": usage,
            "rate_limiting": rate_stats,
            "projects": project_stats
        }


def Tuple():
    pass
