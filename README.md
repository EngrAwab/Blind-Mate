 👁️ BlindMate: AI-Powered Ecosystem for the Visually Impaired
*An affordable, zero-latency assistive device built on the Arduino Uno Q's dual-brain architecture.*
![BlindMate Demo](assets/hero_demo.gif) <!-- IMPORTANT: Replace with a GIF of your project working -->
## 🏆 Project Overview
With over 8 million visually impaired individuals in Pakistan alone, access to education and independent mobility is severely limited by the high cost of commercial assistive technologies. 
**BlindMate** is a wearable, real-time navigation and educational platform designed to solve this. By utilizing the dual-core architecture of the Arduino Uno Q, BlindMate delivers real-time haptic navigation and edge AI object detection at a fraction of the cost of commercial smart glasses (total build cost: ~$100–$150).
### Key Features
*   **Zero-Latency Haptic Navigation:** Dual vibration motors driven directly by the Uno Q microcontroller for instant physical guidance.
*   **Edge Object Detection:** Real-time obstacle detection using a highly optimized **YOLO-X** model via Edge Impulse.
*   **VLM Scene Description & OCR:** Rich environmental descriptions and text-to-speech reading powered by **Qwen2.5 VL**, routed through a local University GPU server via **Tailscale VPN**.
*   **Custom Remote Shield:** A tactile, physical interface designed specifically for visually impaired users to bypass laggy smartphone apps.
---
## 🛒 Bill of Materials (BOM)
BlindMate is designed to be affordable and scalable. The entire hardware stack costs under $150.
| Component | Quantity | Purpose |
| :--- | :--- | :--- |
| **Arduino Uno Q** | 1 | The core dual-brain processor (Linux + RTOS) |
| **Webcam (1080p)** | 1 | Mounted on a cap for environmental capture |
| **Type-C Hub** | 1 | Connects the webcam to the Uno Q |
| **Power Bank (5V/4.5A)** | 1 | Powers the system for 7+ hours |
| **Coin Vibration Motors** | 2 | Actuators for the Haptic Navigation Belt |
| **Custom Remote Shield** | 1 | Tactile user input (buttons wired to GPIO) |
*(Insert an image of your circuit diagram / schematic here)*
---
## 🧠 System Architecture & The "Dual-Brain" Advantage
BlindMate maximizes the Arduino Uno Q's unique hardware by splitting workloads across its two processors, ensuring that high-load AI tasks never delay critical safety hardware.
1.  **The Microprocessor (Linux Domain):** Handles the heavy lifting. It runs the Arduino App Lab Docker containers (`network_video_input` and `remote_data_fetcher`), manages the Tailscale VPN connection to our VLM API, and executes the YOLO-X edge AI model.
2.  **The Microcontroller (RTOS Domain):** Handles real-time safety. It reads the tactile remote shield inputs and drives the haptic belt with zero OS-level latency. 
### Code Highlight: The Asynchronous Bridge
### Code Highlight: The Asynchronous Bridge
To ensure the Python AI loop doesn't block the physical hardware, we utilize the Arduino Router Bridge. When the YOLO model detects an obstacle on the left, Python asynchronously calls the microcontroller to trigger the right haptic motor, guiding the user to safety instantly.
**Python (Linux side):**
```python
# When an obstacle is detected on the left, trigger the right motor to guide the user away
if obstacle_position == "left":
    Bridge.call("trigger_haptic_right")
```
**C++ (Microcontroller side):**
```cpp
// Instantly actuates the motor with zero Linux-kernel latency
void trigger_haptic_right() {
    digitalWrite(RIGHT_MOTOR_PIN, HIGH);
    delay(200); 
    digitalWrite(RIGHT_MOTOR_PIN, LOW);
}
```
---
## 🚀 Setup & Installation Guide
Follow these steps to replicate the BlindMate system.
### 1. Hardware & OS Setup
1. Mount the webcam on a wearable cap and place the Uno Q and Power Bank in a well-ventilated backpack to prevent thermal throttling.
2. Connect the Haptic Belt and Remote Shield to the Uno Q GPIO pins.
3. Power up the Uno Q via the Type-C dongle and connect via SSH:
   ```bash
   sudo apt-get update
   sudo apt-get upgrade
   cd ArduinoApps
   git clone https://github.com/EngrAwab/Blind-Mate.git
   ```
### 2. App Lab Deployment
BlindMate utilizes the modular Arduino App Lab "Bricks" architecture.
1. Open the Arduino App Lab interface on your host machine.
2. Import the project folder to load our custom `network_video_input` and `remote_data_fetcher` bricks.
3. Connect them to the pre-built **Object Detection** and **WebUI** bricks.
4. Update the IP settings in `python/main.py` (Line 19) to match your local smartphone/network IP.
### 3. Tailscale VPN (For Remote VLM Access)
To use the advanced Qwen2.5 Scene Description features off-campus, you must connect the Uno Q to the University GPU via Tailscale.
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```
*(Update `eyemate/python/main.py` on line 17 with your Tailscale Server IP).*
---
## 🔮 Future Roadmap
*   **Autonomous Path Planning:** Utilizing YOLO11n for full floor segmentation to actively route users around complex obstacles.
*   **Hardware Integration:** Miniaturizing the webcam and Uno Q into a standalone, unified glasses form factor.
## ⚠️ Disclaimer
*Please note that a visually impaired person requires proper orientation and mobility training before using this product effectively in real-world scenarios.*
## 🤝 Team / Contact
We are actively looking to turn this prototype into a market-ready product to help students in Pakistan and beyond. If you are interested in supporting inclusive education, please reach out!
