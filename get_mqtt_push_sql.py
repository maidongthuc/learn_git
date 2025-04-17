import paho.mqtt.client as mqtt
import time
import json
from push_sql import connect_to_database
# Thông tin EMQX broker từ cấu hình của bạn
BROKER = "broker.emqx.io"
PORT = 1883
TOPIC = "emqx/esp8266/health"
USERNAME = "admin"
PASSWORD = "06102003#hyy"
CLIENT_ID = "python-mqtt-client"
conn = connect_to_database()

# Callback khi kết nối thành công (phiên bản API 2.0)
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"Kết nối thành công đến {BROKER}")
        client.subscribe(TOPIC, qos=1)
        print(f"Đã subscribe vào topic: {TOPIC}")
    else:
        print(f"Kết nối thất bại, mã lỗi: {reason_code}")

# Callback khi nhận được tin nhắn (phiên bản API 2.0)
def on_message(client, userdata, msg, properties=None):
    parsed_data = json.loads(msg.payload.decode())  # Chuyển đổi thành dictionary
    temp = parsed_data["DATA"]["temp"]
    spo2 = parsed_data["DATA"]["spo2"]
    hr = parsed_data["DATA"]["hr"]
    sys = parsed_data["DATA"]["sys"]
    dia = parsed_data["DATA"]["dia"]

    print(temp, spo2, hr, sys, dia)  # Output: 36.5 98 88 102 75
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO health_data (temp, spo2, hr, sys, dia)
            VALUES (%s, %s, %s, %s, %s)
        """, (temp, spo2, hr, sys, dia))
        conn.commit()
        print("Dữ liệu đã được chèn thành công!")
    else:
        print("Không thể kết nối đến cơ sở dữ liệu.")
# Callback khi subscribe thành công (phiên bản API 2.0)
def on_subscribe(client, userdata, mid, reason_codes, properties=None):
    print(f"Subscribe thành công với reason_codes: {reason_codes}")

# Tạo MQTT client với callback_api_version
client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

# Cấu hình thông tin đăng nhập
client.username_pw_set(USERNAME, PASSWORD)

# Gán các callback
client.on_connect = on_connect
client.on_message = on_message
client.on_subscribe = on_subscribe

# Kết nối đến broker
try:
    client.connect(BROKER, PORT, keepalive=60)
except Exception as e:
    print(f"Lỗi kết nối: {e}")
    exit(1)

# Vòng lặp chính để xử lý tin nhắn
client.loop_start()

# Giữ chương trình chạy
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nĐã dừng chương trình bởi người dùng")
    client.loop_stop()
    client.disconnect()