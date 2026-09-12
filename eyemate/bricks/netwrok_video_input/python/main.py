import cv2
import socketio
import time
import base64
import threading

sio = socketio.Client()

print("Waiting for Main Server to start...")
while True:
    try:
        sio.connect('http://main:7000')
        print("Connected to Main Server successfully!")
        break
    except Exception as e:
        time.sleep(2)

# --- BULLET PROOF CAMERA SCANNER ---
def find_camera():
    print("Scanning USB ports for the true video stream...")
    # Scans indices 0 through 5 to catch shifting Linux ports!
    for index in range(6): 
        print(f"Trying index {index}...")
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            # Grab a frame to prove it's the real camera and not just metadata
            ret, frame = cap.read()
            if ret:
                print(f"✅ SUCCESS: Found actual video stream at index {index}!")
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                return cap
        cap.release()
    return None

cap = find_camera()

# Global variable to store the absolute newest frame
latest_frame = None

def grab_frames_continuously():
    """
    Background thread that constantly reads from the camera to prevent 
    OpenCV's internal buffer from backing up and causing lag.
    """
    global cap, latest_frame
    while True:
        if cap is None or not cap.isOpened():
            print("Camera lost! Hunting for new port...")
            time.sleep(2)
            cap = find_camera()
            continue

        ok, frame = cap.read()
        if not ok:
            print("Failed to read from camera. Retrying...")
            time.sleep(1.0)
            if cap is not None:
                cap.release()
            # If the camera fails, auto-scan to find its new port!
            cap = find_camera()
            continue
        
        # Overwrite with the newest frame
        latest_frame = frame

# Start the background thread
thread = threading.Thread(target=grab_frames_continuously, daemon=True)
thread.start()

print("Grabbing frames from USB Webcam and sending to server...")

while True:
    if latest_frame is not None:
        # Make a quick copy to avoid tearing if the thread updates it while we encode
        frame_to_send = latest_frame.copy()
        
        # Resize just to be absolutely sure
        frame_to_send = cv2.resize(frame_to_send, (320, 240))
        ret, buffer = cv2.imencode('.jpg', frame_to_send)
        
        if ret:
            # Convert to text and blast it to the dashboard
            b64_str = base64.b64encode(buffer).decode('utf-8')
            try:
                sio.emit('relay_frame', b64_str)
            except Exception as e:
                print(f"Socket emit failed: {e}")
                
    # Rest for 0.1s to save CPU (10 FPS)
    time.sleep(0.1)