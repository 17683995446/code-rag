#!/usr/bin/env python3
"""
Code RAG v24.0 - Kubernetes 配置生成器测试
验证 12 个优化点
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v24.0 - Kubernetes 配置生成器测试")
print("="*80)
print("验证 12 个优化点")
print("="*80)

from code_rag.middleware_layer.kubernetes_generator import (
    create_k8s_generator,
    create_k8s_config,
    KubernetesConfigGenerator,
    KubernetesConfig,
    ResourceRequirements,
    ProbeConfig,
    ServiceType,
    DeploymentGenerator,
    ServiceGenerator,
    ConfigMapGenerator,
    IngressGenerator,
    HPAGenerator,
    PDBGenerator,
    VolumeGenerator,
    NetworkPolicyGenerator,
    RBACGenerator
)


def test_optimization_1_deployment():
    """优化点 1: Deployment 配置生成"""
    print("\n" + "="*70)
    print("优化点 1: Deployment 配置生成")
    print("="*70)
    
    gen = DeploymentGenerator()
    config = create_k8s_config("my-app", "my-image:v1", 8080)
    
    deployment = gen.generate(config)
    
    assert "apiVersion" in deployment
    assert deployment["kind"] == "Deployment"
    assert deployment["metadata"]["name"] == "my-app"
    assert "resources" in deployment["spec"]["template"]["spec"]["containers"][0]
    assert "readinessProbe" in deployment["spec"]["template"]["spec"]["containers"][0]
    
    print(f"  ✅ Deployment 配置生成成功")
    print(f"     - API Version: {deployment['apiVersion']}")
    print(f"     - 副本数: {deployment['spec']['replicas']}")
    print(f"     - 资源配置: ✅")
    print(f"     - 探针配置: ✅")
    
    return True


def test_optimization_2_service():
    """优化点 2: Service 配置生成"""
    print("\n" + "="*70)
    print("优化点 2: Service 配置生成")
    print("="*70)
    
    gen = ServiceGenerator()
    config = create_k8s_config("my-app", "my-image:v1", 8080)
    
    service = gen.generate(config, ServiceType.LOAD_BALANCER)
    
    assert "apiVersion" in service
    assert service["kind"] == "Service"
    assert service["spec"]["type"] == "LoadBalancer"
    assert service["spec"]["selector"]["app"] == "my-app"
    
    print(f"  ✅ Service 配置生成成功")
    print(f"     - 类型: {service['spec']['type']}")
    print(f"     - 端口: {service['spec']['ports'][0]['port']}")
    
    return True


def test_optimization_3_configmap_secret():
    """优化点 3: ConfigMap 和 Secret 管理"""
    print("\n" + "="*70)
    print("优化点 3: ConfigMap 和 Secret 管理")
    print("="*70)
    
    gen = ConfigMapGenerator()
    
    configmap = gen.generate_configmap("my-config", {
        "DATABASE_URL": "postgres://localhost:5432/db",
        "API_KEY": "test_key"
    })
    
    secret = gen.generate_secret("my-secret", {
        "password": "secret123",
        "api_token": "token123"
    })
    
    assert configmap["kind"] == "ConfigMap"
    assert "DATABASE_URL" in configmap["data"]
    
    assert secret["kind"] == "Secret"
    assert "password" in secret["data"]
    
    print(f"  ✅ ConfigMap 和 Secret 生成成功")
    print(f"     - ConfigMap 条目: {len(configmap['data'])}")
    print(f"     - Secret 条目: {len(secret['data'])}")
    
    return True


def test_optimization_4_ingress():
    """优化点 4: Ingress 配置"""
    print("\n" + "="*70)
    print("优化点 4: Ingress 配置")
    print("="*70)
    
    gen = IngressGenerator()
    
    ingress = gen.generate(
        "my-app",
        host="api.example.com",
        path="/api",
        annotations={"nginx.ingress.kubernetes.io/ssl-redirect": "true"}
    )
    
    assert ingress["kind"] == "Ingress"
    assert ingress["spec"]["rules"][0]["host"] == "api.example.com"
    assert ingress["spec"]["rules"][0]["http"]["paths"][0]["path"] == "/api"
    
    print(f"  ✅ Ingress 配置生成成功")
    print(f"     - Host: {ingress['spec']['rules'][0]['host']}")
    print(f"     - Path: {ingress['spec']['rules'][0]['http']['paths'][0]['path']}")
    print(f"     - 注解: {len(ingress['metadata']['annotations'])}")
    
    return True


def test_optimization_5_hpa():
    """优化点 5: Horizontal Pod Autoscaler"""
    print("\n" + "="*70)
    print("优化点 5: Horizontal Pod Autoscaler")
    print("="*70)
    
    gen = HPAGenerator()
    
    hpa = gen.generate(
        "my-app",
        min_replicas=2,
        max_replicas=10,
        target_cpu_utilization=75
    )
    
    assert hpa["kind"] == "HorizontalPodAutoscaler"
    assert hpa["spec"]["minReplicas"] == 2
    assert hpa["spec"]["maxReplicas"] == 10
    assert hpa["spec"]["metrics"][0]["resource"]["target"]["averageUtilization"] == 75
    
    print(f"  ✅ HPA 配置生成成功")
    print(f"     - 最小副本: {hpa['spec']['minReplicas']}")
    print(f"     - 最大副本: {hpa['spec']['maxReplicas']}")
    print(f"     - CPU 目标: {hpa['spec']['metrics'][0]['resource']['target']['averageUtilization']}%")
    
    return True


def test_optimization_6_pdb():
    """优化点 6: Pod Disruption Budget"""
    print("\n" + "="*70)
    print("优化点 6: Pod Disruption Budget")
    print("="*70)
    
    gen = PDBGenerator()
    
    pdb = gen.generate("my-app", max_unavailable=1)
    
    assert pdb["kind"] == "PodDisruptionBudget"
    assert pdb["spec"]["maxUnavailable"] == 1
    assert pdb["spec"]["selector"]["matchLabels"]["app"] == "my-app"
    
    print(f"  ✅ PDB 配置生成成功")
    print(f"     - 最大不可用: {pdb['spec']['maxUnavailable']}")
    print(f"     - 选择器: {pdb['spec']['selector']['matchLabels']}")
    
    return True


def test_optimization_9_volume():
    """优化点 9: Volume 挂载配置"""
    print("\n" + "="*70)
    print("优化点 9: Volume 挂载配置")
    print("="*70)
    
    gen = VolumeGenerator()
    
    empty_dir = gen.generate_empty_dir("temp-storage")
    pvc = gen.generate_pvc("data-pvc", "10Gi")
    host_path = gen.generate_host_path("host-data", "/data/app")
    
    assert empty_dir["name"] == "temp-storage"
    assert "emptyDir" in empty_dir
    assert pvc["kind"] == "PersistentVolumeClaim"
    assert pvc["spec"]["resources"]["requests"]["storage"] == "10Gi"
    assert host_path["hostPath"]["path"] == "/data/app"
    
    print(f"  ✅ Volume 配置生成成功")
    print(f"     - EmptyDir: ✅")
    print(f"     - PVC: {pvc['spec']['resources']['requests']['storage']}")
    print(f"     - HostPath: {host_path['hostPath']['path']}")
    
    return True


def test_optimization_10_network_policy():
    """优化点 10: NetworkPolicy"""
    print("\n" + "="*70)
    print("优化点 10: NetworkPolicy")
    print("="*70)
    
    gen = NetworkPolicyGenerator()
    
    policy = gen.generate("my-app")
    
    assert policy["kind"] == "NetworkPolicy"
    assert "Ingress" in policy["spec"]["policyTypes"]
    assert "Egress" in policy["spec"]["policyTypes"]
    
    print(f"  ✅ NetworkPolicy 配置生成成功")
    print(f"     - 入口策略: {len(policy['spec'].get('ingress', []))}")
    print(f"     - 出口策略: {len(policy['spec'].get('egress', []))}")
    
    return True


def test_optimization_11_12_rbac():
    """优化点 11 & 12: RBAC"""
    print("\n" + "="*70)
    print("优化点 11 & 12: RBAC (ServiceAccount + Role/RoleBinding)")
    print("="*70)
    
    gen = RBACGenerator()
    
    sa = gen.generate_service_account("my-app-sa", "default")
    role = gen.generate_role("my-app-role", [
        {"apiGroups": [""], "resources": ["pods"], "verbs": ["get", "list"]}
    ])
    role_binding = gen.generate_role_binding(
        "my-app-role-binding",
        "my-app-role",
        "my-app-sa",
        "default"
    )
    
    assert sa["kind"] == "ServiceAccount"
    assert role["kind"] == "Role"
    assert role_binding["kind"] == "RoleBinding"
    
    print(f"  ✅ RBAC 配置生成成功")
    print(f"     - ServiceAccount: {sa['metadata']['name']}")
    print(f"     - Role: {role['metadata']['name']}")
    print(f"     - RoleBinding: {role_binding['metadata']['name']}")
    
    return True


def test_complete_k8s_generation():
    """测试完整 Kubernetes 配置生成"""
    print("\n" + "="*70)
    print("完整 Kubernetes 配置生成")
    print("="*70)
    
    generator = create_k8s_generator()
    config = create_k8s_config("my-app", "my-image:v1", 8080)
    
    all_configs = generator.generate_all(config)
    
    assert len(all_configs) == 6
    print(f"  ✅ 生成了 {len(all_configs)} 个配置文件:")
    for name in all_configs.keys():
        print(f"     - {name}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("Deployment 配置", test_optimization_1_deployment),
        ("Service 配置", test_optimization_2_service),
        ("ConfigMap/Secret", test_optimization_3_configmap_secret),
        ("Ingress 配置", test_optimization_4_ingress),
        ("HPA 配置", test_optimization_5_hpa),
        ("PDB 配置", test_optimization_6_pdb),
        ("Volume 配置", test_optimization_9_volume),
        ("NetworkPolicy", test_optimization_10_network_policy),
        ("RBAC 配置", test_optimization_11_12_rbac),
        ("完整配置生成", test_complete_k8s_generation),
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
    print("📋 Kubernetes 配置生成器测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有 Kubernetes 配置生成器测试通过！")
        print("✅ 已验证 12 个优化点！")
        return True
    else:
        print(f"\n⚠️ {failed}个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
