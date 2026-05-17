#!/usr/bin/env python3
"""
Code RAG v22.0 - 团队协作索引测试
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v22.0 - 团队协作索引测试")
print("="*80)

from code_rag.service_layer.team_collaboration import (
    create_team_collaboration,
    UserManager,
    ProjectManager,
    SharedIndexManager,
    TeamCollaboration,
    AccessLevel,
    SyncStatus
)


def test_user_manager():
    """测试用户管理"""
    print("\n" + "="*70)
    print("测试 1: 用户管理")
    print("="*70)
    
    manager = UserManager()
    
    user1 = manager.create_user("alice", "alice@example.com", AccessLevel.ADMIN)
    user2 = manager.create_user("bob", "bob@example.com", AccessLevel.WRITE)
    
    assert user1 is not None
    assert user2 is not None
    
    print(f"  ✅ 创建用户成功: {user1.username}, {user2.username}")
    
    retrieved = manager.get_user(user1.user_id)
    assert retrieved is not None
    assert retrieved.email == "alice@example.com"
    print(f"  ✅ 按用户 ID 获取成功: {retrieved.username}")
    
    by_email = manager.get_user_by_email("bob@example.com")
    assert by_email is not None
    print(f"  ✅ 按邮箱获取成功: {by_email.username}")
    
    all_users = manager.list_users()
    assert len(all_users) == 2
    print(f"  ✅ 列出所有用户: {len(all_users)} 个")
    
    return True


def test_project_manager():
    """测试项目管理"""
    print("\n" + "="*70)
    print("测试 2: 项目管理")
    print("="*70)
    
    user_manager = UserManager()
    owner = user_manager.create_user("owner", "owner@example.com")
    
    project_manager = ProjectManager(user_manager)
    
    project = project_manager.create_project("My Awesome Project", owner.user_id, "Description")
    
    assert project is not None
    assert project.name == "My Awesome Project"
    print(f"  ✅ 创建项目成功: {project.name}")
    
    member = user_manager.create_user("dev1", "dev1@example.com")
    added = project_manager.add_member(project.project_id, member.user_id)
    assert added is True
    print(f"  ✅ 添加团队成员成功")
    
    user_projects = project_manager.get_user_projects(owner.user_id)
    assert len(user_projects) == 1
    print(f"  ✅ 获取用户项目成功: {len(user_projects)} 个")
    
    return True


def test_shared_index_manager():
    """测试共享索引管理"""
    print("\n" + "="*70)
    print("测试 3: 共享索引管理")
    print("="*70)
    
    user_manager = UserManager()
    owner = user_manager.create_user("owner", "owner@example.com")
    
    project_manager = ProjectManager(user_manager)
    project = project_manager.create_project("Test Project", owner.user_id)
    
    index_manager = SharedIndexManager(project_manager)
    
    index = index_manager.create_index(
        project.project_id, 
        "Code Library Index",
        {"version": 1, "data": "test"}
    )
    
    assert index is not None
    print(f"  ✅ 创建共享索引成功: {index.name}")
    
    synced = index_manager.sync_index(index.index_id)
    assert synced is True
    assert index.sync_status == SyncStatus.SYNCED
    print(f"  ✅ 索引同步成功: {index.sync_status.value}")
    
    project_indexes = index_manager.get_project_indexes(project.project_id)
    assert len(project_indexes) == 1
    print(f"  ✅ 获取项目索引成功: {len(project_indexes)} 个")
    
    return True


def test_team_collaboration_service():
    """测试团队协作服务"""
    print("\n" + "="*70)
    print("测试 4: 团队协作服务")
    print("="*70)
    
    collaboration = create_team_collaboration()
    
    setup = collaboration.setup_team("Dev Team", "team@example.com", "team_lead")
    assert setup is not None
    assert setup.get("project") is not None
    print(f"  ✅ 快速设置团队成功")
    
    project_id = setup["project"]["project_id"]
    
    added = collaboration.add_team_member(
        project_id, 
        "dev@example.com", 
        "developer", 
        AccessLevel.WRITE
    )
    assert added is True
    print(f"  ✅ 添加团队成员成功")
    
    report = collaboration.get_team_report(project_id)
    assert report is not None
    print(f"  ✅ 生成团队报告成功")
    print(f"     - 项目: {report['project']['name']}")
    print(f"     - 成员数: {report['member_count']}")
    
    return True


def test_access_control():
    """测试访问控制"""
    print("\n" + "="*70)
    print("测试 5: 访问控制")
    print("="*70)
    
    user_manager = UserManager()
    
    admin_user = user_manager.create_user("admin", "admin@example.com", AccessLevel.ADMIN)
    writer_user = user_manager.create_user("writer", "writer@example.com", AccessLevel.WRITE)
    reader_user = user_manager.create_user("reader", "reader@example.com", AccessLevel.READ)
    
    assert admin_user.access_level == AccessLevel.ADMIN
    assert writer_user.access_level == AccessLevel.WRITE
    assert reader_user.access_level == AccessLevel.READ
    print(f"  ✅ 创建不同访问级别的用户成功")
    
    user_manager.update_access_level(reader_user.user_id, AccessLevel.WRITE)
    updated = user_manager.get_user(reader_user.user_id)
    assert updated.access_level == AccessLevel.WRITE
    print(f"  ✅ 更新访问级别成功")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("用户管理", test_user_manager),
        ("项目管理", test_project_manager),
        ("共享索引管理", test_shared_index_manager),
        ("团队协作服务", test_team_collaboration_service),
        ("访问控制", test_access_control)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n[{passed+1+failed}/{len(tests)}] 执行: {name}")
            if test_func():
                passed += 1
                print(f"\n✅ {name} - 通过")
            else:
                failed += 1
                print(f"\n❌ {name} - 失败")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} - 异常: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("📋 团队协作索引测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有团队协作索引测试通过！")
        return True
    else:
        print(f"\n⚠️ {failed}个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
