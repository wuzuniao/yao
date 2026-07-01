"""
AES-256-GCM 对称加密工具
--------------------------------------------------------------------------
用于加密敏感数据（如邮件客户端专用密码），加密后存入数据库，使用时解密。
- 算法：AES-256-GCM（提供机密性与完整性保护）
- 密钥：从环境变量 ENCRYPTION_SECRET_KEY 读取（base64 编码的 32 字节密钥）
- 存储格式：base64(nonce(12B) + ciphertext + tag(16B))
"""
from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..core.config import settings


def _get_key() -> bytes:
    """从配置获取 AES-256 密钥（32 字节）"""
    raw = settings.ENCRYPTION_SECRET_KEY
    if not raw:
        raise RuntimeError("未配置 ENCRYPTION_SECRET_KEY，无法执行加密操作")
    key = base64.b64decode(raw)
    if len(key) != 32:
        raise RuntimeError("ENCRYPTION_SECRET_KEY 必须是 base64 编码的 32 字节密钥")
    return key


def encrypt(plaintext: str) -> str:
    """
    加密字符串，返回 base64 编码的密文（含 nonce 和 tag）
    - 每次加密生成随机 nonce，相同明文每次加密结果不同
    """
    if not plaintext:
        return ""
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # GCM 推荐的 nonce 长度
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt(token: str) -> str:
    """
    解密 encrypt() 生成的密文，返回原始字符串
    - 空字符串原样返回
    - 解密失败（密钥错误/数据损坏）抛出 ValueError
    """
    if not token:
        return ""
    key = _get_key()
    aesgcm = AESGCM(key)
    try:
        raw = base64.b64decode(token)
        nonce = raw[:12]
        ciphertext = raw[12:]
        return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
    except Exception as e:
        raise ValueError(f"解密失败：{e}") from e
