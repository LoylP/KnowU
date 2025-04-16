import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import set_default_openai_client, set_default_openai_api
from agents import Agent, Runner
from agents.mcp import MCPServerSse
from agents.model_settings import ModelSettings

# Load biến môi trường
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Bạn cần thiết lập OPENAI_API_KEY trong file .env")

# Thiết lập OpenAI Client
client = AsyncOpenAI(api_key=openai_api_key)
set_default_openai_client(client)
set_default_openai_api("chat_completions")

model = "gpt-4o"

# Hàm gọi Agent chính
async def async_chat(message: str, user_info: dict) -> str:
    async with MCPServerSse(
        name="SSE Python Server",
        params={"url": "http://localhost:8000/sse"},
    ) as mcp_server:

        instructions = f"""
        Bạn là một trợ lý AI tên KnowU, hỗ trợ người dùng trong nhiều lĩnh vực như định hướng nghề nghiệp, học tập, bản thân, cảm xúc.
        Khi người dùng cần tư vấn những thông tin về bản thân người dùng.
        Hãy làm như sau:
        1. Gọi tool `get_user_info(username: str)` với username="{user_info['username']}"
        2. Dùng thông tin trả về (tên, tuổi, nghề, tóm tắt, sở thích) để trả lời thân thiện, có cảm xúc, đúng ngữ cảnh và đúng yêu cầu, ngắn gọn chứ không dùng hết kết quả thông tin người dùng để trả lời
        3. Nếu thiếu thông tin nào → thẳng thắn nói rõ chưa có dữ liệu đó"""

        agent = Agent(
            name="Assistant",
            model=model,
            instructions=instructions,
            mcp_servers=[mcp_server],
            model_settings=ModelSettings(tool_choice="auto"),
        )

        input_history = [{"role": "user", "content": message}]
        result = await Runner.run(starting_agent=agent, input=input_history, max_turns=5)
        return result.final_output