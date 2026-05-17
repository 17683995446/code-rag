"""统一配置生成器接口

提供统一的 API 访问所有配置生成器
"""

from typing import Dict, Any, Optional, List, Union
import json

from .kubernetes_pydantic import (
    KubernetesConfig as K8sConfig,
    KubernetesConfigGenerator as K8sGenerator,
    DeploymentGenerator,
    ServiceGenerator,
    HPAGenerator,
    ResourceRequirements,
    ProbeConfig
)

from .docker_generator import (
    DockerBuildConfig as DockerConfig,
    DockerConfigGenerator as DockerGenerator,
    BaseImage,
    ImageFlavor
)

from .cloud_generator import (
    AwsConfig,
    GcpConfig,
    AzureConfig,
    CloudConfigGenerator,
    AwsRegion,
    GcpRegion,
    AzureRegion
)

from .cicd_generator import (
    PipelineConfig as CICDConfig,
    CICDConfigGenerator as CICDGenerator,
    DeploymentStrategy,
    Environment,
    CICDPlatform
)

from .validators import (
    KubernetesValidator,
    DockerValidator,
    CloudValidator,
    CICDValidator,
    ValidationError
)


class UnifiedConfigGenerator:
    """统一配置生成器
    
    提供单一接口访问所有云原生配置生成能力
    """
    
    def __init__(self):
        self.k8s_gen = K8sGenerator()
        self.docker_gen = DockerGenerator()
        self.cloud_gen = CloudConfigGenerator()
        self.cicd_gen = CICDGenerator()
    
    def generate_kubernetes(
        self,
        app_name: str,
        image: str,
        port: int = 8080,
        replicas: int = 3,
        namespace: str = "default",
        cpu_request: str = "100m",
        cpu_limit: str = "500m",
        memory_request: str = "128Mi",
        memory_limit: str = "256Mi",
        enable_hpa: bool = True,
        output_format: str = "dict"
    ) -> Union[Dict[str, Any], str]:
        """生成 Kubernetes 配置"""
        config = K8sConfig(
            app_name=app_name,
            image=image,
            port=port,
            replicas=replicas,
            namespace=namespace,
            resources=ResourceRequirements(
                cpu_request=cpu_request,
                cpu_limit=cpu_limit,
                memory_request=memory_request,
                memory_limit=memory_limit
            )
        )
        
        if output_format == "yaml":
            return self.k8s_gen.generate_all_yaml(config)
        return self.k8s_gen.generate_all(config)
    
    def generate_docker(
        self,
        app_name: str,
        language: str = "python",
        base_image: str = "alpine",
        enable_multistage: bool = True,
        enable_security: bool = True,
        output_format: str = "dict"
    ) -> Union[Dict[str, Any], str]:
        """生成 Docker 配置"""
        base = BaseImage.ALPINE if base_image.lower() == "alpine" else BaseImage.DEBIAN
        
        config = DockerConfig(
            app_name=app_name,
            language=language,
            base_image=base,
            enable_multistage=enable_multistage,
            non_root_user=enable_security,
            read_only_rootfs=enable_security,
            enable_image_signing=enable_security
        )
        
        if output_format == "yaml":
            return {k: json.dumps(v, indent=2) if isinstance(v, dict) else v 
                    for k, v in self.docker_gen.generate_all(config).items()}
        return self.docker_gen.generate_all(config)
    
    def generate_cloud(
        self,
        provider: str,
        app_name: str,
        image: str,
        port: int = 8080,
        region: Optional[str] = None,
        enable_autoscaling: bool = True,
        enable_serverless: bool = False,
        output_format: str = "dict"
    ) -> Dict[str, Any]:
        """生成云服务配置"""
        provider = provider.lower()
        
        if provider == "aws":
            aws_region = AwsRegion.US_EAST_1
            if region:
                for r in AwsRegion:
                    if r.value == region:
                        aws_region = r
                        break
            
            config = AwsConfig(
                app_name=app_name,
                image=image,
                port=port,
                region=aws_region,
                enable_fargate=enable_serverless,
                enable_autoscaling=enable_autoscaling
            )
            return self.cloud_gen.generate_aws_configs(config)
        
        elif provider == "gcp":
            gcp_region = GcpRegion.US_CENTRAL1
            if region:
                for r in GcpRegion:
                    if r.value == region:
                        gcp_region = r
                        break
            
            config = GcpConfig(
                app_name=app_name,
                image=image,
                port=port,
                region=gcp_region,
                min_instances=0 if enable_serverless else 1,
                enable_autoscaling=enable_autoscaling
            )
            return self.cloud_gen.generate_gcp_configs(config)
        
        elif provider == "azure":
            azure_region = AzureRegion.EAST_US
            if region:
                for r in AzureRegion:
                    if r.value == region:
                        azure_region = r
                        break
            
            config = AzureConfig(
                app_name=app_name,
                image=image,
                port=port,
                location=azure_region,
                enable_autoscaling=enable_autoscaling
            )
            return self.cloud_gen.generate_azure_configs(config)
        
        else:
            raise ValueError(f"不支持的云提供商: {provider}")
    
    def generate_cicd(
        self,
        app_name: str,
        language: str = "python",
        platform: str = "github_actions",
        deployment_strategy: str = "rolling",
        enable_tests: bool = True,
        enable_security_scan: bool = True,
        output_format: str = "dict"
    ) -> Dict[str, Any]:
        """生成 CI/CD 配置"""
        strategy = DeploymentStrategy.ROLLING
        for s in DeploymentStrategy:
            if s.value == deployment_strategy.lower():
                strategy = s
                break
        
        config = CICDConfig(
            app_name=app_name,
            language=language,
            enable_integration_tests=enable_tests,
            enable_e2e_tests=enable_tests,
            enable_security_scan=enable_security_scan,
            deployment_strategy=strategy,
            enable_rollback=True
        )
        
        return self.cicd_gen.generate_all(config)
    
    def generate_all(
        self,
        app_name: str,
        image: str,
        language: str = "python",
        port: int = 8080,
        cloud_provider: Optional[str] = None,
        cicd_platform: str = "github_actions",
        output_format: str = "dict"
    ) -> Dict[str, Any]:
        """生成所有配置（完整云原生栈）"""
        result = {
            "kubernetes": self.generate_kubernetes(
                app_name, image, port, output_format=output_format
            ),
            "docker": self.generate_docker(
                app_name, language, output_format=output_format
            )
        }
        
        if cloud_provider:
            result["cloud"] = self.generate_cloud(
                cloud_provider, app_name, image, port, output_format=output_format
            )
        
        result["cicd"] = self.generate_cicd(
            app_name, language, cicd_platform, output_format=output_format
        )
        
        return result


class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_kubernetes(config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证 Kubernetes 配置"""
        try:
            K8sConfig(**config)
            return True, None
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def validate_docker(config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证 Docker 配置"""
        required = ['app_name', 'language']
        for field in required:
            if field not in config:
                return False, f"缺少必需字段: {field}"
        return True, None
    
    @staticmethod
    def validate_cloud(provider: str, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证云配置"""
        if provider.lower() not in ['aws', 'gcp', 'azure']:
            return False, f"不支持的提供商: {provider}"
        return True, None


__all__ = [
    'UnifiedConfigGenerator',
    'ConfigValidator',
    'K8sConfig', 'K8sGenerator',
    'DockerConfig', 'DockerGenerator',
    'AwsConfig', 'GcpConfig', 'AzureConfig',
    'CICDConfig', 'CICDGenerator',
    'KubernetesValidator', 'DockerValidator', 'CloudValidator',
    'ResourceRequirements', 'ProbeConfig',
    'BaseImage', 'ImageFlavor',
    'DeploymentStrategy', 'Environment', 'CICDPlatform'
]
