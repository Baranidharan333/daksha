#!/bin/bash
# install_canalyst_udev_rule.sh
# ----------------------------------------------------------------------------
# Installs ONLY the CANalyst-II USB-CAN udev rule (99-canalyst.rules) on this
# machine, so the adapter is accessible to the plugdev group without root.
#
# Use this when you just need CAN adapter permissions set up and don't want
# to run the full robot systemd service installer (install_robot_service.sh
# installs this same rule as part of that larger setup).
#
# Usage:
#   sudo ./install_canalyst_udev_rule.sh        # asks for confirmation
#   sudo ./install_canalyst_udev_rule.sh --yes  # skip confirmation
#
# To remove it, delete /etc/udev/rules.d/99-canalyst.rules and reload rules.
# ----------------------------------------------------------------------------

set -uo pipefail

UDEV_RULE_SRC_NAME="99-canalyst.rules"
UDEV_RULE_DST="/etc/udev/rules.d/${UDEV_RULE_SRC_NAME}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UDEV_RULE_SRC="$SCRIPT_DIR/${UDEV_RULE_SRC_NAME}"

ASSUME_YES=0
for arg in "$@"; do
    case "$arg" in
        --yes|-y) ASSUME_YES=1 ;;
        *) echo "Unknown option: $arg"; exit 1 ;;
    esac
done

if [[ $EUID -ne 0 ]]; then
    echo "This installs a udev rule under /etc/udev/rules.d, so it needs root."
    echo "Re-run as: sudo $0 $*"
    exit 1
fi

if [[ ! -f "$UDEV_RULE_SRC" ]]; then
    echo "Error: udev rule file not found at $UDEV_RULE_SRC"
    exit 1
fi

echo "This will install the CANalyst-II udev rule on this machine:"
echo "  Source: $UDEV_RULE_SRC"
echo "  Dest:   $UDEV_RULE_DST"
echo
cat "$UDEV_RULE_SRC"
echo

if [[ $ASSUME_YES -ne 1 ]]; then
    read -r -p "Proceed with install? [y/N] " answer
    case "$answer" in
        [yY]|[yY][eE][sS]) ;;
        *) echo "Aborted, nothing changed."; exit 0 ;;
    esac
fi

cp "$UDEV_RULE_SRC" "$UDEV_RULE_DST"
udevadm control --reload-rules
udevadm trigger

echo "Installed $UDEV_RULE_DST and reloaded udev rules."
echo "Unplug and replug the CANalyst-II adapter for the new permissions to take effect."
