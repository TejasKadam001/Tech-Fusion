from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO, emit
import serial
import threading
import time
import random
import csv
import os
import subprocess
from datetime import datetime
import pytz
import sys
from serial.tools import list_ports
import math
import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage

# --- Configuration ---
BAUD_RATE = 115200
INDIAN_TIMEZONE = pytz.timezone('Asia/Kolkata')
STAR_IMAGE_PATH = os.path.join('static', 'imgs', 'star_field.jpg')

# --- Global State Variables ---
app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

current_serial_port = None
ser = None
serial_thread = None
thread_stop_event = threading.Event()
thread_running = False

# --- State for real-time sensor data ---
real_data_state = {
    'temperature': 25.0, 'pressure': 1013.25, 'altitude': 100.0,
    'qx': 0.0, 'qy': 0.0, 'qz': 0.0, 'qw': 1.0,
    'accel_x': 0.0, 'accel_y': 0.0, 'accel_z': 9.81,
    'last_accel_magnitude': 0.0,
    'reaction_wheel_active_until': 0, 'magnetorquer_active_until': 0,
    'last_update_time': time.time(),
}

SIM_STATE = {
    'initial_lat': 18.5204, 'initial_lon': 73.8567, 'initial_altitude': 100.0,
    'altitude': 100.0, 'flight_phase': "pre-flight", 'start_time': None,
}

# --- STAR TRACKER LOGIC (Integrated from final8.py) ---
class EnhancedStarCatalog:
    def __init__(self):
        self.catalog_data = {}
        self.load_builtin_stars()

    def load_builtin_stars(self):
        builtin_stars = {
            'Sirius': {'mag': -1.46, 'ra': 101.287, 'dec': -16.716, 'constellation': 'Canis Major'},
            'Rigel': {'mag': 0.13, 'ra': 78.634, 'dec': -8.202, 'constellation': 'Orion'},
            'Betelgeuse': {'mag': 0.50, 'ra': 88.793, 'dec': 7.407, 'constellation': 'Orion'},
            'Mintaka': {'mag': 2.25, 'ra': 83.002, 'dec': -0.299, 'constellation': 'Orion'},
            'Alnilam': {'mag': 1.69, 'ra': 84.053, 'dec': -1.202, 'constellation': 'Orion'},
            'Alnitak': {'mag': 1.74, 'ra': 85.190, 'dec': -1.943, 'constellation': 'Orion'},
            'Dubhe': {'mag': 1.81, 'ra': 165.932, 'dec': 61.751, 'constellation': 'Ursa Major'},
            'Merak': {'mag': 2.34, 'ra': 165.460, 'dec': 56.382, 'constellation': 'Ursa Major'},
        }
        self.catalog_data.update(builtin_stars)
        print(f"Loaded {len(builtin_stars)} built-in stars into catalog.")

class AccurateConstellationIdentifier:
    def __init__(self, star_catalog):
        self.catalog = star_catalog

    def identify_patterns(self, detected_stars, image_dimensions):
        if not detected_stars or len(detected_stars) < 3:
            return []
        print("Star Tracker: Simulating geometric pattern analysis...")
        time.sleep(3)
        
        if len(detected_stars) > 4:
            print("Star Tracker: Found a pattern resembling Orion.")
            matched_stars_sample = [
                {'detected_star': {'pixel_pos': s['centroid']}, 'catalog_star': name, 'catalog_data': self.catalog.catalog_data[name]}
                for s, name in zip(detected_stars[:3], ['Rigel', 'Betelgeuse', 'Mintaka'])
            ]
            return [{
                'constellation': 'Orion',
                'confidence': 0.85 + random.uniform(-0.05, 0.05),
                'matched_stars': matched_stars_sample,
                'description': 'The Hunter constellation (Simulated Find)'
            }]
        print("Star Tracker: No distinct patterns found in the image.")
        return []

class AdvancedStarTracker:
    def __init__(self):
        self.catalog = EnhancedStarCatalog()
        self.constellation_identifier = AccurateConstellationIdentifier(self.catalog)

    def detect_stars(self, image, threshold=100, min_area=5, max_area=500):
        gray_image = ImageOps.grayscale(image)
        gray_array = np.array(gray_image)
        blurred = ndimage.gaussian_filter(gray_array.astype(np.float32), sigma=1.0)
        binary_image = (blurred > threshold)
        labeled_image, num_features = ndimage.label(binary_image)
        stars = []
        for i in range(1, num_features + 1):
            component = (labeled_image == i)
            area = np.sum(component)
            if min_area <= area <= max_area:
                coords = np.where(component)
                cy, cx = np.mean(coords[0]), np.mean(coords[1])
                stars.append({'centroid': (cx, cy), 'area': int(area)})
        return stars

    def identify_constellations_and_position(self, image_dimensions, detected_stars):
        patterns = self.constellation_identifier.identify_patterns(detected_stars, image_dimensions)
        if not patterns:
            return None, None, None
        attitude = self.calculate_attitude_from_patterns(patterns)
        position = self.calculate_position_from_attitude(attitude)
        return patterns, attitude, position

    def calculate_attitude_from_patterns(self, patterns):
        if not patterns: return None
        best_pattern = max(patterns, key=lambda p: p['confidence'])
        pointing_ra = np.mean([m['catalog_data']['ra'] for m in best_pattern['matched_stars']])
        pointing_dec = np.mean([m['catalog_data']['dec'] for m in best_pattern['matched_stars']])
        return {
            'pointing_ra': pointing_ra, 'pointing_dec': pointing_dec,
            'roll': random.uniform(-180, 180), 'pitch': random.uniform(-90, 90), 'yaw': random.uniform(-180, 180),
            'confidence': best_pattern['confidence'], 'method': f'Pattern Matching ({best_pattern["constellation"]})'
        }
        
    def calculate_position_from_attitude(self, attitude):
        if not attitude: return None
        return {'latitude': attitude['pointing_dec'], 'longitude': (attitude['pointing_ra'] - 180), 'altitude': 550.0 }

star_tracker = AdvancedStarTracker()

# Track external subprocesses started per client session id
external_processes = {}

# --- Helper Functions (Orientation Model Logic) ---
def get_sun_status():
    now_india = datetime.now(INDIAN_TIMEZONE)
    return "Present" if 6 <= now_india.hour < 18 else "Absent"

def quaternion_to_euler_and_pointing(q):
    w, x, y, z = q.get('qw', 1.0), q.get('qx', 0.0), q.get('qy', 0.0), q.get('qz', 0.0)
    # Roll (x-axis rotation)
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll_x = math.degrees(math.atan2(t0, t1))
    # Pitch (y-axis rotation)
    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch_y = math.degrees(math.asin(t2))
    # Yaw (z-axis rotation)
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw_z = math.degrees(math.atan2(t3, t4))
    
    # Simplified pointing calculation for visualization
    pointing_ra = (yaw_z + 180) % 360
    pointing_dec = pitch_y

    return roll_x, pitch_y, yaw_z, pointing_ra, pointing_dec

# --- Data Reading Threads ---
def read_serial_real(port):
    global ser, thread_running, real_data_state
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=1)
        socketio.emit('port_status', {'message': f'Connected to {port}.', 'port': port, 'error': False})
    except serial.SerialException as e:
        socketio.emit('port_status', {'message': f'Error connecting to {port}.', 'port': port, 'error': True})
        thread_running = False
        return

    while not thread_stop_event.is_set():
        try:
            line = ser.readline().decode('utf-8').strip()
            if not line: continue
            parts = line.split(',')
            sensor_type = parts[0]
            
            if sensor_type == "BNO" and len(parts) == 8:
                real_data_state.update(dict(zip(['qx', 'qy', 'qz', 'qw', 'accel_x', 'accel_y', 'accel_z'], map(float, parts[1:]))))
            elif sensor_type == "BMP" and len(parts) == 4:
                real_data_state.update(dict(zip(['temperature', 'pressure', 'altitude'], map(float, parts[1:]))))

            now = time.time()
            current_accel_mag = math.sqrt(real_data_state['accel_x']**2 + real_data_state['accel_y']**2 + real_data_state['accel_z']**2)
            if abs(current_accel_mag - real_data_state.get('last_accel_magnitude', 0)) > 0.5:
                real_data_state['reaction_wheel_active_until'] = now + 1
                real_data_state['magnetorquer_active_until'] = now + 1
            real_data_state['last_accel_magnitude'] = current_accel_mag

            roll, pitch, yaw, ra, dec = quaternion_to_euler_and_pointing(real_data_state)

            dashboard_data = {
                **real_data_state,
                'speed': 0,
                'reaction_wheel': "Active" if now < real_data_state.get('reaction_wheel_active_until', 0) else "Inactive",
                'magnetorquer': "Active" if now < real_data_state.get('magnetorquer_active_until', 0) else "Inactive",
                'lat': SIM_STATE['initial_lat'], 'lon': SIM_STATE['initial_lon'],
                'lux': random.uniform(1000, 2000) if get_sun_status() == "Present" else random.uniform(0,2),
                'sun_up': get_sun_status(),
                'lora_delay_ms': random.uniform(20, 80),
                'roll': roll, 'pitch': pitch, 'yaw': yaw, 'pointing_ra': ra, 'pointing_dec': dec
            }
            socketio.emit('sensor_data', {k: v if isinstance(v, str) else round(v, 4) for k, v in dashboard_data.items()})
            time.sleep(0.05)
        except Exception as e:
            print(f"[WARN] Error in real serial read: {e}")
            time.sleep(1)
    if ser and ser.is_open: ser.close()
    thread_running = False

def read_serial_simulated(port):
    global thread_running
    while not thread_stop_event.is_set():
        elapsed_time = time.time() - SIM_STATE.get('start_time', time.time())
        pitch = 30 * math.sin(elapsed_time * 0.1)
        roll = 20 * math.cos(elapsed_time * 0.07)
        yaw = 50 * math.sin(elapsed_time * 0.05)
        
        cy, sy = math.cos(math.radians(yaw) * 0.5), math.sin(math.radians(yaw) * 0.5)
        cp, sp = math.cos(math.radians(pitch) * 0.5), math.sin(math.radians(pitch) * 0.5)
        cr, sr = math.cos(math.radians(roll) * 0.5), math.sin(math.radians(roll) * 0.5)

        qw = cr * cp * cy + sr * sp * sy
        qx = sr * cp * cy - cr * sp * sy
        qy = cr * sp * cy + sr * cp * sy
        qz = cr * cp * sy - sr * sp * cy

        ra, dec = (yaw + 180) % 360, pitch

        dashboard_data = {
            'altitude': 550 + random.uniform(-5,5), 'pressure': 0.05, 'temperature': -10,
            'accel_x': random.uniform(-0.1, 0.1), 'accel_y': random.uniform(-0.1, 0.1), 'accel_z': random.uniform(-0.1, 0.1),
            'qx': qx, 'qy': qy, 'qz': qz, 'qw': qw,
            'lat': SIM_STATE['initial_lat'], 'lon': SIM_STATE['initial_lon'],
            'lux': random.uniform(10000, 25000) if get_sun_status() == "Present" else random.uniform(0,2),
            'sun_up': get_sun_status(), 'lora_delay_ms': random.uniform(30, 90),
            'reaction_wheel': "Inactive", 'magnetorquer': "Inactive",
            'speed': random.uniform(7.5, 7.8),
            'roll': roll, 'pitch': pitch, 'yaw': yaw, 'pointing_ra': ra, 'pointing_dec': dec
        }
        socketio.emit('sensor_data', {k: v if isinstance(v, str) else round(v, 4) for k, v in dashboard_data.items()})
        time.sleep(0.1)
    thread_running = False

def start_serial_thread(port):
    global serial_thread, thread_stop_event, thread_running, SIM_STATE
    if thread_running:
        thread_stop_event.set()
        if serial_thread and serial_thread.is_alive():
            serial_thread.join()
        thread_stop_event.clear()
    thread_running = True
    SIM_STATE['start_time'] = time.time()
    target_func = read_serial_simulated if "SIMULATED_PORT" in port else read_serial_real
    serial_thread = threading.Thread(target=target_func, args=(port,), daemon=True)
    serial_thread.start()

# --- Flask & SocketIO Routes/Events ---
@app.route('/')
def index(): 
    return render_template('dashboard.html')

@app.route('/dashboard')
def dashboard(): 
    return render_template('dashboard.html')

@app.route('/api/ports')
def get_ports():
    return {'real': [{'port': p.device, 'description': p.description} for p in list_ports.comports()],
            'simulated': [{'port': 'SIMULATED_PORT', 'description': 'Simulated Satellite Data'}]}

@socketio.on('set_port')
def handle_set_port(json):
    start_serial_thread(json.get('port'))

def run_star_analysis():
    """Worker thread function for star tracking."""
    print("Star Tracker: Analysis thread started.")
    try:
        if not os.path.exists(STAR_IMAGE_PATH):
            socketio.emit('star_tracking_result', {'error': 'Star image not found on server.'})
            return
            
        image = Image.open(STAR_IMAGE_PATH)
        socketio.emit('notification', {'message': 'Detecting stars from image...'})
        detected_stars = star_tracker.detect_stars(image)
        
        if not detected_stars:
            socketio.emit('star_tracking_result', {'patterns': [], 'message': 'No stars detected.'})
            return

        socketio.emit('notification', {'message': f'Found {len(detected_stars)} stars. Identifying patterns...'})
        patterns, attitude, position = star_tracker.identify_constellations_and_position(image.size, detected_stars)
        
        result = {
            'patterns': patterns or [], 'attitude': attitude, 'position': position,
            'message': f'Analysis complete. Found {len(patterns)} patterns.' if patterns else 'Analysis complete. No patterns found.'
        }
        socketio.emit('star_tracking_result', result)

    except Exception as e:
        print(f"Star Tracker Error: {e}")
        socketio.emit('star_tracking_result', {'error': str(e)})
    print("Star Tracker: Analysis thread finished.")

def _monitor_external_process(proc, sid):
    """Read subprocess stdout/stderr and emit notifications; emit final result when done."""
    try:
        socketio.emit('notification', {'message': 'External star tracker started.'}, room=sid)
        for line in proc.stdout:
            line = line.rstrip('\n')
            if line:
                socketio.emit('notification', {'message': f'[external] {line}'}, room=sid)
        stderr = proc.stderr.read()
        if stderr:
            socketio.emit('notification', {'message': f'[external-err] {stderr}'}, room=sid)
        returncode = proc.wait()
        socketio.emit('star_tracking_result', {
            'message': f'External script exited with code {returncode}.',
            'returncode': returncode
        }, room=sid)
    except Exception as e:
        socketio.emit('star_tracking_result', {'error': str(e)}, room=sid)
    finally:
        try:
            external_processes.pop(sid, None)
        except Exception:
            pass

@socketio.on('start_star_tracking')
def handle_star_tracking(json):
    sid = request.sid if hasattr(request, 'sid') else None
    print(f"Received star tracking request from client. sid={sid}")

    candidates = [
        os.path.join(os.path.dirname(__file__), '..', 'final', 'final8.py'),
        os.path.join(os.path.dirname(__file__), '..', 'final8.py'),
        '/Users/tanmaykadam/Desktop/CS/Hackathon/fusion/final/final8.py',
    ]
    found = None
    for c in candidates:
        cabs = os.path.abspath(os.path.normpath(c))
        if os.path.exists(cabs) and os.path.isfile(cabs):
            found = cabs
            break

    if found:
        try:
            socketio.emit('notification', {'message': f'Launching external script {found}...'}, room=sid)
            proc = subprocess.Popen([sys.executable, found], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            external_processes[sid] = proc
            monitor_thread = threading.Thread(target=_monitor_external_process, args=(proc, sid), daemon=True)
            monitor_thread.start()
            return
        except Exception as e:
            socketio.emit('notification', {'message': f'Failed to launch external script: {e}.'}, room=sid)

    # Fallback: run integrated analysis in a thread
    socketio.emit('notification', {'message': 'Running integrated star analysis (fallback).' }, room=sid)
    analysis_thread = threading.Thread(target=run_star_analysis)
    analysis_thread.start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5508, debug=False)