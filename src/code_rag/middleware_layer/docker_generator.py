"""Docker 编排自动化生成器

阶段 B: Docker 编排自动化
12 个优化点:
1. 多阶段 Dockerfile 生成
2. Docker Compose 文件生成（开发/预发布/生产）
3. BuildKit 配置优化
4. 健康检查实现
5. 层缓存优化
6. 多架构支持
7. 安全最佳实践（非 root 用户、只读文件系统）
8. 开发与生产镜像差异化
9. 卷和网络配置
10. 资源限制（ulimits、shm-size）
11. 构建参数和环境变量
12. 镜像签名和出处验证
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class ImageFlavor(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class BaseImage(Enum):
    ALPINE = "alpine"
    DEBIAN = "debian"
    UBUNTU = "ubuntu"
    DISTROLESS = "distroless"


@dataclass
class DockerBuildConfig:
    app_name: str = "app"
    language: str = "python"
    version: str = "latest"
    base_image: BaseImage = BaseImage.ALPINE
    port: int = 8000
    health_check_path: str = "/health"
    enable_multistage: bool = True
    enable_buildkit: bool = True
    non_root_user: bool = True
    read_only_rootfs: bool = True
    platforms: List[str] = field(default_factory=lambda: ["linux/amd64"])
    build_args: Dict[str, str] = field(default_factory=dict)
    env_vars: Dict[str, str] = field(default_factory=dict)
    volumes: List[str] = field(default_factory=list)
    networks: List[str] = field(default_factory=lambda: ["app-network"])
    shm_size: str = "64m"
    ulimits: Dict[str, int] = field(default_factory=lambda: {"nofile": {"soft": 1024, "hard": 4096}})
    enable_cache: bool = True
    enable_image_signing: bool = False


class DockerfileGenerator:
    """多阶段 Dockerfile 生成器（优化点 1）"""
    
    def generate(self, config: DockerBuildConfig) -> str:
        if config.enable_multistage:
            return self._generate_multistage(config)
        return self._generate_single_stage(config)
    
    def _generate_single_stage(self, config: DockerBuildConfig) -> str:
        base = self._get_base_image(config.base_image, config.language)
        lines = [
            f"FROM {base}",
            "",
            "WORKDIR /app",
        ]
        
        if config.language == "python":
            lines.extend(["COPY requirements.txt .", "RUN pip install --no-cache-dir -r requirements.txt"])
        elif config.language == "node":
            lines.extend(["COPY package*.json .", "RUN npm ci --only=production"])
        
        lines.extend(["COPY . .", f"EXPOSE {config.port}"])
        
        if config.health_check_path:
            lines.append(f"HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f {config.health_check_path} || exit 1")
        
        if config.non_root_user:
            lines.extend(["RUN addgroup -g 1001 appgroup", "RUN adduser -u 1001 -G appgroup -D app", "USER app"])
        
        lines.append(f"CMD [\"python\", \"main.py\"]")
        return "\n".join(lines)
    
    def _generate_multistage(self, config: DockerBuildConfig) -> str:
        lines = [
            "# ============ 阶段 1: 构建 ============",
            f"FROM {self._get_build_base(config.language)} AS builder",
            "",
            "WORKDIR /build",
            "COPY . .",
        ]
        
        if config.language == "python":
            lines.extend(["RUN pip install --no-cache-dir -r requirements.txt", "RUN pip install --target=/build/deps -r requirements.txt"])
        elif config.language == "node":
            lines.extend(["RUN npm ci", "RUN npm run build"])
        
        lines.extend([
            "",
            "# ============ 阶段 2: 运行 ============",
            f"FROM {self._get_base_image(config.base_image, config.language)} AS runtime",
        ])
        
        if config.read_only_rootfs:
            lines.append("RUN microdnf install -y --setopt=install_weak_deps=False curl && microdnf clean all")
        
        lines.extend(["WORKDIR /app", f"COPY --from=builder /build .", f"ENV PORT={config.port}"])
        
        if config.env_vars:
            for key, val in config.env_vars.items():
                lines.append(f"ENV {key}={val}")
        
        lines.append(f"EXPOSE {config.port}")
        
        if config.health_check_path:
            lines.append(f"HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f {config.health_check_path} || exit 1")
        
        if config.non_root_user:
            lines.extend(["RUN addgroup -g 1001 appgroup", "RUN adduser -u 1001 -G appgroup -D app", "USER app"])
        
        if config.read_only_rootfs:
            lines.extend(["VOLUME /tmp", "VOLUME /var/cache", "VOLUME /var/log"])
        
        lines.append('CMD ["python", "main.py"]')
        return "\n".join(lines)
    
    def _get_base_image(self, base: BaseImage, lang: str) -> str:
        images = {
            BaseImage.ALPINE: {"python": "python:3.11-alpine", "node": "node:20-alpine", "go": "golang:alpine"},
            BaseImage.DEBIAN: {"python": "python:3.11-slim", "node": "node:20-slim", "go": "golang:slim"},
            BaseImage.UBUNTU: {"python": "python:3.11-ubuntu", "node": "node:20-ubuntu", "go": "golang:ubuntu"},
            BaseImage.DISTROLESS: {"python": "python:3.11", "node": "node:20", "go": "golang"},
        }
        return images.get(base, images[BaseImage.ALPINE]).get(lang, "alpine")
    
    def _get_build_base(self, lang: str) -> str:
        bases = {"python": "python:3.11-slim", "node": "node:20-slim", "go": "golang:1.21-alpine"}
        return bases.get(lang, "alpine")


class DockerComposeGenerator:
    """Docker Compose 文件生成器（优化点 2）"""
    
    def generate(self, config: DockerBuildConfig, flavor: ImageFlavor = ImageFlavor.DEVELOPMENT) -> Dict:
        compose = {
            "version": "3.9",
            "services": {
                config.app_name: self._generate_service(config, flavor)
            },
            "networks": {"app-network": {"driver": "bridge"}}
        }
        
        if config.volumes:
            compose["volumes"] = {v.split(":")[0]: {} for v in config.volumes}
        
        if flavor == ImageFlavor.PRODUCTION:
            compose["services"][config.app_name]["deploy"] = self._generate_deploy_config(config)
        
        return compose
    
    def _generate_service(self, config: DockerBuildConfig, flavor: ImageFlavor) -> Dict:
        service = {
            "build": {"context": ".", "dockerfile": "Dockerfile"},
            "container_name": f"{config.app_name}-{flavor.value}",
            "ports": [f"{config.port}:{config.port}"],
            "networks": config.networks,
            "restart": "unless-stopped" if flavor == ImageFlavor.PRODUCTION else "no",
        }
        
        if flavor == ImageFlavor.DEVELOPMENT:
            service["volumes"] = [".:/app"]
            service["command"] = "python main.py --debug"
        elif flavor == ImageFlavor.STAGING:
            service["environment"] = {"NODE_ENV": "staging", **config.env_vars}
            service["healthcheck"] = {"test": f"curl -f http://localhost:{config.port}{config.health_check_path}", "interval": "30s", "timeout": "10s", "retries": 3}
        elif flavor == ImageFlavor.PRODUCTION:
            service["image"] = f"{config.app_name}:{config.version}"
            service["environment"] = {"NODE_ENV": "production", **config.env_vars}
            service["read_only"] = config.read_only_rootfs
            service["shm_size"] = config.shm_size
            service["ulimits"] = config.ulimits
        
        return service
    
    def _generate_deploy_config(self, config: DockerBuildConfig) -> Dict:
        return {
            "resources": {
                "limits": {"cpus": "1.0", "memory": "512M"},
                "reservations": {"cpus": "0.25", "memory": "128M"}
            },
            "restart_policy": {"condition": "on-failure", "delay": "5s", "max_attempts": 3}
        }


class BuildKitConfigGenerator:
    """BuildKit 配置生成器（优化点 3）"""
    
    def generate(self, config: DockerBuildConfig) -> Dict:
        cache_config = {}
        if config.enable_cache:
            cache_config = {
                "type": "inline"
            }
        
        return {
            "version": "2",
            "buildkit": {
                "features": {"securityInputs": config.enable_image_signing},
                "runner": {
                    "platforms": config.platforms,
                    "cache": cache_config
                }
            }
        }


class HealthCheckGenerator:
    """健康检查配置生成器（优化点 4）"""
    
    def generate(self, config: DockerBuildConfig) -> Dict:
        return {
            "test": ["CMD", "curl", "-f", f"http://localhost:{config.port}{config.health_check_path}"],
            "interval": "30s",
            "timeout": "10s",
            "start_period": "5s",
            "retries": 3
        }


class LayerCacheConfigGenerator:
    """层缓存优化配置生成器（优化点 5）"""
    
    def generate(self, config: DockerBuildConfig) -> List[str]:
        lines = [
            "# 使用 BuildKit 缓存优化",
            "# 1. 按依赖变更频率排序 COPY 指令",
            "# 2. 先复制依赖文件，再复制源代码",
            "# 3. 使用 --mount=type=cache 挂载缓存目录",
            "",
        ]
        
        if config.language == "python":
            lines.extend([
                "# 依赖缓存挂载",
                "RUN --mount=type=cache,target=/root/.cache/pip \\",
                "    pip install --no-cache-dir -r requirements.txt",
            ])
        elif config.language == "node":
            lines.extend([
                "# npm 缓存挂载",
                "RUN --mount=type=cache,target=/root/.npm \\",
                "    npm ci",
            ])
        
        return lines


class MultiArchConfigGenerator:
    """多架构支持配置生成器（优化点 6）"""
    
    def generate(self, config: DockerBuildConfig) -> Dict:
        return {
            "version": "0.1",
            "platforms": config.platforms,
            "features": {
                "linux/amd64": {"variant": "v3"},
                "linux/arm64": {"variant": "v8"},
                "linux/arm/v7": {"variant": "v7"}
            },
            "qemu": {
                "enabled": True,
                "static": True,
                "images": ["multiarch/qemu-user-static"]
            }
        }


class SecurityConfigGenerator:
    """安全最佳实践配置生成器（优化点 7）"""
    
    def generate(self, config: DockerBuildConfig) -> Dict:
        security = {
            "non_root_user": config.non_root_user,
            "read_only_rootfs": config.read_only_rootfs,
            "no_new_privileges": True,
            "user": {"uid": 1001, "gid": 1001} if config.non_root_user else None,
            "capabilities": {"drop": ["ALL"]},
            "seccomp_profile": "default",
            "apparmor_profile": "docker-default"
        }
        
        return security


class ImageFlavorGenerator:
    """开发与生产镜像差异化配置生成器（优化点 8）"""
    
    def generate(self, config: DockerBuildConfig) -> Dict[str, Dict]:
        return {
            "development": {
                "base_image": self._get_dev_image(config),
                "debug_enabled": True,
                "source_mapping": True,
                "hot_reload": True
            },
            "staging": {
                "base_image": self._get_base_image(config),
                "debug_enabled": False,
                "optimization_level": 1,
                "source_maps": False
            },
            "production": {
                "base_image": self._get_base_image(config),
                "debug_enabled": False,
                "optimization_level": 2,
                "source_maps": False,
                "strip_debugging": True
            }
        }
    
    def _get_dev_image(self, config: DockerBuildConfig) -> str:
        dev_images = {"python": "python:3.11-slim", "node": "node:20-slim"}
        return dev_images.get(config.language, "alpine")
    
    def _get_base_image(self, config: DockerBuildConfig) -> str:
        prod_images = {"python": "python:3.11-alpine", "node": "node:20-alpine"}
        return prod_images.get(config.language, "alpine")


class VolumeNetworkGenerator:
    """卷和网络配置生成器（优化点 9）"""
    
    def generate(self, config: DockerBuildConfig) -> Dict:
        return {
            "volumes": config.volumes or [f"{config.app_name}-data:/data"],
            "networks": config.networks,
            "network_config": {
                "app-network": {
                    "driver": "bridge",
                    "ipam": {"driver": "default", "config": [{"subnet": "172.28.0.0/16"}]}
                }
            }
        }


class ResourceLimitGenerator:
    """资源限制配置生成器（优化点 10）"""
    
    def generate(self, config: DockerBuildConfig) -> Dict:
        return {
            "shm_size": config.shm_size,
            "ulimits": config.ulimits,
            "memory": {"limit": "512m", "reservation": "128m"},
            "cpu": {"count": 2, "percentage": 80}
        }


class BuildArgsGenerator:
    """构建参数和环境变量生成器（优化点 11）"""
    
    def generate(self, config: DockerBuildConfig) -> Dict:
        return {
            "build_args": {
                "BUILDKIT_INLINE_CACHE": "1",
                "NODE_ENV": "production",
                **config.build_args
            },
            "env_vars": {
                "PORT": str(config.port),
                "NODE_ENV": "production",
                **config.env_vars
            }
        }


class ImageSigningGenerator:
    """镜像签名和出处验证配置生成器（优化点 12）"""
    
    def generate(self, config: DockerBuildConfig) -> Dict:
        if not config.enable_image_signing:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "cosign": {
                "key": "cosign.key",
                "certificate": "cosign.crt",
                "attest": True,
                "provenance": True
            },
            "docker_content_trust": {
                "enabled": True,
                "export": True
            },
            "sbom": {
                "enabled": True,
                "format": "spdx"
            }
        }


class DockerConfigGenerator:
    """完整的 Docker 配置生成器"""
    
    def __init__(self):
        self.dockerfile_gen = DockerfileGenerator()
        self.compose_gen = DockerComposeGenerator()
        self.buildkit_gen = BuildKitConfigGenerator()
        self.healthcheck_gen = HealthCheckGenerator()
        self.layer_cache_gen = LayerCacheConfigGenerator()
        self.multiarch_gen = MultiArchConfigGenerator()
        self.security_gen = SecurityConfigGenerator()
        self.flavor_gen = ImageFlavorGenerator()
        self.volume_net_gen = VolumeNetworkGenerator()
        self.resource_gen = ResourceLimitGenerator()
        self.args_gen = BuildArgsGenerator()
        self.signing_gen = ImageSigningGenerator()
    
    def generate_all(self, config: DockerBuildConfig) -> Dict[str, any]:
        configs = {
            "Dockerfile": self.dockerfile_gen.generate(config),
            "docker-compose.yml": self.compose_gen.generate(config),
            "docker-compose.dev.yml": self.compose_gen.generate(config, ImageFlavor.DEVELOPMENT),
            "docker-compose.prod.yml": self.compose_gen.generate(config, ImageFlavor.PRODUCTION),
            "buildkit.toml": self.buildkit_gen.generate(config),
            "healthcheck.yml": self.healthcheck_gen.generate(config),
            "layer-cache.txt": self.layer_cache_gen.generate(config),
            "multiarch.yml": self.multiarch_gen.generate(config),
            "security.yml": self.security_gen.generate(config),
            "flavors.yml": self.flavor_gen.generate(config),
            "volumes-networks.yml": self.volume_net_gen.generate(config),
            "resources.yml": self.resource_gen.generate(config),
            "build-args.yml": self.args_gen.generate(config),
            "image-signing.yml": self.signing_gen.generate(config),
        }
        return configs
