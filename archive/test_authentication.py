"""
增强API认证和授权模块

提供JWT认证、API密钥管理、OAuth2支持等功能
"""

import os
import sys
import json
import time
import hmac
import hashlib
import secrets
import base64
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import urllib.parse


class AuthProvider(Enum):
    LOCAL = "local"
    API_KEY = "api_key"
    JWT = "jwt"
    OAUTH2 = "oauth2"


class TokenType(Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"


@dataclass
class User:
    user_id: str
    username: str
    email: str
    password_hash: str
    salt: str
    provider: AuthProvider
    roles: List[str] = field(default_factory=list)
    created_at: float = 0
    last_login: float = 0
    is_active: bool = True
    metadata: Dict = field(default_factory=dict)


@dataclass
class APIKey:
    key_id: str
    key_hash: str
    user_id: str
    name: str
    scopes: List[str] = field(default_factory=list)
    created_at: float = 0
    expires_at: float = 0
    last_used: float = 0
    is_active: bool = True
    rate_limit: int = 1000


@dataclass
class Token:
    token_type: TokenType
    token: str
    user_id: str
    scopes: List[str]
    created_at: float
    expires_at: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class RefreshToken:
    token_id: str
    user_id: str
    token_hash: str
    created_at: float
    expires_at: float
    is_revoked: bool = False


class PasswordManager:
    def __init__(self, salt_length: int = 32):
        self.salt_length = salt_length

    def hash_password(self, password: str) -> tuple:
        salt = secrets.token_hex(self.salt_length)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return password_hash.hex(), salt

    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        computed_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return hmac.compare_digest(computed_hash.hex(), password_hash)


class JWTTokenManager:
    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.algorithm = algorithm
        self.access_token_expire = access_token_expire_minutes * 60
        self.refresh_token_expire = refresh_token_expire_days * 86400

        self._issued_tokens: Dict[str, Token] = {}
        self._refresh_tokens: Dict[str, RefreshToken] = {}
        self._lock = threading.Lock()

    def _base64_encode(self, data: dict) -> str:
        json_str = json.dumps(data, separators=(',', ':'))
        return base64.urlsafe_b64encode(json_str.encode()).decode()

    def _base64_decode(self, data: str) -> dict:
        try:
            json_str = base64.urlsafe_b64decode(data.encode()).decode()
            return json.loads(json_str)
        except Exception:
            return {}

    def create_access_token(
        self,
        user_id: str,
        scopes: List[str],
        metadata: Dict = None
    ) -> str:
        now = time.time()
        jti = secrets.token_hex(16)

        header = {
            "alg": self.algorithm,
            "typ": "JWT",
            "jti": jti
        }

        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + self.access_token_expire,
            "jti": jti,
            "type": TokenType.ACCESS.value,
            "scopes": scopes,
            "metadata": metadata or {}
        }

        header_b64 = self._base64_encode(header)
        payload_b64 = self._base64_encode(payload)

        message = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        token = f"{message}.{signature}"

        with self._lock:
            self._issued_tokens[jti] = Token(
                token_type=TokenType.ACCESS,
                token=token,
                user_id=user_id,
                scopes=scopes,
                created_at=now,
                expires_at=now + self.access_token_expire,
                metadata=metadata or {}
            )

        return token

    def create_refresh_token(self, user_id: str) -> str:
        now = time.time()
        token_id = secrets.token_hex(16)
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        with self._lock:
            self._refresh_tokens[token_id] = RefreshToken(
                token_id=token_id,
                user_id=user_id,
                token_hash=token_hash,
                created_at=now,
                expires_at=now + self.refresh_token_expire
            )

        return f"{token_id}.{token}"

    def verify_token(self, token: str) -> Optional[Dict]:
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None

            header_b64, payload_b64, signature = parts

            message = f"{header_b64}.{payload_b64}"
            expected_signature = hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                return None

            header = self._base64_decode(header_b64)
            payload = self._base64_decode(payload_b64)

            now = time.time()
            if payload.get('exp', 0) < now:
                return None

            jti = payload.get('jti')
            if jti:
                with self._lock:
                    if jti in self._issued_tokens:
                        return payload

            return payload

        except Exception:
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        try:
            parts = refresh_token.split('.')
            if len(parts) != 2:
                return None

            token_id, token = parts
            token_hash = hashlib.sha256(token.encode()).hexdigest()

            with self._lock:
                if token_id not in self._refresh_tokens:
                    return None

                stored_token = self._refresh_tokens[token_id]

                if stored_token.is_revoked:
                    return None

                if stored_token.token_hash != token_hash:
                    return None

                if stored_token.expires_at < time.time():
                    return None

                return self.create_access_token(
                    stored_token.user_id,
                    stored_token.metadata.get('scopes', [])
                )

        except Exception:
            return None

    def revoke_token(self, jti: str):
        with self._lock:
            if jti in self._issued_tokens:
                del self._issued_tokens[jti]

    def revoke_refresh_token(self, token_id: str):
        with self._lock:
            if token_id in self._refresh_tokens:
                self._refresh_tokens[token_id].is_revoked = True


class APIKeyManager:
    def __init__(self, storage_path: str = "./data/keys"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._keys: Dict[str, APIKey] = {}
        self._load_keys()

    def _get_key_file(self) -> Path:
        return self.storage_path / "api_keys.json"

    def _load_keys(self):
        key_file = self._get_key_file()
        if key_file.exists():
            try:
                with open(key_file) as f:
                    data = json.load(f)

                for key_id, key_data in data.items():
                    self._keys[key_id] = APIKey(
                        key_id=key_data['key_id'],
                        key_hash=key_data['key_hash'],
                        user_id=key_data['user_id'],
                        name=key_data['name'],
                        scopes=key_data.get('scopes', []),
                        created_at=key_data.get('created_at', 0),
                        expires_at=key_data.get('expires_at', 0),
                        last_used=key_data.get('last_used', 0),
                        is_active=key_data.get('is_active', True),
                        rate_limit=key_data.get('rate_limit', 1000)
                    )
            except Exception:
                pass

    def _save_keys(self):
        key_file = self._get_key_file()
        data = {}

        for key_id, key in self._keys.items():
            data[key_id] = {
                'key_id': key.key_id,
                'key_hash': key.key_hash,
                'user_id': key.user_id,
                'name': key.name,
                'scopes': key.scopes,
                'created_at': key.created_at,
                'expires_at': key.expires_at,
                'last_used': key.last_used,
                'is_active': key.is_active,
                'rate_limit': key.rate_limit
            }

        with open(key_file, 'w') as f:
            json.dump(data, f, indent=2)

    def generate_key(
        self,
        user_id: str,
        name: str,
        scopes: List[str] = None,
        expires_in_days: int = 365,
        rate_limit: int = 1000
    ) -> str:
        key_id = secrets.token_hex(8)
        api_key = f"rga_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        now = time.time()

        api_key_obj = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            user_id=user_id,
            name=name,
            scopes=scopes or [],
            created_at=now,
            expires_at=now + expires_in_days * 86400,
            rate_limit=rate_limit
        )

        self._keys[key_id] = api_key_obj
        self._save_keys()

        return f"{key_id}.{api_key}"

    def verify_key(self, provided_key: str) -> Optional[APIKey]:
        try:
            parts = provided_key.split('.')
            if len(parts) != 2:
                return None

            key_id, api_key = parts

            if key_id not in self._keys:
                return None

            stored_key = self._keys[key_id]

            if not stored_key.is_active:
                return None

            if stored_key.expires_at > 0 and stored_key.expires_at < time.time():
                return None

            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            if not hmac.compare_digest(key_hash, stored_key.key_hash):
                return None

            stored_key.last_used = time.time()
            self._save_keys()

            return stored_key

        except Exception:
            return None

    def revoke_key(self, key_id: str) -> bool:
        if key_id in self._keys:
            self._keys[key_id].is_active = False
            self._save_keys()
            return True
        return False

    def list_user_keys(self, user_id: str) -> List[APIKey]:
        return [
            k for k in self._keys.values()
            if k.user_id == user_id and k.is_active
        ]


class PermissionChecker:
    def __init__(self):
        self._permission_map: Dict[str, set] = {
            'admin': {
                'read:all', 'write:all', 'delete:all',
                'admin:users', 'admin:system'
            },
            'manager': {
                'read:projects', 'write:projects', 'read:index',
                'write:index', 'read:users'
            },
            'developer': {
                'read:projects', 'write:projects', 'read:index',
                'write:index'
            },
            'viewer': {
                'read:projects', 'read:index'
            }
        }

    def has_permission(self, roles: List[str], required_permission: str) -> bool:
        for role in roles:
            perms = self._permission_map.get(role, set())
            if required_permission in perms:
                return True

            if required_permission.startswith('read:') and 'read:all' in perms:
                return True
            if required_permission.startswith('write:') and 'write:all' in perms:
                return True

        return False

    def check_scope(self, scopes: List[str], required_scope: str) -> bool:
        return required_scope in scopes or '*' in scopes


class RateLimitTracker:
    def __init__(self):
        self._requests: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int = 60
    ) -> Tuple[bool, int]:
        now = time.time()

        with self._lock:
            if identifier not in self._requests:
                self._requests[identifier] = []

            self._requests[identifier] = [
                t for t in self._requests[identifier]
                if now - t < window_seconds
            ]

            if len(self._requests[identifier]) >= limit:
                return False, limit - len(self._requests[identifier])

            self._requests[identifier].append(now)
            return True, limit - len(self._requests[identifier])

    def get_remaining(self, identifier: str, window_seconds: int = 60) -> int:
        now = time.time()

        with self._lock:
            if identifier not in self._requests:
                return 1000

            recent = [
                t for t in self._requests[identifier]
                if now - t < window_seconds
            ]

            return max(0, 1000 - len(recent))


class AuthenticationManager:
    def __init__(self):
        self.password_manager = PasswordManager()
        self.jwt_manager = JWTTokenManager()
        self.api_key_manager = APIKeyManager()
        self.permission_checker = PermissionChecker()
        self.rate_limiter = RateLimitTracker()

        self._users: Dict[str, User] = {}
        self._username_index: Dict[str, str] = {}
        self._email_index: Dict[str, str] = {}
        self._lock = threading.Lock()

        self._load_users()

    def _get_user_file(self) -> Path:
        return Path("./data/auth/users.json")

    def _load_users(self):
        user_file = self._get_user_file()
        if user_file.exists():
            try:
                with open(user_file) as f:
                    data = json.load(f)

                for user_id, user_data in data.items():
                    user_data['provider'] = AuthProvider(user_data['provider'])
                    self._users[user_id] = User(**user_data)
                    self._username_index[user_data['username']] = user_id
                    self._email_index[user_data['email']] = user_id
            except Exception:
                pass

    def _save_users(self):
        user_file = self._get_user_file()
        user_file.parent.mkdir(parents=True, exist_ok=True)

        data = {}
        for user_id, user in self._users.items():
            data[user_id] = {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'password_hash': user.password_hash,
                'salt': user.salt,
                'provider': user.provider.value,
                'roles': user.roles,
                'created_at': user.created_at,
                'last_login': user.last_login,
                'is_active': user.is_active,
                'metadata': user.metadata
            }

        with open(user_file, 'w') as f:
            json.dump(data, f, indent=2)

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        roles: List[str] = None
    ) -> Optional[User]:
        import uuid

        with self._lock:
            if username in self._username_index or email in self._email_index:
                return None

            password_hash, salt = self.password_manager.hash_password(password)

            user_id = str(uuid.uuid4())

            user = User(
                user_id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                salt=salt,
                provider=AuthProvider.LOCAL,
                roles=roles or ['viewer'],
                created_at=time.time(),
                is_active=True
            )

            self._users[user_id] = user
            self._username_index[username] = user_id
            self._email_index[email] = user_id

            self._save_users()

            return user

    def authenticate(
        self,
        username: str,
        password: str
    ) -> Optional[Dict]:
        with self._lock:
            user_id = self._username_index.get(username)
            if not user_id:
                return None

            user = self._users.get(user_id)
            if not user or not user.is_active:
                return None

            if user.provider != AuthProvider.LOCAL:
                return None

            if not self.password_manager.verify_password(
                password, user.password_hash, user.salt
            ):
                return None

            user.last_login = time.time()
            self._save_users()

        access_token = self.jwt_manager.create_access_token(
            user_id,
            user.roles
        )

        refresh_token = self.jwt_manager.create_refresh_token(user_id)

        return {
            'user_id': user_id,
            'username': user.username,
            'email': user.email,
            'roles': user.roles,
            'access_token': access_token,
            'refresh_token': refresh_token
        }

    def authenticate_with_api_key(self, api_key: str) -> Optional[Dict]:
        key_obj = self.api_key_manager.verify_key(api_key)
        if not key_obj:
            return None

        access_token = self.jwt_manager.create_access_token(
            key_obj.user_id,
            key_obj.scopes,
            {'rate_limit': key_obj.rate_limit}
        )

        return {
            'user_id': key_obj.user_id,
            'scopes': key_obj.scopes,
            'rate_limit': key_obj.rate_limit,
            'access_token': access_token,
            'key_name': key_obj.name
        }

    def verify_jwt(self, token: str) -> Optional[Dict]:
        payload = self.jwt_manager.verify_token(token)
        if not payload:
            return None

        return payload

    def create_api_key(
        self,
        user_id: str,
        name: str,
        scopes: List[str],
        expires_days: int = 365
    ) -> Optional[str]:
        return self.api_key_manager.generate_key(
            user_id, name, scopes, expires_days
        )

    def check_permission(self, user_id: str, permission: str) -> bool:
        with self._lock:
            user = self._users.get(user_id)
            if not user:
                return False

            return self.permission_checker.has_permission(user.roles, permission)

    def check_scope(self, token_payload: Dict, scope: str) -> bool:
        scopes = token_payload.get('scopes', [])
        return self.permission_checker.check_scope(scopes, scope)

    def check_rate_limit(self, identifier: str, limit: int) -> Tuple[bool, int]:
        return self.rate_limiter.check_rate_limit(identifier, limit)


def Tuple():
    pass


def demo_authentication():
    print("\n" + "="*60)
    print("演示: 增强API认证和授权")
    print("="*60)

    auth = AuthenticationManager()

    print("\n👤 步骤1: 注册用户")
    user = auth.register_user(
        username="developer1",
        email="dev@example.com",
        password="SecureP@ss123",
        roles=["developer"]
    )

    if user:
        print(f"   ✅ 用户注册成功")
        print(f"   - 用户名: {user.username}")
        print(f"   - 邮箱: {user.email}")
        print(f"   - 角色: {user.roles}")
    else:
        print("   ❌ 用户注册失败")
        return

    print("\n🔑 步骤2: 用户登录")
    auth_result = auth.authenticate("developer1", "SecureP@ss123")

    if auth_result:
        print(f"   ✅ 登录成功")
        print(f"   - 用户名: {auth_result['username']}")
        print(f"   - Token: {auth_result['access_token'][:50]}...")
    else:
        print("   ❌ 登录失败")
        return

    print("\n🔐 步骤3: 生成API密钥")
    api_key = auth.create_api_key(
        user.user_id,
        "Production API Key",
        scopes=["read:index", "write:index"],
        expires_days=90
    )

    if api_key:
        print(f"   ✅ API密钥生成成功")
        print(f"   - 密钥: {api_key[:30]}...")
    else:
        print("   ❌ API密钥生成失败")

    print("\n🔍 步骤4: 验证JWT Token")
    token_payload = auth.verify_jwt(auth_result['access_token'])

    if token_payload:
        print(f"   ✅ Token验证成功")
        print(f"   - 用户ID: {token_payload.get('sub')}")
        print(f"   - 权限: {token_payload.get('scopes')}")
        print(f"   - 过期时间: {token_payload.get('exp')}")
    else:
        print("   ❌ Token验证失败")

    print("\n🔑 步骤5: 使用API密钥认证")
    key_auth = auth.authenticate_with_api_key(api_key)

    if key_auth:
        print(f"   ✅ API密钥认证成功")
        print(f"   - 用户ID: {key_auth['user_id']}")
        print(f"   - 权限范围: {key_auth['scopes']}")
        print(f"   - 速率限制: {key_auth['rate_limit']}/分钟")
    else:
        print("   ❌ API密钥认证失败")

    print("\n✅ 步骤6: 权限检查")
    test_permissions = [
        "read:projects",
        "write:projects",
        "admin:system"
    ]

    for perm in test_permissions:
        has_perm = auth.check_permission(user.user_id, perm)
        print(f"   {'✅' if has_perm else '❌'} {perm}")

    print("\n⚡ 步骤7: 速率限制测试")
    identifier = f"api:{user.user_id}"

    for i in range(5):
        allowed, remaining = auth.check_rate_limit(identifier, limit=10)
        status = "✅" if allowed else "❌"
        print(f"   {status} 请求 {i+1}: 剩余配额={remaining}")

    print("\n" + "="*60)
    print("认证和授权演示完成！")
    print("="*60)


if __name__ == "__main__":
    demo_authentication()
