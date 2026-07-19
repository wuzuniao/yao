from pydantic import BaseModel, field_validator

from ..core.security import Security


class AnnouncementCreate(BaseModel):
    """
    发布/更新公告请求 Schema
    - title 长度上限与数据库 VARCHAR(200) 对齐
    - content 为长文本
    """

    title: str
    content: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = Security.sanitize_string(v, max_length=200, field_name="公告标题")
        if not v:
            raise ValueError("公告标题不能为空")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = Security.sanitize_string(v, max_length=5000, field_name="公告内容")
        if not v:
            raise ValueError("公告内容不能为空")
        return v


class AnnouncementUpdate(AnnouncementCreate):
    """更新公告请求 Schema（复用 AnnouncementCreate 全部字段校验，announcement_id 由 URL 路径参数提供）"""
