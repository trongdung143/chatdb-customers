from langchain_openai import ChatOpenAI
from fastmcp import FastMCP
from datetime import datetime
from setup import OPENROUTER_API_KEY
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.callbacks import UsageMetadataCallbackHandler
from utils import fix_model_name

mcp = FastMCP("chatdb-mcp-server")


@mcp.tool
async def get_time() -> dict[str, str]:
    """
    Trả về thời gian hiện tại của hệ thống.
    Dùng khi cần mốc thời gian hiện tại để phục vụ việc suy luận,
    so sánh với các mốc thời gian khác hoặc trả lời câu hỏi liên quan đến ngày giờ.
    """
    now = datetime.now()
    return {"result": f"Thời gian hiện tại là {now.strftime("%Y-%m-%d %H:%M:%S")}"}


@mcp.tool
async def get_business_rules_for_sgt(topic: str) -> dict:
    """
    Lấy thông tin quy tắc nghiệp vụ của hệ thống chương trình thẻ thành viên.

    Tool này dùng để tra cứu các quy định nghiệp vụ liên quan đến:
    - Điều kiện nâng hạng thẻ (SEA, SKY, SUN)
    - Điều kiện duy trì hạng thẻ
    - Quy tắc hạ hạng thẻ
    - Quy định về tài khoản tích lũy
    - Quy định về tour trọn gói
    - Các điều kiện xét hạng dựa trên giá trị giao dịch hoặc số lần sử dụng tour

    Sử dụng tool này khi câu hỏi liên quan đến quy định hoặc lý do nghiệp vụ, ví dụ:
    - Tại sao khách hàng chưa được nâng hạng thẻ?
    - Điều kiện để đạt hạng SKY hoặc SUN là gì?
    - Khi nào khách hàng bị hạ hạng thẻ?
    - Điều kiện duy trì hạng SKY là gì?
    - Khách hàng cần bao nhiêu giá trị giao dịch để lên hạng SUN?

    Args:
        topic: Chủ đề nghiệp vụ cần tra cứu (ví dụ: "điều kiện nâng hạng SKY", "hạ hạng SUN", "Tại sao đủ giá trị tích lũy những không được thăng hạng thẻ SUN").

    Returns:
        Nội dung quy tắc nghiệp vụ liên quan đến chủ đề để phục vụ phân tích và trả lời.
    """
    business_rules = """ TÀI KHOẢN TÍCH LŨY
    Là tài khoản ghi nhận tổng giá trị tích lũy dịch vụ và số lần sử dụng tour trọn gói
    của khách hàng. Tài khoản này được dùng làm cơ sở để xét nâng hạng, duy trì hạng
    hoặc hạ hạng thẻ thành viên.

    TOUR TRỌN GÓI
    Là chương trình du lịch do Saigontourist tổ chức, bao gồm thời gian chuyến đi,
    điểm đến, các điểm dừng chân, lưu trú, vận chuyển và các dịch vụ khác,
    đã được xác định mức giá trước.

    HẠNG THẺ SEA
    SEA CARD là hạng thẻ tiêu chuẩn dành cho khách hàng mở thẻ để trải nghiệm dịch vụ.

    Điều kiện đăng ký:
    - Khách hàng đăng ký thông tin mở thẻ thành viên.
    - Phát sinh tối thiểu 01 giao dịch dịch vụ bất kỳ.

    Thời hạn duy trì:
    - Không giới hạn thời gian duy trì hạng thẻ (trừ khi có thông báo thay đổi từ Saigontourist).

    HẠNG THẺ SKY
    Điều kiện xét hạng SKY:
    - Thẻ hiện tại phải là thẻ SEA.
    - Tổng giá trị tích lũy >= 50.000.000 VNĐ
    HOẶC
    Sử dụng tour trọn gói >= 4 lần trong vòng 12 tháng.

    Điều kiện duy trì hạng SKY:
    - Ít nhất 2 lần sử dụng tour trọn gói trong vòng 12 tháng
    HOẶC
    Tổng giá trị giao dịch >= 30.000.000 VNĐ trong vòng 12 tháng.

    Quy tắc hạ hạng:
    - Trong vòng 12 tháng kể từ ngày đạt hạng SKY, nếu khách hàng
    không đủ điều kiện nâng hạng SUN hoặc không đủ điều kiện duy trì hạng SKY,
    hệ thống sẽ xét hạ xuống hạng SEA.

    HẠNG THẺ SUN
    Điều kiện xét hạng SUN:
    - Thẻ hiện tại phải là thẻ SKY.
    - Tổng giá trị tích lũy >= 100.000.000 VNĐ
    HOẶC
    Sử dụng tour trọn gói >= 6 lần trong vòng 12 tháng.

    Điều kiện duy trì hạng SUN:
    - Ít nhất 4 lần sử dụng tour trọn gói trong vòng 12 tháng
    HOẶC
    Tổng giá trị giao dịch >= 60.000.000 VNĐ trong vòng 12 tháng.

    Quy tắc hạ hạng:
    - Trong vòng 12 tháng kể từ ngày đạt hạng SUN, nếu khách hàng
    không đủ điều kiện duy trì hạng SUN thì hệ thống sẽ xét hạ xuống hạng SKY.
    
    Quan trọng:
    - Khách hàng không được phép nhảy bậc khi thăng hạng.
    Ví dụ: dù giá trị tích lũy đạt ≥ 100.000.000 VNĐ, nếu đang ở hạng SEA thì không thể nâng trực tiếp lên SUN.
    - Việc thăng hạng phải tuân theo thứ tự bắt buộc SEA → SKY → SUN.
    - Sau mỗi lần thăng hạng, giá trị tích lũy sẽ được đặt lại về 0 VNĐ để bắt đầu chu kỳ tích lũy mới.
    """
    business_rule_model = ChatOpenAI(
        model="openai/gpt-4o-mini",
        temperature=0,
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        streaming=True,
        timeout=5.0,
    )
    business_rule_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
Bạn là trợ lý đọc tài liệu nghiệp vụ.

Nhiệm vụ của bạn là tìm và trích xuất phần quy tắc nghiệp vụ liên quan
đến chủ đề được yêu cầu từ tài liệu nghiệp vụ bên dưới.

Tài liệu nghiệp vụ:
{business_rules}

Quy tắc trả lời:
1. Chỉ trích xuất các phần liên quan trực tiếp đến chủ đề.
2. Không được tự tạo thêm thông tin ngoài tài liệu.
3. Nếu không tìm thấy thông tin liên quan, trả lời: Không tìm thấy quy tắc nghiệp vụ liên quan.
4. Giữ nguyên ý nghĩa của nội dung gốc, có thể tóm tắt nhưng không làm sai lệch nội dung.
""",
            ),
            (
                "human",
                """
Chủ đề cần tìm:
{topic}

Hãy tìm và trích xuất.
            """,
            ),
        ]
    )
    callback = UsageMetadataCallbackHandler()
    config = {
        "callbacks": [callback],
    }
    chain = business_rule_prompt | business_rule_model
    usage_metadata = {}
    try:
        response = await chain.ainvoke(
            input={"business_rules": business_rules, "topic": topic}, config=config
        )
        usage_metadata = fix_model_name(callback.usage_metadata)
    except Exception as e:
        print(repr(e))
        return "Lấy thông tin nghiệp vụ thất bại!"

    return {"result": response.content, "usage_metadata": usage_metadata}


mcp.run(transport="streamable-http", host="0.0.0.0", port=8123)
