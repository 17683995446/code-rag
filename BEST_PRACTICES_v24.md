# v24.0 最佳实践指南

## 目录

1. [Kubernetes 最佳实践](#kubernetes-最佳实践)
2. [Docker 最佳实践](#docker-最佳实践)
3. [云服务最佳实践](#云服务最佳实践)
4. [CI/CD 最佳实践](#cicd-最佳实践)
5. [性能优化建议](#性能优化建议)
6. [安全建议](#安全建议)

---

## Kubernetes 最佳实践

### 1. 资源配额设置

```python
from code_rag.middleware_layer.kubernetes_generator import KubernetesConfig, ResourceRequirements

# 推荐：设置合理的资源限制
config = KubernetesConfig(
    app_name="my-app",
    image="my-app:v1",
    resources=ResourceRequirements(
        cpu_request="100m",    # 最小需求
        cpu_limit="500m",       # 最大限制
        memory_request="128Mi",
        memory_limit="512Mi"
    )
)
```

### 2. 健康检查配置

```python
from code_rag.middleware_layer.kubernetes_generator import KubernetesConfig, ProbeConfig

config = KubernetesConfig(
    readiness_probe=ProbeConfig(
        enabled=True,
        initial_delay_seconds=30,  # 等待应用启动
        period_seconds=10,
        failure_threshold=3
    ),
    liveness_probe=ProbeConfig(
        enabled=True,
        initial_delay_seconds=60,  # 更长的启动延迟
        period_seconds=30
    )
)
```

### 3. 副本数设置

```python
# 开发环境：1 副本
# 生产环境：3+ 副本（建议奇数）
# 高可用：5+ 副本

config = KubernetesConfig(replicas=3)
```

### 4. 命名规范

```python
# ✅ 正确
config = KubernetesConfig(app_name="my-app", namespace="production")

# ❌ 错误（包含大写）
config = KubernetesConfig(app_name="MyApp")
```

---

## Docker 最佳实践

### 1. 使用多阶段构建

```python
from code_rag.middleware_layer.docker_generator import DockerBuildConfig, BaseImage

config = DockerBuildConfig(
    app_name="my-app",
    language="python",
    base_image=BaseImage.ALPINE,  # 使用 Alpine 减小镜像大小
    enable_multistage=True        # 启用多阶段构建
)
```

### 2. 安全配置

```python
config = DockerBuildConfig(
    non_root_user=True,           # 以非 root 用户运行
    read_only_rootfs=True,        # 只读根文件系统
    enable_image_signing=True     # 启用镜像签名
)
```

### 3. 多架构支持

```python
config = DockerBuildConfig(
    platforms=["linux/amd64", "linux/arm64", "linux/arm/v7"]
)
```

### 4. 构建缓存优化

```python
config = DockerBuildConfig(
    enable_cache=True,
    enable_buildkit=True
)
```

---

## 云服务最佳实践

### 1. AWS ECS/Fargate

```python
from code_rag.middleware_layer.cloud_generator import AwsConfig, AwsRegion

config = AwsConfig(
    app_name="my-app",
    region=AwsRegion.US_EAST_1,
    enable_fargate=True,          # 使用 Fargate 无服务器模式
    spot_instances=True,          # 使用 Spot 实例降低成本
    enable_autoscaling=True,
    desired_count=2,
    min_instances=1,
    max_instances=10
)
```

### 2. GCP Cloud Run

```python
from code_rag.middleware_layer.cloud_generator import GcpConfig, GcpRegion

config = GcpConfig(
    project_id="my-project",
    region=GcpRegion.US_CENTRAL1,
    min_instances=0,              # 零实例时降低成本
    max_instances=100
)
```

### 3. Azure AKS

```python
from code_rag.middleware_layer.cloud_generator import AzureConfig, AzureRegion

config = AzureConfig(
    resource_group="my-rg",
    location=AzureRegion.EAST_US,
    enable_managed_identity=True,  # 使用托管身份
    enable_autoscaling=True,
    cost_optimized=True           # 启用成本优化
)
```

### 4. 多云策略

```python
from code_rag.middleware_layer.cloud_generator import MultiCloudAbstractionGenerator

gen = MultiCloudAbstractionGenerator()
unified = gen.generate_unified_config(config)
```

---

## CI/CD 最佳实践

### 1. 部署策略选择

```python
from code_rag.middleware_layer.cicd_generator import PipelineConfig, DeploymentStrategy

# 开发环境：滚动更新（快速）
# 生产环境：金丝雀（安全）
config = PipelineConfig(
    deployment_strategy=DeploymentStrategy.CANARY,
    enable_rollback=True
)
```

### 2. 安全扫描集成

```python
config = PipelineConfig(
    enable_security_scan=True,
    enable_integration_tests=True,
    enable_e2e_tests=True
)
```

### 3. 通知配置

```python
config = PipelineConfig(
    enable_notifications=True,
    notification_channels=["slack", "email"],
    slack_webhook="https://hooks.slack.com/..."
)
```

### 4. 回滚策略

```python
config = PipelineConfig(
    enable_rollback=True,
    enable_iac=True
)
```

---

## 性能优化建议

### 1. 生成器性能基准

| 操作 | 平均时间 | 说明 |
|------|----------|------|
| Kubernetes 配置生成 | ~0.01 ms | 极快 |
| Docker 配置生成 | ~0.02 ms | 极快 |
| 云配置生成 | ~0.05 ms | 快速 |
| CI/CD 配置生成 | ~0.1 ms | 快速 |

### 2. 内存使用

- 单次生成：~6 KB
- 1000次生成：~6 MB
- 建议：批量生成时使用生成器模式

### 3. 优化建议

```python
# ✅ 推荐：批量配置
generator = KubernetesConfigGenerator()
configs = {f"app-{i}": generator.generate_all(config) for i in range(100)}

# ✅ 推荐：复用生成器实例
gen = KubernetesConfigGenerator()
for config in configs:
    result = gen.generate_all(config)
```

---

## 安全建议

### 1. 镜像安全

```python
# ✅ 使用最小化基础镜像
base_image=BaseImage.DISTROLESS

# ✅ 启用镜像签名
enable_image_signing=True

# ✅ 定期扫描
enable_security_scan=True
```

### 2. 运行时安全

```python
# ✅ 非 root 用户
non_root_user=True

# ✅ 只读文件系统
read_only_rootfs=True

# ✅ 丢弃所有能力
# (在 security.yml 中配置)
```

### 3. 网络安全

```python
# ✅ 使用 NetworkPolicy
config = KubernetesConfig()
# 会生成 network-policy.yaml

# ✅ 限制端口暴露
config = KubernetesConfig(port=8080)  # 仅暴露必要端口
```

### 4. 密钥管理

```python
# ✅ 使用 Kubernetes Secrets
configmap_gen = ConfigMapGenerator()
secret_gen = SecretGenerator()

# ✅ 不要在配置中硬编码密钥
# 使用环境变量或外部密钥管理
```

---

## 配置验证

使用内置验证器检查配置：

```python
from code_rag.middleware_layer.validators import (
    KubernetesValidator,
    DockerValidator,
    CloudValidator
)

# 验证 Kubernetes 配置
valid, error = KubernetesValidator.validate_name("my-app")
if not valid:
    raise ValueError(error)

# 验证端口
valid, error = KubernetesValidator.validate_port(8080)
if not valid:
    raise ValueError(error)

# 验证副本数
valid, error = KubernetesValidator.validate_replicas(3)
if not valid:
    raise ValueError(error)
```

---

## 常见问题解决

### 问题 1: 镜像拉取失败

**解决方案**：
```python
config = KubernetesConfig(
    image="my-registry.com/my-app:v1"  # 使用完整镜像地址
)
```

### 问题 2: 资源限制不足

**解决方案**：
```python
config = KubernetesConfig(
    resources=ResourceRequirements(
        cpu_request="500m",
        cpu_limit="1000m",
        memory_request="256Mi",
        memory_limit="1Gi"
    )
)
```

### 问题 3: 部署超时

**解决方案**：
```python
# 在 helm 命令中添加 --timeout
# helm upgrade --install my-app ./chart --wait --timeout 10m
```

---

*最后更新: 2026-05-16*
