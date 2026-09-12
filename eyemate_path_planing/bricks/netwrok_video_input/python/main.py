import cv2
import socketio
import time
import base64   # <--- Add this import!

sio = socketio.Client()

print("Waiting for Main Server to start...")
while True:
    try:
        sio.connect('http://main:7000')
        print("Connected to Main Server successfully!")
        break
    except Exception as e:
        time.sleep(2)

video_source = "http://192.168.43.112:4747/video"
cap = cv2.VideoCapture(video_source)

print("Grabbing frames and sending to server...")

while True:
    ok, frame = cap.read()
    if not ok:
        time.sleep(0.1)
        continue
    
    frame = cv2.resize(frame, (320, 240))
    ret, buffer = cv2.imencode('.jpg', frame)
    
    if ret:
        # Convert the raw bytes into a pure text string!
        b64_str = base64.b64encode(buffer).decode('utf-8')
        sio.emit('relay_frame', b64_str)
        
    time.sleep(0.05)