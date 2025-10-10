# Satellite Telemetry Dashboard

A real-time rocket telemetry dashboard with comprehensive flight analysis and PDF report generation.

## 🚀 Quick Setup

### Prerequisites
- Python 3.8 or higher
- Web browser (Chrome, Firefox, Safari, Edge)

### Installation
1. **Extract the project** to any folder on your computer
2. **Run setup** (double-click or run in terminal):python3 setup.py
3. **Start the dashboard**:python3 app.py
4. **Open browser** to: http://localhost:5501

## 📱 Access from Other Devices
- **Same network**: http://[YOUR_IP_ADDRESS]:5501
- **Find your IP**: Check terminal output when app starts

## 🎛️ Features

### Real-time Dashboard
- Live telemetry data visualization
- 3D rocket orientation model
- GPS tracking with interactive map
- Multiple sensor data charts
- Connection status monitoring

### Data Logging
- Automatic CSV file generation
- Individual sensor data files
- Combined sensor data file
- Timestamped file naming

### Flight Analysis
- **Stop Flight Button** - Red button with confirmation dialog
- **Comprehensive PDF Reports** - Professional flight analysis
- **Dynamic Calculations** - Motor burnout, parachute deployment, descent rates
- **Multi-page Charts** - Altitude, velocity, acceleration, battery, temperature

### PDF Report Contents
- Flight Card with launch details
- Flight Results with max values
- Altitude vs Time chart
- Velocity vs Time chart  
- Acceleration vs Time chart
- Battery & Temperature analysis
- Professional formatting

## 🔧 Usage

### Simulated Data
1. Select "SIMULATED_PORT" from dropdown
2. Watch real-time rocket simulation
3. Press **Stop Flight** button to generate PDF report

### Real Hardware
1. Connect rocket telemetry hardware via USB/Serial
2. Select correct COM port from dropdown
3. Monitor live flight data
4. Generate post-flight analysis reports

## 📁 File Structure
project-folder/
├── app.py # Main Flask application
├── templates/
│ └── dashboard.html # Dashboard interface
├── requirements.txt # Python dependencies
├── setup.py # Automatic setup script
├── README.md # This file
├── data_log/ # CSV files and PDF reports
└── static/ # Web assets (auto-created)

## 🆘 Troubleshooting

### Port Already in Use
- Change port in app.py: `port=5502`
- Or kill existing process

### Missing Packages
pip install -r requirements.txt

### Permission Errors (Windows)
- Run Command Prompt as Administrator
- Or run: `python setup.py`

### Cannot Access from Network
- Check firewall settings
- Ensure port 5501 is not blocked

## 📊 Data Output

### CSV Files
- `all_sensor_data/` - Combined telemetry data
- `Ms/` - Altitude, pressure, temperature
- `imu/` - Acceleration, gyroscope, magnetometer  
- `gps/` - GPS coordinates
- `battery/` - Battery voltage
- `chute/` - Parachute deployment status
- `lora/` - Radio telemetry data

### PDF Reports
- `Flight_Summary_YYYYMMDD_HHMMSS.pdf`
- Professional flight analysis format
- Stored in `data_log/` folder

## 🔧 Technical Details
- **Backend**: Python Flask + SocketIO
- **Frontend**: HTML5 + JavaScript + Chart.js
- **3D Graphics**: Three.js
- **Maps**: Leaflet.js
- **PDF Generation**: Matplotlib
- **Data Processing**: Pandas + Numpy

---