from langchain_core.tools.base import Field
from pydantic import BaseModel


class DetailUrls(BaseModel):
    urls: dict[str, str] = Field(
        ...,
        description="""Dict ánh xạ giữa định danh và URL.
              - key (str): định danh duy nhất do caller (AI) tự tạo
                           để theo dõi và đối chiếu kết quả trả về
              - value (str): URL tới trang HTML cần lấy dữ liệu""",
    )
