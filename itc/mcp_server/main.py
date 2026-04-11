from fastmcp import FastMCP
from datetime import datetime
from sql_service import SQLService
from conn_db import Database
import signal
import asyncio
from langchain_community.document_loaders import WebBaseLoader

mcp = FastMCP("chatdb-mcp-server")
db = Database()
sql_service = SQLService(db)


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
    Dùng để lấy toàn bộ đơn hàng theo số điện thoại hoặc lấy id để dùng.

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
