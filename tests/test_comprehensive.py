"""Code RAG 全面测试套件

包含单元测试、集成测试和系统测试
"""

import sys
import os
import pytest
import json
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from code_rag.middleware_layer.unified import UnifiedConfigGenerator, ConfigValidator
from code_rag.middleware_layer.kubernetes_pydantic import (
    KubernetesConfig, DeploymentGenerator, ServiceGenerator,
    ResourceRequirements, ProbeConfig
)
from code_rag.middleware_layer.validators import (
    KubernetesValidator, ValidationError
)


class TestUnitTests:
    """单元测试"""
    
    def test_kubernetes_config_creation(self):
        """测试 Kubernetes 配置创建"""
        config = KubernetesConfig(
            app_name="test-app",
            image="test:v1",
            port=8080,
            replicas=3
        )
        assert config.app_name == "test-app"
        assert config.port == 8080
        assert config.replicas == 3
    
    def test_kubernetes_config_defaults(self):
        """测试默认值"""
        config = KubernetesConfig()
        assert config.app_name == "my-app"
        assert config.port == 8080
        assert config.replicas == 3
    
    def test_kubernetes_name_lowercase(self):
        """测试名称自动转小写"""
        config = KubernetesConfig(app_name="MyApp")
        assert config.app_name == "myapp"
    
    def test_resource_requirements(self):
        """测试资源需求"""
        resources = ResourceRequirements(
            cpu_request="500m",
            cpu_limit="1000m",
            memory_request="256Mi",
            memory_limit="512Mi"
        )
        assert resources.cpu_request == "500m"
        assert resources.memory_limit == "512Mi"
    
    def test_probe_config(self):
        """测试探针配置"""
        probe = ProbeConfig(
            enabled=True,
            initial_delay_seconds=30,
            period_seconds=10
        )
        assert probe.enabled is True
        assert probe.initial_delay_seconds == 30
    
    def test_validators(self):
        """测试验证器"""
        valid, error = KubernetesValidator.validate_name("my-app")
        assert valid is True
        
        valid, error = KubernetesValidator.validate_name("MyApp")
        assert valid is False
        
        valid, error = KubernetesValidator.validate_port(8080)
        assert valid is True
        
        valid, error = KubernetesValidator.validate_port(70000)
        assert valid is False


class TestIntegrationTests:
    """集成测试"""
    
    def test_unified_generator_kubernetes(self):
        """测试统一生成器 - Kubernetes"""
        gen = UnifiedConfigGenerator()
        result = gen.generate_kubernetes(
            app_name="test-app",
            image="test:v1",
            port=8080
        )
        
        assert "deployment.yaml" in result
        assert "service.yaml" in result
        assert "hpa.yaml" in result
        
        deployment = result["deployment.yaml"]
        assert deployment["metadata"]["name"] == "test-app"
        assert deployment["spec"]["replicas"] == 3
    
    def test_unified_generator_docker(self):
        """测试统一生成器 - Docker"""
        gen = UnifiedConfigGenerator()
        result = gen.generate_docker(
            app_name="test-app",
            language="python"
        )
        
        assert "Dockerfile" in result
        assert "docker-compose.yml" in result
    
    def test_unified_generator_aws(self):
        """测试统一生成器 - AWS"""
        gen = UnifiedConfigGenerator()
        result = gen.generate_cloud(
            provider="aws",
            app_name="test-app",
            image="test:v1"
        )
        
        assert "ecs-task-definition.json" in result
        assert "eks-cluster.yaml" in result
    
    def test_unified_generator_gcp(self):
        """测试统一生成器 - GCP"""
        gen = UnifiedConfigGenerator()
        result = gen.generate_cloud(
            provider="gcp",
            app_name="test-app",
            image="test:v1"
        )
        
        assert "cloudrun-service.yaml" in result
    
    def test_unified_generator_cicd(self):
        """测试统一生成器 - CI/CD"""
        gen = UnifiedConfigGenerator()
        result = gen.generate_cicd(
            app_name="test-app",
            language="python"
        )
        
        assert "github-actions" in result
        assert "testing" in result
    
    def test_generate_all(self):
        """测试完整生成"""
        gen = UnifiedConfigGenerator()
        result = gen.generate_all(
            app_name="full-app",
            image="full:v1",
            cloud_provider="aws",
            cicd_platform="github_actions"
        )
        
        assert "kubernetes" in result
        assert "docker" in result
        assert "cloud" in result
        assert "cicd" in result
    
    def test_yaml_output(self):
        """测试 YAML 输出"""
        gen = UnifiedConfigGenerator()
        result = gen.generate_kubernetes(
            app_name="yaml-app",
            image="yaml:v1",
            output_format="yaml"
        )
        
        assert "deployment.yaml" in result
        assert isinstance(result["deployment.yaml"], str)
        assert "apiVersion:" in result["deployment.yaml"]


class TestSystemTests:
    """系统测试"""
    
    def test_file_export(self):
        """测试文件导出"""
        gen = UnifiedConfigGenerator()
        config = KubernetesConfig(app_name="export-app", image="export:v1")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            files = gen.k8s_gen.export_to_directory(config, tmpdir)
            
            assert len(files) == 3
            for filepath in files:
                assert Path(filepath).exists()
                content = Path(filepath).read_text()
                assert len(content) > 0
    
    def test_config_validation(self):
        """测试配置验证"""
        valid, error = ConfigValidator.validate_kubernetes({
            "app_name": "test",
            "image": "test:v1",
            "port": 8080
        })
        assert valid is True
    
    def test_error_handling(self):
        """测试错误处理"""
        gen = UnifiedConfigGenerator()
        
        with pytest.raises(ValueError) as exc_info:
            gen.generate_cloud(
                provider="invalid",
                app_name="test",
                image="test:v1"
            )
        assert "不支持" in str(exc_info.value)
    
    def test_large_scale_generation(self):
        """测试大规模生成"""
        gen = UnifiedConfigGenerator()
        
        for i in range(100):
            result = gen.generate_kubernetes(
                app_name=f"app-{i}",
                image=f"app:v{i}"
            )
            assert result["deployment.yaml"]["metadata"]["name"] == f"app-{i}"
    
    def test_concurrent_generation(self):
        """测试并发生成"""
        import concurrent.futures
        
        gen = UnifiedConfigGenerator()
        
        def generate_config(i):
            return gen.generate_kubernetes(
                app_name=f"concurrent-{i}",
                image=f"concurrent:v{i}"
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(generate_config, i) for i in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        assert len(results) == 20
    
    def test_json_serialization(self):
        """测试 JSON 序列化"""
        gen = UnifiedConfigGenerator()
        result = gen.generate_kubernetes(
            app_name="json-test",
            image="json:v1"
        )
        
        json_str = json.dumps(result, indent=2)
        parsed = json.loads(json_str)
        
        assert parsed["deployment.yaml"]["metadata"]["name"] == "json-test"


class TestPerformance:
    """性能测试"""
    
    def test_generation_speed(self):
        """测试生成速度"""
        import time
        
        gen = UnifiedConfigGenerator()
        
        start = time.time()
        for i in range(100):
            gen.generate_kubernetes(app_name=f"perf-{i}", image="test:v1")
        elapsed = time.time() - start
        
        assert elapsed < 1.0
        print(f"\n100 次生成耗时: {elapsed*1000:.2f} ms")
    
    def test_memory_usage(self):
        """测试内存使用"""
        import tracemalloc
        
        gen = UnifiedConfigGenerator()
        
        tracemalloc.start()
        for i in range(100):
            gen.generate_all(app_name=f"mem-{i}", image="test:v1")
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"\n峰值内存: {peak / 1024:.2f} KB")
        assert peak < 50 * 1024 * 1024


def run_all_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_all_tests()
