from pydantic import BaseModel, Field


class FormatForPolicy(BaseModel):
    ids: list[int] = Field(
        default_factory=list,
        description="Danh sách id của chính sách mà câu hỏi của khách hàng liên quan đến",
    )
