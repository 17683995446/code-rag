#!/usr/bin/env python3
"""
多租户和项目隔离演示 - 简化版
"""

import sys
import time
import threading
import uuid
from pathlib import Path
from typing import Dict, List, Optional
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


@dataclass
class ResourceQuota:
    max_projects: int = 10
    max_storage_mb: int = 1024
    max_files: int = 100000
    max_chunks: int = 1000000
    max_api_calls_per_day: int = 10000
    max_concurrent_requests: int = 10


class TenantManager:
    def __init__(self):
        self._tenants: Dict[str, Tenant] = {}
        self._projects: Dict[str, Project] = {}
        self._tenant_projects: Dict[str, set] = defaultdict(set)
        self._lock = threading.Lock()

    def create_tenant(self, name: str, quotas: ResourceQuota = None) -> Tenant:
        with self._lock:
            tenant_id = str(uuid.uuid4())
            default_quotas = quotas or ResourceQuota()

            tenant = Tenant(
                tenant_id=tenant_id,
                name=name,
                status=TenantStatus.ACTIVE,
                created_at=time.time(),
                updated_at=time.time(),
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
            return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)

    def create_project(self, tenant_id: str, name: str, description: str = "") -> Optional[Project]:
        with self._lock:
            tenant = self._tenants.get(tenant_id)
            if not tenant:
                return None

            project_id = str(uuid.uuid4())

            project = Project(
                project_id=project_id,
                tenant_id=tenant_id,
                name=name,
                description=description,
                status=ProjectStatus.ACTIVE,
                created_at=time.time(),
                updated_at=time.time()
            )

            self._projects[project_id] = project
            self._tenant_projects[tenant_id].add(project_id)
            return project

    def get_project(self, project_id: str) -> Optional[Project]:
        return self._projects.get(project_id)

    def list_projects(self, tenant_id: str) -> List[Project]:
        return [self._projects[pid] for pid in self._tenant_projects.get(tenant_id, set())]

    def get_tenant_usage(self, tenant_id: str) -> Dict:
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return {}

        projects = self.list_projects(tenant_id)
        return {
            "project_count": len(projects),
            "max_projects": tenant.quotas.get("max_projects", 10),
            "storage_used_mb": 0,
            "max_storage_mb": tenant.quotas.get("max_storage_mb", 1024),
            "total_chunks": 0,
            "max_chunks": tenant.quotas.get("max_chunks", 1000000),
            "total_files": 0,
            "max_files": tenant.quotas.get("max_files", 100000)
        }


class AccessControl:
    def __init__(self):
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
        return permission in self._permissions.get(role, set())

    def list_user_permissions(self, user_id: str, tenant_id: str) -> List[str]:
        role = self.get_role(user_id, tenant_id)
        if not role:
            return []
        return list(self._permissions.get(role, set()))


class RateLimiter:
    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager
        self._daily_usage: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._concurrent_requests: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    def check_rate_limit(self, tenant_id: str, operation: str = "api_call") -> tuple:
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


class ProjectIsolation:
    def __init__(self):
        self._index_paths: Dict[str, Path] = {}
        self._cache_paths: Dict[str, Path] = {}
        self._log_paths: Dict[str, Path] = {}

    def get_project_path(self, project_id: str, subdir: str = "") -> Path:
        base_path = Path(f"/tmp/multi_tenant_demo/projects/{project_id}")
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

    def get_project_size(self, project_id: str) -> int:
        total_size = 0
        path = Path(f"/tmp/multi_tenant_demo/projects/{project_id}")
        if path.exists():
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except Exception:
                        pass
        return total_size


class TenantFacade:
    def __init__(self):
        self.tenant_manager = TenantManager()
        self.access_control = AccessControl()
        self.isolation = ProjectIsolation()
        self.rate_limiter = RateLimiter(self.tenant_manager)

    def setup_tenant(self, tenant_name: str, admin_email: str, quotas: ResourceQuota = None) -> Dict:
        tenant = self.tenant_manager.create_tenant(tenant_name, quotas=quotas)
        default_project = self.tenant_manager.create_project(
            tenant.tenant_id, "default", "Default project"
        )

        return {
            "tenant": tenant,
            "default_project": default_project
        }

    def verify_access(self, user_id: str, project_id: str, permission: str) -> tuple:
        project = self.tenant_manager.get_project(project_id)
        if not project:
            return False, "Project not found"

        if not self.access_control.has_permission(user_id, project.tenant_id, permission):
            return False, f"Access denied: {permission}"

        allowed, message = self.rate_limiter.check_rate_limit(project.tenant_id)
        if not allowed:
            return False, message

        return True, None

    def create_isolated_project(self, tenant_id: str, project_name: str, description: str = "") -> Optional[Project]:
        project = self.tenant_manager.create_project(tenant_id, project_name, description)
        if project:
            self.isolation.get_index_path(project.project_id)
            self.isolation.get_cache_path(project.project_id)
        return project

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
                "size_mb": size / (1024 * 1024)
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


def demo_tenant_management():
    print("\n" + "="*60)
    print("演示1: 租户管理")
    print("="*60)

    facade = TenantFacade()

    setup = facade.setup_tenant(
        "Acme Corporation",
        "admin@acme.com",
        quotas=ResourceQuota(
            max_projects=5,
            max_storage_mb=5120,
            max_chunks=500000
        )
    )

    tenant = setup["tenant"]
    default_project = setup["default_project"]

    print(f"\n✅ 创建租户: {tenant.name}")
    print(f"   租户ID: {tenant.tenant_id[:8]}...")
    print(f"   配额:")
    print(f"     - 最大项目数: {tenant.quotas['max_projects']}")
    print(f"     - 最大存储: {tenant.quotas['max_storage_mb']} MB")

    projects = facade.tenant_manager.list_projects(tenant.tenant_id)
    print(f"\n📁 当前项目数: {len(projects)}")

    new_project = facade.create_isolated_project(
        tenant.tenant_id,
        "backend-api",
        "后端API服务"
    )

    if new_project:
        print(f"✅ 创建新项目: {new_project.name}")
        print(f"   项目ID: {new_project.project_id[:8]}...")

    return facade, tenant


def demo_access_control():
    print("\n" + "="*60)
    print("演示2: 访问控制")
    print("="*60)

    facade = TenantFacade()
    setup = facade.setup_tenant("Tech Startup", "admin@startup.com")

    tenant = setup["tenant"]
    project = setup["default_project"]

    access = facade.access_control

    print(f"\n👥 分配角色:")
    access.assign_role("user_001", tenant.tenant_id, "admin")
    access.assign_role("user_002", tenant.tenant_id, "manager")
    access.assign_role("user_003", tenant.tenant_id, "user")
    access.assign_role("user_004", tenant.tenant_id, "viewer")
    print("   ✅ 分配完成")

    print(f"\n🔐 权限检查 (user_003 - user角色):")
    for perm in ["tenant:read", "project:write", "index:read"]:
        has_perm = access.has_permission("user_003", tenant.tenant_id, perm)
        print(f"   {'✅' if has_perm else '❌'} {perm}")


def demo_rate_limiting():
    print("\n" + "="*60)
    print("演示3: 速率限制")
    print("="*60)

    facade = TenantFacade()
    setup = facade.setup_tenant("Rate Limited Corp", "admin@ratelimit.com")

    tenant = setup["tenant"]

    print(f"\n⚡ 测试速率限制:")
    print(f"   最大并发: {tenant.quotas['max_concurrent_requests']}")

    success_count = 0
    blocked_count = 0

    for i in range(12):
        allowed, message = facade.rate_limiter.check_rate_limit(tenant.tenant_id)
        if allowed:
            success_count += 1
            if i < 3:
                print(f"   ✅ 请求 {i+1}: 成功")
            facade.rate_limiter.release_request(tenant.tenant_id)
        else:
            blocked_count += 1
            print(f"   ❌ 请求 {i+1}: 阻止 - {message}")

    stats = facade.rate_limiter.get_usage_stats(tenant.tenant_id)
    print(f"\n📊 统计: 成功={success_count}, 阻止={blocked_count}")


def demo_project_isolation():
    print("\n" + "="*60)
    print("演示4: 项目数据隔离")
    print("="*60)

    facade = TenantFacade()

    setup1 = facade.setup_tenant("Company A", "admin@companya.com")
    setup2 = facade.setup_tenant("Company B", "admin@companyb.com")

    project1 = facade.create_isolated_project(setup1["tenant"].tenant_id, "project-alpha", "Alpha项目")
    project2 = facade.create_isolated_project(setup2["tenant"].tenant_id, "project-beta", "Beta项目")

    print(f"\n🏢 创建两个租户的项目")
    print(f"   Company A: {project1.name}")
    print(f"   Company B: {project2.name}")

    path1 = facade.isolation.get_index_path(project1.project_id)
    path2 = facade.isolation.get_index_path(project2.project_id)

    print(f"\n📂 项目数据路径:")
    print(f"   {project1.name}: {path1}")
    print(f"   {project2.name}: {path2}")

    (path1 / "index.db").write_text("这是Alpha项目的索引数据")
    (path2 / "index.db").write_text("这是Beta项目的索引数据")

    data1 = (path1 / "index.db").read_text()
    data2 = (path2 / "index.db").read_text()

    print(f"\n✅ 数据完全隔离，互不干扰！")
    print(f"   Alpha: {data1}")
    print(f"   Beta: {data2}")


def main():
    print("\n" + "="*60)
    print("多租户和项目隔离演示")
    print("="*60)

    try:
        demo_tenant_management()
        demo_access_control()
        demo_rate_limiting()
        demo_project_isolation()

        print("\n" + "="*60)
        print("所有演示完成！")
        print("="*60)

    except KeyboardInterrupt:
        print("\n\n演示已停止")


if __name__ == "__main__":
    main()
