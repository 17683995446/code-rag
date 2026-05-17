"""Code RAG v24.0 使用示例

展示如何使用所有云原生配置生成模块
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from code_rag.middleware_layer.kubernetes_generator import (
    KubernetesConfig, KubernetesConfigGenerator, ResourceRequirements, ProbeConfig
)
from code_rag.middleware_layer.docker_generator import (
    DockerBuildConfig, DockerConfigGenerator, BaseImage, ImageFlavor
)
from code_rag.middleware_layer.cloud_generator import (
    AwsConfig, GcpConfig, AzureConfig, CloudConfigGenerator,
    AwsRegion, GcpRegion, AzureRegion
)
from code_rag.middleware_layer.cicd_generator import (
    PipelineConfig, CICDConfigGenerator, DeploymentStrategy, Environment
)
from code_rag.middleware_layer.validators import (
    KubernetesValidator, validate_and_raise
)


def example_1_kubernetes_simple():
    """示例 1: 简单的 Kubernetes 配置生成"""
    print("\n" + "="*70)
    print("示例 1: 简单的 Kubernetes 配置生成")
    print("="*70)
    
    # 创建配置
    config = KubernetesConfig(
        app_name="my-webapp",
        image="myregistry.com/my-webapp:v1.0.0",
        port=8080,
        replicas=3
    )
    
    # 生成配置
    generator = KubernetesConfigGenerator()
    configs = generator.generate_all(config)
    
    # 打印生成的文件
    print(f"\n生成了 {len(configs)} 个配置文件:")
    for filename, content in configs.items():
        print(f"  - {filename}: {len(str(content))} 字符")
    
    return configs


def example_2_kubernetes_with_resources():
    """示例 2: 带资源限制的 Kubernetes 配置"""
    print("\n" + "="*70)
    print("示例 2: 带资源限制的 Kubernetes 配置")
    print("="*70)
    
    config = KubernetesConfig(
        app_name="api-service",
        image="api:v2.0.0",
        port=3000,
        replicas=5,
        namespace="production",
        resources=ResourceRequirements(
            cpu_request="250m",
            cpu_limit="1000m",
            memory_request="256Mi",
            memory_limit="1Gi"
        ),
        readiness_probe=ProbeConfig(
            enabled=True,
            initial_delay_seconds=15,
            period_seconds=5
        ),
        liveness_probe=ProbeConfig(
            enabled=True,
            initial_delay_seconds=30,
            period_seconds=10,
            failure_threshold=3
        )
    )
    
    generator = KubernetesConfigGenerator()
    deployment = generator.deployment_gen.generate(config)
    
    print(f"Deployment 名称: {deployment['metadata']['name']}")
    print(f"副本数: {deployment['spec']['replicas']}")
    print(f"容器镜像: {deployment['spec']['template']['spec']['containers'][0]['image']}")
    
    resources = deployment['spec']['template']['spec']['containers'][0]['resources']
    print(f"CPU 请求: {resources['requests']['cpu']}")
    print(f"内存限制: {resources['limits']['memory']}")
    
    return deployment


def example_3_docker_multistage():
    """示例 3: Docker 多阶段构建配置"""
    print("\n" + "="*70)
    print("示例 3: Docker 多阶段构建配置")
    print("="*70)
    
    config = DockerBuildConfig(
        app_name="python-api",
        language="python",
        base_image=BaseImage.ALPINE,
        port=8000,
        enable_multistage=True,
        enable_buildkit=True,
        non_root_user=True,
        read_only_rootfs=True,
        platforms=["linux/amd64", "linux/arm64"],
        env_vars={"LOG_LEVEL": "info", "ENV": "production"},
        enable_image_signing=True
    )
    
    generator = DockerConfigGenerator()
    configs = generator.generate_all(config)
    
    print(f"\n生成了 {len(configs)} 个配置文件:")
    for filename in configs.keys():
        print(f"  - {filename}")
    
    # 显示 Dockerfile 片段
    dockerfile = configs["Dockerfile"]
    lines = dockerfile.split("\n")
    print(f"\nDockerfile 片段 (前 15 行):")
    for line in lines[:15]:
        print(f"  {line}")
    
    return configs


def example_4_aws_ecs():
    """示例 4: AWS ECS/Fargate 配置"""
    print("\n" + "="*70)
    print("示例 4: AWS ECS/Fargate 配置")
    print("="*70)
    
    config = AwsConfig(
        app_name="web-service",
        image="my-registry.com/web:v1",
        port=80,
        region=AwsRegion.US_EAST_1,
        cluster_name="production-cluster",
        enable_fargate=True,
        spot_instances=True,
        enable_autoscaling=True,
        desired_count=2,
        min_instances=1,
        max_instances=10,
        environment={"ENV": "production", "LOG_LEVEL": "info"},
        secrets=["DB_PASSWORD", "API_KEY"]
    )
    
    generator = CloudConfigGenerator()
    configs = generator.generate_aws_configs(config)
    
    print(f"\n生成了 {len(configs)} 个 AWS 配置文件:")
    for filename in configs.keys():
        print(f"  - {filename}")
    
    # 显示任务定义片段
    task_def = configs["ecs-task-definition.json"]
    print(f"\nTask Definition:")
    print(f"  Family: {task_def['family']}")
    print(f"  CPU: {task_def['cpu']}")
    print(f"  Memory: {task_def['memory']}")
    print(f"  Container Count: {len(task_def['containerDefinitions'])}")
    
    return configs


def example_5_gcp_cloud_run():
    """示例 5: GCP Cloud Run 配置"""
    print("\n" + "="*70)
    print("示例 5: GCP Cloud Run 配置")
    print("="*70)
    
    config = GcpConfig(
        app_name="cloud-function",
        image="gcr.io/my-project/cloud-function:v1",
        port=8080,
        project_id="my-project",
        region=GcpRegion.US_CENTRAL1,
        service_name="cloud-function",
        min_instances=0,
        max_instances=100,
        enable_autoscaling=True,
        environment={"ENV": "production"}
    )
    
    generator = CloudConfigGenerator()
    configs = generator.generate_gcp_configs(config)
    
    print(f"\n生成了 {len(configs)} 个 GCP 配置文件:")
    for filename in configs.keys():
        print(f"  - {filename}")
    
    # 显示 Cloud Run 配置片段
    service = configs["cloudrun-service.yaml"]
    annotations = service["spec"]["template"]["metadata"]["annotations"]
    print(f"\nCloud Run 配置:")
    print(f"  Min Scale: {annotations['autoscaling.knative.dev/minScale']}")
    print(f"  Max Scale: {annotations['autoscaling.knative.dev/maxScale']}")
    print(f"  Execution Environment: {annotations['run.googleapis.com/execution-environment']}")
    
    return configs


def example_6_azure_aks():
    """示例 6: Azure AKS 配置"""
    print("\n" + "="*70)
    print("示例 6: Azure AKS 配置")
    print("="*70)
    
    config = AzureConfig(
        app_name="aks-service",
        image="myacr.azurecr.io/aks:v1",
        port=443,
        subscription_id="my-subscription-id",
        resource_group="my-resource-group",
        location=AzureRegion.EAST_US,
        enable_managed_identity=True,
        enable_autoscaling=True,
        desired_count=3,
        min_instances=1,
        max_instances=10,
        cost_optimized=True,
        environment={"ENV": "production"}
    )
    
    generator = CloudConfigGenerator()
    configs = generator.generate_azure_configs(config)
    
    print(f"\n生成了 {len(configs)} 个 Azure 配置文件:")
    for filename in configs.keys():
        print(f"  - {filename}")
    
    return configs


def example_7_github_actions():
    """示例 7: GitHub Actions CI/CD 配置"""
    print("\n" + "="*70)
    print("示例 7: GitHub Actions CI/CD 配置")
    print("="*70)
    
    config = PipelineConfig(
        app_name="my-app",
        language="python",
        docker_registry="ghcr.io",
        docker_repo="my-org/my-app",
        environments=[
            Environment.DEVELOPMENT,
            Environment.STAGING,
            Environment.PRODUCTION
        ],
        enable_security_scan=True,
        enable_integration_tests=True,
        enable_e2e_tests=True,
        deployment_strategy=DeploymentStrategy.CANARY,
        enable_rollback=True,
        enable_notifications=True,
        enable_iac=True,
        kubernetes_namespace="default"
    )
    
    generator = CICDConfigGenerator()
    configs = generator.generate_all(config)
    
    print(f"\n生成了 {len(configs)} 个配置模块:")
    for module_name in configs.keys():
        print(f"  - {module_name}")
    
    # 显示 GitHub Actions 工作流
    workflow = configs["github-actions"]["workflows"]["ci-cd.yml"]
    print(f"\nGitHub Actions 工作流:")
    print(f"  Name: {workflow['name']}")
    print(f"  Triggers: {list(workflow['on'].keys())}")
    print(f"  Jobs: {list(workflow['jobs'].keys())}")
    
    return configs


def example_8_validation():
    """示例 8: 使用验证器"""
    print("\n" + "="*70)
    print("示例 8: 使用验证器")
    print("="*70)
    
    # 验证 Kubernetes 名称
    test_names = ["my-app", "MyApp", "_invalid", "app-name", "a" * 253]
    
    print("\n名称验证:")
    for name in test_names:
        valid, error = KubernetesValidator.validate_name(name)
        status = "✅" if valid else "❌"
        print(f"  {status} '{name}': {error or '有效'}")
    
    # 验证端口
    test_ports = [80, 8080, 0, -1, 70000]
    
    print("\n端口验证:")
    for port in test_ports:
        valid, error = KubernetesValidator.validate_port(port)
        status = "✅" if valid else "❌"
        print(f"  {status} {port}: {error or '有效'}")
    
    # 使用 validate_and_raise
    print("\n使用 validate_and_raise:")
    try:
        validate_and_raise(KubernetesValidator.validate_name, "ValidApp", "name")
        print("  ✅ 验证通过")
    except Exception as e:
        print(f"  ❌ {e}")


def example_9_complete_workflow():
    """示例 9: 完整的云原生部署工作流"""
    print("\n" + "="*70)
    print("示例 9: 完整的云原生部署工作流")
    print("="*70)
    
    # 步骤 1: 定义应用
    print("\n📦 步骤 1: 定义应用配置")
    app_config = KubernetesConfig(
        app_name="production-app",
        image="myregistry.com/production-app:v1.0.0",
        port=8080,
        replicas=3,
        namespace="production",
        resources=ResourceRequirements(
            cpu_request="200m",
            cpu_limit="1000m",
            memory_request="256Mi",
            memory_limit="1Gi"
        )
    )
    print(f"  应用名称: {app_config.app_name}")
    print(f"  镜像: {app_config.image}")
    
    # 步骤 2: 生成 Kubernetes 配置
    print("\n📝 步骤 2: 生成 Kubernetes 配置")
    k8s_gen = KubernetesConfigGenerator()
    k8s_configs = k8s_gen.generate_all(app_config)
    print(f"  生成了 {len(k8s_configs)} 个配置文件")
    
    # 步骤 3: 生成 Docker 配置
    print("\n🐳 步骤 3: 生成 Docker 配置")
    docker_config = DockerBuildConfig(
        app_name=app_config.app_name,
        language="python",
        enable_multistage=True,
        non_root_user=True
    )
    docker_gen = DockerConfigGenerator()
    docker_configs = docker_gen.generate_all(docker_config)
    print(f"  生成了 {len(docker_configs)} 个配置文件")
    
    # 步骤 4: 生成云配置
    print("\n☁️ 步骤 4: 生成云配置 (AWS)")
    aws_config = AwsConfig(
        app_name=app_config.app_name,
        image="myregistry.com/" + app_config.app_name + ":latest",
        region=AwsRegion.US_EAST_1,
        enable_fargate=True
    )
    cloud_gen = CloudConfigGenerator()
    cloud_configs = cloud_gen.generate_aws_configs(aws_config)
    print(f"  生成了 {len(cloud_configs)} 个配置文件")
    
    # 步骤 5: 生成 CI/CD
    print("\n🔄 步骤 5: 生成 CI/CD 配置")
    cicd_config = PipelineConfig(
        app_name=app_config.app_name,
        deployment_strategy=DeploymentStrategy.ROLLING,
        enable_rollback=True
    )
    cicd_gen = CICDConfigGenerator()
    cicd_configs = cicd_gen.generate_all(cicd_config)
    print(f"  生成了 {len(cicd_configs)} 个配置模块")
    
    # 总结
    print("\n" + "="*70)
    print("📊 总计")
    print("="*70)
    total = len(k8s_configs) + len(docker_configs) + len(cloud_configs) + len(cicd_configs)
    print(f"  Kubernetes 配置: {len(k8s_configs)} 个文件")
    print(f"  Docker 配置: {len(docker_configs)} 个文件")
    print(f"  云配置: {len(cloud_configs)} 个文件")
    print(f"  CI/CD 配置: {len(cicd_configs)} 个模块")
    print(f"  总计: {total} 个配置项")


def run_all_examples():
    """运行所有示例"""
    print("="*70)
    print("🚀 Code RAG v24.0 使用示例")
    print("="*70)
    
    examples = [
        ("简单 Kubernetes 配置", example_1_kubernetes_simple),
        ("带资源限制的 Kubernetes", example_2_kubernetes_with_resources),
        ("Docker 多阶段构建", example_3_docker_multistage),
        ("AWS ECS/Fargate", example_4_aws_ecs),
        ("GCP Cloud Run", example_5_gcp_cloud_run),
        ("Azure AKS", example_6_azure_aks),
        ("GitHub Actions", example_7_github_actions),
        ("验证器使用", example_8_validation),
        ("完整工作流", example_9_complete_workflow),
    ]
    
    passed = 0
    failed = 0
    
    for name, func in examples:
        try:
            func()
            passed += 1
            print(f"\n✅ {name} - 成功")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} - 失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("📋 示例执行总结")
    print("="*70)
    print(f"✅ 成功: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {100*passed/len(examples):.1f}%")
    print("="*70)


if __name__ == "__main__":
    run_all_examples()
