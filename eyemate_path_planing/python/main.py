from arduino.app_utils import App
from arduino.app_bricks.web_ui import WebUI

web_ui = WebUI()

# 1. Catch BOTH the client ID (sid) and the image data
def handle_frame(sid, data):
    # 2. Bounce the frame out to the Web Browser
    web_ui.send_message('relay_frame', data)

web_ui.on_message('relay_frame', handle_frame)

if __name__ == '__main__':
    App.run()