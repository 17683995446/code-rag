"""Docker 编排自动化生成器测试

阶段 B: Docker 编排自动化
验证 12 个优化点
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from code_rag.middleware_layer.docker_generator import (
    DockerfileGenerator, DockerComposeGenerator, BuildKitConfigGenerator,
    HealthCheckGenerator, LayerCacheConfigGenerator, MultiArchConfigGenerator,
    SecurityConfigGenerator, ImageFlavorGenerator, VolumeNetworkGenerator,
    ResourceLimitGenerator, BuildArgsGenerator, ImageSigningGenerator,
    DockerConfigGenerator, DockerBuildConfig, ImageFlavor, BaseImage
)


def create_docker_config() -> DockerBuildConfig:
    return DockerBuildConfig(
        app_name="my-app",
        language="python",
        version="v1.0.0",
        base_image=BaseImage.ALPINE,
        port=8000,
        health_check_path="/health",
        enable_multistage=True,
        enable_buildkit=True,
        non_root_user=True,
        read_only_rootfs=True,
        platforms=["linux/amd64", "linux/arm64"],
        build_args={"VERSION": "1.0.0"},
        env_vars={"LOG_LEVEL": "info"},
        volumes=["app-data:/data"],
        networks=["app-network"],
        shm_size="64m",
        ulimits={"nofile": {"soft": 1024, "hard": 4096}},
        enable_cache=True,
        enable_image_signing=True
    )


def test_optimization_1_dockerfile():
    """优化点 1: 多阶段 Dockerfile 生成"""
    print("\n" + "="*70)
    print("优化点 1: 多阶段 Dockerfile 生成")
    print("="*70)
    
    gen = DockerfileGenerator()
    config = create_docker_config()
    
    dockerfile = gen.generate(config)
    
    assert "FROM" in dockerfile
    assert "AS builder" in dockerfile or "AS runtime" in dockerfile
    assert f"EXPOSE {config.port}" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "USER app" in dockerfile
    
    print(f"  ✅ Dockerfile 生成成功")
    print(f"     - 多阶段构建: ✅")
    print(f"     - 健康检查: ✅")
    print(f"     - 非 root 用户: ✅")
    
    return True


def test_optimization_2_docker_compose():
    """优化点 2: Docker Compose 文件生成"""
    print("\n" + "="*70)
    print("优化点 2: Docker Compose 文件生成")
    print("="*70)
    
    gen = DockerComposeGenerator()
    config = create_docker_config()
    
    compose_dev = gen.generate(config, ImageFlavor.DEVELOPMENT)
    compose_prod = gen.generate(config, ImageFlavor.PRODUCTION)
    
    assert "services" in compose_dev
    assert "networks" in compose_dev
    assert compose_dev["services"][config.app_name]["container_name"] == f"{config.app_name}-development"
    assert compose_prod["services"][config.app_name]["restart"] == "unless-stopped"
    
    print(f"  ✅ Docker Compose 生成成功")
    print(f"     - 开发配置: ✅")
    print(f"     - 生产配置: ✅")
    
    return True


def test_optimization_3_buildkit():
    """优化点 3: BuildKit 配置优化"""
    print("\n" + "="*70)
    print("优化点 3: BuildKit 配置优化")
    print("="*70)
    
    gen = BuildKitConfigGenerator()
    config = create_docker_config()
    
    buildkit = gen.generate(config)
    
    assert "buildkit" in buildkit
    assert "platforms" in buildkit["buildkit"]["runner"]
    assert buildkit["buildkit"]["runner"]["platforms"] == ["linux/amd64", "linux/arm64"]
    
    print(f"  ✅ BuildKit 配置生成成功")
    print(f"     - 平台支持: {len(buildkit['buildkit']['runner']['platforms'])}")
    
    return True


def test_optimization_4_healthcheck():
    """优化点 4: 健康检查实现"""
    print("\n" + "="*70)
    print("优化点 4: 健康检查实现")
    print("="*70)
    
    gen = HealthCheckGenerator()
    config = create_docker_config()
    
    healthcheck = gen.generate(config)
    
    assert "test" in healthcheck
    assert "interval" in healthcheck
    assert "timeout" in healthcheck
    assert "retries" in healthcheck
    assert healthcheck["retries"] == 3
    
    print(f"  ✅ 健康检查配置生成成功")
    print(f"     - 间隔: {healthcheck['interval']}")
    print(f"     - 超时: {healthcheck['timeout']}")
    print(f"     - 重试次数: {healthcheck['retries']}")
    
    return True


def test_optimization_5_layer_cache():
    """优化点 5: 层缓存优化"""
    print("\n" + "="*70)
    print("优化点 5: 层缓存优化")
    print("="*70)
    
    gen = LayerCacheConfigGenerator()
    config = create_docker_config()
    
    cache_lines = gen.generate(config)
    
    assert len(cache_lines) > 0
    assert any("--mount=type=cache" in line for line in cache_lines)
    
    print(f"  ✅ 层缓存配置生成成功")
    print(f"     - 缓存指令数: {sum(1 for l in cache_lines if '--mount=type=cache' in l)}")
    
    return True


def test_optimization_6_multiarch():
    """优化点 6: 多架构支持"""
    print("\n" + "="*70)
    print("优化点 6: 多架构支持")
    print("="*70)
    
    gen = MultiArchConfigGenerator()
    config = create_docker_config()
    
    multiarch = gen.generate(config)
    
    assert "platforms" in multiarch
    assert "linux/amd64" in multiarch["platforms"]
    assert "linux/arm64" in multiarch["platforms"]
    assert multiarch["qemu"]["enabled"] == True
    
    print(f"  ✅ 多架构配置生成成功")
    print(f"     - 支持平台: {len(multiarch['platforms'])}")
    
    return True


def test_optimization_7_security():
    """优化点 7: 安全最佳实践"""
    print("\n" + "="*70)
    print("优化点 7: 安全最佳实践")
    print("="*70)
    
    gen = SecurityConfigGenerator()
    config = create_docker_config()
    
    security = gen.generate(config)
    
    assert security["non_root_user"] == True
    assert security["read_only_rootfs"] == True
    assert security["no_new_privileges"] == True
    assert "ALL" in security["capabilities"]["drop"]
    
    print(f"  ✅ 安全配置生成成功")
    print(f"     - 非 root 用户: ✅")
    print(f"     - 只读根文件系统: ✅")
    print(f"     - 丢弃所有能力: ✅")
    
    return True


def test_optimization_8_flavor():
    """优化点 8: 开发与生产镜像差异化"""
    print("\n" + "="*70)
    print("优化点 8: 开发与生产镜像差异化")
    print("="*70)
    
    gen = ImageFlavorGenerator()
    config = create_docker_config()
    
    flavors = gen.generate(config)
    
    assert "development" in flavors
    assert "staging" in flavors
    assert "production" in flavors
    assert flavors["development"]["hot_reload"] == True
    assert flavors["production"]["strip_debugging"] == True
    
    print(f"  ✅ 镜像差异化配置生成成功")
    print(f"     - 开发模式热重载: ✅")
    print(f"     - 生产模式优化: ✅")
    
    return True


def test_optimization_9_volume_network():
    """优化点 9: 卷和网络配置"""
    print("\n" + "="*70)
    print("优化点 9: 卷和网络配置")
    print("="*70)
    
    gen = VolumeNetworkGenerator()
    config = create_docker_config()
    
    vol_net = gen.generate(config)
    
    assert "volumes" in vol_net
    assert "networks" in vol_net
    assert "app-network" in vol_net["networks"]
    assert "subnet" in vol_net["network_config"]["app-network"]["ipam"]["config"][0]
    
    print(f"  ✅ 卷和网络配置生成成功")
    print(f"     - 卷: {len(vol_net['volumes'])}")
    print(f"     - 网络: {len(vol_net['networks'])}")
    
    return True


def test_optimization_10_resources():
    """优化点 10: 资源限制"""
    print("\n" + "="*70)
    print("优化点 10: 资源限制")
    print("="*70)
    
    gen = ResourceLimitGenerator()
    config = create_docker_config()
    
    resources = gen.generate(config)
    
    assert "shm_size" in resources
    assert "ulimits" in resources
    assert "memory" in resources
    assert "cpu" in resources
    
    print(f"  ✅ 资源限制配置生成成功")
    print(f"     - SHM 大小: {resources['shm_size']}")
    print(f"     - 内存限制: {resources['memory']['limit']}")
    
    return True


def test_optimization_11_build_args():
    """优化点 11: 构建参数和环境变量"""
    print("\n" + "="*70)
    print("优化点 11: 构建参数和环境变量")
    print("="*70)
    
    gen = BuildArgsGenerator()
    config = create_docker_config()
    
    args = gen.generate(config)
    
    assert "build_args" in args
    assert "env_vars" in args
    assert "BUILDKIT_INLINE_CACHE" in args["build_args"]
    assert "PORT" in args["env_vars"]
    
    print(f"  ✅ 构建参数和环境变量生成成功")
    print(f"     - 构建参数: {len(args['build_args'])}")
    print(f"     - 环境变量: {len(args['env_vars'])}")
    
    return True


def test_optimization_12_signing():
    """优化点 12: 镜像签名和出处验证"""
    print("\n" + "="*70)
    print("优化点 12: 镜像签名和出处验证")
    print("="*70)
    
    gen = ImageSigningGenerator()
    config = create_docker_config()
    
    signing = gen.generate(config)
    
    assert signing["enabled"] == True
    assert "cosign" in signing
    assert "sbom" in signing
    assert signing["sbom"]["enabled"] == True
    
    print(f"  ✅ 镜像签名配置生成成功")
    print(f"     - Cosign 签名: ✅")
    print(f"     - SBOM: ✅")
    
    return True


def test_complete_docker_generation():
    """测试完整 Docker 配置生成"""
    print("\n" + "="*70)
    print("完整 Docker 编排配置生成")
    print("="*70)
    
    generator = DockerConfigGenerator()
    config = create_docker_config()
    
    all_configs = generator.generate_all(config)
    
    expected_files = [
        "Dockerfile", "docker-compose.yml", "docker-compose.dev.yml",
        "docker-compose.prod.yml", "buildkit.toml", "healthcheck.yml",
        "layer-cache.txt", "multiarch.yml", "security.yml", "flavors.yml",
        "volumes-networks.yml", "resources.yml", "build-args.yml", "image-signing.yml"
    ]
    
    for key in expected_files:
        assert key in all_configs, f"Missing: {key}"
    
    print(f"  ✅ 生成了 {len(all_configs)} 个配置文件:")
    for name in all_configs.keys():
        print(f"     - {name}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("="*70)
    print("🧪 Code RAG v24.0 - Docker 编排自动化生成器测试")
    print("="*70)
    print("验证 12 个优化点")
    print("="*70)
    
    tests = [
        ("Dockerfile 多阶段构建", test_optimization_1_dockerfile),
        ("Docker Compose 配置", test_optimization_2_docker_compose),
        ("BuildKit 配置", test_optimization_3_buildkit),
        ("健康检查", test_optimization_4_healthcheck),
        ("层缓存优化", test_optimization_5_layer_cache),
        ("多架构支持", test_optimization_6_multiarch),
        ("安全最佳实践", test_optimization_7_security),
        ("镜像差异化", test_optimization_8_flavor),
        ("卷和网络配置", test_optimization_9_volume_network),
        ("资源限制", test_optimization_10_resources),
        ("构建参数", test_optimization_11_build_args),
        ("镜像签名", test_optimization_12_signing),
        ("完整配置生成", test_complete_docker_generation),
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
            failed += 1
    
    print("\n" + "="*70)
    print("📋 Docker 编排自动化生成器测试总结")
    print("="*70)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {100.0 * passed / len(tests):.1f}%")
    print("="*70)
    
    if failed == 0:
        print("\n🎉 所有 Docker 编排自动化生成器测试通过！")
        print("✅ 已验证 12 个优化点！")
    else:
        print(f"\n⚠️ {failed}个测试失败")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
