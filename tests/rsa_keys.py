"""
测试专用 RSA 密钥与令牌签发工具
--------------------------------------------------------------------------
yao 后端本地验签 auth 服务签发的 RS256 access_token；测试中用本模块生成
一次性密钥对并注入 auth_client 内存缓存（不依赖 auth 服务运行），
直接以测试私钥签发结构与 auth 服务一致的令牌。

注意：TEST_ISSUER 必须与根 conftest.py 设置的 AUTH_ISSUER 环境变量一致。
"""
import hashlib
import time
import uuid

import jwt as pyjwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# 测试签发方标识（根 conftest.py 设置 AUTH_ISSUER 环境变量须与此一致）
TEST_ISSUER = "http://test-auth"

# 一次性 RSA-2048 密钥对（进程内单例，导入时生成）
_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PRIVATE_PEM = _private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)
PUBLIC_PEM = _private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)
# kid 计算方式与 auth 服务一致：公钥 PEM 的 SHA-256 前 16 位 hex
KID = hashlib.sha256(PUBLIC_PEM).hexdigest()[:16]

# 公钥对象（注入 auth_client._jwks_keys 内存缓存用）
PUBLIC_KEY_OBJ = pyjwt.algorithms.RSAAlgorithm.from_jwk(
    pyjwt.algorithms.RSAAlgorithm.to_jwk(_private_key.public_key())
)


def sign_token(
    user_id: int,
    role: int = 0,
    expires_in: int = 3600,
    issued_at: int | None = None,
    issuer: str = TEST_ISSUER,
) -> str:
    """
    用测试私钥签发 access_token（claims 结构与 auth 服务签发的一致）
    :param user_id: 用户ID（写入 sub）
    :param role: 角色（0-普通用户，7-管理员）
    :param expires_in: 有效期（秒）
    :param issued_at: 签发时间戳（默认当前时间；测试撤销比对时可指定历史时间）
    :param issuer: 签发方标识（默认 TEST_ISSUER）
    """
    iat = int(time.time()) if issued_at is None else issued_at
    payload = {
        "iss": issuer,
        "sub": str(user_id),
        "role": role,
        "azp": "yao",
        "jti": uuid.uuid4().hex,
        "iat": iat,
        "exp": iat + expires_in,
    }
    return pyjwt.encode(payload, PRIVATE_PEM, algorithm="RS256", headers={"kid": KID})
