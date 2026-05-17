"""
Configuration and Settings - Product-level implementation
Provides flexible configuration management with multiple backends
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum


class ConfigSource(Enum):
    """Configuration source types"""
    ENVIRONMENT = "environment"
    FILE = "file"
    DEFAULTS = "defaults"


@dataclass
class CodeRAGSettings:
    """Main configuration settings for Code RAG"""
    
    # General settings
    app_name: str = "code_rag"
    app_version: str = "11.0.0"
    debug: bool = False
    
    # Embedding settings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    embedding_cache_size: int = 10000
    embedding_batch_size: int = 32
    
    # Vector index settings
    vector_index_type: str = "flat"  # flat, ivf, hnsw
    vector_index_path: Optional[str] = None
    vector_index_dimension: int = 384
    
    # Search settings
    search_top_k: int = 10
    search_similarity_threshold: float = 0.0
    hybrid_search_weight: float = 0.5  # BM25 vs Vector
    
    # LLM settings
    llm_backend: str = "smart_rule"  # smart_rule, openai, anthropic, local
    llm_model: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1000
    llm_api_key: Optional[str] = None
    llm_api_base: Optional[str] = None
    
    # Logging settings
    log_level: str = "INFO"
    log_dir: Optional[str] = None
    log_max_files: int = 10
    log_max_size_mb: int = 10
    
    # Performance settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size_mb: int = 10
    max_files_per_index: int = 10000
    
    # Storage settings
    data_dir: Optional[str] = None
    index_dir: Optional[str] = None
    backup_dir: Optional[str] = None
    
    # Security settings
    enable_auth: bool = False
    auth_token: Optional[str] = None
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 3600
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key"""
        return getattr(self, key, default)
    
    def set(self, key: str, value: Any):
        """Set a setting value"""
        if hasattr(self, key):
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def from_dict(self, data: Dict[str, Any]):
        """Load from dictionary"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class ConfigManager:
    """
    Centralized configuration manager
    Handles loading, saving, and merging configuration from multiple sources
    """
    
    def __init__(self, settings: Optional[CodeRAGSettings] = None):
        self.settings = settings or CodeRAGSettings()
        self.config_sources: Dict[str, Dict] = {}
        self._load_from_defaults()
    
    def _load_from_defaults(self):
        """Load default configuration"""
        self.config_sources[ConfigSource.DEFAULTS.value] = self.settings.to_dict()
    
    def load_from_env(self, prefix: str = "CODE_RAG_"):
        """Load configuration from environment variables"""
        env_config = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                # Convert string values to appropriate types
                env_config[config_key] = self._parse_env_value(value)
        
        if env_config:
            self.config_sources[ConfigSource.ENVIRONMENT.value] = env_config
            self._merge_config(env_config)
    
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type"""
        # Try booleans
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False
        
        # Try integers
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try floats
        try:
            return float(value)
        except ValueError:
            pass
        
        # Try JSON
        if (value.startswith('{') and value.endswith('}')) or \
           (value.startswith('[') and value.endswith(']')):
            try:
                return json.loads(value)
            except:
                pass
        
        # String
        return value
    
    def load_from_file(self, filepath: Union[str, Path]):
        """Load configuration from JSON/YAML file"""
        filepath = Path(filepath)
        
        if not filepath.exists():
            return
        
        file_config = {}
        
        if filepath.suffix == '.json':
            with open(filepath, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
        elif filepath.suffix in ('.yaml', '.yml'):
            try:
                import yaml
                with open(filepath, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
            except ImportError:
                print("Warning: PyYAML not available, cannot load YAML config")
        
        if file_config:
            self.config_sources[ConfigSource.FILE.value] = file_config
            self._merge_config(file_config)
    
    def _merge_config(self, config: Dict[str, Any]):
        """Merge configuration into settings"""
        for key, value in config.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
    
    def save_to_file(self, filepath: Union[str, Path]):
        """Save current configuration to file"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.settings.to_dict()
        
        if filepath.suffix == '.json':
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif filepath.suffix in ('.yaml', '.yml'):
            try:
                import yaml
                with open(filepath, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            except ImportError:
                print("Warning: PyYAML not available, using JSON format")
                json_path = filepath.with_suffix('.json')
                self.save_to_file(json_path)
    
    def get_config_sources(self) -> Dict[str, Dict]:
        """Get all configuration sources"""
        return self.config_sources.copy()
    
    def reset_to_defaults(self):
        """Reset settings to defaults"""
        self.settings = CodeRAGSettings()
        self.config_sources = {}
        self._load_from_defaults()


class ConfigLoader:
    """
    Easy configuration loader
    Provides simple interface for getting configuration
    """
    
    _instance: Optional['ConfigLoader'] = None
    _config_manager: Optional[ConfigManager] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config_manager is None:
            self._config_manager = ConfigManager()
    
    def get_config(self) -> CodeRAGSettings:
        """Get current configuration"""
        return self._config_manager.settings
    
    def load_config(self, config_path: Optional[Union[str, Path]] = None,
                    env_prefix: str = "CODE_RAG_"):
        """Load configuration from all sources"""
        if config_path:
            self._config_manager.load_from_file(config_path)
        self._config_manager.load_from_env(env_prefix)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting with optional default"""
        return self._config_manager.settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a setting value"""
        self._config_manager.settings.set(key, value)


# Global instances
_global_config_manager: Optional[ConfigManager] = None
_global_settings: Optional[CodeRAGSettings] = None


def get_config_manager() -> ConfigManager:
    """Get the global config manager"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def get_settings() -> CodeRAGSettings:
    """Get the global settings instance"""
    global _global_settings
    if _global_settings is None:
        _global_settings = CodeRAGSettings()
    return _global_settings


# Simple fallback if other modules are not available
def simple_log(message: str, level: str = "INFO"):
    """Simple logging function for graceful degradation"""
    print(f"[{level}] {message}")


if __name__ == "__main__":
    # Test configuration
    config = ConfigLoader()
    settings = config.get_config()
    
    print("Default settings:")
    print(f"  app_name: {settings.app_name}")
    print(f"  embedding_model: {settings.embedding_model}")
    print(f"  llm_backend: {settings.llm_backend}")
    
    # Test setting values
    settings.set("debug", True)
    print(f"  debug: {settings.debug}")
