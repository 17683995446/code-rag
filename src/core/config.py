"""
配置管理 - 产品级 (增强版)
支持环境变量、YAML、JSON配置文件
站在巨人的肩膀上 - 使用pyyaml
"""

import os
import json
from pathlib import Path
from typing import Any, Optional, Dict, Union
from dataclasses import dataclass, field, asdict

from .logger import get_logger

logger = get_logger(__name__)

# 尝试导入yaml，如果失败则使用fallback
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logger.warning("yaml not available, YAML configuration loading disabled")


class ConfigLoader:
    """
    产品级配置加载器
    支持多种配置源：环境变量、YAML、JSON
    """

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._sources: list = []

    def load_env(self, prefix: str = "CODE_RAG_") -> "ConfigLoader":
        """从环境变量加载"""
        env_config = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower().replace("_", ".")
                env_config[config_key] = self._parse_value(value)
        self._config.update(env_config)
        self._sources.append("environment")
        logger.debug(f"从环境变量加载了 {len(env_config)} 个配置项")
        return self

    def load_yaml(self, file_path: str) -> "ConfigLoader":
        """从YAML文件加载"""
        if not YAML_AVAILABLE:
            logger.warning(f"YAML not available, skipping YAML load: {file_path}")
            return self
            
        path = Path(file_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f) or {}
                self._config.update(yaml_config)
            self._sources.append(f"yaml:{file_path}")
            logger.debug(f"从YAML加载了 {len(yaml_config)} 个配置项: {file_path}")
        return self

    def load_json(self, file_path: str) -> "ConfigLoader":
        """从JSON文件加载"""
        path = Path(file_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                json_config = json.load(f)
                self._config.update(json_config)
            self._sources.append(f"json:{file_path}")
            logger.debug(f"从JSON加载了 {len(json_config)} 个配置项: {file_path}")
        return self

    def load_defaults(self, defaults: Dict[str, Any]) -> "ConfigLoader":
        """加载默认值"""
        self._config.update(defaults)
        self._sources.append("defaults")
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._config.copy()

    def get_sources(self) -> list:
        """获取配置源列表"""
        return self._sources.copy()

    def _parse_value(self, value: str) -> Any:
        """解析环境变量值"""
        # 布尔值
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False

        # 数字
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # 列表（逗号分隔）
        if ',' in value:
            items = [item.strip() for item in value.split(',')]
            return items

        return value


class ConfigManager:
    """
    产品级配置管理器
    支持配置验证、默认值、配置重载
    """

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._loader = ConfigLoader()
        self._initialized = False

    def initialize(self,
                  config_file: Optional[str] = None,
                  env_prefix: str = "CODE_RAG_",
                  defaults: Optional[Dict[str, Any]] = None) -> None:
        """初始化配置"""
        if defaults:
            self._loader.load_defaults(defaults)

        if config_file:
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                self._loader.load_yaml(config_file)
            elif config_file.endswith('.json'):
                self._loader.load_json(config_file)

        self._loader.load_env(env_prefix)

        self._config = self._loader.to_dict()
        self._initialized = True
        logger.info(f"配置初始化完成，来源: {self._loader.get_sources()}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        if not self._initialized:
            logger.warning("配置未初始化，使用默认值")
            return default
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置"""
        self._loader.set(key, value)
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def reload(self) -> None:
        """重新加载配置"""
        logger.info("重新加载配置")
        self._config = self._loader.to_dict()

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()

    def validate(self, schema: Dict[str, Any]) -> bool:
        """验证配置"""
        for key, rules in schema.items():
            value = self.get(key)

            # 必需检查
            if rules.get('required', False) and value is None:
                logger.error(f"必需配置项缺失: {key}")
                return False

            # 类型检查
            if value is not None and 'type' in rules:
                expected_type = rules['type']
                if not isinstance(value, expected_type):
                    logger.error(f"配置项类型错误: {key}, 期望 {expected_type}, 实际 {type(value)}")
                    return False

            # 范围检查
            if value is not None:
                if 'min' in rules and value < rules['min']:
                    logger.error(f"配置项值过小: {key}")
                    return False
                if 'max' in rules and value > rules['max']:
                    logger.error(f"配置项值过大: {key}")
                    return False

        return True


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def init_config(config_file: Optional[str] = None,
                env_prefix: str = "CODE_RAG_",
                defaults: Optional[Dict[str, Any]] = None) -> ConfigManager:
    """初始化配置（便捷函数）"""
    manager = get_config_manager()
    manager.initialize(config_file, env_prefix, defaults)
    return manager


def get_config(key: str, default: Any = None) -> Any:
    """获取配置值（便捷函数）"""
    return get_config_manager().get(key, default)


def set_config(key: str, value: Any) -> None:
    """设置配置值（便捷函数）"""
    get_config_manager().set(key, value)
