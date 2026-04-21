from fastmcp import FastMCP
from datetime import datetime

import signal
import asyncio


from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import ChatOpenAI

from setup import OPENROUTER_API_KEY
from sql_service import SQLService
from conn_db import Database
from documents import INFO_ABOUT_POLICY_DETAILS, SHOP_INFO
from schema import FormatForPolicy
from utils import normalize_usage, merge_usage, response_detail

mcp = FastMCP("chatdb-mcp-server")
db = Database()
sql_service = SQLService(db)


model = ChatOpenAI(
    model="openai/gpt-4o-mini",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    streaming=True,
    timeout=5.0,
)


@mcp.tool
async def get_time() -> dict:
    """
    Trả về thời gian hiện tại của hệ thống.
    Dùng khi cần mốc thời gian hiện tại để phục vụ việc suy luận,
    so sánh với các mốc thời gian khác hoặc trả lời câu hỏi liên quan đến ngày giờ.
    """
    now = datetime.now()
    return {"result": f"Thời gian hiện tại là {now.strftime("%Y-%m-%d %H:%M:%S")}"}


@mcp.tool
async def insert_order(
    full_name: str, email: str, phone: str, address: str, note: str, products: str
) -> dict:
    """
    Thêm mới một đơn hàng.

    Args:
        full_name: Họ tên khách hàng
        email: Email khách hàng
        phone: Số điện thoại
        address: Địa chỉ
        note: Ghi chú
        products: Sản phẩm (tên, số lượng, mã sản phẩm)

    Returns:
        Kết quả xử lý.
    """
    result = await sql_service.execute(
        "INSERT INTO OrderAis (FullName, Email, Phone, Address, Note, Products, CreatedDate, Status) "
        "VALUES (:full_name, :email, :phone, :address, :note, :products, GETDATE(), :status)",
        {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "address": address,
            "note": note,
            "products": products,
            "status": 1,
        },
    )
    if result["success"]:
        return {"result": "Xử lý thành công"}
    return {"result": "Xử lý thất bại"}


@mcp.tool
async def update_order(
    id: int,
    full_name: str,
    email: str,
    phone: str,
    address: str,
    note: str,
    products: str,
) -> dict:
    """
    Cập nhật thông tin một đơn hàng theo Id.

    Args:
        id: Một số nguyên Id của đơn hàng cần cập nhật
        full_name: Họ tên khách hàng
        email: Email khách hàng
        phone: Số điện thoại
        address: Địa chỉ
        note: Ghi chú
        products: Sản phẩm (tên, số lượng, mã sản phẩm)

    Returns:
        Kết quả xử lý.
    """
    result = await sql_service.execute(
        "UPDATE OrderAis SET FullName=:full_name, Email=:email, Phone=:phone, "
        "Address=:address, Note=:note, Products=:products WHERE Id=:id",
        {
            "id": id,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "address": address,
            "note": note,
            "products": products,
        },
    )
    if result["rowcount"] == 0:
        return {"result": "Không tìm thấy đơn hàng để cập nhật"}

    return {"result": "Cập nhật thành công"}


@mcp.tool
async def remove_order(phone: str, reject_reason: str, id: str) -> dict:
    """
    Xóa một đơn hàng theo số điện thoại và Id của đơn hàng.

    Args:

        phone: Số điện thoại của đơn hàng cần xóa
        reject_reason: lý do hủy đơn hàng (nếu có)
        id: Id của đơn hàng cần xóa

    Returns:
        Kết quả xử lý.
    """
    check = await sql_service.execute(
        "SELECT * FROM OrderAis WHERE Phone=:phone AND Id=:id",
        {"phone": phone, "id": id},
    )

    if not check:
        return {"result": "Không tìm thấy đơn hàng để xóa kiểm lại Id"}

    if check and check[0]["Status"] == 3:
        return {"result": "Đơn hàng đã bị xóa trước đó hãy kiểm tra lại Id"}

    result = await sql_service.execute(
        "UPDATE OrderAis SET Status=:status, RejectReason=:reject_reason WHERE Phone=:phone AND Id=:id",
        {"phone": phone, "status": 3, "reject_reason": reject_reason, "id": id},
    )
    if result["rowcount"] == 0:
        return {"result": "Không tìm thấy đơn hàng để xóa"}

    return {"result": "Xóa thành công"}


@mcp.tool
async def get_order(phone: str) -> dict:
    """
    Dùng để lấy toàn bộ đơn hàng theo số điện thoại hoặc lấy id để thao tác.

    Args:
        phone: số điện thoại dùng để lấy đơn hàng

    Returns:
        Các đơn hàng theo số điện thoại.
    """
    result = await sql_service.execute(
        "SELECT * FROM OrderAis WHERE Phone=:phone",
        {"phone": phone},
    )
    if result and len(result) > 0:
        return {"result": result}
    return {"result": []}


@mcp.tool
async def get_detail_from_html(url: str) -> dict:
    """
    Lấy thông tin sản phẩm từ file HTML.

    Args:
        url: đường dẫn file html

    Returns:
        Kết quả thông tin của sản phẩm.
    """
    try:
        if url.startswith("https://itcshop.iteccom.vn/"):
            url = url.replace("https://itcshop.iteccom.vn/", "")
        BASE_URL = "http://192.168.1.100:7295/"
        url = BASE_URL + url
        loader = WebBaseLoader(url)
        documents = loader.load()
        return {"result": documents[0].page_content}
    except Exception as e:
        print(e)
        return {"result": "Không thể lấy thông tin kĩ thuật của sản phẩm"}


@mcp.tool
async def get_info_shop(query: str) -> dict:
    """
    Lấy thông tin cửa hàng (số điện thoại, địa chỉ, email, giờ mở cửa, phương thức thanh toán...).

    Args:
        query: câu hỏi về thông tin cửa hàng

    Returns:
        Kết quả thông tin của cửa hàng.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                # Bạn là một trợ lý ảo hỗ trợ trả lời các câu hỏi liên quan đến cửa hàng ITC Shop dựa trên thông tin sau:     
                {shop_info}
                """,
            ),
            (
                "user",
                """
                Câu hỏi của khách hàng:
                {query}
             """,
            ),
        ]
    )

    chain = prompt | model
    response = await chain.ainvoke({"shop_info": SHOP_INFO, "query": query})
    return {
        "result": response.content,
        "usage_metadata": {"openai/gpt-4o-mini": response.usage_metadata},
    }


@mcp.tool
async def get_info_about_policy(query: str) -> dict:
    """
    Lấy thông tin về các chính sách của hệ thống/cửa hàng dựa trên câu hỏi của người dùng.

    Bao gồm các nội dung:
    - Mua hàng và thanh toán online
    - Mua hàng trả góp
    - Mua hàng trả góp bằng thẻ tín dụng
    - Chính sách giao hàng
    - Chính sách đổi trả
    - Tra thông tin bảo hành
    - Tra cứu hóa đơn điện tử
    - Thông tin hóa đơn mua hàng
    - Trung tâm bảo hành chính hãng
    - VAT Refund (hoàn thuế)

    Args:
        query (str): Câu hỏi hoặc từ khóa liên quan đến chính sách.

    Returns:
        dict: Thông tin chi tiết tương ứng với chính sách được yêu cầu.
    """
    INFO_ABOUT_POLICY = {
        1: "Mua hàng và thanh toán online",
        2: "Mua hàng trả góp",
        3: "Mua hàng trả góp bằng thẻ tín dụng",
        4: "Chính sách giao hàng",
        5: "Chính sách đổi trả",
        6: "Tra thông tin bảo hành",
        7: "Tra cứu hóa đơn điện tử",
        8: "Thông tin hóa đơn mua hàng",
        9: "Trung tâm bảo hành chính hãng",
        10: "VAT Refund (hoàn thuế)",
    }

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                # Bạn là một trợ lý ảo hỗ trợ trả lời các câu hỏi liên quan đến chính sách của ITC Shop dựa trên thông tin sau:     
                {info_about_policy}
                
                Trả về danh sách id của chính sách mà câu hỏi của khách hàng liên quan đến.
                
                Chỉ trả về duy nhất danh sách id.
                ["1", ...] 
                """,
            ),
            (
                "user",
                """
                Câu hỏi của khách hàng:
                {query}
             """,
            ),
        ]
    )

    chain = prompt | model.with_structured_output(FormatForPolicy, include_raw=True)
    response: FormatForPolicy = await chain.ainvoke(
        {"info_about_policy": INFO_ABOUT_POLICY, "query": query}
    )

    raw, parsed = response_detail(response)

    ids = parsed.ids

    usage_metadata = normalize_usage("openai/gpt-4o-mini", raw)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                # Bạn là một trợ lý ảo hỗ trợ trả lời các câu hỏi liên quan đến chính sách của ITC Shop dựa trên thông tin sau:     
                {info_about_policy_details}
                
                Trả về chi tiết của chính sách dựa trên id được yêu cầu.
                """,
            ),
            (
                "user",
                """
                Câu hỏi của khách hàng:
                {query}
             """,
            ),
        ]
    )

    chain = prompt | model
    response = await chain.ainvoke(
        {
            "info_about_policy_details": {
                INFO_ABOUT_POLICY.get(id): INFO_ABOUT_POLICY_DETAILS.get(id, "")
                for id in ids
            },
            "query": query,
        }
    )

    return {
        "result": response.content,
        "usage_metadata": merge_usage(
            usage_metadata, {"openai/gpt-4o-mini": response.usage_metadata}
        ),
    }


loop = asyncio.get_event_loop()


async def shutdown():
    print("Shutting down DB...")
    await db.close()


def handle_signal(sig, frame):
    print("Received shutdown signal...")
    loop.run_until_complete(shutdown())
    loop.stop()


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


mcp.run(transport="streamable-http", host="0.0.0.0", port=8123)
