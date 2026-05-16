#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "Harshal";         // <-- CHANGE THIS
const char* password = "harsh150allsmall"; // <-- CHANGE THIS

// Define ESP32-CAM Pins
const int BUZZER_PIN = 12;
const int SENSOR_PIN = 13;
const int RELAY_PIN = 14; 

WebServer server(80);

void lockDoor() {
  digitalWrite(RELAY_PIN, HIGH);
}

void unlockDoor() {
  digitalWrite(RELAY_PIN, LOW);
}

void handleOpen() {
  Serial.println("\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>");
  Serial.println("🟢 SUCCESS: PYTHON AND ESP32 ARE COMMUNICATING!");
  Serial.println(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n");

  
  server.send(200, "text/plain", "Door Unlocked"); 

  unlockDoor();
  delay(3000); 
  lockDoor();
}


void setup() {
  Serial.begin(115200);

  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(SENSOR_PIN, INPUT_PULLUP); 

  pinMode(RELAY_PIN, OUTPUT_OPEN_DRAIN);
  lockDoor(); 

  // Wi-Fi Connection Loop
  Serial.print("Connecting to Wi-Fi");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    attempts++;
    if(attempts % 10 == 0) {
        Serial.println(" Still trying... check WiFi name/password!");
    }
  }
  
  Serial.println("\n✅ WiFi connected!");
  Serial.print("IMPORTANT: Your ESP32-CAM IP Address is: ");
  Serial.println(WiFi.localIP()); 
  
  server.on("/open", handleOpen);
  server.begin();
}


void loop() {
  server.handleClient(); 

  if (digitalRead(SENSOR_PIN) == LOW) { 
    digitalWrite(BUZZER_PIN, HIGH); 
    delay(500);                     
    digitalWrite(BUZZER_PIN, LOW);  
    delay(3000); 
  }
}