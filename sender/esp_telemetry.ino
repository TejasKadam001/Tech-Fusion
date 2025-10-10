#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <Adafruit_BMP280.h>

// Serial baud must match app.py BAUD_RATE (115200)
#define BAUD_RATE 115200

// LED pin (change if using different board). On many ESP32 dev boards onboard LED is GPIO 2.
#define LED_PIN 2

// Use pointer for BNO so we can try different I2C addresses (0x28/0x29)
Adafruit_BNO055 *bno = nullptr;
Adafruit_BMP280 bmp; // I2C

// Global flags to remember initialization state from setup()
bool g_bno_ok = false;
bool g_bmp_ok = false;

unsigned long lastBlink = 0;
bool ledState = false;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.begin(BAUD_RATE);
  while (!Serial) { delay(10); } // wait for Serial

  // Explicit I2C pins for common ESP32 boards (change if your board uses different pins)
  // SDA = 21, SCL = 22 on many ESP32 dev boards
  Wire.begin(21, 22);

  // Initialize sensors once and keep status flags
  bool bno_ok = false;
  bool bmp_ok = false;

  // Run a quick I2C scan and show all devices found (helps debug addresses)
  Serial.println("Running I2C scan...");
  bool found28 = false;
  bool found29 = false;
  for (uint8_t address = 1; address < 127; ++address) {
    Wire.beginTransmission(address);
    uint8_t err = Wire.endTransmission();
    if (err == 0) {
      Serial.printf("Found I2C device at 0x%02X (err=%d)\n", address, err);
      if (address == 0x28) found28 = true;
      if (address == 0x29) found29 = true;
    }
  }
  Serial.println("I2C scan complete.");

  // Try to initialize BNO at detected address preference (28 first then 29)
  if (found28 || found29) {
    uint8_t tryAddr = found28 ? 0x28 : 0x29;
    Serial.printf("Attempting to init BNO055 at 0x%02X...\n", tryAddr);
    bno = new Adafruit_BNO055(55, tryAddr);
    if (bno->begin()) {
      delay(100);
      bno->setExtCrystalUse(true);
      Serial.printf("BNO055 initialized at 0x%02X\n", tryAddr);
      bno_ok = true;
    } else {
      Serial.printf("Failed to init BNO055 at 0x%02X\n", tryAddr);
      // try the other address if available
      if (tryAddr == 0x28 && found29) {
        delete bno; bno = new Adafruit_BNO055(55, 0x29);
        if (bno->begin()) { delay(100); bno->setExtCrystalUse(true); Serial.println("BNO055 initialized at 0x29"); bno_ok = true; }
      }
    }
  } else {
    Serial.println("BNO055 not found on bus (addresses 0x28/0x29).\nCheck wiring, power, pull-ups.");
  }

  // Try BMP addresses once
  if (bmp.begin(0x76)) {
    Serial.println("BMP280 initialized at 0x76");
    bmp_ok = true;
  } else if (bmp.begin(0x77)) {
    Serial.println("BMP280 initialized at 0x77");
    bmp_ok = true;
  } else {
    Serial.println("BMP280 not detected at 0x76/0x77. If you saw other addresses in the scan above, check which device corresponds.");
    bmp_ok = false;
  }

  // Optional: configure BMP sampling for faster updates
  bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,
                  Adafruit_BMP280::SAMPLING_X2, // temperature
                  Adafruit_BMP280::SAMPLING_X16, // pressure
                  Adafruit_BMP280::FILTER_X16,
                  Adafruit_BMP280::STANDBY_MS_500);

  // persist flags for loop()
  g_bno_ok = bno_ok;
  g_bmp_ok = bmp_ok;

  Serial.println("ESP telemetry uploader ready. Streaming BNO/BMP data...");
}

void loop() {
  // Heartbeat LED blink (toggle every 500ms)
  unsigned long now = millis();
  if (now - lastBlink > 500) {
    lastBlink = now;
    ledState = !ledState;
    digitalWrite(LED_PIN, ledState ? HIGH : LOW);
  }

  // Read BNO quaternion + accelerometer (only if initialized)
  static bool firstLoop = true;
  static bool bno_ok_loop = false;
  static bool bmp_ok_loop = false;
  static unsigned long lastReinitAttempt = 0;
  if (firstLoop) {
    // reflect setup state
    bno_ok_loop = g_bno_ok && (bno != nullptr);
    bmp_ok_loop = g_bmp_ok;
    firstLoop = false;
  }

  // If BNO isn't initialized, try re-initializing every 5 seconds (in case wiring/power stabilizes)
  if (!bno_ok_loop && millis() - lastReinitAttempt > 5000) {
    lastReinitAttempt = millis();
    Serial.println("Attempting to re-detect BNO055 on addresses 0x28/0x29...");
    // Try 0x28 then 0x29
    Adafruit_BNO055 *trybno = new Adafruit_BNO055(55, 0x28);
    if (trybno->begin()) {
      trybno->setExtCrystalUse(true);
      if (bno) delete bno; bno = trybno; bno_ok_loop = true; Serial.println("BNO055 re-initialized at 0x28");
    } else {
      delete trybno;
      trybno = new Adafruit_BNO055(55, 0x29);
      if (trybno->begin()) { trybno->setExtCrystalUse(true); if (bno) delete bno; bno = trybno; bno_ok_loop = true; Serial.println("BNO055 re-initialized at 0x29"); }
      else { delete trybno; Serial.println("Re-init failed for BNO055 at both addresses."); }
    }
  }

  if (bno_ok_loop && bno != nullptr) {
    imu::Quaternion quat = bno->getQuat();
    float qw = quat.w();
    float qx = quat.x();
    float qy = quat.y();
    float qz = quat.z();

  imu::Vector<3> accel = bno->getVector(Adafruit_BNO055::VECTOR_ACCELEROMETER);
    float ax = accel.x();
    float ay = accel.y();
    float az = accel.z();

    // Output in expected format for app.py's parser
    // BNO,qx,qy,qz,qw,accel_x,accel_y,accel_z
    Serial.printf("BNO,%.6f,%.6f,%.6f,%.6f,%.4f,%.4f,%.4f\n", qx, qy, qz, qw, ax, ay, az);
  } else {
    // If BNO not initialized, print zeros and a hint in serial
    Serial.println("BNO,0,0,0,1,0,0,0");
    if (bno == nullptr) {
      Serial.println("Debug: bno pointer is NULL. Sensor not initialized.");
    }
  }

  // Read BMP (only if initialized in setup)
  if (bmp_ok_loop) {
    float tempC = bmp.readTemperature();
    float pressure_hPa = bmp.readPressure() / 100.0F; // Pa -> hPa
    float altitude_m = bmp.readAltitude(1013.25);
    Serial.printf("BMP,%.2f,%.2f,%.2f\n", tempC, pressure_hPa, altitude_m);
  } else {
    Serial.println("BMP,0,0,0");
  }

  // Small delay so we don't flood serial (approx 10Hz)
  delay(100);
}
