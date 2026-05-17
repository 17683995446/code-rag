"""
Code RAG v24.0 - Kubernetes 集成与配置生成器
完整的 Kubernetes 配置生成系统（12 个优化点）
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ServiceType(Enum):
    """Kubernetes Service 类型"""
    CLUSTER_IP = "ClusterIP"
    NODE_PORT = "NodePort"
    LOAD_BALANCER = "LoadBalancer"


class Protocol(Enum):
    """协议类型"""
    TCP = "TCP"
    UDP = "UDP"
    HTTP = "HTTP"
    HTTPS = "HTTPS"


@dataclass
class ResourceRequirements:
    """资源需求"""
    cpu_request: str = "100m"
    cpu_limit: str = "500m"
    memory_request: str = "128Mi"
    memory_limit: str = "512Mi"


@dataclass
class ProbeConfig:
    """探针配置"""
    enabled: bool = True
    initial_delay_seconds: int = 30
    period_seconds: int = 10
    timeout_seconds: int = 5
    failure_threshold: int = 3
    success_threshold: int = 1


@dataclass
class KubernetesConfig:
    """Kubernetes 配置"""
    app_name: str = "my-app"
    image: str = "my-app:latest"
    port: int = 8080
    replicas: int = 3
    namespace: str = "default"
    labels: Dict[str, str] = field(default_factory=dict)
    resources: ResourceRequirements = field(default_factory=lambda: ResourceRequirements())
    readiness_probe: ProbeConfig = field(default_factory=lambda: ProbeConfig())
    liveness_probe: ProbeConfig = field(default_factory=lambda: ProbeConfig())


class DeploymentGenerator:
    """Deployment 配置生成器（优化点 1）"""
    
    def __init__(self):
        self.config = None
    
    def generate(self, k8s_config: KubernetesConfig) -> Dict:
        """生成 Deployment 配置"""
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": k8s_config.app_name,
                "namespace": k8s_config.namespace,
                "labels": {
                    "app": k8s_config.app_name,
                    "version": "v1",
                    **k8s_config.labels
                }
            },
            "spec": {
                "replicas": k8s_config.replicas,
                "selector": {
                    "matchLabels": {
                        "app": k8s_config.app_name
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": k8s_config.app_name,
                            "version": "v1"
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": k8s_config.app_name,
                            "image": k8s_config.image,
                            "ports": [{
                                "containerPort": k8s_config.port
                            }],
                            "resources": {
                                "requests": {
                                    "cpu": k8s_config.resources.cpu_request if k8s_config.resources else "100m",
                                    "memory": k8s_config.resources.memory_request if k8s_config.resources else "128Mi"
                                },
                                "limits": {
                                    "cpu": k8s_config.resources.cpu_limit if k8s_config.resources else "500m",
                                    "memory": k8s_config.resources.memory_limit if k8s_config.resources else "512Mi"
                                }
                            }
                        }]
                    }
                }
            }
        }
        
        container = deployment["spec"]["template"]["spec"]["containers"][0]
        
        if k8s_config.readiness_probe.enabled:
            container["readinessProbe"] = {
                "httpGet": {
                    "path": "/health",
                    "port": k8s_config.port
                },
                "initialDelaySeconds": k8s_config.readiness_probe.initial_delay_seconds,
                "periodSeconds": k8s_config.readiness_probe.period_seconds,
                "timeoutSeconds": k8s_config.readiness_probe.timeout_seconds,
                "failureThreshold": k8s_config.readiness_probe.failure_threshold
            }
        
        if k8s_config.liveness_probe.enabled:
            container["livenessProbe"] = {
                "httpGet": {
                    "path": "/health",
                    "port": k8s_config.port
                },
                "initialDelaySeconds": k8s_config.liveness_probe.initial_delay_seconds,
                "periodSeconds": k8s_config.liveness_probe.period_seconds,
                "timeoutSeconds": k8s_config.liveness_probe.timeout_seconds,
                "failureThreshold": k8s_config.liveness_probe.failure_threshold
            }
        
        return deployment
    
    def to_yaml(self, deployment: Dict) -> str:
        """转换为 YAML（简化版）"""
        lines = []
        for key, value in deployment.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)


class ServiceGenerator:
    """Service 配置生成器（优化点 2）"""
    
    def generate(self, k8s_config: KubernetesConfig, 
                service_type: ServiceType = ServiceType.CLUSTER_IP) -> Dict:
        """生成 Service 配置"""
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": f"{k8s_config.app_name}-service",
                "namespace": k8s_config.namespace,
                "labels": {
                    "app": k8s_config.app_name
                }
            },
            "spec": {
                "type": service_type.value,
                "selector": {
                    "app": k8s_config.app_name
                },
                "ports": [{
                    "port": 80,
                    "targetPort": k8s_config.port,
                    "protocol": "TCP",
                    "name": "http"
                }]
            }
        }
        
        return service


class ConfigMapGenerator:
    """ConfigMap 和 Secret 管理器（优化点 3）"""
    
    def generate_configmap(self, name: str, data: Dict[str, str], 
                          namespace: str = "default") -> Dict:
        """生成 ConfigMap"""
        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "data": data
        }
    
    def generate_secret(self, name: str, data: Dict[str, str],
                      namespace: str = "default") -> Dict:
        """生成 Secret"""
        import base64
        
        encoded_data = {}
        for key, value in data.items():
            encoded_data[key] = base64.b64encode(value.encode()).decode()
        
        return {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "type": "Opaque",
            "data": encoded_data
        }


class IngressGenerator:
    """Ingress 配置生成器（优化点 4）"""
    
    def generate(self, app_name: str, host: str = "example.com",
                path: str = "/", namespace: str = "default",
                annotations: Optional[Dict] = None) -> Dict:
        """生成 Ingress 配置"""
        ingress = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": f"{app_name}-ingress",
                "namespace": namespace,
                "annotations": annotations or {
                    "nginx.ingress.kubernetes.io/rewrite-target": "/",
                    "kubernetes.io/ingress.class": "nginx"
                }
            },
            "spec": {
                "rules": [{
                    "host": host,
                    "http": {
                        "paths": [{
                            "path": path,
                            "pathType": "Prefix",
                            "backend": {
                                "service": {
                                    "name": f"{app_name}-service",
                                    "port": {
                                        "number": 80
                                    }
                                }
                            }
                        }]
                    }
                }]
            }
        }
        
        return ingress


class HPAGenerator:
    """Horizontal Pod Autoscaler 生成器（优化点 5）"""
    
    def generate(self, app_name: str, namespace: str = "default",
                min_replicas: int = 2, max_replicas: int = 10,
                target_cpu_utilization: int = 70) -> Dict:
        """生成 HPA 配置"""
        return {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": f"{app_name}-hpa",
                "namespace": namespace
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": app_name
                },
                "minReplicas": min_replicas,
                "maxReplicas": max_replicas,
                "metrics": [{
                    "type": "Resource",
                    "resource": {
                        "name": "cpu",
                        "target": {
                            "type": "Utilization",
                            "averageUtilization": target_cpu_utilization
                        }
                    }
                }]
            }
        }


class PDBGenerator:
    """Pod Disruption Budget 生成器（优化点 6）"""
    
    def generate(self, app_name: str, namespace: str = "default",
                max_unavailable: int = 1) -> Dict:
        """生成 PDB 配置"""
        return {
            "apiVersion": "policy/v1",
            "kind": "PodDisruptionBudget",
            "metadata": {
                "name": f"{app_name}-pdb",
                "namespace": namespace
            },
            "spec": {
                "maxUnavailable": max_unavailable,
                "selector": {
                    "matchLabels": {
                        "app": app_name
                    }
                }
            }
        }


class VolumeGenerator:
    """Volume 挂载配置生成器（优化点 9）"""
    
    def generate_empty_dir(self, name: str) -> Dict:
        """生成 EmptyDir Volume"""
        return {
            "name": name,
            "emptyDir": {}
        }
    
    def generate_pvc(self, name: str, storage_size: str = "1Gi",
                    namespace: str = "default") -> Dict:
        """生成 PVC"""
        return {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {
                    "requests": {
                        "storage": storage_size
                    }
                }
            }
        }
    
    def generate_host_path(self, name: str, host_path: str) -> Dict:
        """生成 HostPath Volume"""
        return {
            "name": name,
            "hostPath": {
                "path": host_path,
                "type": "DirectoryOrCreate"
            }
        }


class NetworkPolicyGenerator:
    """NetworkPolicy 生成器（优化点 10）"""
    
    def generate(self, app_name: str, namespace: str = "default",
                pod_selector: Optional[Dict] = None) -> Dict:
        """生成 NetworkPolicy"""
        return {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
                "name": f"{app_name}-network-policy",
                "namespace": namespace
            },
            "spec": {
                "podSelector": pod_selector or {"matchLabels": {"app": app_name}},
                "policyTypes": ["Ingress", "Egress"],
                "ingress": [{
                    "from": [{
                        "podSelector": {
                            "matchLabels": {
                                "app": app_name
                            }
                        }
                    }],
                    "ports": [{
                        "protocol": "TCP",
                        "port": 8080
                    }]
                }],
                "egress": [{
                    "to": [{
                        "namespaceSelector": {}
                    }],
                    "ports": [{
                        "protocol": "TCP",
                        "port": 53
                    }, {
                        "protocol": "UDP",
                        "port": 53
                    }]
                }]
            }
        }


class RBACGenerator:
    """RBAC 角色绑定生成器（优化点 11 & 12）"""
    
    def generate_service_account(self, name: str, 
                                 namespace: str = "default") -> Dict:
        """生成 ServiceAccount"""
        return {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": name,
                "namespace": namespace
            }
        }
    
    def generate_role(self, name: str, rules: List[Dict],
                      namespace: str = "default") -> Dict:
        """生成 Role"""
        return {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "Role",
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "rules": rules
        }
    
    def generate_role_binding(self, name: str, role_name: str,
                              service_account_name: str,
                              namespace: str = "default") -> Dict:
        """生成 RoleBinding"""
        return {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "RoleBinding",
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "subjects": [{
                "kind": "ServiceAccount",
                "name": service_account_name,
                "namespace": namespace
            }],
            "roleRef": {
                "kind": "Role",
                "name": role_name,
                "apiGroup": "rbac.authorization.k8s.io"
            }
        }


class KubernetesConfigGenerator:
    """完整的 Kubernetes 配置生成器"""
    
    def __init__(self):
        self.deployment_gen = DeploymentGenerator()
        self.service_gen = ServiceGenerator()
        self.configmap_gen = ConfigMapGenerator()
        self.ingress_gen = IngressGenerator()
        self.hpa_gen = HPAGenerator()
        self.pdb_gen = PDBGenerator()
        self.volume_gen = VolumeGenerator()
        self.network_policy_gen = NetworkPolicyGenerator()
        self.rbac_gen = RBACGenerator()
    
    def generate_all(self, config: KubernetesConfig) -> Dict[str, Dict]:
        """生成所有 Kubernetes 配置"""
        configs = {}
        
        configs["deployment.yaml"] = self.deployment_gen.generate(config)
        configs["service.yaml"] = self.service_gen.generate(config)
        configs["hpa.yaml"] = self.hpa_gen.generate(config.app_name, config.namespace)
        configs["pdb.yaml"] = self.pdb_gen.generate(config.app_name, config.namespace)
        configs["network-policy.yaml"] = self.network_policy_gen.generate(config.app_name, config.namespace)
        configs["service-account.yaml"] = self.rbac_gen.generate_service_account(
            config.app_name, config.namespace
        )
        
        return configs
    
    def generate_manifest_file(self, configs: Dict[str, Dict]) -> str:
        """生成单个 YAML 文件（多个资源）"""
        manifests = []
        for name, config in configs.items():
            manifests.append(f"# {name}")
            manifests.append(self.deployment_gen.to_yaml(config))
            manifests.append("---")
        
        return "\n".join(manifests)


def create_k8s_generator() -> KubernetesConfigGenerator:
    """创建 Kubernetes 配置生成器"""
    return KubernetesConfigGenerator()


def create_k8s_config(app_name: str, image: str, port: int = 8080) -> KubernetesConfig:
    """创建 Kubernetes 配置"""
    return KubernetesConfig(
        app_name=app_name,
        image=image,
        port=port,
        replicas=3,
        namespace="default",
        resources=ResourceRequirements(
            cpu_request="100m",
            cpu_limit="500m",
            memory_request="128Mi",
            memory_limit="512Mi"
        ),
        readiness_probe=ProbeConfig(
            enabled=True,
            initial_delay_seconds=30,
            period_seconds=10
        ),
        liveness_probe=ProbeConfig(
            enabled=True,
            initial_delay_seconds=60,
            period_seconds=10
        )
    )
