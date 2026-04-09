from fastmcp import FastMCP
from datetime import datetime
from sql_service import SQLService
from conn_db import Database
import signal
import asyncio

mcp = FastMCP("chatdb-mcp-server")
db = Database()
sql_service = SQLService(db)


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
async def insert_order(
    full_name: str, email: str, phone: str, address: str, note: str, products: str
) -> str:
    """
    Thêm mới một order.

    Args:
        full_name: Họ tên khách hàng
        email: Email khách hàng
        phone: Số điện thoại
        address: Địa chỉ
        note: Ghi chú
        products: Sản phẩm (tên, số lượng, mã sản phẩm)

    Returns:
        Id của order vừa tạo.
    """
    result = await sql_service.execute(
        "INSERT INTO OrderAis (FullName, Email, Phone, Address, Note, Products, CreatedDate) "
        "VALUES (:full_name, :email, :phone, :address, :note, :products, GETDATE())",
        {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "address": address,
            "note": note,
            "products": products,
        },
    )
    if result:
        return "Xử lý thành công"
    return "Xử lý thất bại"


@mcp.tool
async def update_order(
    id: int,
    full_name: str,
    email: str,
    phone: str,
    address: str,
    note: str,
    products: str,
) -> str:
    """
    Cập nhật thông tin một order theo Id.

    Args:
        id: Id của order cần cập nhật
        full_name: Họ tên khách hàng
        email: Email khách hàng
        phone: Số điện thoại
        address: Địa chỉ
        note: Ghi chú
        products: Sản phẩm (tên, số lượng, mã sản phẩm)

    Returns:
        Số dòng bị ảnh hưởng.
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
    if result:
        return "Xử lý thành công"
    return "Xử lý thất bại"


@mcp.tool
async def remove_order(id: int) -> str:
    """
    Xóa một order theo Id.

    Args:
        id: Id của order cần xóa

    Returns:
        Số dòng bị ảnh hưởng.
    """
    result = await sql_service.execute(
        "DELETE FROM OrderAis WHERE Id=:id",
        {"id": id},
    )
    if result:
        return "Xử lý thành công"
    return "Xử lý thất bại"


@mcp.tool
async def get_order(phone: str) -> dict:
    """
    Dùng để lấy toàn bộ order theo số điện thoại hoặc lấy id để dùng.

    Args:
        phone: số điện thoại dùng để lấy order

    Returns:
        Các order theo số điện thoại.
    """
    result = await sql_service.execute(
        "SELECT Id, FullName, Email, Phone, Address, Note, Products, CreatedDate "
        "FROM OrderAis WHERE Phone=:phone",
        {"phone": phone},
    )
    if result:
        return result
    return "Xử lý thất bại"


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
