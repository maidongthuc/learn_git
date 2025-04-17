import paho.mqtt.client as mqtt
import time

mqtt_server = "1df19fa858774630a1197a48081cc0c1.s1.eu.hivemq.cloud"
mqtt_port = 8883
mqtt_username = "chechanh2003"
mqtt_password = "0576289825Asd"
topic = "Livingroom/device_1"

# Callback khi kết nối thành công
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(topic)
    else:
        print(f"⚠️ Failed to connect, return code {rc}")

# Callback khi nhận tin nhắn
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(topic)
    else:
        print(f"⚠️ Failed to connect, return code {rc}")

# Callback khi nhận tin nhắn
def on_message(client, userdata, msg):
    
    data = msg.payload.decode()
    # Chuỗi đầu vào
    input_string = data
    print(data)

    # Tách chuỗi bằng dấu '&'
    parts = input_string.split('&')

    # Khởi tạo các biến
    SpO2 = None
    HR = None
    Temp = None
    BP1 = None
    BP2 = None

    for part in parts:
        if '=' in part:
            key, value = part.split('=')
            if key == "SpO2":
                SpO2 = int(value)
            elif key == "HR":
                HR = int(value)
            elif key == "Temp":
                Temp = float(value)
            elif key == "BP":
                BP1, BP2 = map(int, value.split('/'))
                
    print(SpO2, HR, Temp, BP1, BP2)


# Khởi tạo MQTT Client với TLS/SSL
client = mqtt.Client()
client.username_pw_set(mqtt_username, mqtt_password)  # Đăng nhập
client.tls_set()  # Kích hoạt TLS

# Gán callback
#quan lý kết nối và nhận tin nhắn
client.on_connect = on_connect
client.on_message = on_message

print("🔄 Connecting to broker...")
client.connect(mqtt_server, mqtt_port, 60)

client.loop_start()

time.sleep(2)
client.publish(topic, "Hello from Python MQTT over TLS!")

try:
    while True:
        time.sleep(1)  
except KeyboardInterrupt:
    print("❌ Disconnecting...")
    client.loop_stop()
    client.disconnect()
