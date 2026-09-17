
import can
import threading
import subprocess

import rclpy
from rclpy.node import Node


# =========================================================
# VCAN MANAGER
# =========================================================

class VCANManager:

    def __init__(self, logger):

        self.logger = logger

        self.interfaces = ["vcan0", "vcan1"]

    def create(self):

        subprocess.run(
            ["sudo", "modprobe", "vcan"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        for iface in self.interfaces:

            subprocess.run(
                [
                    "sudo",
                    "ip",
                    "link",
                    "add",
                    "dev",
                    iface,
                    "type",
                    "vcan"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            subprocess.run(
                [
                    "sudo",
                    "ip",
                    "link",
                    "set",
                    "up",
                    iface
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        self.logger.info("VCAN Interfaces Created")

    def delete(self):

        for iface in self.interfaces:

            subprocess.run(
                [
                    "sudo",
                    "ip",
                    "link",
                    "delete",
                    iface
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        # Printed rather than logged: this runs during shutdown, after
        # the ROS context may already be invalid for rosout publishing.
        print("VCAN Interfaces Deleted")


# =========================================================
# CAN BRIDGE
# =========================================================

class DualCANBridge:

    def __init__(self, logger):

        self.logger = logger

        self.stop_event = threading.Event()

        # =====================================
        # SINGLE USB HANDLE
        # IMPORTANT:
        # Use ONE bus object only
        # =====================================

        self.bus = can.Bus(
            interface="canalystii",
            channel=(0, 1),
            bitrate=1000000
        )

        # =====================================
        # VCAN INTERFACES
        # =====================================

        self.vcan0 = can.Bus(
            interface="socketcan",
            channel="vcan0"
        )

        self.vcan1 = can.Bus(
            interface="socketcan",
            channel="vcan1"
        )

        self.threads = []

    # =====================================================
    # CAN -> VCAN
    # =====================================================

    def can_to_vcan(self):

        while not self.stop_event.is_set():

            try:

                msg = self.bus.recv(timeout=0.1)

                if msg is None:
                    continue

                # =================================
                # CHANNEL 0
                # =================================

                if msg.channel == 0:

                    self.vcan0.send(msg)

                # =================================
                # CHANNEL 1
                # =================================

                elif msg.channel == 1:

                    self.vcan1.send(msg)

            except can.CanOperationError:

                break

            except Exception as e:

                if self.stop_event.is_set():
                    break

                self.logger.error(f"CAN -> VCAN Error: {e}")

    # =====================================================
    # VCAN0 -> CAN0
    # =====================================================

    def vcan0_to_can0(self):

        while not self.stop_event.is_set():

            try:

                msg = self.vcan0.recv(timeout=0.1)

                if msg is None:
                    continue

                msg.channel = 0

                self.bus.send(msg)

            except can.CanOperationError:

                break

            except Exception as e:

                if self.stop_event.is_set():
                    break

                self.logger.error(f"VCAN0 -> CAN0 Error: {e}")

    # =====================================================
    # VCAN1 -> CAN1
    # =====================================================

    def vcan1_to_can1(self):

        while not self.stop_event.is_set():

            try:

                msg = self.vcan1.recv(timeout=0.1)

                if msg is None:
                    continue

                msg.channel = 1

                self.bus.send(msg)

            except can.CanOperationError:

                break

            except Exception as e:

                if self.stop_event.is_set():
                    break

                self.logger.error(f"VCAN1 -> CAN1 Error: {e}")

    # =====================================================
    # START
    # =====================================================

    def start(self):

        self.threads = [

            threading.Thread(
                target=self.can_to_vcan
            ),

            threading.Thread(
                target=self.vcan0_to_can0
            ),

            threading.Thread(
                target=self.vcan1_to_can1
            )
        ]

        for t in self.threads:
            t.start()

        self.logger.info("Dual CAN Bridge Running (CAN0<->VCAN0, CAN1<->VCAN1)")

    # =====================================================
    # STOP
    # =====================================================

    def stop(self):

        # Printed rather than logged: this runs during shutdown, after
        # the ROS context may already be invalid for rosout publishing.
        print("Stopping Bridge...")

        self.stop_event.set()

        # Wait for worker threads to actually exit before touching
        # the buses they may still be blocked on inside recv()/send().
        for t in self.threads:
            t.join(timeout=2)

        try:
            self.vcan0.shutdown()
        except Exception:
            pass

        try:
            self.vcan1.shutdown()
        except Exception:
            pass

        try:
            self.bus.shutdown()
        except Exception:
            pass

        print("Bridge Stopped")


# =========================================================
# ROS 2 NODE
# =========================================================

class DualCANBridgeNode(Node):

    def __init__(self):

        super().__init__("dual_can_bridge")

        self.vcan_manager = VCANManager(self.get_logger())
        self.vcan_manager.create()

        self.bridge = DualCANBridge(self.get_logger())
        self.bridge.start()

    def cleanup(self):

        # Called from main()'s finally block, before destroy_node(), while
        # the node/context are still valid enough to attempt ROS logging.
        # Uses print() as a fallback since shutdown may already be underway.

        print("Shutting down Dual CAN Bridge node...")

        try:
            self.bridge.stop()
        except Exception as e:
            print(f"Bridge stop failed: {e}")

        try:
            self.vcan_manager.delete()
        except Exception as e:
            print(f"VCAN delete failed: {e}")


# =========================================================
# MAIN
# =========================================================

def main(args=None):

    rclpy.init(args=args)

    node = DualCANBridgeNode()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        node.cleanup()
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
