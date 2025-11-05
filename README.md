# Satellite Operations Dashboard

### Overview
This project is a real‑time satellite operations dashboard built with Flask and Socket.IO that visualizes telemetry, attitude, and star tracking outputs, with support for real serial hardware and a built‑in simulator mode for demos. The frontend dashboard includes live status tiles, orientation, telemetry panels, and an AI orbital collision detection section designed for hackathon demonstrations.

### Features
- Real‑time telemetry via Socket.IO for quaternion, acceleration, environment, LoRa latency, sun status, and more.
- Hardware streaming at 115200 baud from a serial device that periodically outputs BNO and BMP CSV lines.
- One‑click simulated data mode via a pseudo port named SIMULATED_PORT for demos without hardware.
- Integrated star tracking analysis using a server‑side image, with optional external script fallback if available.
- Dashboard sections for status, satellite orientation, telemetry, star tracking params, ACDS, and common system parameters.

### Tech stack
- Backend: Flask + Flask‑SocketIO running in threading mode (no eventlet/gevent requirement).
- Serial: pyserial for device enumeration and streaming (serial.tools.list_ports).
- Star tracking: Pillow (PIL), NumPy, SciPy for image processing and constellation identification logic.
- Frontend: HTML/CSS/JS dashboard template rendered at / and /dashboard.

### Repository layout
- app.py — Flask + Socket.IO server, serial reader threads, simulated data generator, star tracking, and API/events.
- templates/dashboard.html — main UI served by Flask (ensure this file is in templates/).
- static/imgs/star_field.jpg — star tracker input image used by integrated analysis (ensure this path exists).

### Requirements
- Python 3.9+ recommended for compatibility with Flask‑SocketIO, PIL, NumPy, SciPy, and pyserial.
- Python packages: flask, flask‑socketio, pyserial, pytz, pillow, numpy, scipy (Flask‑SocketIO pulls socketio/engineio deps automatically).

Example install:
- python -m venv .venv; source .venv/bin/activate (or .venv\Scripts\activate on Windows).
- pip install flask flask-socketio pyserial pytz pillow numpy scipy.

### Run the server
- Launch: python app.py (binds 0.0.0.0:5508).
- Navigate to http://localhost:5508 or your host’s IP at port 5508 to open the dashboard.
- The dashboard is served at / and /dashboard and will connect to Socket.IO automatically.

### Serial data formats
The server expects newline‑terminated CSV frames with these prefixes and fields at BAUD_RATE = 115200.
- BNO lines: BNO,qx,qy,qz,qw,accel_x,accel_y,accel_z (7 numeric values after the prefix).
- BMP lines: BMP,temperature,pressure,altitude (3 numeric values after the prefix).

Example frames:
- BNO,0.01,0.02,0.03,0.99,0.1,-0.1,9.70.
- BMP,24.8,1012.6,98.7.

### How to connect your serial device
- Use the correct baud: 115200 (set both your microcontroller and the server’s device to 115200).
- Ensure your device prints the BNO/BMP CSV frames exactly as above, each line ending with newline for reliable .readline() parsing.
- Start the server, open the dashboard, choose your serial port from the UI (the server lists ports via /api/ports) and the backend will start a reader thread and emit live sensor_data events to the UI.

### Finding your serial port
macOS:
- Use ls /dev/tty.usb* to see USB serial devices like /dev/tty.usbmodemXXXXXX or /dev/tty.usbserial‑XXXX.
- You can also compare /dev/tty* before/after plugging in to find the new device (e.g., ls -lha /dev/tty* and diff).
- For quick terminal testing, connect with screen /dev/tty.usbserial-XXXX 115200 (replace with your device path).

Windows:
- Open Device Manager and check Ports (COM & LPT) to find your device’s COM number (e.g., COM7).
- You can change or verify a COM assignment via Device Manager > Port Settings > Advanced if needed.
- pyserial exposes command‑line and Python APIs to list ports (python -m serial.tools.list_ports or serial.tools.list_ports.comports()).

Linux:
- USB adapters typically show up as /dev/ttyUSB0, /dev/ttyUSB1, etc.; list with ls /dev/ttyS* /dev/ttyUSB* to identify devices.
- For a persistent and unambiguous view, check /dev/serial/by-id for symlinks naming each device by VID:PID and serial.
- You can also use screen /dev/ttyUSB0 115200 to verify output from your device on common distros.

### Selecting ports in the app
- The app exposes GET /api/ports that returns two lists: real (system ports) and simulated (includes SIMULATED_PORT).
- The frontend triggers a Socket.IO set_port event with the selected port; the server picks real vs. simulated reader accordingly.
- Choose SIMULATED_PORT to run a full demo with smooth changing attitude and telemetry without any hardware connected.

### What the backend emits
- sensor_data: periodic packets with rounded values for UI tiles (orientation, quaternion, accel, environment, sun status, LoRa delay, gps placeholders, etc.).
- port_status: connection messages for success/failure when trying to open a serial port.
- notification: textual updates during star tracking processes and external script monitoring.
- star_tracking_result: final outputs from integrated or external star tracking analysis.

### Star tracking analysis
- The integrated pipeline loads static/imgs/star_field.jpg, detects stars, identifies patterns, estimates attitude, and infers a simple geo‑position proxy for demo purposes.
- If an external final8.py exists at known paths, the server tries to launch it and streams its output into notifications and final results; otherwise it falls back to the integrated analyzer.
- Triggering analysis publishes progress notifications and a result payload with patterns, derived attitude, and a demo position estimate.

### Orientation math (server side)
- Quaternions are converted to roll/pitch/yaw and a visualization pointing RA/Dec using quaternion_to_euler_and_pointing in the backend.
- The server uses these angles for the dashboard orientation indicators and pointing display alongside raw quaternion values.

### Dashboard guide
- The top section presents AI Orbital Collision Detection widgets with model status, training loss, accuracy, and predictions placeholders for hackathon presentations.
- Real‑Time Status shows Speed, Reaction Wheel, Magnetorquers, Lux, and Sun Status derived or simulated by the backend.
- Telemetry panels include Quaternion, Altitude, Temperature, Acceleration axes, and downstream sections for Star Tracking, ACDS, and general system parameters.

### Configuration
- BAUD_RATE = 115200 (change in app.py if your device uses a different baud).
- Server binds to host 0.0.0.0, port 5508; edit socketio.run(...) if you need a different port.
- The India timezone (Asia/Kolkata) is used for sun presence logic in get_sun_status.

### Typical workflow
- Start server: python app.py, then open the dashboard in a browser.
- Pick your serial port from the UI to start the real serial reader thread, or pick SIMULATED_PORT to stream demo data.
- Watch the dashboard tiles update in real time; trigger star tracking from the UI to run integrated or external analysis.

### Troubleshooting
- No ports listed: verify drivers and list ports with python -m serial.tools.list_ports or via Device Manager/macOS /dev to confirm OS sees the device.
- Garbage characters: confirm both device and app use 115200 8N1, and that lines end with newline for .readline() parsing.
- No updates after connect: ensure your device prints BNO/BMP frames matching the expected CSV formats shown above.
- Star image not found: create static/imgs/star_field.jpg or update STAR_IMAGE_PATH in app.py to a valid image path.

### API and events (quick reference)
- GET /, /dashboard → serves dashboard.html.
- GET /api/ports → lists real and simulated ports.
- Socket.IO set_port → selects real serial or SIMULATED_PORT and starts the appropriate reader.
- Socket.IO start_star_tracking → runs external final8.py if found, else runs integrated analysis thread.

### Team
Lazy Loopers — Hackathon build focused on real‑time satellite ops visualization, serial telemetry ingestion, and demo‑friendly simulation and analysis flows.
