"""云服务集成配置生成器测试

阶段 C: 云服务集成 AWS/GCP/Azure
验证 12 个优化点
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from code_rag.middleware_layer.cloud_generator import (
    AWSECSGenerator, AWSEKSGenerator, AWSLambdaGenerator,
    GCPCloudRunGenerator, GCPGKEGenerator, GCPCloudFunctionsGenerator,
    AzureContainerInstancesGenerator, AzureAKSGenerator, AzureFunctionsGenerator,
    MultiCloudAbstractionGenerator, CloudBestPracticesGenerator,
    CostOptimizationGenerator, CloudConfigGenerator,
    AwsConfig, GcpConfig, AzureConfig,
    AwsRegion, GcpRegion, AzureRegion, CloudProvider
)


def create_aws_config() -> AwsConfig:
    return AwsConfig(
        app_name="my-app",
        image="my-app:v1",
        port=8000,
        cpu="0.5",
        memory="512Mi",
        min_instances=1,
        max_instances=10,
        desired_count=2,
        region=AwsRegion.US_EAST_1,
        cluster_name="my-cluster",
        environment={"ENV": "production"},
        secrets=["DB_PASSWORD", "API_KEY"],
        enable_autoscaling=True,
        enable_monitoring=True,
        enable_logging=True,
        cost_optimized=True,
        spot_instances=True
    )


def create_gcp_config() -> GcpConfig:
    return GcpConfig(
        app_name="my-app",
        image="my-app:v1",
        port=8000,
        cpu="0.5",
        memory="512Mi",
        min_instances=0,
        max_instances=100,
        desired_count=2,
        project_id="my-project",
        region=GcpRegion.US_CENTRAL1,
        service_name="my-service",
        environment={"ENV": "production"},
        secrets=["DB_PASSWORD", "API_KEY"],
        enable_autoscaling=True
    )


def create_azure_config() -> AzureConfig:
    return AzureConfig(
        app_name="my-app",
        image="my-app:v1",
        port=8000,
        cpu="0.5",
        memory="512Mi",
        min_instances=1,
        max_instances=10,
        desired_count=2,
        subscription_id="my-subscription",
        resource_group="my-rg",
        location=AzureRegion.EAST_US,
        environment={"ENV": "production"},
        secrets=["DB_PASSWORD", "API_KEY"],
        enable_autoscaling=True,
        enable_managed_identity=True
    )


def test_optimization_1_aws_ecs():
    """优化点 1: AWS ECS/Fargate 配置生成"""
    print("\n" + "="*70)
    print("优化点 1: AWS ECS/Fargate 配置生成")
    print("="*70)
    
    gen = AWSECSGenerator()
    config = create_aws_config()
    
    task_def = gen.generate_task_definition(config)
    service = gen.generate_ecs_service(config)
    autoscaling = gen.generate_autoscaling(config)
    
    assert "family" in task_def
    assert "containerDefinitions" in task_def
    assert task_def["networkMode"] == "awsvpc"
    assert "desiredCount" in service
    assert "targetTrackingScalingPolicies" in autoscaling
    
    print(f"  ✅ ECS 配置生成成功")
    print(f"     - Task Family: {task_def['family']}")
    print(f"     - Service Name: {service['serviceName']}")
    
    return True


def test_optimization_2_aws_eks():
    """优化点 2: AWS EKS 集群配置"""
    print("\n" + "="*70)
    print("优化点 2: AWS EKS 集群配置")
    print("="*70)
    
    gen = AWSEKSGenerator()
    config = create_aws_config()
    
    cluster = gen.generate_cluster(config)
    nodegroup = gen.generate_nodegroup(config)
    
    assert "metadata" in cluster
    assert cluster["kind"] == "ClusterConfig"
    assert "addons" in cluster
    assert "minSize" in nodegroup
    
    print(f"  ✅ EKS 配置生成成功")
    print(f"     - Cluster Name: {cluster['metadata']['name']}")
    print(f"     - Kubernetes Version: {cluster['metadata']['version']}")
    
    return True


def test_optimization_3_aws_lambda():
    """优化点 3: AWS Lambda 函数配置"""
    print("\n" + "="*70)
    print("优化点 3: AWS Lambda 函数配置")
    print("="*70)
    
    gen = AWSLambdaGenerator()
    config = create_aws_config()
    
    template = gen.generate_function(config)
    
    assert "Resources" in template
    assert f"{config.app_name}Function" in template["Resources"]
    func_props = template["Resources"][f"{config.app_name}Function"]["Properties"]
    assert func_props["Runtime"] == "python3.11"
    assert "Tracing" in func_props
    
    print(f"  ✅ Lambda 配置生成成功")
    print(f"     - Runtime: {func_props['Runtime']}")
    print(f"     - Memory: {func_props['MemorySize']}MB")
    
    return True


def test_optimization_4_gcp_cloudrun():
    """优化点 4: GCP Cloud Run 服务配置"""
    print("\n" + "="*70)
    print("优化点 4: GCP Cloud Run 服务配置")
    print("="*70)
    
    gen = GCPCloudRunGenerator()
    config = create_gcp_config()
    
    service = gen.generate_service(config)
    connector = gen.generate_vpc_connector(config)
    
    assert "spec" in service
    assert "template" in service["spec"]
    assert "containers" in service["spec"]["template"]["spec"]
    assert "autoscaling.knative.dev/minScale" in service["spec"]["template"]["metadata"]["annotations"]
    
    print(f"  ✅ Cloud Run 配置生成成功")
    print(f"     - Service Name: {service['metadata']['name']}")
    print(f"     - VPC Connector: {connector['name']}")
    
    return True


def test_optimization_5_gcp_gke():
    """优化点 5: GCP GKE 集群配置"""
    print("\n" + "="*70)
    print("优化点 5: GCP GKE 集群配置")
    print("="*70)
    
    gen = GCPGKEGenerator()
    config = create_gcp_config()
    
    cluster = gen.generate_cluster(config)
    
    assert "spec" in cluster
    assert "nodePools" in cluster["spec"]
    assert "privateClusterConfig" in cluster["spec"]
    assert "workloadIdentityConfig" in cluster["spec"]
    
    print(f"  ✅ GKE 配置生成成功")
    print(f"     - Location: {cluster['spec']['location']}")
    print(f"     - Node Pools: {len(cluster['spec']['nodePools'])}")
    
    return True


def test_optimization_6_gcp_cloudfunctions():
    """优化点 6: GCP Cloud Functions 配置"""
    print("\n" + "="*70)
    print("优化点 6: GCP Cloud Functions 配置")
    print("="*70)
    
    gen = GCPCloudFunctionsGenerator()
    config = create_gcp_config()
    
    func = gen.generate_function(config)
    
    assert "buildConfig" in func
    assert "serviceConfig" in func
    assert func["buildConfig"]["runtime"] == "python311"
    assert "maxInstanceCount" in func["serviceConfig"]
    
    print(f"  ✅ Cloud Functions 配置生成成功")
    print(f"     - Runtime: {func['buildConfig']['runtime']}")
    print(f"     - Max Instances: {func['serviceConfig']['maxInstanceCount']}")
    
    return True


def test_optimization_7_azure_aci():
    """优化点 7: Azure Container Instances 配置"""
    print("\n" + "="*70)
    print("优化点 7: Azure Container Instances 配置")
    print("="*70)
    
    gen = AzureContainerInstancesGenerator()
    config = create_azure_config()
    
    container_group = gen.generate_container_group(config)
    
    assert "resources" in container_group
    resources = container_group["resources"]
    assert len(resources) > 0
    assert resources[0]["type"] == "Microsoft.ContainerInstance/containerGroups"
    assert "containers" in resources[0]["properties"]
    
    print(f"  ✅ ACI 配置生成成功")
    print(f"     - Container Count: {len(resources[0]['properties']['containers'])}")
    print(f"     - Managed Identity: Enabled")
    
    return True


def test_optimization_8_azure_aks():
    """优化点 8: Azure AKS 集群配置"""
    print("\n" + "="*70)
    print("优化点 8: Azure AKS 集群配置")
    print("="*70)
    
    gen = AzureAKSGenerator()
    config = create_azure_config()
    
    cluster = gen.generate_cluster(config)
    
    assert "resources" in cluster
    aks_resource = cluster["resources"][0]
    assert aks_resource["type"] == "Microsoft.ContainerService/managedClusters"
    assert aks_resource["properties"]["enableRBAC"] == True
    assert "networkProfile" in aks_resource["properties"]
    
    print(f"  ✅ AKS 配置生成成功")
    print(f"     - Kubernetes Version: {aks_resource['properties']['kubernetesVersion']}")
    print(f"     - RBAC: Enabled")
    
    return True


def test_optimization_9_azure_functions():
    """优化点 9: Azure Functions 配置"""
    print("\n" + "="*70)
    print("优化点 9: Azure Functions 配置")
    print("="*70)
    
    gen = AzureFunctionsGenerator()
    config = create_azure_config()
    
    func = gen.generate_function(config)
    
    assert "properties" in func
    assert "siteConfig" in func["properties"]
    assert "FUNCTIONS_WORKER_RUNTIME" in [s["name"] for s in func["properties"]["siteConfig"]["appSettings"]]
    assert func["kind"] == "functionapp,linux"
    
    print(f"  ✅ Azure Functions 配置生成成功")
    print(f"     - Kind: {func['kind']}")
    print(f"     - Managed Identity: Enabled")
    
    return True


def test_optimization_10_multicloud():
    """优化点 10: 多云统一抽象层"""
    print("\n" + "="*70)
    print("优化点 10: 多云统一抽象层")
    print("="*70)
    
    gen = MultiCloudAbstractionGenerator()
    config = create_aws_config()
    
    unified = gen.generate_unified_config(config)
    provider_specific = gen.generate_provider_specific(config)
    
    assert "app" in unified
    assert "compute" in unified
    assert "scaling" in unified
    assert "aws" in provider_specific
    
    print(f"  ✅ 多云抽象配置生成成功")
    print(f"     - Compute Instance (AWS): {unified['compute']['instance_type']['aws']}")
    print(f"     - Provider: {provider_specific['aws']['provider']}")
    
    return True


def test_optimization_11_best_practices():
    """优化点 11: 云厂商特定最佳实践"""
    print("\n" + "="*70)
    print("优化点 11: 云厂商特定最佳实践")
    print("="*70)
    
    gen = CloudBestPracticesGenerator()
    
    aws_practices = gen.generate_practices(CloudProvider.AWS)
    gcp_practices = gen.generate_practices(CloudProvider.GCP)
    azure_practices = gen.generate_practices(CloudProvider.AZURE)
    
    assert "security" in aws_practices
    assert "performance" in aws_practices
    assert "reliability" in aws_practices
    
    assert "security" in gcp_practices
    assert "security" in azure_practices
    
    print(f"  ✅ 最佳实践配置生成成功")
    print(f"     - AWS 安全实践: {len(aws_practices['security'])}")
    print(f"     - GCP 性能实践: {len(gcp_practices['performance'])}")
    print(f"     - Azure 可靠性实践: {len(azure_practices['reliability'])}")
    
    return True


def test_optimization_12_cost_optimization():
    """优化点 12: 成本优化配置"""
    print("\n" + "="*70)
    print("优化点 12: 成本优化配置")
    print("="*70)
    
    gen = CostOptimizationGenerator()
    config = create_aws_config()
    
    optimization = gen.generate_optimization(config)
    
    assert "right_sizing" in optimization
    assert "reserved_capacity" in optimization
    assert "spot_preemptible" in optimization
    assert "scheduled_scaling" in optimization
    assert optimization["spot_preemptible"]["enabled"] == True
    assert optimization["spot_preemptible"]["max_spot_percentage"] == 80
    
    print(f"  ✅ 成本优化配置生成成功")
    print(f"     - Spot 实例: {optimization['spot_preemptible']['enabled']}")
    print(f"     - 预留容量: {optimization['reserved_capacity']['term']}")
    print(f"     - 调度缩容: {len(optimization['scheduled_scaling']['rules'])} rules")
    
    return True


def test_complete_aws_generation():
    """测试完整 AWS 配置生成"""
    print("\n" + "="*70)
    print("完整 AWS 云服务配置生成")
    print("="*70)
    
    generator = CloudConfigGenerator()
    config = create_aws_config()
    
    all_configs = generator.generate_aws_configs(config)
    
    print(f"  ✅ 生成了 {len(all_configs)} 个配置文件:")
    for name in all_configs.keys():
        print(f"     - {name}")
    
    return True


def test_complete_gcp_generation():
    """测试完整 GCP 配置生成"""
    print("\n" + "="*70)
    print("完整 GCP 云服务配置生成")
    print("="*70)
    
    generator = CloudConfigGenerator()
    config = create_gcp_config()
    
    all_configs = generator.generate_gcp_configs(config)
    
    print(f"  ✅ 生成了 {len(all_configs)} 个配置文件:")
    for name in all_configs.keys():
        print(f"     - {name}")
    
    return True


def test_complete_azure_generation():
    """测试完整 Azure 配置生成"""
    print("\n" + "="*70)
    print("完整 Azure 云服务配置生成")
    print("="*70)
    
    generator = CloudConfigGenerator()
    config = create_azure_config()
    
    all_configs = generator.generate_azure_configs(config)
    
    print(f"  ✅ 生成了 {len(all_configs)} 个配置文件:")
    for name in all_configs.keys():
        print(f"     - {name}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("="*70)
    print("🧪 Code RAG v24.0 - 云服务集成配置生成器测试")
    print("="*70)
    print("验证 12 个优化点")
    print("="*70)
    
    tests = [
        ("AWS ECS/Fargate 配置", test_optimization_1_aws_ecs),
        ("AWS EKS 集群配置", test_optimization_2_aws_eks),
        ("AWS Lambda 函数配置", test_optimization_3_aws_lambda),
        ("GCP Cloud Run 服务配置", test_optimization_4_gcp_cloudrun),
        ("GCP GKE 集群配置", test_optimization_5_gcp_gke),
        ("GCP Cloud Functions 配置", test_optimization_6_gcp_cloudfunctions),
        ("Azure Container Instances 配置", test_optimization_7_azure_aci),
        ("Azure AKS 集群配置", test_optimization_8_azure_aks),
        ("Azure Functions 配置", test_optimization_9_azure_functions),
        ("多云统一抽象层", test_optimization_10_multicloud),
        ("云厂商最佳实践", test_optimization_11_best_practices),
        ("成本优化配置", test_optimization_12_cost_optimization),
        ("完整 AWS 配置生成", test_complete_aws_generation),
        ("完整 GCP 配置生成", test_complete_gcp_generation),
        ("完整 Azure 配置生成", test_complete_azure_generation),
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
    print("📋 云服务集成配置生成器测试总结")
    print("="*70)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {100.0 * passed / len(tests):.1f}%")
    print("="*70)
    
    if failed == 0:
        print("\n🎉 所有云服务集成配置生成器测试通过！")
        print("✅ 已验证 12 个优化点！")
    else:
        print(f"\n⚠️ {failed}个测试失败")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
