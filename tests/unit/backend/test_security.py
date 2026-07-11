"""
Security 类单元测试
--------------------------------------------------------------------------
覆盖密码哈希、密码校验、密码复杂度、用户名校验、验证码校验、邮箱校验、
SMTP 校验、输入净化、正整数校验、JWT 生成与校验、输出过滤
"""
import time

import pytest

from app.core.security import Security


class TestPasswordHashing:
    """密码哈希与校验"""

    @pytest.mark.unit
    def test_hash_password_returns_bcrypt_hash(self):
        hashed = Security.hash_password("Test1234!")
        assert hashed != "Test1234!"
        assert hashed.startswith("$2")

    @pytest.mark.unit
    def test_hash_password_different_each_time(self):
        h1 = Security.hash_password("Test1234!")
        h2 = Security.hash_password("Test1234!")
        assert h1 != h2

    @pytest.mark.unit
    def test_verify_password_correct(self):
        hashed = Security.hash_password("Test1234!")
        assert Security.verify_password("Test1234!", hashed) is True

    @pytest.mark.unit
    def test_verify_password_wrong(self):
        hashed = Security.hash_password("Test1234!")
        assert Security.verify_password("WrongPass!", hashed) is False


class TestValidatePassword:
    """密码复杂度校验"""

    @pytest.mark.unit
    def test_valid_password(self):
        assert Security.validate_password("Abc1234!") == "Abc1234!"

    @pytest.mark.unit
    def test_too_short(self):
        with pytest.raises(ValueError, match="密码长度需为 8-20 位"):
            Security.validate_password("Ab1!")

    @pytest.mark.unit
    def test_too_long(self):
        with pytest.raises(ValueError, match="密码长度需为 8-20 位"):
            Security.validate_password("Abc12345!Abc12345!Abc")

    @pytest.mark.unit
    def test_only_two_categories(self):
        with pytest.raises(ValueError, match="至少三种"):
            Security.validate_password("abcdef12")

    @pytest.mark.unit
    def test_not_string(self):
        with pytest.raises(ValueError, match="密码必须为字符串"):
            Security.validate_password(12345678)

    @pytest.mark.unit
    def test_strips_control_chars(self):
        # 控制字符被移除后仍需满足复杂度
        result = Security.validate_password("Abc1234!\x00")
        assert "\x00" not in result


class TestValidateUsername:
    """用户名校验"""

    @pytest.mark.unit
    def test_valid_username(self):
        assert Security.validate_username("测试用户") == "测试用户"

    @pytest.mark.unit
    def test_valid_english_username(self):
        assert Security.validate_username("testuser") == "testuser"

    @pytest.mark.unit
    def test_too_short(self):
        with pytest.raises(ValueError, match="用户名长度需为 2-15"):
            Security.validate_username("a")

    @pytest.mark.unit
    def test_invalid_chars(self):
        with pytest.raises(ValueError, match="仅允许中文、英文及数字"):
            Security.validate_username("user@name")

    @pytest.mark.unit
    def test_strips_whitespace(self):
        assert Security.validate_username("  testuser  ") == "testuser"

    @pytest.mark.unit
    def test_not_string(self):
        with pytest.raises(ValueError, match="用户名必须为字符串"):
            Security.validate_username(123)

    @pytest.mark.unit
    def test_too_long(self):
        with pytest.raises(ValueError, match="用户名长度不能超过"):
            Security.validate_username("a" * 16)


class TestValidateCode:
    """验证码校验"""

    @pytest.mark.unit
    def test_valid_code(self):
        assert Security.validate_code("123456") == "123456"

    @pytest.mark.unit
    def test_not_six_digits(self):
        with pytest.raises(ValueError):
            Security.validate_code("12345")

    @pytest.mark.unit
    def test_contains_letters(self):
        with pytest.raises(ValueError):
            Security.validate_code("12ab56")

    @pytest.mark.unit
    def test_strips_whitespace(self):
        assert Security.validate_code("  123456  ") == "123456"

    @pytest.mark.unit
    def test_not_string(self):
        with pytest.raises(ValueError, match="验证码必须为字符串"):
            Security.validate_code(123456)


class TestValidateEmail:
    """邮箱校验"""

    @pytest.mark.unit
    def test_valid_email(self):
        assert Security.validate_email("test@example.com") == "test@example.com"

    @pytest.mark.unit
    def test_no_at_sign(self):
        with pytest.raises(ValueError, match="邮箱地址格式不正确"):
            Security.validate_email("invalidemail")

    @pytest.mark.unit
    def test_not_string(self):
        with pytest.raises(ValueError, match="邮箱必须为字符串"):
            Security.validate_email(123)


class TestValidateSmtp:
    """SMTP 校验"""

    @pytest.mark.unit
    def test_valid_host(self):
        assert Security.validate_smtp_host("smtp.example.com") == "smtp.example.com"

    @pytest.mark.unit
    def test_empty_host(self):
        with pytest.raises(ValueError, match="不能为空"):
            Security.validate_smtp_host("   ")

    @pytest.mark.unit
    def test_valid_port(self):
        assert Security.validate_smtp_port(465) == 465

    @pytest.mark.unit
    def test_port_out_of_range(self):
        with pytest.raises(ValueError, match="端口范围"):
            Security.validate_smtp_port(70000)

    @pytest.mark.unit
    def test_port_zero(self):
        with pytest.raises(ValueError, match="端口范围"):
            Security.validate_smtp_port(0)

    @pytest.mark.unit
    def test_port_not_int(self):
        with pytest.raises(ValueError, match="端口必须为整数"):
            Security.validate_smtp_port("465")


class TestSanitizeString:
    """输入净化"""

    @pytest.mark.unit
    def test_strips_whitespace(self):
        assert Security.sanitize_string("  hello  ") == "hello"

    @pytest.mark.unit
    def test_removes_control_chars(self):
        assert Security.sanitize_string("hello\x00world") == "helloworld"

    @pytest.mark.unit
    def test_too_long(self):
        with pytest.raises(ValueError, match="长度不能超过"):
            Security.sanitize_string("a" * 11, max_length=10)

    @pytest.mark.unit
    def test_not_string(self):
        with pytest.raises(ValueError, match="必须为字符串"):
            Security.sanitize_string(123)

    @pytest.mark.unit
    def test_custom_field_name(self):
        with pytest.raises(ValueError, match="自定义字段"):
            Security.sanitize_string("a" * 11, max_length=10, field_name="自定义字段")


class TestValidatePositiveInt:
    """正整数校验"""

    @pytest.mark.unit
    def test_valid_int(self):
        assert Security.validate_positive_int(1) == 1

    @pytest.mark.unit
    def test_zero(self):
        with pytest.raises(ValueError, match="必须为正整数"):
            Security.validate_positive_int(0)

    @pytest.mark.unit
    def test_negative(self):
        with pytest.raises(ValueError, match="必须为正整数"):
            Security.validate_positive_int(-1)

    @pytest.mark.unit
    def test_not_int(self):
        with pytest.raises(ValueError, match="必须为正整数"):
            Security.validate_positive_int("1")


class TestJWT:
    """JWT 生成与校验"""

    @pytest.mark.unit
    def test_generate_and_verify_token(self):
        token = Security.generate_token(1)
        payload = Security.verify_token(token)
        assert payload["sub"] == "1"
        assert "iat" in payload
        assert "exp" in payload

    @pytest.mark.unit
    def test_generate_token_invalid_user_id(self):
        with pytest.raises(ValueError, match="用户ID必须为正整数"):
            Security.generate_token(0)

    @pytest.mark.unit
    def test_generate_token_negative_user_id(self):
        with pytest.raises(ValueError, match="用户ID必须为正整数"):
            Security.generate_token(-1)

    @pytest.mark.unit
    def test_verify_token_empty(self):
        with pytest.raises(ValueError, match="令牌不能为空"):
            Security.verify_token("")

    @pytest.mark.unit
    def test_verify_token_invalid(self):
        with pytest.raises(ValueError, match="登录凭证无效"):
            Security.verify_token("invalid.token.here")

    @pytest.mark.unit
    def test_verify_token_not_string(self):
        with pytest.raises(ValueError, match="令牌不能为空"):
            Security.verify_token(None)


class TestFilterOutput:
    """输出过滤"""

    @pytest.mark.unit
    def test_removes_sensitive_fields(self):
        data = {
            "id": 1,
            "username": "test",
            "password_hash": "$2b$12$xxx",
            "session_key": "abc",
            "token": "xyz",
        }
        filtered = Security.filter_output(data)
        assert "password_hash" not in filtered
        assert "session_key" not in filtered
        assert "token" not in filtered
        assert filtered["id"] == 1
        assert filtered["username"] == "test"

    @pytest.mark.unit
    def test_filter_output_non_dict(self):
        assert Security.filter_output("not a dict") == "not a dict"

    @pytest.mark.unit
    def test_filter_output_no_sensitive_fields(self):
        data = {"id": 1, "username": "test"}
        filtered = Security.filter_output(data)
        assert filtered == data
