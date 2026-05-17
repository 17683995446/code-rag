"""CI/CD Pipeline 生成器测试

阶段 D: CI/CD Pipeline 生成
验证 12 个优化点
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from code_rag.middleware_layer.cicd_generator import (
    GitHubActionsGenerator, GitLabCIGenerator, JenkinsPipelineGenerator,
    ArgoCDGenerator, TektonPipelineGenerator, AutomatedTestingGenerator,
    SecurityScanGenerator, ContainerBuildGenerator, DeploymentStrategyGenerator,
    IaCIntegrationGenerator, NotificationGenerator, RollbackRecoveryGenerator,
    CICDConfigGenerator, PipelineConfig, DeploymentStrategy, Environment
)


def create_pipeline_config() -> PipelineConfig:
    return PipelineConfig(
        app_name="my-app",
        language="python",
        docker_registry="ghcr.io",
        docker_repo="my-org/my-app",
        environments=[Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION],
        enable_security_scan=True,
        enable_integration_tests=True,
        enable_e2e_tests=True,
        deployment_strategy=DeploymentStrategy.CANARY,
        enable_rollback=True,
        enable_notifications=True,
        enable_iac=True,
        kubernetes_namespace="default"
    )


def test_optimization_1_github_actions():
    """优化点 1: GitHub Actions 工作流生成"""
    print("\n" + "="*70)
    print("优化点 1: GitHub Actions 工作流生成")
    print("="*70)
    
    gen = GitHubActionsGenerator()
    config = create_pipeline_config()
    
    workflow = gen.generate_workflow(config)
    
    assert "name" in workflow
    assert "on" in workflow
    assert "jobs" in workflow
    assert "lint" in workflow["jobs"]
    assert "test" in workflow["jobs"]
    assert "build" in workflow["jobs"]
    assert "deploy-production" in workflow["jobs"]
    
    print(f"  ✅ GitHub Actions 工作流生成成功")
    print(f"     - Jobs: {len(workflow['jobs'])}")
    print(f"     - Build 输出: {'image_tag' in workflow['jobs']['build'].get('outputs', {})}")
    
    return True


def test_optimization_2_gitlab_ci():
    """优化点 2: GitLab CI Pipeline 配置"""
    print("\n" + "="*70)
    print("优化点 2: GitLab CI Pipeline 配置")
    print("="*70)
    
    gen = GitLabCIGenerator()
    config = create_pipeline_config()
    
    pipeline = gen.generate_pipeline(config)
    
    assert "stages" in pipeline
    assert "lint" in pipeline
    assert "test" in pipeline
    assert "build" in pipeline
    assert "deploy-production" in pipeline
    
    print(f"  ✅ GitLab CI Pipeline 生成成功")
    print(f"     - Stages: {len(pipeline['stages'])}")
    print(f"     - Jobs: {len(pipeline) - 2}")  # excluding stages and variables
    
    return True


def test_optimization_3_jenkins():
    """优化点 3: Jenkins Pipeline (Jenkinsfile)"""
    print("\n" + "="*70)
    print("优化点 3: Jenkins Pipeline (Jenkinsfile)")
    print("="*70)
    
    gen = JenkinsPipelineGenerator()
    config = create_pipeline_config()
    
    jenkinsfile = gen.generate_jenkinsfile(config)
    
    assert "pipeline {" in jenkinsfile
    assert "stages {" in jenkinsfile or "stage('Checkout')" in jenkinsfile
    assert "stage('Lint')" in jenkinsfile
    assert "stage('Test')" in jenkinsfile
    assert "stage('Deploy to Production')" in jenkinsfile
    
    print(f"  ✅ Jenkinsfile 生成成功")
    print(f"     - 文件大小: {len(jenkinsfile)} 字符")
    print(f"     - 包含 post 块: {'post {' in jenkinsfile}")
    
    return True


def test_optimization_4_argocd():
    """优化点 4: ArgoCD Application 配置"""
    print("\n" + "="*70)
    print("优化点 4: ArgoCD Application 配置")
    print("="*70)
    
    gen = ArgoCDGenerator()
    config = create_pipeline_config()
    
    application = gen.generate_application(config)
    app_of_apps = gen.generate_app_of_apps(config)
    
    assert application["kind"] == "Application"
    assert "spec" in application
    assert "syncPolicy" in application["spec"]
    assert application["spec"]["syncPolicy"]["automated"]["prune"] == True
    
    print(f"  ✅ ArgoCD 配置生成成功")
    print(f"     - Application: {application['metadata']['name']}")
    print(f"     - 自动同步: ✅")
    
    return True


def test_optimization_5_tekton():
    """优化点 5: Tekton Pipeline 配置"""
    print("\n" + "="*70)
    print("优化点 5: Tekton Pipeline 配置")
    print("="*70)
    
    gen = TektonPipelineGenerator()
    config = create_pipeline_config()
    
    pipeline = gen.generate_pipeline(config)
    
    assert pipeline["kind"] == "Pipeline"
    assert "tasks" in pipeline["spec"]
    assert len(pipeline["spec"]["tasks"]) == 5
    assert any(t["name"] == "git-clone" for t in pipeline["spec"]["tasks"])
    assert any(t["name"] == "deploy" for t in pipeline["spec"]["tasks"])
    
    print(f"  ✅ Tekton Pipeline 生成成功")
    print(f"     - Tasks: {len(pipeline['spec']['tasks'])}")
    
    return True


def test_optimization_6_testing():
    """优化点 6: 自动化测试集成"""
    print("\n" + "="*70)
    print("优化点 6: 自动化测试集成")
    print("="*70)
    
    gen = AutomatedTestingGenerator()
    config = create_pipeline_config()
    
    test_config = gen.generate_test_config(config)
    
    assert "unit_tests" in test_config
    assert "integration_tests" in test_config
    assert "e2e_tests" in test_config
    assert test_config["integration_tests"]["framework"] == "pytest"
    assert test_config["e2e_tests"]["framework"] == "playwright"
    
    print(f"  ✅ 测试配置生成成功")
    print(f"     - 单元测试框架: {test_config['unit_tests']['framework']}")
    print(f"     - E2E 测试框架: {test_config['e2e_tests']['framework']}")
    
    return True


def test_optimization_7_security():
    """优化点 7: 安全扫描集成"""
    print("\n" + "="*70)
    print("优化点 7: 安全扫描集成")
    print("="*70)
    
    gen = SecurityScanGenerator()
    config = create_pipeline_config()
    
    security = gen.generate_security_config(config)
    
    assert security["enabled"] == True
    assert "sast" in security
    assert "dast" in security
    assert "sca" in security
    assert "container_scan" in security
    assert len(security["sast"]["tools"]) >= 2
    
    print(f"  ✅ 安全扫描配置生成成功")
    print(f"     - SAST 工具: {len(security['sast']['tools'])}")
    print(f"     - SCA 工具: {len(security['sca']['tools'])}")
    
    return True


def test_optimization_8_container():
    """优化点 8: 容器镜像构建与推送"""
    print("\n" + "="*70)
    print("优化点 8: 容器镜像构建与推送")
    print("="*70)
    
    gen = ContainerBuildGenerator()
    config = create_pipeline_config()
    
    build_config = gen.generate_build_config(config)
    
    assert "registry" in build_config
    assert "tags" in build_config
    assert "buildx" in build_config
    assert build_config["buildx"]["enabled"] == True
    assert "linux/amd64" in build_config["buildx"]["platforms"]
    assert "provenance" in build_config
    assert "sbom" in build_config
    
    print(f"  ✅ 容器构建配置生成成功")
    print(f"     - 多架构: {len(build_config['buildx']['platforms'])}")
    print(f"     - Provenance: ✅")
    print(f"     - SBOM: ✅")
    
    return True


def test_optimization_9_deployment():
    """优化点 9: 部署策略"""
    print("\n" + "="*70)
    print("优化点 9: 部署策略")
    print("="*70)
    
    gen = DeploymentStrategyGenerator()
    config = create_pipeline_config()
    
    strategy = gen.generate_strategy(config)
    
    assert "strategy" in strategy
    assert strategy["strategy"] == "canary"
    assert "steps" in strategy
    assert len(strategy["steps"]) >= 3
    assert "analysis" in strategy
    
    print(f"  ✅ 部署策略配置生成成功")
    print(f"     - 策略类型: {strategy['strategy']}")
    print(f"     - 渐进式步骤: {len(strategy['steps'])}")
    
    return True


def test_optimization_10_iac():
    """优化点 10: 基础设施即代码集成"""
    print("\n" + "="*70)
    print("优化点 10: 基础设施即代码集成")
    print("="*70)
    
    gen = IaCIntegrationGenerator()
    config = create_pipeline_config()
    
    iac_config = gen.generate_iac_config(config)
    
    assert iac_config["enabled"] == True
    assert "terraform" in iac_config
    assert "helm" in iac_config
    assert "kustomize" in iac_config
    assert "security_scan" in iac_config["terraform"]
    
    print(f"  ✅ IaC 配置生成成功")
    print(f"     - Terraform workspace: {len(iac_config['terraform']['workspace'])}")
    print(f"     - Kustomize overlays: {len(iac_config['kustomize']['overlays'])}")
    
    return True


def test_optimization_11_notifications():
    """优化点 11: 通知与告警集成"""
    print("\n" + "="*70)
    print("优化点 11: 通知与告警集成")
    print("="*70)
    
    gen = NotificationGenerator()
    config = create_pipeline_config()
    
    notifications = gen.generate_notification_config(config)
    
    assert notifications["enabled"] == True
    assert "slack" in notifications["channels"]
    assert "email" in notifications["channels"]
    assert "pagerduty" in notifications
    assert "events" in notifications["slack"]
    
    print(f"  ✅ 通知配置生成成功")
    print(f"     - 通知渠道: {len(notifications['channels'])}")
    print(f"     - Slack 事件: {len(notifications['slack']['events'])}")
    
    return True


def test_optimization_12_rollback():
    """优化点 12: 回滚与恢复机制"""
    print("\n" + "="*70)
    print("优化点 12: 回滚与恢复机制")
    print("="*70)
    
    gen = RollbackRecoveryGenerator()
    config = create_pipeline_config()
    
    rollback = gen.generate_rollback_config(config)
    
    assert rollback["enabled"] == True
    assert "automatic_rollback" in rollback
    assert "manual_rollback" in rollback
    assert "backup" in rollback
    assert "recovery" in rollback
    assert len(rollback["automatic_rollback"]["triggers"]) >= 2
    
    print(f"  ✅ 回滚配置生成成功")
    print(f"     - 自动回滚触发器: {len(rollback['automatic_rollback']['triggers'])}")
    print(f"     - 备份: ✅")
    
    return True


def test_complete_cicd_generation():
    """测试完整 CI/CD 配置生成"""
    print("\n" + "="*70)
    print("完整 CI/CD Pipeline 配置生成")
    print("="*70)
    
    generator = CICDConfigGenerator()
    config = create_pipeline_config()
    
    all_configs = generator.generate_all(config)
    
    print(f"  ✅ 生成了 {len(all_configs)} 个配置模块:")
    for name in all_configs.keys():
        print(f"     - {name}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("="*70)
    print("🧪 Code RAG v24.0 - CI/CD Pipeline 生成器测试")
    print("="*70)
    print("验证 12 个优化点")
    print("="*70)
    
    tests = [
        ("GitHub Actions 工作流", test_optimization_1_github_actions),
        ("GitLab CI Pipeline", test_optimization_2_gitlab_ci),
        ("Jenkins Pipeline", test_optimization_3_jenkins),
        ("ArgoCD Application", test_optimization_4_argocd),
        ("Tekton Pipeline", test_optimization_5_tekton),
        ("自动化测试集成", test_optimization_6_testing),
        ("安全扫描集成", test_optimization_7_security),
        ("容器镜像构建", test_optimization_8_container),
        ("部署策略", test_optimization_9_deployment),
        ("IaC 集成", test_optimization_10_iac),
        ("通知与告警", test_optimization_11_notifications),
        ("回滚与恢复", test_optimization_12_rollback),
        ("完整配置生成", test_complete_cicd_generation),
    ]
    
    passed = 0
    failed = 0
    
    for i, (name, test_func) in enumerate(tests, 1):
        print(f"\n[{i}/{len(tests)}] 执行: {name}")
        try:
            if test_func():
                print(f"\n✅ {name} - 通过")
                passed += 1
            else:
                print(f"\n❌ {name} - 失败")
                failed += 1
        except Exception as e:
            print(f"\n❌ {name} - 异常: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print("📋 CI/CD Pipeline 生成器测试总结")
    print("="*70)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {100.0 * passed / len(tests):.1f}%")
    print("="*70)
    
    if failed == 0:
        print("\n🎉 所有 CI/CD Pipeline 生成器测试通过！")
        print("✅ 已验证 12 个优化点！")
    else:
        print(f"\n⚠️ {failed}个测试失败")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
