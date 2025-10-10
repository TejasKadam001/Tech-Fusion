Satellite Telemetry Dashboard

This repository contains a real-time telemetry dashboard and supporting components for visualizing sensor data, running simple analysis, and interacting with devices over serial or WebSocket. The dashboard displays orientation (quaternion), accelerometer data, altitude, temperature, and other telemetry in charts and an interactive 3D viewer.

This README intentionally avoids domain-specific language and focuses on how to set up and use the software components in a general-purpose telemetry project.

Contents
- `app.py` - Flask + Flask-SocketIO server that provides the web dashboard, serial port helpers, simulated data mode, and a simple star-tracking image analysis tool.
- `templates/dashboard.html` - Main front-end dashboard UI. Uses Chart.js, Three.js, Leaflet, and GSAP.
- `static/` - Static assets: JavaScript libs, CSS, images, models, and fonts used by the dashboard.
- `sender/esp_telemetry.ino` - Example microcontroller sketch that streams sensor telemetry over serial in the format expected by `app.py`.
- `final/` - (Optional) directory that may contain auxiliary scripts or tools. Not required for core dashboard operation.

Features
- Live plotting of telemetry streams with Chart.js (multiple datasets supported).
- 3D model viewer with pointer orbit and wheel zoom using Three.js, with auto-scaling to fit the viewport.
- Map view using Leaflet for displaying geo-coordinates received from telemetry.
- Serial port chooser and simulated data mode for local testing without hardware.
- Server-side image analysis function (optional), which can be triggered from the dashboard and returns detection results via WebSocket.

Requirements
- Python 3.8+ recommended
- Node.js is not required to run the server, but the front-end uses browser libraries delivered from the `static/` directory.
- Python dependencies (install with pip):
  - Flask
  - Flask-SocketIO
  - pyserial
  - Pillow
  - numpy
  - scipy
  - pytz

Example installation (create a venv first):

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Running the server
1. Start the Flask server:

python app.py

2. Open the dashboard in your browser at http://127.0.0.1:5501/dashboard

Connecting hardware or using simulated data
- The dashboard provides an API endpoint `/api/ports` that lists available serial ports and a simulated option. Choose a port from the UI to start telemetry streaming.
- The `sender/esp_telemetry.ino` sketch is an example for microcontrollers using I2C sensors. It prints telemetry lines in two formats:
  - BNO,qx,qy,qz,qw,accel_x,accel_y,accel_z
  - BMP,temperature_c,pressure_hPa,altitude_m
- `app.py` expects those CSV lines on the serial port and parses them into the dashboard data model.

Troubleshooting serial/I2C devices
- Ensure devices share a common ground with the host that reads serial.
- Use 3.3V power for sensors if you are using an ESP32 (avoid 5V on I2C lines).
- If I2C devices aren't responding, run the I2C scanner (the provided ESP sketch prints addresses) and verify wiring and pull-ups.
- Check the server logs for socket events and any parsing errors; the server will log warnings when serial reading fails.

Security and safety
- The server includes code that can spawn an external analysis script if present. Be cautious about running untrusted scripts. The example in this repository only checks a small set of expected candidate paths before launching.
- The built-in development server is not suitable for production deployment. Use a WSGI server (like gunicorn) and a proper async worker configuration for production.

Extending the project
- Add new telemetry channels to the front-end charts by updating `templates/dashboard.html` and emitting the appropriate `sensor_data` structure from the server.
- Swap the 3D model in `static/models/` with another GLTF file; the loader auto-scales the geometry to fit.
- Add persistent logging or database integration to store telemetry for later analysis.

License
- This project is provided as-is. Add your preferred license file if you plan to distribute it.

Contact
- For questions about running or extending the dashboard, check the code comments in `app.py` and the front-end template for guidance.