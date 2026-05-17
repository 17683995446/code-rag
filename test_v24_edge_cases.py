"""v24.0 边界情况和综合测试

验证所有生成器的健壮性和边界处理能力
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from code_rag.middleware_layer.kubernetes_generator import (
    KubernetesConfig, KubernetesConfigGenerator, DeploymentGenerator
)
from code_rag.middleware_layer.docker_generator import (
    DockerConfigGenerator, DockerBuildConfig
)
from code_rag.middleware_layer.cloud_generator import (
    CloudConfigGenerator, AwsConfig, GcpConfig, AzureConfig
)
from code_rag.middleware_layer.cicd_generator import (
    CICDConfigGenerator, PipelineConfig
)
from code_rag.middleware_layer.validators import (
    KubernetesValidator, DockerValidator, CloudValidator, CICDValidator
)


def test_validators():
    """测试所有验证器"""
    print("\n" + "="*70)
    print("测试 1: 验证器")
    print("="*70)
    
    results = []
    
    # Kubernetes 验证器
    tests = [
        ("K8s: 有效名称", KubernetesValidator.validate_name("my-app"), True),
        ("K8s: 无效名称(大写)", KubernetesValidator.validate_name("MyApp"), False),
        ("K8s: 无效名称(_开头)", KubernetesValidator.validate_name("_app"), False),
        ("K8s: 有效端口", KubernetesValidator.validate_port(8080), True),
        ("K8s: 无效端口(0)", KubernetesValidator.validate_port(0), False),
        ("K8s: 无效端口(负)", KubernetesValidator.validate_port(-1), False),
        ("K8s: 无效端口(超)", KubernetesValidator.validate_port(70000), False),
        ("K8s: 有效副本", KubernetesValidator.validate_replicas(3), True),
        ("K8s: 无效副本(负)", KubernetesValidator.validate_replicas(-1), False),
        ("K8s: 有效CPU", KubernetesValidator.validate_cpu("500m"), True),
        ("K8s: 有效内存", KubernetesValidator.validate_memory("1Gi"), True),
    ]
    
    for name, (valid, error), expected in tests:
        passed = valid == expected
        results.append(passed)
        print(f"{'✅' if passed else '❌'} {name}")
    
    return all(results)


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "="*70)
    print("测试 2: 边界情况")
    print("="*70)
    
    results = []
    k8s_gen = KubernetesConfigGenerator()
    docker_gen = DockerConfigGenerator()
    cloud_gen = CloudConfigGenerator()
    cicd_gen = CICDConfigGenerator()
    
    # Kubernetes 边界测试
    edge_configs = [
        ("K8s: 空配置", lambda: KubernetesConfig()),
        ("K8s: 超长名称", lambda: KubernetesConfig(app_name='a'*253)),
        ("K8s: 零副本", lambda: KubernetesConfig(replicas=0)),
        ("K8s: Unicode", lambda: KubernetesConfig(app_name='应用-测试')),
        ("K8s: 带点号", lambda: KubernetesConfig(app_name='app.v1.0')),
        ("K8s: 最小资源", lambda: KubernetesConfig(resources=None)),
    ]
    
    for name, config_func in edge_configs:
        try:
            config = config_func()
            result = k8s_gen.deployment_gen.generate(config)
            results.append(True)
            print(f"✅ {name}")
        except Exception as e:
            results.append(False)
            print(f"❌ {name}: {e}")
    
    # Docker 边界测试
    docker_edge = [
        ("Docker: 空配置", lambda: DockerBuildConfig()),
        ("Docker: 长名称", lambda: DockerBuildConfig(app_name='my-very-long-application-name')),
    ]
    
    for name, config_func in docker_edge:
        try:
            config = config_func()
            result = docker_gen.generate_all(config)
            results.append(True)
            print(f"✅ {name}")
        except Exception as e:
            results.append(False)
            print(f"❌ {name}: {e}")
    
    return all(results)


def test_performance():
    """测试性能"""
    print("\n" + "="*70)
    print("测试 3: 性能")
    print("="*70)
    
    import time
    
    k8s_gen = KubernetesConfigGenerator()
    docker_gen = DockerConfigGenerator()
    
    # Kubernetes 性能
    start = time.time()
    for i in range(100):
        config = KubernetesConfig(app_name=f"app-{i}")
        k8s_gen.generate_all(config)
    k8s_time = time.time() - start
    
    # Docker 性能
    start = time.time()
    for i in range(100):
        config = DockerBuildConfig(app_name=f"app-{i}")
        docker_gen.generate_all(config)
    docker_time = time.time() - start
    
    print(f"✅ Kubernetes: 100 次生成耗时 {k8s_time*1000:.2f} ms ({k8s_time*10:.3f} ms/次)")
    print(f"✅ Docker: 100 次生成耗时 {docker_time*1000:.2f} ms ({docker_time*10:.3f} ms/次)")
    
    return True


def test_outputs():
    """测试输出完整性"""
    print("\n" + "="*70)
    print("测试 4: 输出完整性")
    print("="*70)
    
    results = []
    
    # Kubernetes 输出
    k8s_gen = KubernetesConfigGenerator()
    k8s_result = k8s_gen.generate_all(KubernetesConfig())
    k8s_keys = list(k8s_result.keys())
    expected_k8s = ["deployment.yaml", "service.yaml", "hpa.yaml", "pdb.yaml", "network-policy.yaml", "service-account.yaml"]
    
    for key in expected_k8s:
        present = key in k8s_keys
        results.append(present)
        print(f"{'✅' if present else '❌'} K8s: {key}")
    
    # Docker 输出
    docker_gen = DockerConfigGenerator()
    docker_result = docker_gen.generate_all(DockerBuildConfig())
    docker_keys = list(docker_result.keys())
    expected_docker = ["Dockerfile", "docker-compose.yml", "buildkit.toml", "security.yml"]
    
    for key in expected_docker:
        present = key in docker_keys
        results.append(present)
        print(f"{'✅' if present else '❌'} Docker: {key}")
    
    return all(results)


def test_error_handling():
    """测试错误处理"""
    print("\n" + "="*70)
    print("测试 5: 错误处理")
    print("="*70)
    
    results = []
    
    # 测试无效输入是否抛出正确异常
    try:
        from code_rag.middleware_layer.validators import validate_and_raise, ValidationError
        validate_and_raise(KubernetesValidator.validate_name, "", "name")
        results.append(False)
        print("❌ 应该抛出异常")
    except ValidationError:
        results.append(True)
        print("✅ 正确抛出 ValidationError")
    except Exception as e:
        results.append(False)
        print(f"❌ 抛出错误异常: {e}")
    
    return all(results)


def run_all_tests():
    """运行所有测试"""
    print("="*70)
    print("🧪 Code RAG v24.0 - 边界情况和综合测试")
    print("="*70)
    
    all_passed = True
    
    all_passed &= test_validators()
    all_passed &= test_edge_cases()
    all_passed &= test_performance()
    all_passed &= test_outputs()
    all_passed &= test_error_handling()
    
    print("\n" + "="*70)
    if all_passed:
        print("🎉 所有边界测试通过！")
    else:
        print("⚠️ 部分测试失败")
    print("="*70)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
