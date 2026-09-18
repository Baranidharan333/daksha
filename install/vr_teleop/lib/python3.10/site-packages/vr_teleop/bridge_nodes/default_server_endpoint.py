#!/usr/bin/env python

import rclpy

from vr_teleop import TcpServer


def main(args=None):
    rclpy.init(args=args)
    tcp_server = TcpServer("UnityEndpoint")

    try:
        tcp_server.start()
        tcp_server.setup_executor()
    except KeyboardInterrupt:
        pass
    finally:
        # Previously an exception out of setup_executor() skipped both of these,
        # leaving the socket bound and the nodes undestroyed.
        try:
            tcp_server.destroy_nodes()
        except Exception as e:
            print("Error during shutdown: {}".format(e))
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
