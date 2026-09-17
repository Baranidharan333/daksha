#!/bin/bash
# uninstall_robot_service.sh
# ----------------------------------------------------------------------------
# Removes the Gen2 robot startup service (and its udev rule) from this
# machine: stops it, disables it, deletes the unit file.
#
# Usage:
#   sudo ./uninstall_robot_service.sh
# ----------------------------------------------------------------------------

set -uo pipefail

SERVICE_NAME="gen2-robot.service"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}"
UDEV_RULE_DST="/etc/udev/rules.d/99-canalyst.rules"
SUDOERS_FILE="/etc/sudoers.d/99-gen2-vcan"
LOG_FILE="/var/log/gen2-robot-install.log"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo "$msg" | tee -a "$LOG_FILE"
}

if [[ $EUID -ne 0 ]]; then
    echo "This removes a systemd service and udev rule, so it needs root."
    echo "Re-run as: sudo $0"
    exit 1
fi

touch "$LOG_FILE" 2>/dev/null || LOG_FILE="$REPO_ROOT/install_robot_service.log"

log "==== uninstall_robot_service.sh starting ===="

if [[ -f "$SERVICE_PATH" ]] || systemctl list-unit-files 2>/dev/null | grep -q "^${SERVICE_NAME}"; then
    log "Stopping ${SERVICE_NAME} (can take up to ~20s while ROS 2 nodes shut down, please wait)..."
    systemctl stop "$SERVICE_NAME" 2>&1 | tee -a "$LOG_FILE"
    systemctl disable "$SERVICE_NAME" 2>&1 | tee -a "$LOG_FILE"
    rm -f "$SERVICE_PATH"
    systemctl daemon-reload
    log "Service removed: $SERVICE_PATH"
else
    log "No ${SERVICE_NAME} installed, nothing to stop."
fi

if [[ -f "$UDEV_RULE_DST" ]]; then
    rm -f "$UDEV_RULE_DST"
    udevadm control --reload-rules 2>&1 | tee -a "$LOG_FILE"
    log "Removed udev rule: $UDEV_RULE_DST"
else
    log "No udev rule installed, nothing to remove."
fi

if [[ -f "$SUDOERS_FILE" ]]; then
    rm -f "$SUDOERS_FILE"
    log "Removed sudoers rule: $SUDOERS_FILE"
else
    log "No sudoers rule installed, nothing to remove."
fi

log "==== uninstall complete ===="
