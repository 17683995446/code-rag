#!/usr/bin/env python3
"""
多租户和项目隔离演示

演示如何使用多租户系统隔离不同项目的数据和资源
"""

import sys
import time
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from optimized.multi_tenant import (
    TenantFacade,
    TenantManager,
    AccessControl,
    ProjectIsolation,
    RateLimiter,
    ResourceQuota,
    TenantStatus,
    ProjectStatus
)


def demo_tenant_management():
    """
    演示租户管理
    """
    print("\n" + "="*60)
    print("演示1: 租户管理")
    print("="*60)

    facade = TenantFacade("/tmp/multi_tenant_demo/tenants")

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
    print(f"   租户ID: {tenant.tenant_id}")
    print(f"   配额:")
    print(f"     - 最大项目数: {tenant.quotas['max_projects']}")
    print(f"     - 最大存储: {tenant.quotas['max_storage_mb']} MB")
    print(f"     - 最大chunks: {tenant.quotas['max_chunks']}")

    print(f"\n✅ 创建默认项目: {default_project.name}")
    print(f"   项目ID: {default_project.project_id}")

    projects = facade.tenant_manager.list_projects(tenant.tenant_id)
    print(f"\n📁 当前项目数: {len(projects)}")

    new_project = facade.create_isolated_project(
        tenant.tenant_id,
        "backend-api",
        "后端API服务"
    )

    if new_project:
        print(f"✅ 创建新项目: {new_project.name} ({new_project.project_id})")
        print(f"   描述: {new_project.description}")

        index_path = facade.isolation.get_index_path(new_project.project_id)
        print(f"   索引路径: {index_path}")

        cache_path = facade.isolation.get_cache_path(new_project.project_id)
        print(f"   缓存路径: {cache_path}")

    usage = facade.tenant_manager.get_tenant_usage(tenant.tenant_id)
    print(f"\n📊 资源使用情况:")
    print(f"   项目数: {usage['project_count']}/{usage['max_projects']}")
    print(f"   存储使用: {usage['storage_used_mb']:.2f}/{usage['max_storage_mb']} MB")
    print(f"   Chunks: {usage['total_chunks']}/{usage['max_chunks']}")

    return facade, tenant


def demo_access_control():
    """
    演示访问控制
    """
    print("\n" + "="*60)
    print("演示2: 访问控制")
    print("="*60)

    facade = TenantFacade("/tmp/multi_tenant_demo/tenants")
    setup = facade.setup_tenant("Tech Startup", "admin@startup.com")

    tenant = setup["tenant"]
    project = setup["default_project"]

    access = facade.access_control

    print(f"\n👥 分配角色:")

    access.assign_role("user_001", tenant.tenant_id, "admin")
    print(f"   user_001 -> admin")

    access.assign_role("user_002", tenant.tenant_id, "manager")
    print(f"   user_002 -> manager")

    access.assign_role("user_003", tenant.tenant_id, "user")
    print(f"   user_003 -> user")

    access.assign_role("user_004", tenant.tenant_id, "viewer")
    print(f"   user_004 -> viewer")

    print(f"\n🔐 权限检查:")

    users = ["user_001", "user_002", "user_003", "user_004"]
    permissions = ["tenant:write", "project:write", "index:read", "api:admin"]

    for user_id in users:
        print(f"\n   {user_id}:")
        for perm in permissions:
            has_perm = access.has_permission(user_id, tenant.tenant_id, perm)
            status = "✅" if has_perm else "❌"
            print(f"     {status} {perm}")

    role = access.get_role("user_002", tenant.tenant_id)
    perms = access.list_user_permissions("user_002", tenant.tenant_id)
    print(f"\n   user_002 角色: {role}")
    print(f"   权限数量: {len(perms)}")


def demo_rate_limiting():
    """
    演示速率限制
    """
    print("\n" + "="*60)
    print("演示3: 速率限制")
    print("="*60)

    facade = TenantFacade("/tmp/multi_tenant_demo/tenants")
    setup = facade.setup_tenant("Rate Limited Corp", "admin@ratelimit.com")

    tenant = setup["tenant"]

    print(f"\n⚡ 测试速率限制:")
    print(f"   最大并发请求: {tenant.quotas['max_concurrent_requests']}")
    print(f"   每日API限制: {tenant.quotas['max_api_calls_per_day']}")

    print(f"\n📈 模拟API调用:")

    success_count = 0
    blocked_count = 0

    for i in range(15):
        allowed, message = facade.rate_limiter.check_rate_limit(
            tenant.tenant_id,
            "api_call"
        )

        if allowed:
            success_count += 1
            if success_count % 5 == 0:
                print(f"   ✅ 请求 {i+1}: 成功")
                facade.rate_limiter.release_request(tenant.tenant_id)
        else:
            blocked_count += 1
            print(f"   ❌ 请求 {i+1}: 阻止 - {message}")

    stats = facade.rate_limiter.get_usage_stats(tenant.tenant_id)
    print(f"\n📊 最终统计:")
    print(f"   成功请求: {success_count}")
    print(f"   阻止请求: {blocked_count}")
    print(f"   剩余配额: {stats['remaining']}/{stats['daily_limit']}")


def demo_project_isolation():
    """
    演示项目隔离
    """
    print("\n" + "="*60)
    print("演示4: 项目数据隔离")
    print("="*60)

    facade = TenantFacade("/tmp/multi_tenant_demo/tenants")

    tenant1_setup = facade.setup_tenant("Company A", "admin@companya.com")
    tenant2_setup = facade.setup_tenant("Company B", "admin@companyb.com")

    tenant1 = tenant1_setup["tenant"]
    tenant2 = tenant2_setup["tenant"]

    project1 = facade.create_isolated_project(tenant1.tenant_id, "project-alpha", "Alpha项目")
    project2 = facade.create_isolated_project(tenant2.tenant_id, "project-beta", "Beta项目")

    print(f"\n🏢 创建两个租户的项目:")
    print(f"   租户A: {tenant1.name}")
    print(f"     - 项目: {project1.name}")
    print(f"   租户B: {tenant2.name}")
    print(f"     - 项目: {project2.name}")

    path1 = facade.isolation.get_index_path(project1.project_id)
    path2 = facade.isolation.get_index_path(project2.project_id)

    print(f"\n📂 项目数据路径:")
    print(f"   {project1.name}: {path1}")
    print(f"   {project2.name}: {path2}")

    path1.mkdir(parents=True, exist_ok=True)
    path2.mkdir(parents=True, exist_ok=True)

    (path1 / "index.db").write_text("这是Alpha项目的索引数据")
    (path2 / "index.db").write_text("这是Beta项目的索引数据")

    print(f"\n✅ 写入隔离数据:")

    data1 = (path1 / "index.db").read_text()
    data2 = (path2 / "index.db").read_text()

    print(f"   Alpha项目数据: {data1}")
    print(f"   Beta项目数据: {data2}")

    size1 = facade.isolation.get_project_size(project1.project_id)
    size2 = facade.isolation.get_project_size(project2.project_id)

    print(f"\n💾 项目大小:")
    print(f"   Alpha: {size1} bytes")
    print(f"   Beta: {size2} bytes")

    print(f"\n🔒 数据完全隔离，互不干扰！")


def demo_full_workflow():
    """
    演示完整工作流
    """
    print("\n" + "="*60)
    print("完整工作流演示")
    print("="*60)

    facade = TenantFacade("/tmp/multi_tenant_demo/tenants")

    print("\n🚀 步骤1: 创建企业租户")
    enterprise = facade.setup_tenant(
        "Enterprise Corp",
        "it@enterprise.com",
        quotas=ResourceQuota(
            max_projects=20,
            max_storage_mb=10240,
            max_api_calls_per_day=50000
        )
    )
    tenant = enterprise["tenant"]
    print(f"   创建租户: {tenant.name}")

    print("\n👥 步骤2: 创建用户和分配角色")
    facade.access_control.assign_role("admin_user", tenant.tenant_id, "admin")
    facade.access_control.assign_role("dev_user", tenant.tenant_id, "manager")
    facade.access_control.assign_role("test_user", tenant.tenant_id, "user")
    print(f"   分配3个用户角色")

    print("\n📁 步骤3: 创建多个项目")
    projects = []
    for name, desc in [
        ("frontend", "前端应用"),
        ("backend-api", "后端API"),
        ("mobile-app", "移动应用"),
        ("data-pipeline", "数据管道")
    ]:
        proj = facade.create_isolated_project(tenant.tenant_id, name, desc)
        if proj:
            projects.append(proj)
            print(f"   ✅ 创建项目: {proj.name}")

    print("\n🔐 步骤4: 验证访问控制")
    test_user = "test_user"
    test_project = projects[0].project_id

    allowed, msg = facade.verify_access(test_user, test_project, "index:read")
    print(f"   {test_user} 读取 {projects[0].name}: {'✅ 允许' if allowed else '❌ 拒绝'}")

    allowed, msg = facade.verify_access(test_user, test_project, "project:delete")
    print(f"   {test_user} 删除 {projects[0].name}: {'✅ 允许' if allowed else '❌ 拒绝'}")

    print("\n📊 步骤5: 生成使用报告")
    report = facade.get_full_usage_report(tenant.tenant_id)
    print(f"   租户: {report['tenant']['name']}")
    print(f"   项目数: {len(report['projects'])}")
    print(f"   存储使用: {report['usage']['storage_used_mb']:.2f} MB")
    print(f"   API配额: {report['rate_limiting']['daily_usage']}/{report['rate_limiting']['daily_limit']}")

    print("\n🧹 步骤6: 清理资源")
    facade.delete_tenant_with_data(tenant.tenant_id)
    print(f"   ✅ 删除租户及其所有项目数据")


def main():
    print("\n" + "="*60)
    print("多租户和项目隔离演示")
    print("="*60)
    print("\n本示例演示了完整的SaaS多租户架构，")
    print("包括租户管理、访问控制、速率限制和项目隔离。")

    try:
        demo_tenant_management()
        demo_access_control()
        demo_rate_limiting()
        demo_project_isolation()
        demo_full_workflow()

        print("\n" + "="*60)
        print("所有演示完成！")
        print("\n功能总结:")
        print("1. 租户管理：创建、更新、删除租户")
        print("2. 项目隔离：每个项目有独立的数据存储")
        print("3. 访问控制：基于角色的权限管理")
        print("4. 速率限制：API调用频率和并发控制")
        print("5. 资源配额：可配置的存储和用量限制")
        print("="*60)

    except KeyboardInterrupt:
        print("\n\n演示已停止")


if __name__ == "__main__":
    main()
