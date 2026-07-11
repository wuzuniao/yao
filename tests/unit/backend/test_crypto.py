"""
AES-256-GCM 加密工具单元测试
--------------------------------------------------------------------------
覆盖加密、解密、空值处理、密钥校验、篡改检测
"""
import base64

import pytest

from app.utils.crypto import decrypt, encrypt


class TestEncryptDecrypt:
    """加密与解密"""

    @pytest.mark.unit
    def test_encrypt_returns_base64(self):
        result = encrypt("test data")
        # base64 编码的字符串
        base64.b64decode(result)

    @pytest.mark.unit
    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "敏感数据123!@#"
        encrypted = encrypt(plaintext)
        decrypted = decrypt(encrypted)
        assert decrypted == plaintext

    @pytest.mark.unit
    def test_encrypt_different_each_time(self):
        e1 = encrypt("same data")
        e2 = encrypt("same data")
        assert e1 != e2

    @pytest.mark.unit
    def test_encrypt_empty_returns_empty(self):
        assert encrypt("") == ""

    @pytest.mark.unit
    def test_decrypt_empty_returns_empty(self):
        assert decrypt("") == ""

    @pytest.mark.unit
    def test_decrypt_corrupted_data(self):
        with pytest.raises(ValueError, match="解密失败"):
            decrypt("not_valid_base64_encrypted_data!!!")

    @pytest.mark.unit
    def test_decrypt_tampered_ciphertext(self):
        encrypted = encrypt("secret")
        # 篡改密文（翻转最后一个字符）
        tampered = encrypted[:-1] + ("A" if encrypted[-1] != "A" else "B")
        with pytest.raises(ValueError, match="解密失败"):
            decrypt(tampered)

    @pytest.mark.unit
    def test_encrypt_unicode(self):
        plaintext = "中文测试🚀"
        encrypted = encrypt(plaintext)
        decrypted = decrypt(encrypted)
        assert decrypted == plaintext
