# Smart AI Doorbell: Facial Recognition & IoT Security System

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![C++](https://img.shields.io/badge/C++-ESP32-purple?style=for-the-badge&logo=cplusplus)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer_Vision-green?style=for-the-badge&logo=opencv)
![IoT](https://img.shields.io/badge/Blynk-IoT_Cloud-orange?style=for-the-badge)

## Project Overview
An edge-computing, biometric access control system that replaces traditional keys with facial recognition. This project utilizes an **ESP32-CAM** for local hardware actuation and a **Python-based local server** for heavy machine learning inference. It features real-time cloud logging and mobile alerting via **ImgBB** and **Blynk IoT**.

## Key Features
* **Touchless Biometric Entry:** Extracts 128-point facial encodings via OpenCV to authenticate and unlock the door in under 2 seconds.
* **Proactive Mobile Alerts:** Captures snapshots of unknown visitors and pushes live image URLs directly to the owner's smartphone.
* **Global Remote Access:** Allows the owner to monitor entry logs and manually trigger the door lock from anywhere in the world using the Blynk app.
* **Asynchronous Execution:** The ESP32 utilizes a non-blocking web server to handle physical door mechanics without interrupting the high-FPS Python video stream.

## System Architecture

### 1. The "Brain" (Software/Edge Node)
* **Hardware:** Local Python Server (Laptop/Raspberry Pi Target) + Webcam
* **Role:** Processes live video, runs biometric comparisons, and handles all outgoing Cloud API requests.

### 2. The "Muscle" (Hardware/Microcontroller Node)
* **Hardware:** ESP32-CAM + IR Proximity Sensor + Active Buzzer
* **Role:** Detects physical presence, manages local chime, and hosts the async HTTP server listening for unlock commands.

### 3. The "Bridge" (High-Voltage Actuator)
* **Hardware:** 5V Active-Low Relay + 11.1V Dedicated Battery + Solenoid Lock
* **Role:** Safely isolates the 3.3V/5V logic circuit from the 11.1V mechanical lock circuit.

## Tech Stack
* **Languages:** Python, C++ (Arduino Framework)
* **Computer Vision:** `OpenCV`, `face_recognition`
* **Network/IoT:** `requests`, ESP32 `WebServer.h`, Blynk IoT API, ImgBB API

## Engineering Solutions
* **Logic Level Conflict Resolution:** The 3.3V ESP32 GPIO pins were initially unable to fully deactivate the 5V Active-Low Relay. This was solved by engineering an `OUTPUT_OPEN_DRAIN` pin configuration in C++, allowing the microcontroller to safely ground the relay without logic voltage conflicts.
* **Power Stability:** To prevent brownout crashes caused by simultaneous Wi-Fi, Camera, and Solenoid power draws, the system architecture utilizes an isolated 11.1V battery circuit exclusively for the lock mechanism.

## How It Works
1. **Trigger:** Visitor approaches; IR sensor triggers the local buzzer.
2. **Analysis:** Python captures a webcam frame and checks for a facial match.
3. **Scenario A (Match):** Python sends an HTTP `GET /open` to the ESP32. The ESP32 triggers the relay, dropping the lock for 3 seconds. The event is logged to the Blynk app.
4. **Scenario B (No Match):** Python converts the frame to Base64, uploads it to ImgBB, and pushes the live URL to the Blynk app, alerting the owner of a stranger. 
5. **Override:** The owner views the photo on their phone and can press a remote unlock button to let the guest in.

## Setup & Installation (Local Dev)
1. Flash the `esp32_doorbell.ino` code to your ESP32-CAM using the MB Shield. Update the Wi-Fi credentials inside the code.
2. Connect the IR Sensor to GPIO 13, Buzzer to GPIO 12, and Relay `IN` to GPIO 14.
3. Install Python dependencies: `pip install opencv-python face_recognition requests`
4. Place a clear photo of the authorized user named `owner.jpeg` in the project directory.
5. Update the `ESP32_IP`, `BLYNK_TOKEN`, and `IMGBB_API_KEY` variables in `main.py`.
6. Run `python main.py` to start the edge server.
