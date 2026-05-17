"""
Code RAG v17.0 - 代码生成模块
基于模板和上下文的智能代码生成
"""

import re
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CodeTemplate:
    """代码模板"""
    name: str
    description: str
    language: str
    template: str
    variables: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


@dataclass
class GeneratedCode:
    """生成的代码"""
    code: str
    language: str
    template_name: str
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationRequest:
    """生成请求"""
    intent: str
    language: Optional[str] = None
    framework: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


class CodeGenerator:
    """
    代码生成器
    基于模板的智能代码生成
    """

    def __init__(self):
        self.templates = self._initialize_templates()
        self.similarity_threshold = 0.6

    def _initialize_templates(self) -> Dict[str, List[CodeTemplate]]:
        """初始化代码模板库"""
        templates = {
            'api': [
                CodeTemplate(
                    name='REST API Endpoint',
                    description='RESTful API接口',
                    language='python',
                    template='''@app.{method}("/{path}")
async def {function_name}({parameters}):
    """
    {description}
    
    Args:
{args_doc}
    
    Returns:
        JSON response
    """
    try:
        # TODO: Implement logic
        result = {{}}
        return {{"success": True, "data": result}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}''',
                    variables=['method', 'path', 'function_name', 'parameters', 'description', 'args_doc']
                ),
                CodeTemplate(
                    name='Flask Route',
                    description='Flask路由',
                    language='python',
                    template='''@app.route('/{path}', methods=['{methods}'])
def {function_name}():
    """
    {description}
    """
    try:
        # TODO: Implement logic
        return jsonify({{"success": True}})
    except Exception as e:
        return jsonify({{"success": False, "error": str(e)}}), 500''',
                    variables=['path', 'methods', 'function_name', 'description']
                ),
                CodeTemplate(
                    name='FastAPI Endpoint',
                    description='FastAPI端点',
                    language='python',
                    template='''from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class {request_model}(BaseModel):
    {model_fields}

@router.{method}("/{path}")
async def {function_name}({parameters}) -> dict:
    """
    {description}
    """
    try:
        # TODO: Implement logic
        return {{"success": True, "data": {{}}}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))''',
                    variables=['request_model', 'model_fields', 'method', 'path', 'function_name', 'parameters', 'description']
                )
            ],
            'model': [
                CodeTemplate(
                    name='Data Model',
                    description='数据模型',
                    language='python',
                    template='''class {class_name}:
    """
    {description}
    """
    
    def __init__(self{constructor_params}):
{assignments}
    
    def to_dict(self) -> dict:
        return {{k: v for k, v in self.__dict__.items() if not k.startswith('_')}}
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls({from_dict_params})''',
                    variables=['class_name', 'description', 'constructor_params', 'assignments', 'from_dict_params']
                ),
                CodeTemplate(
                    name='Pydantic Model',
                    description='Pydantic数据模型',
                    language='python',
                    template='''from pydantic import BaseModel, Field
from typing import Optional

class {model_name}(BaseModel):
    """
    {description}
    """
{fields}
    
    class Config:
        json_schema_extra = {{
            "example": {{
                "id": 1,
                "name": "example"
            }}
        }}''',
                    variables=['model_name', 'description', 'fields']
                ),
                CodeTemplate(
                    name='SQLAlchemy Model',
                    description='SQLAlchemy ORM模型',
                    language='python',
                    template='''from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class {model_name}(Base):
    """
    {description}
    """
    __tablename__ = '{table_name}'
    
{id_field}
{fields}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)''',
                    variables=['model_name', 'description', 'table_name', 'id_field', 'fields']
                )
            ],
            'auth': [
                CodeTemplate(
                    name='User Authentication',
                    description='用户认证',
                    language='python',
                    template='''import hashlib
import secrets
from datetime import datetime, timedelta

class {class_name}:
    """
    {description}
    """
    
    def __init__(self):
        self.salt_length = 32
        self.token_expiry = timedelta(hours=24)
    
    def hash_password(self, password: str) -> str:
        salt = secrets.token_hex(self.salt_length)
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return f"$pbkdf2$salt=${salt}$hash=${pwd_hash.hex()}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        # TODO: Implement verification
        return True
    
    def generate_token(self, user_id: str) -> str:
        token = secrets.token_urlsafe(32)
        # TODO: Store token with expiry
        return token
    
    def authenticate(self, username: str, password: str) -> dict:
        # TODO: Check credentials
        return {{"success": False, "message": "Invalid credentials"}}''',
                    variables=['class_name', 'description']
                ),
                CodeTemplate(
                    name='JWT Token Handler',
                    description='JWT令牌处理',
                    language='python',
                    template='''import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
TOKEN_EXPIRY = timedelta(hours=24)

def create_token(user_id: str, extra_claims: dict = None) -> str:
    """
    创建JWT令牌
    """
    payload = {{
        "user_id": user_id,
        "exp": datetime.utcnow() + TOKEN_EXPIRY,
        "iat": datetime.utcnow()
    }}
    if extra_claims:
        payload.update(extra_claims)
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """
    验证JWT令牌
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {{"valid": True, "payload": payload}}
    except jwt.ExpiredSignatureError:
        return {{"valid": False, "error": "Token expired"}}
    except jwt.InvalidTokenError:
        return {{"valid": False, "error": "Invalid token"}}''',
                    variables=[]
                )
            ],
            'database': [
                CodeTemplate(
                    name='Database Connection',
                    description='数据库连接',
                    language='python',
                    template='''import sqlite3
from contextlib import contextmanager
from typing import Optional

class {class_name}:
    """
    {description}
    """
    
    def __init__(self, db_path: str = "{db_path}"):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def execute(self, query: str, params: tuple = ()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_one(self, query: str, params: tuple = ()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()''',
                    variables=['class_name', 'description', 'db_path']
                ),
                CodeTemplate(
                    name='CRUD Operations',
                    description='CRUD操作',
                    language='python',
                    template='''class {class_name}Repository:
    """
    {description}
    """
    
    def __init__(self, db):
        self.db = db
        self.table_name = "{table_name}"
    
    def create(self, data: dict) -> int:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO {{self.table_name}} ({{columns}}) VALUES ({{placeholders}})"
        cursor = self.db.execute(query, tuple(data.values()))
        return cursor.lastrowid
    
    def read(self, id: int) -> dict:
        query = f"SELECT * FROM {{self.table_name}} WHERE id = ?"
        result = self.db.execute_one(query, (id,))
        if result:
            columns = [desc[0] for desc in self.db.execute("PRAGMA table_info(" + self.table_name + ")")]
            return dict(zip(columns, result))
        return None
    
    def update(self, id: int, data: dict) -> bool:
        set_clause = ", ".join([f"{{k}} = ?" for k in data.keys()])
        query = f"UPDATE {{self.table_name}} SET {{set_clause}} WHERE id = ?"
        params = tuple(data.values()) + (id,)
        self.db.execute(query, params)
        return True
    
    def delete(self, id: int) -> bool:
        query = f"DELETE FROM {{self.table_name}} WHERE id = ?"
        self.db.execute(query, (id,))
        return True
    
    def list_all(self, limit: int = 100, offset: int = 0) -> list:
        query = f"SELECT * FROM {{self.table_name}} LIMIT ? OFFSET ?"
        return self.db.execute(query, (limit, offset))''',
                    variables=['class_name', 'description', 'table_name']
                )
            ],
            'error': [
                CodeTemplate(
                    name='Error Handler',
                    description='错误处理',
                    language='python',
                    template='''import logging
from typing import Optional

logger = logging.getLogger(__name__)

class {class_name}Error(Exception):
    """自定义错误类"""
    
    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        return {{
            "error": {{
                "code": self.code,
                "message": self.message
            }}
        }}

class ErrorHandler:
    """
    统一错误处理
    """
    
    def __init__(self):
        self.error_log = []
    
    def handle(self, error: Exception, context: dict = None) -> dict:
        error_info = {{
            "type": type(error).__name__,
            "message": str(error),
            "context": context or {{}}
        }}
        
        if isinstance(error, {class_name}Error):
            return error.to_dict()
        
        logger.error(f"Error occurred: {{error_info}}")
        self.error_log.append(error_info)
        
        return {{
            "success": False,
            "error": {{
                "code": "INTERNAL_ERROR",
                "message": "An error occurred"
            }}
        }}''',
                    variables=['class_name']
                )
            ]
        }
        
        return templates

    def generate(self, request: GenerationRequest) -> GeneratedCode:
        """
        生成代码
        
        Args:
            request: 生成请求
            
        Returns:
            生成的代码
        """
        category = self._identify_category(request.intent)
        
        templates = self.templates.get(category, [])
        if not templates:
            return GeneratedCode(
                code=f"# No template found for: {request.intent}",
                language=request.language or "python",
                template_name="",
                variables={},
                metadata={'error': 'No matching template'}
            )
        
        template = templates[0]
        
        code = self._fill_template(template, request)
        
        return GeneratedCode(
            code=code,
            language=template.language,
            template_name=template.name,
            variables={},
            metadata={
                'category': category,
                'description': template.description
            }
        )

    def _identify_category(self, intent: str) -> str:
        """识别意图类别"""
        intent_lower = intent.lower()
        
        categories = {
            'api': ['api', '接口', 'endpoint', 'route', 'rest'],
            'model': ['model', '模型', 'data', 'schema', 'class'],
            'auth': ['auth', '认证', 'login', 'register', 'token', 'jwt'],
            'database': ['database', 'db', 'sql', 'query', 'crud'],
            'error': ['error', '异常', 'exception', 'handler']
        }
        
        for category, keywords in categories.items():
            if any(kw in intent_lower for kw in keywords):
                return category
        
        return 'api'

    def _fill_template(
        self,
        template: CodeTemplate,
        request: GenerationRequest
    ) -> str:
        """填充模板"""
        code = template.template
        
        replacements = {
            '{class_name}': request.context.get('class_name', 'MyClass'),
            '{function_name}': request.context.get('function_name', 'my_function'),
            '{description}': request.context.get('description', 'Description here'),
            '{path}': request.context.get('path', 'resource'),
            '{method}': request.context.get('method', 'post'),
            '{methods}': request.context.get('methods', 'POST'),
            '{parameters}': request.context.get('parameters', 'data: dict'),
            '{model_name}': request.context.get('model_name', 'MyModel'),
            '{table_name}': request.context.get('table_name', 'my_table'),
            '{db_path}': request.context.get('db_path', 'database.db'),
            '{model_fields}': request.context.get('model_fields', 'name: str'),
            '{fields}': request.context.get('fields', 'id: int = Field(default=1)'),
            '{id_field}': request.context.get('id_field', 'id = Column(Integer, primary_key=True)'),
            '{args_doc}': request.context.get('args_doc', '    data: dict'),
            '{constructor_params}': request.context.get('constructor_params', ''),
            '{assignments}': request.context.get('assignments', '    pass'),
            '{from_dict_params}': request.context.get('from_dict_params', '')
        }
        
        for placeholder, value in replacements.items():
            code = code.replace(placeholder, value)
        
        return code

    def list_templates(self, category: Optional[str] = None) -> List[Dict]:
        """列出模板"""
        if category:
            templates = self.templates.get(category, [])
            return [{'name': t.name, 'description': t.description} for t in templates]
        
        result = []
        for cat, templates in self.templates.items():
            result.append({
                'category': cat,
                'templates': [{'name': t.name, 'description': t.description} for t in templates]
            })
        
        return result


def create_code_generator() -> CodeGenerator:
    """创建代码生成器"""
    return CodeGenerator()
