import base64
import numpy as np
import cv2
import time
import datetime
import threading
import requests
import io
from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.object_detection import ObjectDetection

# ==========================================
# CONFIGURATION: URLs
# ==========================================
# Change this URL if your external AI VLM server IP changes
REMOTE_SERVER_URL = "http://100.89.100.36:5000/image-query"

web_ui = WebUI()
object_detection = ObjectDetection()

current_mode = "idle"
latest_frame_b64 = None

# ==========================================
# 1. HARDWARE PIN EDGE-DETECTION & ROUTER
# ==========================================
pin_mapping = {
    2: "vlm",
    3: "liveguide",
    4: "read text",
    5: "time"
}

# 1 = Button Pressed (HIGH), 0 = Button Released (LOW)
last_pin_states = {2: "0", 3: "0", 4: "0", 5: "0"}

# --- Software Debounce tracking ---
last_trigger_times = {2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
DEBOUNCE_DELAY = 1.5  # Seconds to wait before allowing another press

def handle_hardware_pins(data):
    global last_pin_states, last_trigger_times
    
    # Strip any hidden formatting Python might add
    clean_data = str(data).replace("b'", "").replace("'", "").strip()
    values = clean_data.split(",")
    
    # We are tracking exactly 4 values (Pins 2 to 5)
    if len(values) == 4:
        
        # 1. Instantly light up the UI dashboard
        pin_data_for_ui = {}
        for i in range(4):
            pin_num = i + 2
            pin_data_for_ui[str(pin_num)] = "HIGH" if values[i] == "1" else "LOW"
            
        try:
            web_ui.send_message('pin_update', pin_data_for_ui)
        except Exception:
            pass

        # 2. Check for button presses to trigger commands
        for i in range(4):
            pin_num = i + 2
            current_state = values[i]
            prev_state = last_pin_states[pin_num]
            
            # TRIGGER ON HIGH: Fires exactly when pin goes from 0 -> 1
            if prev_state == "0" and current_state == "1":
                current_time = time.time()
                
                # SOFTWARE DEBOUNCE: Only trigger if 1.5 seconds have passed!
                if current_time - last_trigger_times[pin_num] > DEBOUNCE_DELAY:
                    command = pin_mapping[pin_num]
                    print(f"Hardware button {pin_num} HIGH! Injecting command: {command}")
                    handle_sensor('local_pin', command)
                    
                    # Record the exact time we triggered this
                    last_trigger_times[pin_num] = current_time
                else:
                    # It bounced! Ignore it.
                    pass
                
            last_pin_states[pin_num] = current_state

# The Global Container listens to the C++ Bridge
Bridge.provide('hardware_pins', handle_hardware_pins)


# ==========================================
# 2. AI & VISION LOGIC
# ==========================================
def get_ai_results(frame, pos=False):
    frame_width = 320
    frame = cv2.resize(frame, (frame_width, 320))
    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret: return [], []
    img_bytes = buffer.tobytes()

    out = object_detection.detect(img_bytes, confidence=0.60)
    
    class_labels = []
    positions = []
    detected_classes_positions = {}

    if out and "detection" in out:
        for obj in out["detection"]:
            class_name = obj.get("class_name")
            box = obj.get("bounding_box_xyxy") 
            
            if class_name and box:
                x1, y1, x2, y2 = box
                center_x = (x1 + x2) / 2
                
                if pos:
                    if center_x < frame_width / 3: position = 'left'
                    elif center_x > 2 * frame_width / 3: position = 'right'
                    else: position = 'front'
                else:
                    position = ""

                if class_name not in detected_classes_positions:
                    detected_classes_positions[class_name] = set()
                detected_classes_positions[class_name].add(position)

    for class_name, positions_set in detected_classes_positions.items():
        for position in positions_set:
            class_labels.append(class_name)
            positions.append(position if pos else "")

    return class_labels, positions


# ==========================================
# 3. VIDEO ROUTING
# ==========================================
def handle_frame(sid, data):
    global latest_frame_b64
    latest_frame_b64 = data

def video_broadcaster():
    global latest_frame_b64
    while True:
        if latest_frame_b64 is not None:
            web_ui.send_message('relay_frame', latest_frame_b64)
        time.sleep(0.1)


# ==========================================
# 4. AGNOSTIC COMMAND EXECUTOR
# ==========================================
def handle_sensor(sid, data):
    global current_mode, latest_frame_b64
    keyword = str(data).strip().lower()
    
    # Instantly update the dashboard command text
    web_ui.send_message('relay_sensor', keyword) 
    
    if keyword == "time":
        current_time = datetime.datetime.now().strftime("%I:%M:%S %p")
        web_ui.send_message('ui_update', {"data": f"System Time: {current_time}"})
        
    elif keyword == "liveguide":
        if current_mode == "liveguide":
            current_mode = "idle"
            web_ui.send_message('ui_update', {"data": "Live Guide Mode: OFF"})
        else:
            current_mode = "liveguide"
            
    elif keyword == "obstacle detection":
        if latest_frame_b64 is not None:
            img_data = base64.b64decode(latest_frame_b64)
            np_arr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            labels, positions = get_ai_results(frame, pos=False)
            
            combined_text = ""
            for i in range(len(labels)):
                combined_text += f"{labels[i]}, "
                
            if len(labels) == 0:
                combined_text = "Nothing"
                
            web_ui.send_message('ui_update', {"data": f" {combined_text.strip(', ')}"})
        else:
            web_ui.send_message('ui_update', {"data": "Error: Waiting for camera..."})

    elif keyword == "vlm" or keyword == "read text":
        if latest_frame_b64 is not None:
            web_ui.send_message('ui_update', {"data": "Processing image..."})
            
            img_bytes = base64.b64decode(latest_frame_b64)
            
            def fetch_vlm(kwd, raw_bytes):
                # Uses the clean URL variable from the top of the file!
                prompt = "Describe what is happening in this image in detail." if kwd == "vlm" else "Extract all text from this image."
                files = {"image": ("frame.jpg", io.BytesIO(raw_bytes), "image/jpeg")}
                data = {"text_query": prompt}
                
                try:
                    res = requests.post(REMOTE_SERVER_URL, files=files, data=data, timeout=20)
                    if res.status_code == 200:
                        resp_json = res.json()
                        if isinstance(resp_json, dict):
                            final_text = resp_json.get("response", resp_json.get("result", resp_json.get("text", str(resp_json))))
                        else:
                            final_text = str(resp_json)
                        web_ui.send_message('ui_update', {"data": final_text})
                    else:
                        web_ui.send_message('ui_update', {"data": "Error from external server."})
                except Exception as e:
                    web_ui.send_message('ui_update', {"data": "Server connection failed."})
                    
            threading.Thread(target=fetch_vlm, args=(keyword, img_bytes), daemon=True).start()
        else:
            web_ui.send_message('ui_update', {"data": "Error: Waiting for camera..."})

def liveguide_worker():
    global current_mode, latest_frame_b64
    while True:
        if current_mode == "liveguide" and latest_frame_b64 is not None:
            img_data = base64.b64decode(latest_frame_b64)
            np_arr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            labels, positions = get_ai_results(frame, pos=True)
            
            combined_text = ""
            for i in range(len(labels)):
                combined_text += f"{labels[i]} {positions[i]}, "
                
            if len(labels) == 0:
                combined_text = "Nothing"
                
            web_ui.send_message('ui_update', {"data": f"{combined_text.strip(', ')}"})
            
            time.sleep(1.5)
        else:
            time.sleep(0.1)

web_ui.on_message('relay_frame', handle_frame)
web_ui.on_message('relay_sensor', handle_sensor)

if __name__ == '__main__':
    threading.Thread(target=liveguide_worker, daemon=True).start()
    threading.Thread(target=video_broadcaster, daemon=True).start()
    App.run()