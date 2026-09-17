#include "camera_page.hpp"
#include <gst/gst.h>
#include <gst/sdp/sdp.h>
#include <gst/webrtc/webrtc.h>
#include <gst/video/video-event.h>

#include <boost/asio.hpp>
#include <boost/beast.hpp>
#include <linux/videodev2.h>
#include <nlohmann/json.hpp>

#include <algorithm>
#include <array>
#include <atomic>
#include <cctype>
#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <mutex>
#include <optional>
#include <set>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#include <arpa/inet.h>
#include <fcntl.h>
#include <ifaddrs.h>
#include <net/if.h>
#include <netinet/in.h>
#include <sys/ioctl.h>
#include <unistd.h>

namespace asio = boost::asio;
namespace beast = boost::beast;
namespace http = beast::http;
namespace websocket = beast::websocket;
using tcp = asio::ip::tcp;
using json = nlohmann::json;

namespace {

constexpr std::array<const char*, 3> kGroups{
    "239.255.42.1", "239.255.42.2", "239.255.42.3"};
constexpr std::array<int, 3> kPorts{5004, 5006, 5008};

int env_int(const char* name, int fallback) {
  if (const char* value = std::getenv(name)) {
    try { return std::stoi(value); } catch (...) {}
  }
  return fallback;
}

std::string env_string(const char* name, const char* fallback) {
  if (const char* value = std::getenv(name); value && *value) return value;
  return fallback;
}

const int kWidth = env_int("STREAM_WIDTH", 1280);
const int kHeight = env_int("STREAM_HEIGHT", 720);
const int kFps = env_int("STREAM_FPS", 30);
const int kBitrateKbps = std::clamp(env_int("STREAM_BITRATE_KBPS", 1800), 100, 20000);
const int kKeyframeInterval = std::clamp(env_int("STREAM_KEYFRAME_INTERVAL", kFps), 1, 300);
const int kWebRtcLatencyMs = std::clamp(env_int("STREAM_WEBRTC_LATENCY_MS", 0), 0, 1000);
const std::string kUdpInterface = env_string("STREAM_UDP_INTERFACE", "lo");

std::vector<std::string> split(const std::string& input, char separator) {
  std::vector<std::string> output;
  std::stringstream stream(input);
  for (std::string item; std::getline(stream, item, separator);) {
    if (!item.empty()) output.push_back(item);
  }
  return output;
}

std::optional<std::string> color_capture_bus(const std::filesystem::path& path) {
  const int fd = ::open(path.c_str(), O_RDONLY | O_NONBLOCK);
  if (fd < 0) return std::nullopt;
  v4l2_capability caps{};
  const bool capture = ::ioctl(fd, VIDIOC_QUERYCAP, &caps) == 0 &&
      ((caps.device_caps ? caps.device_caps : caps.capabilities) & V4L2_CAP_VIDEO_CAPTURE);
  bool yuyv = false;
  if (capture) {
    v4l2_fmtdesc format{};
    format.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    for (format.index = 0; ::ioctl(fd, VIDIOC_ENUM_FMT, &format) == 0; ++format.index) {
      if (format.pixelformat == V4L2_PIX_FMT_YUYV) {
        yuyv = true;
        break;
      }
    }
  }
  ::close(fd);
  if (!capture || !yuyv) return std::nullopt;
  return reinterpret_cast<const char*>(caps.bus_info);
}

std::vector<std::string> discover_devices() {
  if (const char* configured = std::getenv("CAMERA_DEVICES")) {
    auto devices = split(configured, ',');
    if (devices.size() > 3) devices.resize(3);
    return devices;
  }

  std::vector<std::filesystem::path> candidates;
  std::error_code ec;
  for (const auto& entry : std::filesystem::directory_iterator("/dev", ec)) {
    const auto name = entry.path().filename().string();
    if (name.rfind("video", 0) == 0 && name.size() > 5 &&
        std::all_of(name.begin() + 5, name.end(),
                    [](unsigned char character) { return std::isdigit(character) != 0; })) {
      candidates.push_back(entry.path());
    }
  }
  std::sort(candidates.begin(), candidates.end(), [](const auto& left, const auto& right) {
    return std::stoi(left.filename().string().substr(5)) <
           std::stoi(right.filename().string().substr(5));
  });

  std::vector<std::string> devices;
  std::set<std::string> physical_buses;
  for (const auto& candidate : candidates) {
    // Multi-sensor cameras expose depth, infrared, metadata, and color nodes.
    // Select one YUYV color stream per physical USB bus rather than the first
    // three /dev/video nodes.
    const auto bus = color_capture_bus(candidate);
    if (bus && physical_buses.insert(*bus).second) devices.push_back(candidate.string());
    if (devices.size() == 3) break;
  }
  return devices;
}

std::vector<std::string> lan_addresses() {
  std::vector<std::string> addresses;
  ifaddrs* interfaces = nullptr;
  if (::getifaddrs(&interfaces) != 0) return addresses;
  for (ifaddrs* item = interfaces; item; item = item->ifa_next) {
    if (!item->ifa_addr || item->ifa_addr->sa_family != AF_INET ||
        (item->ifa_flags & IFF_LOOPBACK) || !(item->ifa_flags & IFF_UP)) {
      continue;
    }
    char value[INET_ADDRSTRLEN]{};
    const auto* address = reinterpret_cast<const sockaddr_in*>(item->ifa_addr);
    if (::inet_ntop(AF_INET, &address->sin_addr, value, sizeof(value))) {
      addresses.emplace_back(value);
    }
  }
  ::freeifaddrs(interfaces);
  std::sort(addresses.begin(), addresses.end());
  addresses.erase(std::unique(addresses.begin(), addresses.end()), addresses.end());
  return addresses;
}

class CameraStream {
 public:
  CameraStream(int index, std::optional<std::string> device)
      : index_(index), device_(std::move(device)) {}

  ~CameraStream() { stop(); }
  CameraStream(const CameraStream&) = delete;
  CameraStream& operator=(const CameraStream&) = delete;

  bool start() {
    std::lock_guard lock(mutex_);
    if (pipeline_) return true;
    if (!device_ || !std::filesystem::exists(*device_)) {
      error_ = "Camera device not found";
      return false;
    }

    std::ostringstream description;
    description
        << "v4l2src device=" << *device_ << " do-timestamp=true "
        << "! video/x-raw,format=YUY2,framerate=" << kFps << "/1 "
        // Discard old whole frames before conversion/encoding under load.
        // Dropping packets after encoding corrupts reference frames instead.
        << "! queue leaky=downstream max-size-buffers=1 max-size-bytes=0 max-size-time=0 "
        << "! videoconvert ! videoscale add-borders=true "
        << "! video/x-raw,format=I420,width=" << kWidth << ",height=" << kHeight
        << ",pixel-aspect-ratio=1/1 "
        << "! x264enc name=encoder tune=zerolatency speed-preset=ultrafast "
        << "bitrate=" << kBitrateKbps << " key-int-max=" << kKeyframeInterval << ' '
        << "bframes=0 rc-lookahead=0 sync-lookahead=0 sliced-threads=true threads=2 "
        << "byte-stream=true cabac=false vbv-buf-capacity=100 "
        << "! video/x-h264,profile=constrained-baseline,stream-format=byte-stream,alignment=au "
        << "! rtph264pay name=rtp_pay pt=96 config-interval=-1 aggregate-mode=zero-latency mtu=1200 "
        << "! udpsink host=" << group() << " port=" << port()
        << " multicast-iface=" << kUdpInterface
        << " auto-multicast=true ttl-mc=1 sync=false async=false";

    GError* gst_error = nullptr;
    pipeline_ = gst_parse_launch(description.str().c_str(), &gst_error);
    if (gst_error || !pipeline_) {
      error_ = gst_error ? gst_error->message : "Unable to create GStreamer pipeline";
      if (gst_error) g_error_free(gst_error);
      if (pipeline_) gst_object_unref(pipeline_);
      pipeline_ = nullptr;
      return false;
    }
    const auto state_change = gst_element_set_state(pipeline_, GST_STATE_PLAYING);
    GstState current = GST_STATE_NULL;
    const auto settled = state_change == GST_STATE_CHANGE_FAILURE
        ? GST_STATE_CHANGE_FAILURE
        : gst_element_get_state(pipeline_, &current, nullptr, 3 * GST_SECOND);
    if (settled == GST_STATE_CHANGE_FAILURE) {
      GstBus* bus = gst_element_get_bus(pipeline_);
      GstMessage* message = gst_bus_pop_filtered(bus, GST_MESSAGE_ERROR);
      if (message) {
        GError* error = nullptr;
        gchar* debug = nullptr;
        gst_message_parse_error(message, &error, &debug);
        error_ = error ? error->message : "Camera pipeline negotiation failed";
        if (error) g_error_free(error);
        g_free(debug);
        gst_message_unref(message);
      } else {
        error_ = "Camera pipeline could not enter PLAYING state";
      }
      gst_object_unref(bus);
      gst_element_set_state(pipeline_, GST_STATE_NULL);
      gst_object_unref(pipeline_);
      pipeline_ = nullptr;
      return false;
    }
    error_.clear();
    return true;
  }

  void stop() {
    std::lock_guard lock(mutex_);
    if (!pipeline_) return;
    gst_element_set_state(pipeline_, GST_STATE_NULL);
    gst_object_unref(pipeline_);
    pipeline_ = nullptr;
  }

  json status() const {
    std::lock_guard lock(mutex_);
    GstState state = GST_STATE_NULL;
    if (pipeline_) gst_element_get_state(pipeline_, &state, nullptr, 0);
    return {
        {"id", index_},
        {"name", "Camera " + (index_ < 9 ? std::string("0") : "") + std::to_string(index_ + 1)},
        {"device", device_ ? json(*device_) : json(nullptr)},
        {"udp", group() + ":" + std::to_string(port())},
        {"available", device_ && std::filesystem::exists(*device_)},
        {"running", pipeline_ && (state == GST_STATE_PLAYING || state == GST_STATE_PAUSED)},
        {"error", error_.empty() ? json(nullptr) : json(error_)},
        {"keyframeRequests", keyframe_requests_.load()},
    };
  }

  int index() const { return index_; }
  int port() const { return kPorts[index_]; }
  std::string group() const { return kGroups[index_]; }

  void request_keyframe() {
    GstElement* encoder = nullptr;
    {
      std::lock_guard lock(mutex_);
      // Several viewers may request recovery simultaneously; avoid IDR storms.
      const gint64 now = g_get_monotonic_time();
      if (!pipeline_ || now - last_keyframe_request_ < 250000) return;
      encoder = gst_bin_get_by_name(GST_BIN(pipeline_), "encoder");
      if (!encoder) return;
      last_keyframe_request_ = now;
    }
    // Producer and viewer pipelines use different running times. Request the
    // next available frame, instead of forwarding the viewer's timestamp.
    if (gst_element_send_event(encoder, gst_video_event_new_upstream_force_key_unit(
            GST_CLOCK_TIME_NONE, TRUE, 0))) {
      ++keyframe_requests_;
    }
    gst_object_unref(encoder);
  }

  std::string rtp_caps() const {
    std::lock_guard lock(mutex_);
    if (!pipeline_) return {};
    GstElement* payloader = gst_bin_get_by_name(GST_BIN(pipeline_), "rtp_pay");
    if (!payloader) return {};
    GstPad* pad = gst_element_get_static_pad(payloader, "src");
    GstCaps* caps = gst_pad_get_current_caps(pad);
    std::string result;
    if (caps) {
      // Preserve the encoder's actual H.264 profile/level, packetization mode,
      // SPS/PPS and SSRC in WebRTC signaling; do not guess codec parameters.
      gchar* value = gst_caps_to_string(caps);
      result = value;
      g_free(value);
      gst_caps_unref(caps);
    }
    gst_object_unref(pad);
    gst_object_unref(payloader);
    return result;
  }

 private:
  int index_;
  std::optional<std::string> device_;
  GstElement* pipeline_ = nullptr;
  std::string error_;
  gint64 last_keyframe_request_ = 0;
  std::atomic_uint keyframe_requests_{0};
  mutable std::mutex mutex_;
};

std::array<std::unique_ptr<CameraStream>, 3> cameras;
bool webrtc_ready = false;

class WebRtcSession {
 public:
  WebRtcSession(tcp::socket socket, CameraStream& camera)
      : ws_(std::move(socket)), camera_(camera) {}

  void run(http::request<http::string_body> request) {
    beast::error_code ec;
    ws_.set_option(websocket::stream_base::timeout::suggested(beast::role_type::server));
    ws_.set_option(websocket::stream_base::decorator([](websocket::response_type& response) {
      response.set(http::field::server, "VIVEKA/1.0");
    }));
    ws_.accept(request, ec);
    if (ec) return;

    if (!webrtc_ready) {
      send({{"type", "error"}, {"message", "GStreamer webrtcbin plugin is unavailable"}});
      close();
      return;
    }

    if (!camera_.start()) {
      send({{"type", "error"}, {"message", "Camera pipeline failed to start"}});
      close();
      return;
    }
    if (!create_pipeline()) {
      close();
      return;
    }

    gst_element_set_state(pipeline_, GST_STATE_PLAYING);
    beast::flat_buffer buffer;
    while (!stopped_) {
      buffer.clear();
      ws_.read(buffer, ec);
      if (ec) break;
      try {
        const auto message = json::parse(beast::buffers_to_string(buffer.data()));
        if (message.value("type", "") == "answer") {
          apply_answer(message.at("sdp").get<std::string>());
        } else if (message.value("type", "") == "ice" && message.contains("candidate")) {
          const int line = message.value("sdpMLineIndex", 0);
          const auto candidate = message.at("candidate").get<std::string>();
          g_signal_emit_by_name(webrtc_, "add-ice-candidate", line, candidate.c_str());
        }
      } catch (const std::exception& error) {
        send({{"type", "error"}, {"message", std::string("Bad signaling message: ") + error.what()}});
      }
    }
    close();
  }

 private:
  static void negotiation_needed(GstElement*, gpointer user_data) {
    auto* self = static_cast<WebRtcSession*>(user_data);
    GstPromise* promise = gst_promise_new_with_change_func(offer_created, self, nullptr);
    g_signal_emit_by_name(self->webrtc_, "create-offer", nullptr, promise);
  }

  static void offer_created(GstPromise* promise, gpointer user_data) {
    auto* self = static_cast<WebRtcSession*>(user_data);
    if (self->stopped_) {
      gst_promise_unref(promise);
      return;
    }
    const GstStructure* reply = gst_promise_get_reply(promise);
    GstWebRTCSessionDescription* offer = nullptr;
    gst_structure_get(reply, "offer", GST_TYPE_WEBRTC_SESSION_DESCRIPTION, &offer, nullptr);
    gst_promise_unref(promise);
    if (!offer) {
      self->send({{"type", "error"}, {"message", "Could not create WebRTC offer"}});
      return;
    }

    GstPromise* local = gst_promise_new();
    g_signal_emit_by_name(self->webrtc_, "set-local-description", offer, local);
    gst_promise_interrupt(local);
    gst_promise_unref(local);
    gchar* text = gst_sdp_message_as_text(offer->sdp);
    self->send({{"type", "offer"}, {"sdp", text}});
    g_free(text);
    gst_webrtc_session_description_free(offer);
  }

  static void ice_candidate(GstElement*, guint line, gchar* candidate, gpointer user_data) {
    auto* self = static_cast<WebRtcSession*>(user_data);
    self->send({{"type", "ice"}, {"candidate", candidate}, {"sdpMLineIndex", line}});
  }

  bool create_pipeline() {
    // A live pipeline can reach PLAYING before the first encoded buffer sets
    // the RTP caps. A browser opened during service startup must wait for those
    // real caps rather than fail intermittently or negotiate a guessed profile.
    std::string caps;
    for (int attempt = 0; attempt < 60; ++attempt) {
      caps = camera_.rtp_caps();
      if (!caps.empty()) break;
      std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
    if (caps.empty()) {
      send({{"type", "error"}, {"message", "Camera has not produced an H.264 stream yet; reconnect to retry"}});
      return false;
    }
    gchar* escaped_caps = g_strescape(caps.c_str(), nullptr);
    std::ostringstream description;
    description << "udpsrc name=rtp_source address=" << camera_.group() << " port=" << camera_.port()
                << " multicast-iface=" << kUdpInterface
                << " auto-multicast=true buffer-size=131072 caps=\"" << escaped_caps << "\" "
                // Do not use a tiny leaky RTP queue: an IDR spans many packets.
                << "! webrtcbin name=peer bundle-policy=max-bundle latency=" << kWebRtcLatencyMs;
    g_free(escaped_caps);
    GError* error = nullptr;
    pipeline_ = gst_parse_launch(description.str().c_str(), &error);
    if (error || !pipeline_) {
      send({{"type", "error"}, {"message", error ? error->message : "WebRTC pipeline failed"}});
      if (error) g_error_free(error);
      return false;
    }
    webrtc_ = gst_bin_get_by_name(GST_BIN(pipeline_), "peer");
    if (!webrtc_) {
      send({{"type", "error"}, {"message", "GStreamer did not create webrtcbin"}});
      return false;
    }
    g_signal_connect(webrtc_, "on-negotiation-needed", G_CALLBACK(negotiation_needed), this);
    g_signal_connect(webrtc_, "on-ice-candidate", G_CALLBACK(ice_candidate), this);
    // The shared CameraStream outlives every peer. Carry recovery requests
    // across the UDP boundary so loss does not wait for the periodic keyframe.
    g_signal_connect(webrtc_, "notify::connection-state", G_CALLBACK(connection_state_changed), &camera_);
    GstElement* source = gst_bin_get_by_name(GST_BIN(pipeline_), "rtp_source");
    GstPad* source_pad = gst_element_get_static_pad(source, "src");
    gst_pad_add_probe(source_pad, GST_PAD_PROBE_TYPE_EVENT_UPSTREAM, keyframe_feedback, &camera_, nullptr);
    gst_object_unref(source_pad);
    gst_object_unref(source);
    return true;
  }

  static GstPadProbeReturn keyframe_feedback(GstPad*, GstPadProbeInfo* info, gpointer data) {
    GstEvent* event = GST_PAD_PROBE_INFO_EVENT(info);
    if (event && gst_video_event_is_force_key_unit(event)) {
      static_cast<CameraStream*>(data)->request_keyframe();
      return GST_PAD_PROBE_DROP;
    }
    return GST_PAD_PROBE_OK;
  }

  static void connection_state_changed(GObject* object, GParamSpec*, gpointer data) {
    GstWebRTCPeerConnectionState state;
    g_object_get(object, "connection-state", &state, nullptr);
    if (state == GST_WEBRTC_PEER_CONNECTION_STATE_CONNECTED) {
      static_cast<CameraStream*>(data)->request_keyframe();
    }
  }

  void apply_answer(const std::string& text) {
    GstSDPMessage* sdp = nullptr;
    if (gst_sdp_message_new(&sdp) != GST_SDP_OK ||
        gst_sdp_message_parse_buffer(reinterpret_cast<const guint8*>(text.data()), text.size(), sdp) != GST_SDP_OK) {
      if (sdp) gst_sdp_message_free(sdp);
      send({{"type", "error"}, {"message", "Invalid WebRTC answer"}});
      return;
    }
    auto* answer = gst_webrtc_session_description_new(GST_WEBRTC_SDP_TYPE_ANSWER, sdp);
    GstPromise* promise = gst_promise_new();
    g_signal_emit_by_name(webrtc_, "set-remote-description", answer, promise);
    gst_promise_interrupt(promise);
    gst_promise_unref(promise);
    gst_webrtc_session_description_free(answer);
  }

  void send(const json& message) {
    std::lock_guard lock(write_mutex_);
    if (stopped_) return;
    beast::error_code ec;
    const auto body = message.dump();
    ws_.text(true);
    ws_.write(asio::buffer(body), ec);
    if (ec) stopped_ = true;
  }

  void close() {
    stopped_ = true;
    if (closed_.exchange(true)) return;
    if (webrtc_) g_signal_handlers_disconnect_by_data(webrtc_, this);
    if (pipeline_) {
      gst_element_set_state(pipeline_, GST_STATE_NULL);
      if (webrtc_) gst_object_unref(webrtc_);
      gst_object_unref(pipeline_);
      webrtc_ = nullptr;
      pipeline_ = nullptr;
    }
    std::lock_guard lock(write_mutex_);
    beast::error_code ec;
    ws_.close(websocket::close_code::normal, ec);
  }

  websocket::stream<tcp::socket> ws_;
  CameraStream& camera_;
  GstElement* pipeline_ = nullptr;
  GstElement* webrtc_ = nullptr;
  std::atomic_bool stopped_{false};
  std::atomic_bool closed_{false};
  std::mutex write_mutex_;
};

http::response<http::string_body> response(http::status status, std::string body,
                                           std::string content_type, int version) {
  http::response<http::string_body> result{status, version};
  result.set(http::field::server, "VIVEKA/1.0");
  result.set(http::field::content_type, content_type);
  result.set(http::field::cache_control, "no-cache");
  result.body() = std::move(body);
  result.prepare_payload();
  return result;
}

json status_payload() {
  json list = json::array();
  for (const auto& camera : cameras) list.push_back(camera->status());
  return {
      {"cameras", list},
      {"gateway", {{"ready", webrtc_ready}, {"gstreamer", true},
                   {"message", webrtc_ready ? json(nullptr)
                                              : json("GStreamer WebRTC plugin is not installed")}}},
      {"video", {{"width", kWidth}, {"height", kHeight}, {"fps", kFps},
                 {"codec", "H264"}, {"bitrateKbps", kBitrateKbps},
                 {"keyframeInterval", kKeyframeInterval}, {"webrtcLatencyMs", kWebRtcLatencyMs},
                 {"udpInterface", kUdpInterface}}},
  };
}

std::optional<int> camera_id_from_target(const std::string& target, const std::string& prefix) {
  if (target.rfind(prefix, 0) != 0) return std::nullopt;
  try {
    const int id = std::stoi(target.substr(prefix.size()));
    if (id >= 0 && id < 3) return id;
  } catch (...) {}
  return std::nullopt;
}

void serve_http(tcp::socket socket) {
  beast::flat_buffer buffer;
  http::request<http::string_body> request;
  beast::error_code ec;
  http::read(socket, buffer, request, ec);
  if (ec) return;
  const std::string target(request.target());

  if (websocket::is_upgrade(request)) {
    if (auto id = camera_id_from_target(target, "/ws/")) {
      WebRtcSession(std::move(socket), *cameras[*id]).run(std::move(request));
      return;
    }
  }

  http::response<http::string_body> result;
  if (request.method() == http::verb::get && target == "/api/status") {
    result = response(http::status::ok, status_payload().dump(), "application/json", request.version());
  } else if (request.method() == http::verb::post) {
    const std::string prefix = "/api/cameras/";
    const std::string suffix = "/start";
    auto middle = target;
    if (middle.rfind(prefix, 0) == 0 && middle.size() > prefix.size() + suffix.size() &&
        middle.substr(middle.size() - suffix.size()) == suffix) {
      middle = middle.substr(0, middle.size() - suffix.size());
      if (auto id = camera_id_from_target(middle, prefix)) {
        cameras[*id]->start();
        result = response(http::status::ok, cameras[*id]->status().dump(), "application/json", request.version());
      } else {
        result = response(http::status::not_found, "Not found", "text/plain", request.version());
      }
    } else {
      result = response(http::status::not_found, "Not found", "text/plain", request.version());
    }
  } else if (request.method() == http::verb::get && target == "/") {
    result = response(http::status::ok, kCameraPage, "text/html; charset=utf-8", request.version());
  } else {
    result = response(http::status::not_found, "Not found", "text/plain", request.version());
  }
  result.keep_alive(false);
  http::write(socket, result, ec);
  socket.shutdown(tcp::socket::shutdown_send, ec);
}

}  // namespace

int main(int argc, char** argv) {
  // ROS launch appends remapping arguments; this native server is not a ROS node.
  for (int i = 1; i < argc; ++i) {
    if (std::string(argv[i]) == "--ros-args") { argc = i; argv[i] = nullptr; break; }
  }
  gst_init(&argc, &argv);
  GstElementFactory* webrtc_factory = gst_element_factory_find("webrtcbin");
  if (!webrtc_factory) {
    std::cerr << "Warning: missing webrtcbin; camera streaming is unavailable.\n";
  } else {
    webrtc_ready = true;
    gst_object_unref(webrtc_factory);
  }

  // 8080 is commonly occupied by ROS web_video_server on robotics devices.
  const int port = env_int("STREAM_PORT", 7002);
  const std::string host = env_string("STREAM_HOST", "0.0.0.0");
  try {
    asio::io_context context{1};
    const auto bind_address = asio::ip::make_address_v4(host);
    tcp::acceptor acceptor(context);
    acceptor.open(tcp::v4());
    acceptor.set_option(asio::socket_base::reuse_address(true));
    acceptor.bind({bind_address, static_cast<unsigned short>(port)});
    acceptor.listen(asio::socket_base::max_listen_connections);
  const auto devices = discover_devices();
  for (int index = 0; index < 3; ++index) {
    std::optional<std::string> device;
    if (static_cast<std::size_t>(index) < devices.size()) device = devices[index];
    cameras[index] = std::make_unique<CameraStream>(index, std::move(device));
    cameras[index]->start();
  }


    std::cout << "VIVEKA C++ camera UI listening on " << host << ':' << port << "\n";
    std::cout << "Local URL: http://localhost:" << port << "\n";
    if (bind_address == asio::ip::address_v4::any()) {
      for (const auto& address : lan_addresses()) {
        std::cout << "LAN URL:   http://" << address << ':' << port << "\n";
      }
    } else if (!bind_address.is_loopback()) {
      std::cout << "LAN URL:   http://" << host << ':' << port << "\n";
    }
    std::cout << "Detected " << devices.size() << " capture device(s)\n";
    while (true) {
      tcp::socket socket(context);
      acceptor.accept(socket);
      std::thread(serve_http, std::move(socket)).detach();
    }
  } catch (const std::exception& error) {
    std::cerr << "Server error: " << error.what() << '\n';
    return 1;
  }
}
