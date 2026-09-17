#!/usr/bin/env python3
"""Check the compiled server without opening cameras or disturbing TriView."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import build_opener, ProxyHandler

binary = Path(sys.argv[1]).resolve()
with socket.socket() as probe:
    probe.bind(('127.0.0.1', 0))
    port = probe.getsockname()[1]
env = dict(os.environ, STREAM_HOST='127.0.0.1', STREAM_PORT=str(port), CAMERA_DEVICES='')
http = build_opener(ProxyHandler({}))
base = f'http://127.0.0.1:{port}'
with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryFile() as log:
    process = subprocess.Popen([str(binary), '--ros-args', '-r', '__node:=viveka_test'],
                               cwd=cwd, env=env, stdout=log, stderr=log)
    try:
        for attempt in range(50):
            if process.poll() is not None:
                raise RuntimeError('Native server exited during startup')
            try:
                with http.open(base, timeout=1) as response:
                    html = response.read().decode()
                    assert response.status == 200
                    assert response.headers['Server'] == 'VIVEKA/1.0'
                break
            except URLError:
                time.sleep(0.1)
        else:
            raise RuntimeError('Native server did not start')
        assert html.count('<video ') == 4
        assert 'const gateway = location.origin;' in html
        assert '%%GATEWAY_JSON%%' not in html
        assert 'top:-50%;width:200%;height:200%' in html
        with http.open(base + '/api/status', timeout=2) as response:
            status = json.load(response)
        assert len(status['cameras']) == 3
        assert all(not camera['running'] for camera in status['cameras'])
        try:
            http.open(base + '/missing', timeout=2)
            raise AssertionError('Unknown route did not return 404')
        except HTTPError as error:
            assert error.code == 404
        duplicate = subprocess.run([str(binary)], cwd=cwd, env=env,
                                   capture_output=True, timeout=10)
        assert duplicate.returncode != 0
        assert b'Address already in use' in duplicate.stderr
        print('PASS: embedded four-frame UI, same-origin gateway, API, ROS arguments, 404, duplicate-port rejection')
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
