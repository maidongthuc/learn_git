import paho.mqtt.client as mqtt
from fastapi import FastAPI, WebSocket
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import json
import asyncio
from collections import deque
from starlette.requests import Request
import joblib
import numpy as np
import torch
import torch.nn as nn
import requests
# Cấu hình MQTT
BROKER = "1df19fa858774630a1197a48081cc0c1.s1.eu.hivemq.cloud"
PORT = 8883
TOPIC = "Livingroom/device_1"
USERNAME = "chechanh2003"
PASSWORD = "0576289825Asd"

# Hàng đợi lưu trữ dữ liệu mới nhất
data_queue = deque(maxlen=1)
COZE_URL = 'https://api.coze.com/open_api/v2/chat'
token = 'pat_GojthSW0XTyNqKlxxuahD7LLLvP1NUIccWDzQ49DN3ZUaxqgsKI4jn1k0m4WKrMh'
COZE_HEADERS = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'Connection': 'keep-alive',
    'Accept': '*/*',
}

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class Autoencoder(nn.Module):
    def __init__(self):
        super(Autoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(5, 2),  # Phải giữ nguyên số neuron như model cũ
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(2, 5),
            nn.Sigmoid()
        )

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x

# Khởi tạo model mới với đúng kiến trúc cũ
model = Autoencoder()

# Load lại model với weights_only=True (cách an toàn)
model.load_state_dict(torch.load("model_5.pth", weights_only=True))

# Đặt model ở chế độ đánh giá
model.eval()

# Load scaler
scaler = joblib.load("scaler_5.pkl")

threshold = 1.4658211469650269

# Hàm dự đoán và phân tích đơn giản (có thể tùy chỉnh)
def predict_data(data):
    new_data = np.array([data])  # Ví dụ: [nhiệt độ, SpO2, nhịp tim, huyết áp, ...]

    # 1. Chuẩn hóa dữ liệu mới
    new_data_scaled = scaler.transform(new_data)  # Sử dụng cùng bộ scaler đã huấn luyện

    # Chuyển đổi dữ liệu thành tensor PyTorch
    new_data_scaled = torch.tensor(new_data_scaled, dtype=torch.float32)

    # 2. Tính sai số tái tạo
    model.eval()  # Đặt mô hình vào chế độ đánh giá
    with torch.no_grad():
        reconstruction = model(new_data_scaled)  # Tái tạo dữ liệu
        mse = torch.mean((new_data_scaled - reconstruction) ** 2).item()  # Tính sai số tái tạo tổng thể
        feature_wise_mse = torch.mean((new_data_scaled - reconstruction) ** 2, dim=0).numpy()  # Tính sai số cho từng đặc trưng

    # 3. So sánh với ngưỡng và phân loại
    if mse > threshold:
        prediction = f"Dữ liệu mới là BAD (bất thường). Sai số tái tạo: {mse:.4f}"
    else:
        prediction = f"Dữ liệu mới là GOOD (tốt). Sai số tái tạo: {mse:.4f}"

    return prediction
def analysis_data(content):
    data = json.dumps({
        "conversation_id": "demo-0",
        "bot_id": "7476437008655876114",
        "user": "demo-user",
        "query": content,
        "stream": False
    })

    resp = requests.post(COZE_URL, data=data, headers=COZE_HEADERS)
    return resp.json()['messages'][0]['content']
# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(TOPIC)
    else:
        print(f"⚠️ Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    data = msg.payload.decode()
    parts = data.split('&')
    
    health_data = {"temp": 0, "spo2": 0, "hr": 0, "sys": 0, "dia": 0}
    for part in parts:
        if '=' in part:
            key, value = part.split('=')
            if key == "SpO2":
                health_data["spo2"] = int(value)
            elif key == "HR":
                health_data["hr"] = int(value)
            elif key == "Temp":
                health_data["temp"] = float(value)
            elif key == "BP":
                health_data["sys"], health_data["dia"] = map(int, value.split('/'))
    
    # Thêm dự đoán và phân tích
    input = [health_data["spo2"],health_data["hr"],health_data["temp"],health_data["sys"], health_data["dia"]]
    content = f"Nhiệt độ cơ thể: {health_data["temp"]}°C; Nhịp tim: {health_data["hr"]} bpm; SpO2: {health_data["spo2"]}%; Huyết áp: {health_data["sys"]}/{health_data["dia"]} mmHg"
    print('HELLO')
    print(input)
    prediction = predict_data(input)
    print(prediction)
    analysis = "Đang phân tích..."
    health_data["prediction"] = prediction
    health_data["analysis"] = analysis
    data_queue.append(health_data)

    analysis = analysis_data(content)
    health_data["analysis"] = analysis
    data_queue.append(health_data)


# Khởi tạo MQTT Client
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()
client.on_connect = on_connect
client.on_message = on_message

# Kết nối MQTT
print("🔄 Connecting to broker...")
client.connect(BROKER, PORT, 60)
client.loop_start()

# FastAPI routes
@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            if data_queue:
                print('đã vào')
                latest_data = data_queue[-1]
                print(f"🔄 Sending data: {latest_data}")  # Debug
                await websocket.send_text(json.dumps(latest_data))
            await asyncio.sleep(1)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Dừng MQTT khi ứng dụng tắt
@app.on_event("shutdown")
def shutdown_event():
    client.loop_stop()
    client.disconnect()