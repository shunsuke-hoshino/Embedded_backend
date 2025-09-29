from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import asyncio
import logging
import os
from datetime import datetime
import requests

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="組み込みボード制御API", version="1.0.0")

# CORS設定（フロントエンドからのアクセスを許可）
# Azure App Service用に本番URLも追加
allowed_origins = [
    "http://localhost:3000",  # 開発環境
    "https://*.azurestaticapps.net",  # Azure Static Web Apps
    "https://*.azurewebsites.net",  # Azure App Service
]

# 環境変数から追加のオリジンを取得
frontend_url = os.environ.get("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データモデル
class Point(BaseModel):
    x: float
    y: float

class PathData(BaseModel):
    path: List[Point]
    timestamp: str

class BoardResponse(BaseModel):
    success: bool
    message: str
    processed_points: int

# グローバル変数
current_path = []
ESP32_URL = "http://192.168.1.100"  # ESP32のIPアドレス（実際の環境に合わせて変更）

@app.get("/")
async def root():
    return {"message": "組み込みボード制御APIサーバーが稼働中です"}

@app.post("/api/path")
async def receive_path(path_data: PathData):
    """フロントエンドから描画パスを受信し、ESP32に送信"""
    try:
        logger.info(f"パスデータを受信: {len(path_data.path)} 点")
        
        # パスデータを保存
        global current_path
        current_path = path_data.path
        
        # ESP32用にパスデータを変換
        esp32_data = convert_path_for_esp32(path_data.path)
        
        # ESP32に送信を試行
        board_result = await send_to_esp32(esp32_data)
        
        return {
            "success": True,
            "message": "パスデータを受信し、ボードに送信しました",
            "points_received": len(path_data.path),
            "board_response": board_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"パス処理エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"パス処理中にエラーが発生しました: {str(e)}")

@app.get("/api/status")
async def get_status():
    """現在のステータスを取得"""
    return {
        "status": "active",
        "current_path_points": len(current_path),
        "esp32_url": ESP32_URL,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/path/current")
async def get_current_path():
    """現在保存されているパスデータを取得"""
    return {
        "path": current_path,
        "points_count": len(current_path),
        "timestamp": datetime.now().isoformat()
    }

def convert_path_for_esp32(path: List[Point]) -> dict:
    """パスデータをESP32用の形式に変換"""
    
    # キャンバスサイズ（800x600）をボードの座標系に変換
    # 例: キャンバス800x600 → ボード100x100の座標系
    canvas_width, canvas_height = 800, 600
    board_width, board_height = 100, 100
    
    converted_points = []
    for point in path:
        # 座標を正規化してボード座標系に変換
        board_x = int((point.x / canvas_width) * board_width)
        board_y = int((point.y / canvas_height) * board_height)
        converted_points.append({"x": board_x, "y": board_y})
    
    # パスを間引いてデータ量を削減（10点ごとに1点採用）
    simplified_points = converted_points[::10] if len(converted_points) > 50 else converted_points
    
    return {
        "command": "move_path",
        "points": simplified_points,
        "total_points": len(simplified_points),
        "speed": 50,  # 移動速度（0-100）
        "timestamp": datetime.now().isoformat()
    }

async def send_to_esp32(data: dict) -> dict:
    """ESP32ボードにデータを送信"""
    try:
        # 実際のESP32への送信を試行
        logger.info(f"ESP32へデータ送信を試行: {ESP32_URL}")
        
        # タイムアウト付きでHTTP POST送信
        response = requests.post(
            f"{ESP32_URL}/api/move",
            json=data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("ESP32への送信成功")
            return result
        else:
            logger.warning(f"ESP32からエラーレスポンス: {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        # ESP32に接続できない場合はシミュレーションモード
        logger.warning(f"ESP32接続失敗、シミュレーションモードで動作: {str(e)}")
        
        # シミュレーション処理
        await asyncio.sleep(1)  # 処理時間をシミュレート
        
        return {
            "success": True,
            "message": "シミュレーションモードで実行",
            "processed_points": len(data.get("points", [])),
            "mode": "simulation"
        }

@app.post("/api/esp32/config")
async def update_esp32_config(config: dict):
    """ESP32の接続設定を更新"""
    global ESP32_URL
    
    if "ip_address" in config:
        ESP32_URL = f"http://{config['ip_address']}"
        logger.info(f"ESP32 URL更新: {ESP32_URL}")
    
    return {
        "success": True,
        "esp32_url": ESP32_URL,
        "message": "設定を更新しました"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)