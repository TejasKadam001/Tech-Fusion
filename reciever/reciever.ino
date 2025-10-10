#include <HardwareSerial.h>

HardwareSerial lora(1);

// LoRa configuration
#define RX1 27
#define TX1 26

// Buffer for incoming data
String receivedData = "";
unsigned long lastReceiveTime = 0;
const unsigned long RECEIVE_TIMEOUT = 1000; // 1 second timeout
const int MAX_MESSAGE_LENGTH = 300; // Maximum expected message length

// Statistics
unsigned long totalReceived = 0;
unsigned long validForwarded = 0;
unsigned long lastStatsTime = 0;

void setup() {
  // Serial for USB connection to computer (connects to app.py)
  Serial.begin(115200);
  
  // LoRa serial connection
  lora.begin(115200, SERIAL_8N1, RX1, TX1);
  
  Serial.println("STARTUP_PACKET");
  Serial.println("LoRa Receiver Ready");
  
  delay(1000);
}

void loop() {
  // Read data from LoRa module
  while (lora.available()) {
    char inChar = lora.read();
    
    if (inChar == '\n') {
      // Complete message received
      if (receivedData.length() > 0) {
        // Process the received message
        processMessage(receivedData);
        receivedData = "";
      }
      lastReceiveTime = millis();
    } else if (inChar != '\r') {
      // Accumulate characters (ignore carriage return)
      receivedData += inChar;
      lastReceiveTime = millis();
    }
  }
  
  // Timeout check - clear buffer if incomplete message takes too long
  if (receivedData.length() > 0 && (millis() - lastReceiveTime > RECEIVE_TIMEOUT)) {
    Serial.println("[WARN] Incomplete message timeout. Clearing buffer.");
    receivedData = "";
  }
}

void processMessage(String message) {
  // Validate message format
  if (message.startsWith("STARTUP_PACKET")) {
    Serial.println("STARTUP_PACKET");
    return;
  }
  
  // Check if message starts with correct key (10)
  if (!message.startsWith("10,")) {
    Serial.println("[WARN] Invalid message key: " + message);
    return;
  }
  
  // Count commas to verify field count (should have 24 commas for 25 fields)
  int commaCount = 0;
  for (int i = 0; i < message.length(); i++) {
    if (message[i] == ',') commaCount++;
  }
  
  if (commaCount != 24) {
    Serial.println("[WARN] Invalid field count (" + String(commaCount) + " commas): " + message);
    return;
  }
  
  // Message is valid - forward to computer via USB Serial
  Serial.println(message);
  
  // Optional: Debug output (comment out in production)
  // Serial.println("[DEBUG] Forwarded: " + message);
}