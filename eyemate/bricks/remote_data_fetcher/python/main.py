import time
import requests
import socketio
import threading

# Import the App object to keep the container alive!
from arduino.app_utils import App

sio = socketio.Client()

print("Waiting for Main Server to start...")
while True:
    try:
        sio.connect('http://main:7000')
        print("Connected to Main Server successfully!")
        break
    except Exception as e:
        time.sleep(2)

fetch_url = "http://192.168.43.190:8080"
post_url = "http://192.168.43.190:8081"

last_remote_command = ""

# ==========================================
# 1. SEND AI OUTPUT BACK TO PHONE
# ==========================================
@sio.on('ui_update')
def on_ui_update(data):
    try:
        message = data.get("data", "")
        print(f"Sending audio text to phone: {message}", flush=True)
        
        # Phone specifically expects x-www-form-urlencoded instead of JSON!
        payload = {"message": message}
        requests.post(
            post_url, 
            headers={"Content-Type": "application/x-www-form-urlencoded"}, 
            data=payload, 
            timeout=2
        )
    except Exception as e:
        pass


# ==========================================
# 2. FETCH COMMANDS FROM PHONE
# ==========================================
def remote_polling_worker():
    global last_remote_command
    while True:
        try:
            response = requests.get(fetch_url, timeout=2)
            if response.status_code == 200:
                current_data = response.text.strip().lower()
                
                if current_data != last_remote_command:
                    last_remote_command = current_data
                    print(f"Phone app command: {current_data}", flush=True)
                    sio.emit('relay_sensor', current_data)
        except Exception as e:
            pass 
            
        time.sleep(0.1)

if __name__ == '__main__':
    # Start checking the mobile app in the background
    threading.Thread(target=remote_polling_worker, daemon=True).start()
    
    # Start the native App Lab engine
    App.run()