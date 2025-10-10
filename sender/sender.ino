#include <Wire.h>
#include <SPI.h>
#include <MS5611.h>
#include <Adafruit_BNO055.h>
#include <Adafruit_Sensor.h>
#include <TinyGPS++.h>
#include <HardwareSerial.h>

HardwareSerial lora(1);

// Sensor and module instances
MS5611 ms5611(0x77);
Adafruit_BNO055 bno = Adafruit_BNO055(55);
TinyGPSPlus gps;
HardwareSerial gpsSerial(2);

// LoRa configuration
#define RX1 27
#define TX1 26

// GPS Serial configuration
#define GPS_RX_PIN 16
#define GPS_TX_PIN 17

// Parachute status pins
#define DROGUE_PIN 2
#define MAIN_PIN 4

// Battery monitoring pin
#define BATTERY_PIN 34

// Timing - INCREASED to prevent buffer overflow
unsigned long lastSendTime = 0;
// *** EDITED: Increased interval to 500ms (2 messages/sec) for robustness ***
const unsigned long SEND_INTERVAL = 500; // 500ms = 2 messages per second (much safer)

void setup() {
  Serial.begin(115200);
  Wire.begin();

  // Initialize LoRa serial
  lora.begin(115200, SERIAL_8N1, RX1, TX1);
  Serial.println("LoRa serial ready");

  // Initialize GPS serial
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
  Serial.println("GPS serial ready");

  // Initialize MS5611 - try both possible addresses
  Serial.println("Attempting MS5611 at 0x77...");
  if (!ms5611.begin()) {
    Serial.println("MS5611 not found at 0x77, trying 0x76...");
    MS5611 ms5611_alt(0x76);
    if (!ms5611_alt.begin()) {
      Serial.println("MS5611 not found at either address");
      Serial.println("Continuing without MS5611 (using dummy data)");
      // Don't halt - continue with other sensors
    } else {
      Serial.println("MS5611 found at 0x76");
      ms5611 = ms5611_alt;
    }
  } else {
    Serial.println("MS5611 initialized at 0x77");
  }

  // Initialize BNO055
  if (!bno.begin()) {
    Serial.println("BNO055 not found");
    while (1);
  }
  // Set operation mode (NDOF = Nine Degrees of Freedom fusion mode)
  bno.setMode(OPERATION_MODE_NDOF);
  Serial.println("BNO055 initialized");
  
  pinMode(DROGUE_PIN, INPUT_PULLUP);
  pinMode(MAIN_PIN, INPUT_PULLUP);
  pinMode(BATTERY_PIN, INPUT);

  // Send startup packet
  lora.println("STARTUP_PACKET");
  Serial.println("LoRa Sender Ready");
  
  delay(1000);
}

void loop() {
  unsigned long currentTime = millis();
  
  // Send data at fixed interval
  if (currentTime - lastSendTime >= SEND_INTERVAL) {
    lastSendTime = currentTime;
    
    // Read GPS data
    while (gpsSerial.available()) {
      gps.encode(gpsSerial.read());
    }

    // Read MS5611 sensor data
    ms5611.read();
    float temperature = ms5611.getTemperature();
    float pressure = ms5611.getPressure();
    float altitude_m = 44330.0f * (1.0f - pow(pressure / 101325.0f, 0.1903f));

    // Read BNO055 IMU data
    sensors_event_t accel, gyro, mag;
    bno.getEvent(&accel, Adafruit_BNO055::VECTOR_ACCELEROMETER);
    bno.getEvent(&gyro, Adafruit_BNO055::VECTOR_GYROSCOPE);

    // Get Euler angles
    imu::Vector euler = bno.getVector(Adafruit_BNO055::VECTOR_EULER);
    float roll = euler.x();
    float pitch = euler.y();
    float yaw = euler.z();
    
    // Get linear acceleration
    imu::Vector linear_accel = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);
    float lax = linear_accel.x();
    float lay = linear_accel.y();
    float laz = linear_accel.z();
    
    // Read battery voltage
    float battery = (float)analogRead(BATTERY_PIN) * (3.3f / 4095.0f) * 2.0f;
    
    // Signal strength (placeholder - will be measured at receiver)
    int signal_strength = -65;
    float range_km = 0.0;

    // Read parachute status (0 or 1)
    int drogue_status = (digitalRead(DROGUE_PIN) == LOW) ? 1 : 0;
    int main_status = (digitalRead(MAIN_PIN) == LOW) ? 1 : 0;

    // GPS coordinates (handle invalid GPS)
    float latitude = gps.location.isValid() ? gps.location.lat() : 0.0;
    float longitude = gps.location.isValid() ? gps.location.lng() : 0.0;

    // Message format matching app.py expectations:
    // key,temperature,pressure,altitude,latitude,longitude,
    // ax,ay,az,roll,pitch,yaw,lax,lay,laz,wx,wy,wz,
    // battery,signal_strength,range_km,drogue_status,main_status,timestamp_ms,rssi
    
    // *** EDITED: Reduced decimal precision on float values to shrink the message size significantly ***
    String message = "10," +                                // key (must be 10)
                     String(temperature, 1) + "," +         // Temp: 1 decimal place
                     String(pressure, 0) + "," +            // Pressure: 0 decimal places (no need for 1Pa precision)
                     String(altitude_m, 1) + "," +          // Altitude: 1 decimal place
                     String(latitude, 4) + "," +            // Lat: 4 decimal places (sufficient for rocketry)
                     String(longitude, 4) + "," +           // Lon: 4 decimal places
                     String(accel.acceleration.x, 1) + "," +// Accel X: 1 decimal place
                     String(accel.acceleration.y, 1) + "," +// Accel Y: 1 decimal place
                     String(accel.acceleration.z, 1) + "," +// Accel Z: 1 decimal place
                     String(roll, 1) + "," +                // Roll: 1 decimal place
                     String(pitch, 1) + "," +               // Pitch: 1 decimal place
                     String(yaw, 1) + "," +                 // Yaw: 1 decimal place
                     String(lax, 1) + "," +                 // Lin Accel X: 1 decimal place
                     String(lay, 1) + "," +                 // Lin Accel Y: 1 decimal place
                     String(laz, 1) + "," +                 // Lin Accel Z: 1 decimal place
                     String(gyro.gyro.x, 1) + "," +         // Gyro X: 1 decimal place
                     String(gyro.gyro.y, 1) + "," +         // Gyro Y: 1 decimal place
                     String(gyro.gyro.z, 1) + "," +         // Gyro Z: 1 decimal place
                     String(battery, 1) + "," +             // Battery: 1 decimal place
                     String(signal_strength) + "," +
                     String(range_km, 2) + "," +
                     String(drogue_status) + "," +          // Integer 0 or 1
                     String(main_status) + "," +            // Integer 0 or 1
                     String(currentTime) + "," +            // Timestamp in milliseconds
                     String(signal_strength);              // RSSI (placeholder)

    // Send via LoRa
    lora.println(message);
    
    // Debug output
    Serial.println(message);
  }
}
