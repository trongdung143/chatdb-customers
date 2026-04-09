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


mcp.run(transport="streamable-http", host="0.0.0.0", port=8123)
