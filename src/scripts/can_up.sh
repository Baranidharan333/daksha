#!/bin/bash

BITRATE=1000000
RESTART_MS=100

for IFACE in can0 can1
do
    echo "Bringing up $IFACE..."

    sudo ip link set $IFACE down 2>/dev/null

    sudo ip link set $IFACE type can bitrate $BITRATE restart-ms $RESTART_MS

    sudo ip link set $IFACE up

    if ip link show $IFACE | grep -q "state UP"; then
        echo "✅ $IFACE is UP"
    else
        echo "❌ Failed to bring up $IFACE"
    fi
done

echo
echo "========== CAN Status =========="
ip -details link show can0
echo
ip -details link show can1
