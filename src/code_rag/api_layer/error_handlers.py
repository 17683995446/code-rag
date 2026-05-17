"""
API Error Handlers and Validators
Enhanced error handling and request validation for production use
"""

from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import re


class APIError(Exception):
    """API错误基类"""

    def __init__(
        self,
        code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.error_code = error_code or f"ERR_{code}"
        super().__init__(self.message)


class ValidationError(APIError):
    """验证错误"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=400,
            message=message,
            details=details,
            error_code="VALIDATION_ERROR"
        )


class NotFoundError(APIError):
    """资源未找到错误"""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            code=404,
            message=f"{resource} not found: {identifier}",
            details={"resource": resource, "identifier": identifier},
            error_code="NOT_FOUND"
        )


class UnauthorizedError(APIError):
    """未授权错误"""

    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(
            code=401,
            message=message,
            error_code="UNAUTHORIZED"
        )


class RateLimitError(APIError):
    """速率限制错误"""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            code=429,
            message="Rate limit exceeded",
            details={"retry_after": retry_after},
            error_code="RATE_LIMIT_EXCEEDED"
        )


class InternalServerError(APIError):
    """内部服务器错误"""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            code=500,
            message=message,
            error_code="INTERNAL_ERROR"
        )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """
    API错误处理器
    """
    return JSONResponse(
        status_code=exc.code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "path": str(request.url),
                "method": request.method
            }
        }
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用错误处理器
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"type": type(exc).__name__},
                "path": str(request.url)
            }
        }
    )


class SearchRequestValidator(BaseModel):
    """搜索请求验证器"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query text"
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Number of results to return"
    )

    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata filters"
    )

    use_cache: bool = Field(
        default=True,
        description="Whether to use cached results"
    )

    @validator('query')
    def validate_query(cls, v: str) -> str:
        """验证查询文本"""
        v = v.strip()
        if not v:
            raise ValueError('Query cannot be empty or whitespace only')

        if len(v) < 2 and not any(c.isalnum() for c in v):
            raise ValueError('Query must contain at least one alphanumeric character')

        return v

    @validator('filters')
    def validate_filters(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """验证过滤器"""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Filters must be a dictionary')
        return v


class DocumentAddRequestValidator(BaseModel):
    """文档添加请求验证器"""

    content: str = Field(
        ...,
        min_length=1,
        max_length=1000000,
        description="Document content"
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Document metadata"
    )

    chunk_size: Optional[int] = Field(
        default=None,
        ge=100,
        le=10000,
        description="Chunk size for splitting"
    )

    chunk_overlap: Optional[int] = Field(
        default=None,
        ge=0,
        le=1000,
        description="Overlap between chunks"
    )

    @validator('content')
    def validate_content(cls, v: str) -> str:
        """验证文档内容"""
        v = v.strip()
        if not v:
            raise ValueError('Content cannot be empty')
        return v

    @validator('metadata')
    def validate_metadata(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """验证元数据"""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Metadata must be a dictionary')

            for key, value in v.items():
                if not isinstance(key, str):
                    raise ValueError(f'Metadata keys must be strings, got {type(key)}')

                if isinstance(value, (dict, list)):
                    import json
                    try:
                        json.dumps(value)
                    except:
                        raise ValueError(f'Metadata value for key "{key}" is not JSON serializable')

        return v


class QueryRequestValidator(BaseModel):
    """问答请求验证器"""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Question text"
    )

    context_limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of context documents to use"
    )

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM temperature"
    )

    max_tokens: int = Field(
        default=1000,
        ge=100,
        le=4000,
        description="Maximum tokens to generate"
    )

    @validator('question')
    def validate_question(cls, v: str) -> str:
        """验证问题文本"""
        v = v.strip()
        if not v:
            raise ValueError('Question cannot be empty')

        question_marks = v.count('?') + v.count('？')
        if question_marks > 5:
            raise ValueError('Question contains too many question marks')

        return v


def sanitize_input(text: str) -> str:
    """
    清理输入文本
    防止注入攻击
    """
    if not text:
        return ""

    text = text.strip()

    dangerous_patterns = [
        (r'<script[^>]*>.*?</script>', ''),
        (r'javascript:', ''),
        (r'on\w+\s*=', ''),
    ]

    for pattern, replacement in dangerous_patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE | re.DOTALL)

    return text


def validate_file_path(path: str) -> bool:
    """
    验证文件路径
    防止路径遍历攻击
    """
    if not path:
        return False

    path = path.strip()

    dangerous_patterns = ['../', '..\\', '~/', '/etc/', 'C:\\']
    for pattern in dangerous_patterns:
        if pattern in path:
            return False

    return True


class ErrorResponse(BaseModel):
    """错误响应模型"""

    error: Dict[str, Any] = Field(
        ...,
        description="Error details"
    )

    request_id: Optional[str] = Field(
        default=None,
        description="Request ID for tracking"
    )

    timestamp: str = Field(
        ...,
        description="Error timestamp"
    )
