# cd D:\pythonFile\Lab4\weather\my_project
# uvicorn main:app --reload
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import aiohttp
import asyncio
import csv
from typing import List, Dict

from starlette.responses import HTMLResponse

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 存储所有城市及其天气数据
weather_data = []  # 用于存储天气数据，初始化为空


# 异步函数 get_weather
async def get_weather(session, city_name, latitude, longitude) -> Dict[str, str]:
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
    async with session.get(url) as response:
        data = await response.json()
        temperature = data['current_weather']['temperature']
        return {'city': city_name, 'temperature': temperature}


# 异步函数 load_city_coordinates
async def load_city_coordinates(file_path: str) -> List[Dict[str, str]]:
    cities = []
    with open(file_path, mode='r',encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            cities.append({
                'city': row['capital'],
                'country': row['country'],
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude']),
            })
    return cities


# 异步函数 fetch_weather_for_all
async def fetch_weather_for_all(cities: List[Dict[str, str]]):
    async with aiohttp.ClientSession() as session:
        tasks = [
            get_weather(session, f"{city['city']}, {city['country']}", city['latitude'], city['longitude'])
            for city in cities
        ]
        weather_results = await asyncio.gather(*tasks)
        return weather_results


# 首页路由，渲染HTML页面
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# 更新天气数据的路由
@app.get("/update")
async def fetch_weather():
    global weather_data  # 使用全局变量存储城市天气数据
    cities = await load_city_coordinates('europe.csv')  # 修改为正确的文件路径
    weather_data = await fetch_weather_for_all(cities)
    return weather_data


# 删除城市的路由
@app.delete("/remove_city/{city_name}")
async def remove_city(city_name: str):
    global weather_data  # 使用全局变量存储城市天气数据
    # 查找要删除的城市
    city_to_remove = next((city for city in weather_data if city['city'] == city_name), None)

    if city_to_remove is None:
        raise HTTPException(status_code=404, detail="City not found")

    # 从数据中移除该城市
    weather_data = [city for city in weather_data if city['city'] != city_name]

    return JSONResponse(content={"status": "success", "message": f"City {city_name} removed successfully."})

