// C++ port of vcan_bridge.py.
//
// Bridges a CANalyst-II USB-CAN adapter (2 physical channels) to two Linux
// SocketCAN vcan interfaces (vcan0, vcan1), so the rest of the stack can
// talk to vcan0/vcan1 exactly as it does today.
//
// This IS built (see hw_interface/CMakeLists.txt) and IS the default bridge
// launched by gen2/launch/bringup.launch.py (use_cpp_vcan_bridge:=true). Run
// it manually only for standalone debugging, e.g.:
//
//   g++ -std=c++17 -O2 -o vcan_bridge vcan_bridge.cpp -lusb-1.0 -lpthread
//   sudo VCAN_SUDO_PASSWORD=yourpassword ./vcan_bridge
//
// (Or run as a user with passwordless sudo for `modprobe`/`ip link`, in
// which case VCAN_SUDO_PASSWORD can be left unset.)
//
// Protocol reference: the "canalystii" PyPI package (device.py / protocol.py),
// which is itself a reverse-engineered description of the CANalyst-II's raw
// USB bulk-transfer protocol.

#include <libusb-1.0/libusb.h>
#include <linux/can.h>
#include <linux/can/raw.h>
#include <net/if.h>
#include <poll.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <unistd.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <csignal>
#include <map>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

// =========================================================
// CANalyst-II USB protocol
// =========================================================

namespace canalystii {

constexpr uint16_t USB_VENDOR_ID = 0x04D8;
constexpr uint16_t USB_PRODUCT_ID = 0x0053;

constexpr uint32_t COMMAND_INIT = 0x1;
constexpr uint32_t COMMAND_START = 0x2;
constexpr uint32_t COMMAND_STOP = 0x3;
constexpr uint32_t COMMAND_MESSAGE_STATUS = 0x0A;

// Command EP for channels 0, 1
constexpr int CHANNEL_TO_COMMAND_EP[2] = {2, 4};
// CAN message EP for channels 0, 1
constexpr int CHANNEL_TO_MESSAGE_EP[2] = {1, 3};

#pragma pack(push, 1)

struct Message {
  uint32_t can_id{0};
  uint32_t timestamp{0};
  int8_t time_flag{1};
  int8_t send_type{0};
  uint8_t remote{0};
  uint8_t extended{0};
  uint8_t data_len{8};
  uint8_t data[8]{};
};
static_assert(sizeof(Message) == 0x15, "Message must be packed to 21 bytes");

struct MessageBuffer {
  int8_t count{0};
  Message messages[3]{};
};
static_assert(sizeof(MessageBuffer) == 0x40, "MessageBuffer must be packed to 64 bytes");

struct SimpleCommand {
  uint32_t command{0};
  uint32_t padding[15]{};
  SimpleCommand() = default;
  explicit SimpleCommand(uint32_t cmd) : command(cmd) {}
};
static_assert(sizeof(SimpleCommand) == 0x40, "SimpleCommand must be packed to 64 bytes");

struct InitCommand {
  uint32_t command{COMMAND_INIT};
  uint32_t acc_code{0x1};
  uint32_t acc_mask{0xFFFFFFFF};
  uint32_t unknown0{0};
  uint32_t filter{0x1};
  uint32_t unknown1{0};
  uint32_t timing0{0};
  uint32_t timing1{0};
  uint32_t mode{0};
  uint32_t unknown2{0x1};
  uint32_t padding[6]{};
};
static_assert(sizeof(InitCommand) == 0x40, "InitCommand must match SimpleCommand size");

struct MessageStatusResponse {
  uint32_t command{0};
  uint32_t rx_pending{0};
  uint16_t tx_pending{0};
  uint16_t unknown{0};
  uint32_t padding[13]{};
};
static_assert(sizeof(MessageStatusResponse) == 0x40, "MessageStatusResponse must be 64 bytes");

#pragma pack(pop)

// Bitrate -> (BTR0, BTR1)
const std::map<uint32_t, std::pair<uint32_t, uint32_t>> kTimings = {
    {5000, {0xBF, 0xFF}},   {10000, {0x31, 0x1C}},  {20000, {0x18, 0x1C}},
    {33330, {0x09, 0x6F}},  {40000, {0x87, 0xFF}},  {50000, {0x09, 0x1C}},
    {66660, {0x04, 0x6F}},  {80000, {0x83, 0xFF}},  {83330, {0x03, 0x6F}},
    {100000, {0x04, 0x1C}}, {125000, {0x03, 0x1C}}, {200000, {0x81, 0xFA}},
    {250000, {0x01, 0x1C}}, {400000, {0x80, 0xFA}}, {500000, {0x00, 0x1C}},
    {666000, {0x80, 0xB6}}, {800000, {0x00, 0x16}}, {1000000, {0x00, 0x14}},
};

class CanalystDevice {
 public:
  explicit CanalystDevice(int device_index = 0) {
    if (libusb_init(&ctx_) < 0) {
      throw std::runtime_error("libusb_init failed");
    }

    libusb_device** list = nullptr;
    ssize_t count = libusb_get_device_list(ctx_, &list);
    libusb_device* target = nullptr;
    int seen = 0;

    for (ssize_t i = 0; i < count; i++) {
      libusb_device_descriptor desc{};
      if (libusb_get_device_descriptor(list[i], &desc) != 0) continue;

      if (desc.idVendor == USB_VENDOR_ID && desc.idProduct == USB_PRODUCT_ID) {
        if (seen == device_index) {
          target = list[i];
          break;
        }
        seen++;
      }
    }

    if (!target) {
      libusb_free_device_list(list, 1);
      throw std::runtime_error("No CANalyst-II USB device found");
    }

    int rc = libusb_open(target, &handle_);
    libusb_free_device_list(list, 1);

    if (rc != 0) {
      throw std::runtime_error(std::string("Failed to open CANalyst-II device: ") +
                                libusb_error_name(rc));
    }

    // Only (re-)issue SET_CONFIGURATION when the device isn't already on
    // configuration 1 (mirrors the working Python reference, which checks
    // get_active_configuration() first). Forcing a redundant SET_CONFIGURATION
    // on a device that's already configured resets its internal endpoint
    // state on this firmware and was reliably causing the very next bulk
    // write to fail with LIBUSB_ERROR_IO.
    int current_config = -1;
    libusb_get_configuration(handle_, &current_config);
    if (current_config != 1) {
      libusb_set_configuration(handle_, 1);
    }

    if (libusb_kernel_driver_active(handle_, 0) == 1) {
      libusb_detach_kernel_driver(handle_, 0);
    }

    rc = libusb_claim_interface(handle_, 0);
    if (rc != 0) {
      libusb_close(handle_);
      throw std::runtime_error(std::string("Failed to claim CANalyst-II interface: ") +
                                libusb_error_name(rc));
    }
  }

  ~CanalystDevice() {
    if (handle_) {
      // The Python reference (canalystii's CanalystDevice.__del__) does a
      // full USB port reset before releasing the device, noting that
      // without it the device firmware is left in a state that makes the
      // *next* open's first bulk transfer fail. This port never did that,
      // so repeated launch/crash/relaunch cycles progressively wedge the
      // adapter (first as LIBUSB_ERROR_IO, then LIBUSB_ERROR_TIMEOUT on the
      // first command write of the next run) until it's power-cycled.
      libusb_reset_device(handle_);
      libusb_release_interface(handle_, 0);
      libusb_close(handle_);
    }
    if (ctx_) {
      libusb_exit(ctx_);
    }
  }

  CanalystDevice(const CanalystDevice&) = delete;
  CanalystDevice& operator=(const CanalystDevice&) = delete;

  void init(int channel, uint32_t bitrate) {
    auto it = kTimings.find(bitrate);
    if (it == kTimings.end()) {
      throw std::runtime_error("Unsupported bitrate " + std::to_string(bitrate));
    }

    InitCommand cmd{};
    cmd.timing0 = it->second.first;
    cmd.timing1 = it->second.second;

    send_command(channel, &cmd, sizeof(cmd));
    initialized_[channel] = true;
    start(channel);
  }

  void start(int channel) {
    SimpleCommand cmd(COMMAND_START);
    send_command(channel, &cmd, sizeof(cmd));
    started_[channel] = true;
  }

  void stop(int channel) {
    SimpleCommand cmd(COMMAND_STOP);
    send_command(channel, &cmd, sizeof(cmd));
    started_[channel] = false;
  }

  // Poll the device for pending RX messages on `channel` (non-blocking:
  // returns immediately if nothing is pending).
  std::vector<Message> receive(int channel) {
    std::vector<Message> result;
    if (!started_[channel]) return result;

    SimpleCommand status_cmd(COMMAND_MESSAGE_STATUS);
    MessageStatusResponse status{};
    send_command(channel, &status_cmd, sizeof(status_cmd), &status, sizeof(status));

    if (status.rx_pending == 0) return result;

    const int rx_buffer_num = (static_cast<int>(status.rx_pending) + 2) / 3 + 1;
    const int rx_buffer_size = rx_buffer_num * static_cast<int>(sizeof(MessageBuffer));

    std::vector<uint8_t> rx_data(rx_buffer_size);
    int actual = 0;
    const int ep = CHANNEL_TO_MESSAGE_EP[channel] | 0x80;

    int rc = libusb_bulk_transfer(handle_, ep, rx_data.data(), rx_buffer_size, &actual, 1000);
    if (rc != 0 && rc != LIBUSB_ERROR_TIMEOUT) {
      throw std::runtime_error(std::string("USB message read failed: ") + libusb_error_name(rc));
    }

    const int num_buffers = actual / static_cast<int>(sizeof(MessageBuffer));
    for (int i = 0; i < num_buffers; i++) {
      MessageBuffer buf{};
      std::memcpy(&buf, rx_data.data() + i * sizeof(MessageBuffer), sizeof(MessageBuffer));
      const int cnt = std::min<int>(std::max<int>(buf.count, 0), 3);
      for (int m = 0; m < cnt; m++) result.push_back(buf.messages[m]);
    }
    return result;
  }

  void send(int channel, const std::vector<Message>& messages) {
    if (!started_[channel] || messages.empty()) return;

    const int tx_buffer_num = (static_cast<int>(messages.size()) + 2) / 3;
    std::vector<MessageBuffer> buffers(tx_buffer_num);

    for (size_t idx = 0; idx < messages.size(); idx++) {
      const int buf_idx = static_cast<int>(idx) / 3;
      buffers[buf_idx].messages[idx % 3] = messages[idx];
      buffers[buf_idx].count++;
    }

    const int ep = CHANNEL_TO_MESSAGE_EP[channel];
    int actual = 0;
    libusb_bulk_transfer(handle_, ep, reinterpret_cast<uint8_t*>(buffers.data()),
                          static_cast<int>(buffers.size() * sizeof(MessageBuffer)), &actual, 1000);
  }

 private:
  void send_command(int channel, const void* packet, int packet_len, void* response = nullptr,
                     int response_len = 0) {
    const int ep_out = CHANNEL_TO_COMMAND_EP[channel];
    int actual = 0;

    int rc = libusb_bulk_transfer(handle_, ep_out,
                                   const_cast<uint8_t*>(static_cast<const uint8_t*>(packet)),
                                   packet_len, &actual, 1000);
    if (rc != 0) {
      throw std::runtime_error(std::string("USB command write failed: ") + libusb_error_name(rc));
    }

    if (response) {
      const int ep_in = ep_out | 0x80;
      uint8_t buf[64];
      rc = libusb_bulk_transfer(handle_, ep_in, buf, sizeof(buf), &actual, 1000);
      if (rc != 0) {
        throw std::runtime_error(std::string("USB command read failed: ") + libusb_error_name(rc));
      }
      if (actual < response_len) {
        throw std::runtime_error("Short response from CANalyst-II device");
      }
      std::memcpy(response, buf, response_len);
    }
  }

  libusb_context* ctx_{nullptr};
  libusb_device_handle* handle_{nullptr};
  bool initialized_[2]{false, false};
  bool started_[2]{false, false};
};

}  // namespace canalystii

// =========================================================
// SocketCAN (vcan0 / vcan1) raw socket wrapper
// =========================================================

class SocketCanPort {
 public:
  explicit SocketCanPort(const std::string& iface) {
    sock_ = socket(PF_CAN, SOCK_RAW, CAN_RAW);
    if (sock_ < 0) {
      throw std::runtime_error("socket() failed for " + iface);
    }

    struct ifreq ifr{};
    std::strncpy(ifr.ifr_name, iface.c_str(), IFNAMSIZ - 1);
    if (ioctl(sock_, SIOCGIFINDEX, &ifr) < 0) {
      close(sock_);
      throw std::runtime_error("ioctl(SIOCGIFINDEX) failed for " + iface +
                                " (does the interface exist?)");
    }

    struct sockaddr_can addr{};
    addr.can_family = AF_CAN;
    addr.can_ifindex = ifr.ifr_ifindex;

    if (bind(sock_, reinterpret_cast<struct sockaddr*>(&addr), sizeof(addr)) < 0) {
      close(sock_);
      throw std::runtime_error("bind() failed for " + iface);
    }
  }

  ~SocketCanPort() {
    if (sock_ >= 0) close(sock_);
  }

  SocketCanPort(const SocketCanPort&) = delete;
  SocketCanPort& operator=(const SocketCanPort&) = delete;

  bool recv(struct can_frame& frame, int timeout_ms) {
    struct pollfd pfd{sock_, POLLIN, 0};
    if (poll(&pfd, 1, timeout_ms) <= 0) return false;
    return read(sock_, &frame, sizeof(frame)) == sizeof(frame);
  }

  bool send(const struct can_frame& frame) {
    return write(sock_, &frame, sizeof(frame)) == static_cast<ssize_t>(sizeof(frame));
  }

 private:
  int sock_{-1};
};

// =========================================================
// VCAN interface lifecycle (mirrors VCANManager in vcan_bridge.py)
// =========================================================

class VcanManager {
 public:
  void create() {
    run_sudo({"modprobe", "vcan"});
    for (const char* iface : {"vcan0", "vcan1"}) {
      run_sudo({"ip", "link", "add", "dev", iface, "type", "vcan"});
      run_sudo({"ip", "link", "set", "up", iface});
    }
    std::printf("VCAN Interfaces Created\n");
  }

  void destroy() {
    for (const char* iface : {"vcan0", "vcan1"}) {
      run_sudo({"ip", "link", "delete", iface});
    }
    std::printf("VCAN Interfaces Deleted\n");
  }

 private:
  // `args` are always fixed literals from this file (never external input),
  // so building a shell command string here carries no injection risk.
  void run_sudo(const std::vector<std::string>& args) {
    std::string cmd = "sudo -S";
    for (const auto& a : args) cmd += " " + a;
    cmd += " > /dev/null 2>&1";

    FILE* pipe = popen(cmd.c_str(), "w");
    if (!pipe) return;

    if (const char* pw = std::getenv("VCAN_SUDO_PASSWORD")) {
      std::fprintf(pipe, "%s\n", pw);
    }
    pclose(pipe);
  }
};

// =========================================================
// Bridge threads
// =========================================================

std::atomic<bool> g_signal_received{false};
std::atomic<bool> g_stop{false};

void signal_handler(int) { g_signal_received = true; }

void can_to_vcan_loop(canalystii::CanalystDevice& device, SocketCanPort& vcan0,
                       SocketCanPort& vcan1) {
  // How often we ask the USB adapter for pending frames. The adapter has a
  // finite onboard RX buffer per channel and this protocol exposes no
  // overrun/drop counter (see MessageStatusResponse) - if bus traffic
  // outpaces polling, the adapter silently drops frames internally before
  // this bridge ever sees them, and that loss is invisible everywhere
  // downstream (arm_interface's missed-cycle counter only trips after ~50
  // fully-missed control cycles, so a frame dropped here and there never
  // shows up as "Communication Lost" - it just shows up as a stale/late
  // position jumping to a newer one once a frame finally gets through).
  // Default lowered from 20ms (50 Hz) to keep the adapter's buffer drained
  // well under its capacity with 8 motors/arm reporting feedback.
  // Override via env var if profiling shows this can go lower (or needs to
  // go higher to reduce USB/CPU load).
  const char* poll_env = std::getenv("VCAN_BRIDGE_POLL_MS");
  const int poll_ms = poll_env ? std::atoi(poll_env) : 2;

  uint64_t poll_count = 0;
  auto last_rate_log = std::chrono::steady_clock::now();

  while (!g_stop.load()) {
    try {
      for (int channel = 0; channel < 2; channel++) {
        for (const auto& m : device.receive(channel)) {
          struct can_frame cf{};
          cf.can_id = m.extended ? (m.can_id & CAN_EFF_MASK) | CAN_EFF_FLAG
                                  : (m.can_id & CAN_SFF_MASK);
          if (m.remote) cf.can_id |= CAN_RTR_FLAG;
          cf.can_dlc = std::min<uint8_t>(m.data_len, 8);
          std::memcpy(cf.data, m.data, cf.can_dlc);

          (channel == 0 ? vcan0 : vcan1).send(cf);
        }
      }
    } catch (const std::exception& e) {
      if (g_stop.load()) break;
      std::fprintf(stderr, "CAN -> VCAN Error: %s\n", e.what());
    }

    // Cheap canary for "the adapter poll loop is falling behind" - doesn't
    // detect adapter-internal drops directly (the protocol can't), but a
    // poll rate that's drifted well below 1000/poll_ms means receive()
    // and/or the vcan sends are taking longer than the poll period, which
    // is exactly the condition that lets the adapter's buffer overflow.
    poll_count++;
    auto now = std::chrono::steady_clock::now();
    auto elapsed = now - last_rate_log;
    if (elapsed >= std::chrono::seconds(5)) {
      double actual_hz = poll_count / std::chrono::duration<double>(elapsed).count();
      double target_hz = 1000.0 / poll_ms;
      if (actual_hz < 0.8 * target_hz) {
        std::fprintf(stderr,
            "CAN->VCAN poll loop running at %.0f Hz (target %.0f Hz) - "
            "adapter RX buffer may be overflowing under load\n",
            actual_hz, target_hz);
      }
      poll_count = 0;
      last_rate_log = now;
    }

    std::this_thread::sleep_for(std::chrono::milliseconds(poll_ms));
  }
}

void vcan_to_can_loop(SocketCanPort& vcan, canalystii::CanalystDevice& device, int channel) {
  while (!g_stop.load()) {
    try {
      struct can_frame cf{};
      if (!vcan.recv(cf, 100)) continue;

      const bool extended = cf.can_id & CAN_EFF_FLAG;

      canalystii::Message msg{};
      msg.can_id = extended ? (cf.can_id & CAN_EFF_MASK) : (cf.can_id & CAN_SFF_MASK);
      msg.timestamp = 0;
      msg.time_flag = 1;
      msg.send_type = 0;
      msg.remote = (cf.can_id & CAN_RTR_FLAG) ? 1 : 0;
      msg.extended = extended ? 1 : 0;
      msg.data_len = cf.can_dlc;
      std::memcpy(msg.data, cf.data, 8);

      device.send(channel, {msg});
    } catch (const std::exception& e) {
      if (g_stop.load()) break;
      std::fprintf(stderr, "VCAN%d -> CAN%d Error: %s\n", channel, channel, e.what());
    }
  }
}

// =========================================================
// main
// =========================================================

int main() {
  std::signal(SIGINT, signal_handler);
  std::signal(SIGTERM, signal_handler);

  VcanManager vcan_manager;
  vcan_manager.create();

  int exit_code = 0;

  try {
    canalystii::CanalystDevice device(0);
    device.init(0, 1000000);
    device.init(1, 1000000);

    SocketCanPort vcan0("vcan0");
    SocketCanPort vcan1("vcan1");

    std::printf("Dual CAN Bridge Running (CAN0<->VCAN0, CAN1<->VCAN1)\n");

    std::thread t_can_to_vcan(can_to_vcan_loop, std::ref(device), std::ref(vcan0), std::ref(vcan1));
    std::thread t_vcan0_to_can0(vcan_to_can_loop, std::ref(vcan0), std::ref(device), 0);
    std::thread t_vcan1_to_can1(vcan_to_can_loop, std::ref(vcan1), std::ref(device), 1);

    while (!g_signal_received.load()) {
      std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }

    // Grace period before we stop relaying and tear down vcan0/vcan1.
    //
    // A motor-disable frame triggered by shutdown elsewhere in the stack has
    // to travel through vcan0/vcan1 -> this bridge -> the USB adapter -> the
    // motor. Stopping the relay threads immediately on signal could drop
    // that frame in flight and leave a motor enabled. g_stop is only
    // flipped after this sleep, so the threads above keep relaying normally
    // for the whole grace window.
    const char* grace_env = std::getenv("VCAN_BRIDGE_SHUTDOWN_GRACE_S");
    const double grace_s = grace_env ? std::atof(grace_env) : 1.5;
    std::printf("Waiting %.2fs grace period for in-flight motor-disable frames...\n", grace_s);
    std::this_thread::sleep_for(std::chrono::duration<double>(grace_s));

    std::printf("Stopping Bridge...\n");
    g_stop = true;

    t_can_to_vcan.join();
    t_vcan0_to_can0.join();
    t_vcan1_to_can1.join();

    device.stop(0);
    device.stop(1);

    std::printf("Bridge Stopped\n");

  } catch (const std::exception& e) {
    std::fprintf(stderr, "Fatal error: %s\n", e.what());
    exit_code = 1;
  }

  vcan_manager.destroy();
  return exit_code;
}
