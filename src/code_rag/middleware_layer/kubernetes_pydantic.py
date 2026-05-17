"""Kubernetes 配置生成器 (Pydantic + PyYAML 版本)

使用开源工具进行类型安全的配置生成
"""

import yaml
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class ResourceRequirements(BaseModel):
    """资源需求模型"""
    cpu_request: str = Field(default="100m", description="CPU 请求")
    cpu_limit: str = Field(default="500m", description="CPU 限制")
    memory_request: str = Field(default="128Mi", description="内存请求")
    memory_limit: str = Field(default="512Mi", description="内存限制")
    
    @field_validator('cpu_request', 'cpu_limit')
    @classmethod
    def validate_cpu(cls, v: str) -> str:
        if not (v.endswith('m') or '.' in v):
            raise ValueError(f"无效的 CPU 值: {v}，应如 '100m' 或 '0.5'")
        return v
    
    @field_validator('memory_request', 'memory_limit')
    @classmethod
    def validate_memory(cls, v: str) -> str:
        if not any(v.endswith(unit) for unit in ['Ki', 'Mi', 'Gi', 'Ti', 'K', 'M', 'G']):
            raise ValueError(f"无效的内存值: {v}")
        return v


class ProbeConfig(BaseModel):
    """健康检查配置模型"""
    enabled: bool = Field(default=True, description="是否启用")
    initial_delay_seconds: int = Field(default=30, ge=0, le=300)
    period_seconds: int = Field(default=10, ge=1, le=60)
    timeout_seconds: int = Field(default=5, ge=1, le=30)
    failure_threshold: int = Field(default=3, ge=1, le=10)
    success_threshold: int = Field(default=1, ge=1, le=5)


class KubernetesConfig(BaseModel):
    """Kubernetes 配置模型"""
    app_name: str = Field(default="my-app", min_length=1, max_length=253)
    image: str = Field(default="my-app:latest", description="容器镜像")
    port: int = Field(default=8080, ge=1, le=65535)
    replicas: int = Field(default=3, ge=0, le=10000)
    namespace: str = Field(default="default")
    labels: Dict[str, str] = Field(default_factory=dict)
    resources: Optional[ResourceRequirements] = Field(default_factory=ResourceRequirements)
    readiness_probe: Optional[ProbeConfig] = Field(default_factory=ProbeConfig)
    liveness_probe: Optional[ProbeConfig] = Field(default_factory=ProbeConfig)
    
    @field_validator('app_name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError(f"应用名称只能包含字母、数字、'-' 和 '_'")
        if not v[0].isalnum() or not v[-1].isalnum():
            raise ValueError("名称必须以字母或数字开头和结尾")
        return v.lower()
    
    @field_validator('namespace')
    @classmethod
    def validate_namespace(cls, v: str) -> str:
        return v.lower()
    
    def model_dump_k8s(self) -> Dict[str, Any]:
        """导出为 Kubernetes 资源字典"""
        return self.model_dump(exclude_none=True)


class DeploymentGenerator:
    """Deployment 配置生成器"""
    
    def __init__(self):
        self.version = "1.0.0"
    
    def generate(self, config: KubernetesConfig) -> Dict[str, Any]:
        """生成 Deployment 配置"""
        container = {
            "name": config.app_name,
            "image": config.image,
            "ports": [{"containerPort": config.port}],
            "resources": {
                "requests": {
                    "cpu": config.resources.cpu_request if config.resources else "100m",
                    "memory": config.resources.memory_request if config.resources else "128Mi"
                },
                "limits": {
                    "cpu": config.resources.cpu_limit if config.resources else "500m",
                    "memory": config.resources.memory_limit if config.resources else "512Mi"
                }
            }
        }
        
        if config.readiness_probe and config.readiness_probe.enabled:
            container["readinessProbe"] = {
                "httpGet": {"path": "/health", "port": config.port},
                "initialDelaySeconds": config.readiness_probe.initial_delay_seconds,
                "periodSeconds": config.readiness_probe.period_seconds,
                "timeoutSeconds": config.readiness_probe.timeout_seconds,
                "failureThreshold": config.readiness_probe.failure_threshold
            }
        
        if config.liveness_probe and config.liveness_probe.enabled:
            container["livenessProbe"] = {
                "httpGet": {"path": "/health", "port": config.port},
                "initialDelaySeconds": config.liveness_probe.initial_delay_seconds,
                "periodSeconds": config.liveness_probe.period_seconds,
                "failureThreshold": config.liveness_probe.failure_threshold
            }
        
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": config.app_name,
                "namespace": config.namespace,
                "labels": {"app": config.app_name, "version": "v1", **config.labels},
                "creationTimestamp": datetime.now().isoformat() + "Z"
            },
            "spec": {
                "replicas": config.replicas,
                "selector": {"matchLabels": {"app": config.app_name}},
                "template": {
                    "metadata": {"labels": {"app": config.app_name, "version": "v1"}},
                    "spec": {"containers": [container]}
                }
            }
        }
    
    def to_yaml(self, config: KubernetesConfig) -> str:
        """导出为 YAML 格式"""
        return yaml.dump(self.generate(config), default_flow_style=False, sort_keys=False, allow_unicode=True)


class ServiceGenerator:
    """Service 配置生成器"""
    
    def generate(self, config: KubernetesConfig, service_type: str = "LoadBalancer") -> Dict[str, Any]:
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": config.app_name,
                "namespace": config.namespace,
                "labels": {"app": config.app_name}
            },
            "spec": {
                "type": service_type,
                "selector": {"app": config.app_name},
                "ports": [{
                    "port": 80,
                    "targetPort": config.port,
                    "protocol": "TCP"
                }]
            }
        }
    
    def to_yaml(self, config: KubernetesConfig) -> str:
        return yaml.dump(self.generate(config), default_flow_style=False, sort_keys=False)


class HPAGenerator:
    """Horizontal Pod Autoscaler 生成器"""
    
    def generate(self, app_name: str, namespace: str = "default") -> Dict[str, Any]:
        return {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {"name": app_name, "namespace": namespace},
            "spec": {
                "scaleTargetRef": {"apiVersion": "apps/v1", "kind": "Deployment", "name": app_name},
                "minReplicas": 2,
                "maxReplicas": 10,
                "metrics": [{
                    "type": "Resource",
                    "resource": {"name": "cpu", "target": {"type": "Utilization", "averageUtilization": 75}}
                }]
            }
        }
    
    def to_yaml(self, app_name: str, namespace: str = "default") -> str:
        return yaml.dump(self.generate(app_name, namespace), default_flow_style=False)


class KubernetesConfigGenerator:
    """完整的 Kubernetes 配置生成器 (支持 YAML 输出)"""
    
    def __init__(self):
        self.deployment_gen = DeploymentGenerator()
        self.service_gen = ServiceGenerator()
        self.hpa_gen = HPAGenerator()
        self.yaml_available = True
    
    def generate_all(self, config: KubernetesConfig) -> Dict[str, Any]:
        """生成所有配置（字典格式）"""
        return {
            "deployment.yaml": self.deployment_gen.generate(config),
            "service.yaml": self.service_gen.generate(config),
            "hpa.yaml": self.hpa_gen.generate(config.app_name, config.namespace)
        }
    
    def generate_all_yaml(self, config: KubernetesConfig) -> Dict[str, str]:
        """生成所有配置（YAML 格式）"""
        return {
            "deployment.yaml": self.deployment_gen.to_yaml(config),
            "service.yaml": self.service_gen.to_yaml(config),
            "hpa.yaml": self.hpa_gen.to_yaml(config.app_name, config.namespace)
        }
    
    def export_to_directory(self, config: KubernetesConfig, output_dir: str) -> List[str]:
        """导出配置到指定目录"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        files = []
        for filename, content in self.generate_all_yaml(config).items():
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            files.append(filepath)
        
        return files


def demo():
    """演示 Pydantic 验证"""
    print("="*70)
    print("Pydantic 验证演示")
    print("="*70)
    
    # 有效配置
    print("\n1. 有效配置:")
    valid_config = KubernetesConfig(app_name="my-app", port=8080)
    print(f"   ✅ app_name: {valid_config.app_name}")
    print(f"   ✅ port: {valid_config.port}")
    
    # 无效名称 (会被自动修正为小写)
    print("\n2. 名称修正 (自动转小写):")
    config = KubernetesConfig(app_name="MyApp")
    print(f"   → 修正后: {config.app_name}")
    
    # YAML 输出
    print("\n3. YAML 输出:")
    gen = DeploymentGenerator()
    yaml_output = gen.to_yaml(valid_config)
    print(yaml_output)
    
    # 验证失败示例
    print("\n4. 验证失败示例:")
    try:
        invalid = KubernetesConfig(app_name="-invalid-")
    except Exception as e:
        print(f"   ❌ 捕获验证错误: {e}")


if __name__ == "__main__":
    demo()
