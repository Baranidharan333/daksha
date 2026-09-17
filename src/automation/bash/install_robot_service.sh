#!/bin/bash
# install_robot_service.sh
# ----------------------------------------------------------------------------
# Installs (or reinstalls) the Gen2 robot startup service on this machine, so
# start_robot.sh runs automatically on boot via systemd.
#
# Usage:
#   sudo ./install_robot_service.sh        # asks for confirmation
#   sudo ./install_robot_service.sh --yes  # skip confirmation
#
# To remove the service, use uninstall_robot_service.sh instead.
#
# Same script for every robot: it resolves the workspace path from its own
# location, so it works regardless of the machine's username or where the
# repo was cloned (as long as .../src/automation/bash/ layout is preserved).
# ----------------------------------------------------------------------------

set -uo pipefail

SERVICE_NAME="gen2-robot.service"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}"
UDEV_RULE_SRC_NAME="99-canalyst.rules"
UDEV_RULE_DST="/etc/udev/rules.d/${UDEV_RULE_SRC_NAME}"
LOG_FILE="/var/log/gen2-robot-install.log"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
START_SCRIPT="$SCRIPT_DIR/start_robot.sh"
UDEV_RULE_SRC="$SCRIPT_DIR/${UDEV_RULE_SRC_NAME}"

ASSUME_YES=0
for arg in "$@"; do
    case "$arg" in
        --yes|-y) ASSUME_YES=1 ;;
        *) echo "Unknown option: $arg"; exit 1 ;;
    esac
done

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo "$msg" | tee -a "$LOG_FILE"
}

if [[ $EUID -ne 0 ]]; then
    echo "This installs a systemd service and udev rule, so it needs root."
    echo "Re-run as: sudo $0 $*"
    exit 1
fi

touch "$LOG_FILE" 2>/dev/null || LOG_FILE="$REPO_ROOT/install_robot_service.log"

REAL_USER="${SUDO_USER:-root}"
if [[ "$REAL_USER" == "root" ]]; then
    echo "Could not determine the non-root user to run the service as"
    echo "(re-run with sudo from a normal user login, not as root directly)."
    exit 1
fi

log "==== install_robot_service.sh starting (repo: $REPO_ROOT, user: $REAL_USER) ===="

remove_existing_service() {
    if [[ -f "$SERVICE_PATH" ]] || systemctl list-unit-files 2>/dev/null | grep -q "^${SERVICE_NAME}"; then
        log "Existing ${SERVICE_NAME} found — stopping it (can take up to ~20s while ROS 2 nodes shut down, please wait)..."
        systemctl stop "$SERVICE_NAME" 2>&1 | tee -a "$LOG_FILE"
        log "Stop finished, disabling..."
        systemctl disable "$SERVICE_NAME" 2>&1 | tee -a "$LOG_FILE"
        rm -f "$SERVICE_PATH"
        systemctl daemon-reload
        log "Old service removed."
    else
        log "No existing ${SERVICE_NAME} found."
    fi
}

echo "This will install/reinstall the Gen2 robot startup service on this machine:"
echo "  Service:     $SERVICE_NAME"
echo "  Runs as:     $REAL_USER"
echo "  Workspace:   $REPO_ROOT"
echo "  Starts:      $START_SCRIPT"
echo "  Auto-starts: on every boot (systemd, Restart=always)"
echo

if [[ $ASSUME_YES -ne 1 ]]; then
    read -r -p "Proceed with install? [y/N] " answer
    case "$answer" in
        [yY]|[yY][eE][sS]) ;;
        *) echo "Aborted, nothing changed."; exit 0 ;;
    esac
fi

log "User confirmed install (assume_yes=$ASSUME_YES)."

remove_existing_service

chmod +x "$START_SCRIPT"

log "Writing $SERVICE_PATH"
cat > "$SERVICE_PATH" <<EOF
[Unit]
Description=Gen2 Robot Startup (VCAN bridge + bringup + gesture management)
After=network.target

[Service]
Type=simple
User=${REAL_USER}
WorkingDirectory=${REPO_ROOT}
ExecStart=/bin/bash ${START_SCRIPT}
Restart=always
RestartSec=5
KillMode=control-group
KillSignal=SIGINT
TimeoutStopSec=20

[Install]
WantedBy=multi-user.target
EOF

if [[ -f "$UDEV_RULE_SRC" ]]; then
    log "Installing udev rule -> $UDEV_RULE_DST"
    cp "$UDEV_RULE_SRC" "$UDEV_RULE_DST"
    udevadm control --reload-rules 2>&1 | tee -a "$LOG_FILE"
    udevadm trigger 2>&1 | tee -a "$LOG_FILE"
else
    log "WARNING: udev rule file not found at $UDEV_RULE_SRC, skipping."
fi

SUDOERS_FILE="/etc/sudoers.d/99-gen2-vcan"
MODPROBE_BIN="$(command -v modprobe || echo /usr/sbin/modprobe)"
IP_BIN="$(command -v ip || echo /usr/sbin/ip)"
log "Configuring passwordless sudo for VCAN setup (bringup's vcan_bridge_node calls" \
    "'sudo modprobe/ip link ...' for vcan0/vcan1, but there's no TTY under systemd" \
    "to enter a password on)..."
SUDOERS_TMP="$(mktemp)"
cat > "$SUDOERS_TMP" <<EOF
# Lets the gen2-robot service (headless, no TTY) bring up vcan0/vcan1 without
# an interactive sudo password. Managed by install_robot_service.sh — remove
# via uninstall_robot_service.sh, or just delete this file, if not needed.
${REAL_USER} ALL=(root) NOPASSWD: ${MODPROBE_BIN} vcan, \
  ${IP_BIN} link add dev vcan0 type vcan, \
  ${IP_BIN} link add dev vcan1 type vcan, \
  ${IP_BIN} link set up vcan0, \
  ${IP_BIN} link set up vcan1, \
  ${IP_BIN} link delete vcan0, \
  ${IP_BIN} link delete vcan1
EOF
if visudo -c -f "$SUDOERS_TMP" >/dev/null 2>&1; then
    install -o root -g root -m 0440 "$SUDOERS_TMP" "$SUDOERS_FILE"
    log "Installed $SUDOERS_FILE"
else
    log "WARNING: generated sudoers rule failed validation — NOT installing it." \
        "VCAN sudo calls will keep failing until this is fixed by hand."
fi
rm -f "$SUDOERS_TMP"

log "Installing ROS 2 controller packages (skipped if already present)..."
for pkg in ros-humble-joint-state-broadcaster ros-humble-ros2-controllers; do
    if dpkg -s "$pkg" >/dev/null 2>&1; then
        log "  $pkg already installed."
    else
        log "  installing $pkg ..."
        apt-get install -y "$pkg" 2>&1 | tee -a "$LOG_FILE"
    fi
done

log "Reloading systemd and enabling ${SERVICE_NAME}..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME" 2>&1 | tee -a "$LOG_FILE"
systemctl restart "$SERVICE_NAME" 2>&1 | tee -a "$LOG_FILE"

sleep 2
log "Status:"
systemctl status "$SERVICE_NAME" --no-pager 2>&1 | tee -a "$LOG_FILE"

log "==== install complete ===="
echo
echo "View live logs with:  journalctl -u ${SERVICE_NAME} -f"
echo "Uninstall with:       sudo $SCRIPT_DIR/uninstall_robot_service.sh"
