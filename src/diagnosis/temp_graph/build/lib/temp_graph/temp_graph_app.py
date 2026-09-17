#!/usr/bin/env python3
import os
import json
import time
import threading
import logging
from datetime import datetime

import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy, QoSHistoryPolicy
from sensor_msgs.msg import JointState
from hw_interface.msg import MotorStatusArray
from flask import Flask, jsonify, render_template, request, send_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

BASE_DIR = '/home/thunder/gen2/gen2_full/src/temp_graph'
DATA_DIR = os.path.join(BASE_DIR, 'dataset')
JSON_DIR = os.path.join(DATA_DIR, 'json')
LOG_DIR = os.path.join(DATA_DIR, 'logs')
GRAPH_DIR = os.path.join(DATA_DIR, 'graphs')
ROTATED_DIR = os.path.join(JSON_DIR, 'rotated')
MAX_JSON_AGE_DAYS = 30
SAVE_INTERVAL = 1.0
GESTURE_RECORDINGS_DIR = '/home/thunder/gen2/gen2_full/src/gesture_management/recordings'
RECORDING_SCAN_INTERVAL_S = 5.0

MOTOR_STATUS_TOPICS = [
    '/LeftArmSystem/motor_status',
    '/RightArmSystem/motor_status',
]
JOINT_STATE_TOPICS = [
    '/LeftArmSystem_ordered_joint_states',
    '/RightArmSystem_ordered_joint_states',
]

os.makedirs(JSON_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(GRAPH_DIR, exist_ok=True)
os.makedirs(ROTATED_DIR, exist_ok=True)

MOTOR_STATUS_QOS = QoSProfile(
    depth=10,
    reliability=QoSReliabilityPolicy.RELIABLE,
    durability=QoSDurabilityPolicy.VOLATILE,
    history=QoSHistoryPolicy.KEEP_LAST,
)

LOG_PATH = os.path.join(LOG_DIR, 'events.json')
SESSION_PATH = os.path.join(JSON_DIR, 'session.json')
MOTOR_JSON_PATH = os.path.join(JSON_DIR, 'motor_status.json')
JOINT_JSON_PATH = os.path.join(JSON_DIR, 'joint_states.json')
RECORDING_HISTORY_PATH = os.path.join(JSON_DIR, 'recording_history.json')
GRAPH_HTML_PATH = os.path.join(GRAPH_DIR, 'graph.html')


def now_iso():
    return datetime.now().isoformat(timespec='seconds')


def write_json_atomic(path, data):
    tmp = path + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return default


def rotate_json_files():
    today = datetime.now().date()
    for fn in os.listdir(JSON_DIR):
        if not fn.endswith('.json'):
            continue
        path = os.path.join(JSON_DIR, fn)
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(path)).date()
        except Exception:
            continue
        age = (today - mtime).days
        if age >= MAX_JSON_AGE_DAYS:
            dst = os.path.join(ROTATED_DIR, fn)
            if os.path.exists(dst):
                base, ext = os.path.splitext(fn)
                dst = os.path.join(ROTATED_DIR, f'{base}-{int(time.time())}{ext}')
            os.rename(path, dst)
            log_event(f'Rotated aged JSON file {fn} -> rotated/{os.path.basename(dst)}')


def log_event(message, level='info'):
    entry = {'ts': now_iso(), 'level': level, 'message': message}
    logs = load_json(LOG_PATH, default={'events': []}) or {'events': []}
    logs['events'].append(entry)
    write_json_atomic(LOG_PATH, logs)
    logging.info(message)


class TempGraphNode(Node):
    def __init__(self):
        super().__init__('temp_graph_node')
        self._cb_group = ReentrantCallbackGroup()
        self._motor_lock = threading.Lock()
        self._motor_latest = {}
        self._motor_history = []
        self._joint_latest = {}
        self._joint_history = []
        self._session_start = datetime.now()
        self._last_save = time.time()
        self._init_subscriptions()
        self._save_session()
        self._start_persistence_timer()
        self._start_recording_scanner()

    def _init_subscriptions(self):
        for topic in MOTOR_STATUS_TOPICS:
            try:
                self.create_subscription(
                    MotorStatusArray,
                    topic,
                    lambda msg, topic=topic: self._motor_status_cb(topic, msg),
                    MOTOR_STATUS_QOS,
                    callback_group=self._cb_group,
                )
                log_event(f'Subscribed to motor status topic: {topic}')
            except Exception as e:
                log_event(f'Failed to subscribe to {topic}: {e}', level='warn')
        for topic in JOINT_STATE_TOPICS:
            try:
                self.create_subscription(
                    JointState,
                    topic,
                    lambda msg, topic=topic: self._joint_state_cb(topic, msg),
                    MOTOR_STATUS_QOS,
                    callback_group=self._cb_group,
                )
                log_event(f'Subscribed to joint state topic: {topic}')
            except Exception as e:
                log_event(f'Failed to subscribe to {topic}: {e}', level='warn')

    def _motor_status_cb(self, topic, msg):
        timestamp = self.get_clock().now().nanoseconds / 1e9
        motors = [{
            'arm_name': m.arm_name,
            'id': int(m.id),
            'error': int(m.error),
            'error_name': m.error_name,
            'mos_temp': float(m.mos_temp),
            'rotor_temp': float(m.rotor_temp),
        } for m in msg.motors]
        sample = {
            'timestamp': timestamp,
            'datetime': now_iso(),
            'topic': topic,
            'motors': motors,
        }
        with self._motor_lock:
            self._motor_latest[topic] = sample
            self._motor_history.append(sample)

    def _joint_state_cb(self, topic, msg):
        timestamp = self.get_clock().now().nanoseconds / 1e9
        sample = {
            'timestamp': timestamp,
            'datetime': now_iso(),
            'topic': topic,
            'names': list(msg.name),
            'position': list(msg.position),
            'velocity': list(msg.velocity),
            'effort': list(msg.effort),
        }
        with self._motor_lock:
            self._joint_latest[topic] = sample
            self._joint_history.append(sample)

    def _start_recording_scanner(self):
        def scan_loop():
            seen = set()
            while rclpy.ok():
                try:
                    files = [f for f in os.listdir(GESTURE_RECORDINGS_DIR) if f.endswith('.parquet')]
                except Exception:
                    files = []
                new_files = [f for f in files if f not in seen]
                if new_files:
                    self._save_recording_history(new_files)
                    seen.update(new_files)
                time.sleep(RECORDING_SCAN_INTERVAL_S)
        thread = threading.Thread(target=scan_loop, daemon=True)
        thread.start()

    def _save_recording_history(self, filenames):
        history = load_json(RECORDING_HISTORY_PATH, default={'recordings': []}) or {'recordings': []}
        for fn in filenames:
            history['recordings'].append({'file': fn, 'logged_at': now_iso()})
        write_json_atomic(RECORDING_HISTORY_PATH, history)
        log_event(f'Logged {len(filenames)} recording file(s)')

    def _save_session(self):
        session = {
            'started_at': self._session_start.isoformat(timespec='seconds'),
            'last_updated': now_iso(),
            'duration_s': round((datetime.now() - self._session_start).total_seconds(), 1),
        }
        write_json_atomic(SESSION_PATH, session)

    def _start_persistence_timer(self):
        def tick():
            while rclpy.ok():
                time.sleep(SAVE_INTERVAL)
                self._save_jsons()
        thread = threading.Thread(target=tick, daemon=True)
        thread.start()

    def _save_jsons(self):
        rotate_json_files()
        with self._motor_lock:
            if self._motor_history:
                write_json_atomic(MOTOR_JSON_PATH, {'samples': self._motor_history})
            if self._joint_history:
                write_json_atomic(JOINT_JSON_PATH, {'samples': self._joint_history[-2000:]})
            self._save_session()
            self._write_graph_html()

    def _write_graph_html(self):
        try:
            motor_data = load_json(MOTOR_JSON_PATH, default={'samples': []}) or {'samples': []}
            traces = []
            topics = sorted({sample['topic'] for sample in motor_data['samples']})
            for topic in topics:
                topic_samples = [s for s in motor_data['samples'] if s['topic'] == topic]
                times = [s['datetime'] for s in topic_samples]
                mos = [sum(m['mos_temp'] for m in s['motors']) / max(1, len(s['motors'])) for s in topic_samples]
                rotor = [sum(m['rotor_temp'] for m in s['motors']) / max(1, len(s['motors'])) for s in topic_samples]
                traces.append({'name': f'{topic} MOS', 'x': times, 'y': mos, 'yaxis': 'y1'})
                traces.append({'name': f'{topic} Rotor', 'x': times, 'y': rotor, 'yaxis': 'y2'})
            html = f"""<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8'>
<title>Temp Graph</title>
<script src='https://cdn.plot.ly/plotly-2.37.0.min.js'></script>
<style>body{{margin:20px;font-family:Arial,sans-serif;background:#0f172a;color:#e2e8f0;}}h1{{margin-bottom:12px;}}</style>
</head>
<body>
<h1>Motor Temperature Graph</h1>
<div id='plot' style='width:100%;height:80vh;'></div>
<script>
const data = {json.dumps(traces)};
const layout = {{title:'MOS and Rotor Temperature over Time',xaxis:{{title:'Time'}},yaxis:{{title:'MOS °C',side:'left'}},yaxis2:{{title:'Rotor °C',overlaying:'y',side:'right'}}}};
Plotly.newPlot('plot', data, layout);
</script>
</body>
</html>"""
            with open(GRAPH_HTML_PATH, 'w') as f:
                f.write(html)
        except Exception as e:
            log_event(f'Failed to write graph.html: {e}', level='warn')

    def get_status(self):
        with self._motor_lock:
            return {
                'motor_samples': len(self._motor_history),
                'joint_samples': len(self._joint_history),
                'motor_topics': list(self._motor_latest.keys()),
                'joint_topics': list(self._joint_latest.keys()),
            }


app = Flask(__name__, template_folder='templates', static_folder='static')
node = None


def _require_ros():
    if node is None:
        return jsonify({'success': False, 'message': 'ROS 2 node not started.'}), 503
    return None


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    err = _require_ros()
    if err:
        return err
    return jsonify(node.get_status())


@app.route('/api/session')
def api_session():
    session = load_json(SESSION_PATH, default={}) or {}
    return jsonify(session)


@app.route('/api/logs')
def api_logs():
    logs = load_json(LOG_PATH, default={'events': []}) or {'events': []}
    return jsonify(logs)


@app.route('/api/recordings')
def api_recordings():
    history = load_json(RECORDING_HISTORY_PATH, default={'recordings': []}) or {'recordings': []}
    return jsonify(history)


@app.route('/api/available_topics')
def api_available_topics():
    return jsonify({'topics': MOTOR_STATUS_TOPICS})


@app.route('/api/dataset')
def api_dataset():
    files = []
    for root, _, filenames in os.walk(DATA_DIR):
        for fn in filenames:
            rel = os.path.relpath(os.path.join(root, fn), DATA_DIR)
            files.append(rel)
    return jsonify({'files': sorted(files)})


@app.route('/graph')
def graph_page():
    if not os.path.exists(GRAPH_HTML_PATH):
        return 'Graph data not ready yet', 503
    return send_file(GRAPH_HTML_PATH)


@app.route('/dataset/<path:filename>')
def dataset_file(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return jsonify({'success': False, 'message': 'File not found'}), 404
    return send_file(path)


@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Not found'}), 404


def main():
    global node
    rclpy.init()
    node = TempGraphNode()
    log_event('temp_graph dashboard started')
    try:
        app.run(host='0.0.0.0', port=6060, threaded=True)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
