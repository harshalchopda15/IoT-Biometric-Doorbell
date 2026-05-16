import cv2
import face_recognition
import requests
import time
from datetime import datetime
import base64

# Configuration
ESP32_IP = "10.183.4.60" 
ESP32_URL = f"http://{ESP32_IP}/open"

# Blynk
BLYNK_TOKEN = "YOUR BLYNK TOKEN"
BLYNK_WRITE_URL = f"https://blynk.cloud/external/api/update?token={BLYNK_TOKEN}"
BLYNK_READ_URL = f"https://blynk.cloud/external/api/get?token={BLYNK_TOKEN}"
BLYNK_PROP_URL = f"https://blynk.cloud/external/api/update/property?token={BLYNK_TOKEN}"

# ImgBB
IMGBB_API_KEY = "YOUR API KEY" 
DUMMY_VISITOR_URL = "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?fit=crop&w=500&q=80"
KNOWN_FACE_IMAGE_PATH = "owner.jpeg"

# Cloud
def upload_to_imgbb(video_frame):
    """Takes a live OpenCV frame, converts it, and uploads it to ImgBB."""
    if not IMGBB_API_KEY:
        print("No ImgBB API Key found. Using dummy stock photo.")
        return DUMMY_VISITOR_URL
        
    print("Uploading visitor snapshot to the cloud...")
    try:
        _, buffer = cv2.imencode('.jpg', video_frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        url = "https://api.imgbb.com/1/upload"
        payload = {"key": IMGBB_API_KEY, "image": img_base64}
        response = requests.post(url, data=payload, timeout=5)
        
        if response.status_code == 200:
            image_url = response.json()['data']['url']
            print("Upload Successful!")
            return image_url
        else:
            print(f"Upload failed with status {response.status_code}")
            return DUMMY_VISITOR_URL
    except Exception as e:
        print(f"Upload error: {e}")
        return DUMMY_VISITOR_URL


print("Loading reference image and building AI encodings...")
try:
    known_image = face_recognition.load_image_file(KNOWN_FACE_IMAGE_PATH)
    known_encoding = face_recognition.face_encodings(known_image)[0] 
except FileNotFoundError:
    print(f"Error: Could not find '{KNOWN_FACE_IMAGE_PATH}'. Check your file path!")
    exit()

print("Starting laptop webcam...")
cap = cv2.VideoCapture(0)

print("Stream active! Looking for faces...")
print("Checking for remote unlock commands from Blynk...")

last_owner_scan = 0
last_visitor_scan = 0

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # Resize for faster processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    current_time = time.time()

    #Blynk Button
    try:
        btn_response = requests.get(f"{BLYNK_READ_URL}&v2", timeout=1)
        clean_status = btn_response.text.strip().replace('[', '').replace(']', '').replace('"', '')
        
        if clean_status == '1':
            print("\nBLYNK OVERRIDE: Unlock Button Pressed!")
            try:
                requests.get(ESP32_URL, timeout=2)
                print("-> ESP32 Triggered via App!")
            except requests.exceptions.RequestException:
                print("Communicating with ESP32 on the network.")
            
            requests.get(f"{BLYNK_WRITE_URL}&v2=0", timeout=2)
            time.sleep(3)
    except Exception:
        pass 

    # --- 2. PROCESS FACES ---
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4
        
        matches = face_recognition.compare_faces([known_encoding], face_encoding, tolerance=0.5)

        # SCENARIO A: IT IS THE OWNER
        if True in matches:
            color = (0, 255, 0)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, "ACCESS GRANTED", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            if current_time - last_owner_scan > 10:
                print("\nOWNER DETECTED!")
                try:
                    requests.get(ESP32_URL, timeout=2)
                    print("-> Door Unlocked!")
                except requests.exceptions.RequestException:
                    print("Trying to send signal to ESP32.")

                try:
                    timestamp = datetime.now().strftime("%I:%M %p")
                    log_msg = f"Harsh checked in at {timestamp}"
                    requests.get(f"{BLYNK_WRITE_URL}&v0={log_msg}", timeout=2)
                    print("-> Blynk Log Updated!")
                except:
                    pass 
                
                last_owner_scan = current_time

        # SCENARIO B: IT IS A STRANGER
        else:
            color = (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, "UNKNOWN VISITOR", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            if current_time - last_visitor_scan > 15:
                print("\nUNKNOWN VISITOR DETECTED!")
                live_snapshot_url = upload_to_imgbb(frame)
                
                try:
                    requests.get(f"{BLYNK_PROP_URL}&pin=v1&urls={live_snapshot_url}", timeout=2)
                    requests.get(f"{BLYNK_WRITE_URL}&v1=1", timeout=2)
                    print("-> Sent visitor photo to your phone!")
                except:
                    print("Could not reach Blynk.")
                
                last_visitor_scan = current_time

    cv2.imshow("Smart Doorbell System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()