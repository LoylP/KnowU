import os
import requests
import pandas as pd
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()
mcp = FastMCP(name="mcp-server")

# 🧠 Tool: Lấy thời tiết theo thành phố
@mcp.tool()
def get_current_temperature_by_city(city_name: str) -> str:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Missing API key"

    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city_name,
                "appid": api_key,
                "units": "metric",
                "lang": "vi"
            }
        )
        data = response.json()
        if response.status_code != 200:
            return f"Error: {data.get('message', 'Unknown error')}"

        temp = data["main"]["temp"]
        weather_desc = data["weather"][0]["description"]
        return f"Nhiệt độ tại {city_name} là {temp}°C, thời tiết: {weather_desc}"

    except Exception as e:
        return f"Lỗi khi gọi API: {str(e)}"

# 🧠 Tool: Lấy thông tin người dùng từ in4.csv
@mcp.tool()
def get_user_info(username: str) -> dict:
    try:
        df = pd.read_csv("in4.csv")
        user_row = df[df["username"] == username]
        if user_row.empty:
            return {"error": "Không tìm thấy người dùng"}
        user = user_row.iloc[0]
        return {
            "fullname": user.get("fullname", "Chưa rõ"),
            "age": int(user.get("age", 0)),
            "role": user.get("role", "Chưa rõ"),
            "summary": user.get("summary", "Chưa có mô tả"),
            "location": user.get("location", "Chưa rõ"),
            "interests": user.get("interests", "Chưa rõ")
        }
    except Exception as e:
        return {"error": str(e)}

# 📦 Resource đơn giản
@mcp.resource("resource://say_hi/{name}")
def say_hi(name: str) -> str:
    return f"Hello {name}"

# 🧠 Prompt xử lý văn bản
@mcp.prompt()
def review_sentence(sentence: str) -> str:
    return f"Review this sentence, remove any personal information: \n\n{sentence}"

if __name__ == "__main__":
    mcp.run(transport='sse')