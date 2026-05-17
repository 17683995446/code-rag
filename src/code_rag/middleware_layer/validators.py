"""Kubernetes 验证和工具模块

提供输入验证、错误处理和辅助函数
"""

import re
from typing import List, Optional, Tuple


class ValidationError(Exception):
    """验证错误异常"""
    pass


class KubernetesValidator:
    """Kubernetes 配置验证器"""
    
    MAX_NAME_LENGTH = 253
    MAX_LABEL_LENGTH = 63
    VALID_NAME_PATTERN = re.compile(r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$')
    VALID_LABEL_PATTERN = re.compile(r'^([a-z0-9]([-a-z0-9]*[a-z0-9])?)?$')
    
    @classmethod
    def validate_name(cls, name: str, field: str = "name") -> Tuple[bool, Optional[str]]:
        """验证 Kubernetes 资源名称"""
        if not name:
            return False, f"{field} cannot be empty"
        
        if len(name) > cls.MAX_NAME_LENGTH:
            return False, f"{field} exceeds maximum length of {cls.MAX_NAME_LENGTH}"
        
        if not cls.VALID_NAME_PATTERN.match(name):
            return False, f"{field} must consist of lowercase alphanumeric characters or '-', and must start and end with an alphanumeric character"
        
        return True, None
    
    @classmethod
    def validate_port(cls, port: int) -> Tuple[bool, Optional[str]]:
        """验证端口号"""
        if not isinstance(port, int):
            return False, "port must be an integer"
        
        if port < 1 or port > 65535:
            return False, f"port must be between 1 and 65535, got {port}"
        
        return True, None
    
    @classmethod
    def validate_replicas(cls, replicas: int) -> Tuple[bool, Optional[str]]:
        """验证副本数"""
        if not isinstance(replicas, int):
            return False, "replicas must be an integer"
        
        if replicas < 0:
            return False, f"replicas cannot be negative, got {replicas}"
        
        if replicas > 10000:
            return False, f"replicas exceeds maximum of 10000, got {replicas}"
        
        return True, None
    
    @classmethod
    def validate_memory(cls, memory: str) -> Tuple[bool, Optional[str]]:
        """验证内存格式"""
        if not isinstance(memory, str):
            return False, "memory must be a string like '128Mi' or '1Gi'"
        
        pattern = re.compile(r'^\d+(Ei|Pi|Ti|Gi|Mi|Ki|E|P|T|G|M|K)?$')
        if not pattern.match(memory):
            return False, f"invalid memory format: {memory}. Use formats like '128Mi', '1Gi'"
        
        return True, None
    
    @classmethod
    def validate_cpu(cls, cpu: str) -> Tuple[bool, Optional[str]]:
        """验证 CPU 格式"""
        if not isinstance(cpu, str):
            return False, "cpu must be a string like '100m' or '0.5'"
        
        pattern = re.compile(r'^(\d+m|\d+\.\d+)$')
        if not pattern.match(cpu):
            return False, f"invalid cpu format: {cpu}. Use formats like '100m' or '0.5'"
        
        return True, None


class DockerValidator:
    """Docker 配置验证器"""
    
    MAX_IMAGE_TAG_LENGTH = 128
    VALID_TAG_PATTERN = re.compile(r'^[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}$')
    
    @classmethod
    def validate_image_name(cls, image: str) -> Tuple[bool, Optional[str]]:
        """验证 Docker 镜像名称"""
        if not image:
            return False, "image name cannot be empty"
        
        if len(image) > 255:
            return False, "image name exceeds maximum length of 255"
        
        return True, None
    
    @classmethod
    def validate_tag(cls, tag: str) -> Tuple[bool, Optional[str]]:
        """验证镜像标签"""
        if not tag:
            return False, "tag cannot be empty"
        
        if len(tag) > cls.MAX_IMAGE_TAG_LENGTH:
            return False, f"tag exceeds maximum length of {cls.MAX_IMAGE_TAG_LENGTH}"
        
        if not cls.VALID_TAG_PATTERN.match(tag):
            return False, "tag must consist of alphanumeric characters, underscores, hyphens, and periods"
        
        return True, None


class CloudValidator:
    """云配置验证器"""
    
    @classmethod
    def validate_aws_region(cls, region: str) -> Tuple[bool, Optional[str]]:
        """验证 AWS 区域"""
        valid_regions = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'eu-west-1', 'eu-west-2', 'eu-central-1',
            'ap-northeast-1', 'ap-southeast-1', 'ap-southeast-2'
        ]
        
        if region not in valid_regions:
            return False, f"invalid AWS region: {region}"
        
        return True, None
    
    @classmethod
    def validate_gcp_project(cls, project_id: str) -> Tuple[bool, Optional[str]]:
        """验证 GCP 项目 ID"""
        if not project_id:
            return False, "project_id cannot be empty"
        
        if len(project_id) < 6 or len(project_id) > 30:
            return False, "project_id must be between 6 and 30 characters"
        
        if not re.match(r'^[a-z0-9-]+$', project_id):
            return False, "project_id must contain only lowercase letters, numbers, and hyphens"
        
        return True, None


class CICDValidator:
    """CI/CD 配置验证器"""
    
    @classmethod
    def validate_branch_name(cls, branch: str) -> Tuple[bool, Optional[str]]:
        """验证 Git 分支名称"""
        if not branch:
            return False, "branch name cannot be empty"
        
        reserved = ['HEAD', 'master', 'main'] if branch.lower() in ['master', 'main'] else []
        if branch in reserved and branch.lower() == branch:
            return False, f"branch name '{branch}' is reserved"
        
        return True, None
    
    @classmethod
    def validate_timeout(cls, timeout: int) -> Tuple[bool, Optional[str]]:
        """验证超时设置"""
        if not isinstance(timeout, int):
            return False, "timeout must be an integer"
        
        if timeout < 1:
            return False, "timeout must be at least 1 minute"
        
        if timeout > 360:
            return False, "timeout cannot exceed 360 minutes"
        
        return True, None


def validate_and_raise(validator_func, value, field_name: str):
    """验证并抛出异常"""
    valid, error = validator_func(value)
    if not valid:
        raise ValidationError(f"Invalid {field_name}: {error}")
    return value
