# Native VIVEKA camera UI

A single C++17 executable captures three V4L2 cameras, encodes H.264 with
GStreamer, negotiates WebRTC, and serves the camera-only UI on port 7002.
No Python server or separate TriView process is required. HTML/JavaScript is
embedded in the executable at build time and runs in the viewer's browser.

The equal 2×2 grid shows the first camera's stereo left/right views above the
two arm cameras. The stereo display crops the padding in the gateway's current
1280×720 letterboxed side-by-side input. Double-click a panel for fullscreen.

From `/home/s1/.ihub/.final_gen2`:

```bash
cmake -S src/ui/Clients_UI/daksha_ui/camera_cpp -B build/viveka_camera_native -DCMAKE_BUILD_TYPE=Release
cmake --build build/viveka_camera_native -j2
./build/viveka_camera_native/viveka_camera_ui
```

Open http://192.168.11.200:7002 (or any printed LAN address). Stop the old
Python camera UI and TriView before launching: only one gateway should own the
camera devices and internal UDP channels. Ctrl+C stops the native program.

The native executable is also built and installed by the `daksha_ui` ROS
package; `client_ui.launch.py` selects it for the camera UI. The other dashboard
applications remain unchanged. The legacy Python camera script remains available.

Dependencies on Ubuntu:

```bash
sudo apt install build-essential cmake pkg-config libboost-dev nlohmann-json3-dev \
  libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly gstreamer1.0-nice
```

Settings are inherited from the TriView backend: `STREAM_HOST` (0.0.0.0),
`STREAM_PORT` (7002), `CAMERA_DEVICES` (auto-discovery, or a comma-separated list
in stereo/arm/arm order), `STREAM_WIDTH` (1280), `STREAM_HEIGHT` (720),
`STREAM_FPS` (30), `STREAM_BITRATE_KBPS` (1800), `STREAM_KEYFRAME_INTERVAL` (30),
`STREAM_WEBRTC_LATENCY_MS` (0), and `STREAM_UDP_INTERFACE` (lo).

For example:

```bash
CAMERA_DEVICES=/dev/video0,/dev/video6,/dev/video12 ./build/viveka_camera_native/viveka_camera_ui
```

Edit `static/index.html` to change the browser UI, then rebuild. CMake embeds
that file into the binary; no runtime static-file path is needed. The backend
in `src/main.cpp` is adapted from the local `/home/s1/.ihub/camera` TriView source.

A camera-free server smoke check can run alongside an existing gateway:

```bash
python3 src/ui/Clients_UI/daksha_ui/camera_cpp/tests/smoke.py build/viveka_camera_native/viveka_camera_ui
```

Python is only used by this optional test. The test checks the embedded page,
API, ROS launch arguments, unknown routes and duplicate-port handling; it does
not verify browser video decoding.
