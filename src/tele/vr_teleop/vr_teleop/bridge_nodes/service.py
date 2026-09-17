#  Copyright 2020 Unity Technologies
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import rclpy
import re
import threading

from rclpy.serialization import deserialize_message

from .communication import RosSender


class RosService(RosSender):
    """
    Class to send messages to a ROS service.
    """

    def __init__(self, service, service_class):
        """
        Args:
            service:        The service name in ROS
            service_class:  The service class in catkin workspace
        """
        strippedService = re.sub("[^A-Za-z0-9_]+", "", service)
        node_name = f"{strippedService}_RosService"
        RosSender.__init__(self, node_name)

        self.service_topic = service
        self.cli = self.create_client(service_class, service)
        self.req = service_class.Request()
        # how long to wait for the ROS service to answer before giving up
        self.response_timeout = 30.0

    def send(self, data):
        """
        Takes in serialized message data from source outside of the ROS network,
        deserializes it into it's class, calls the service with the message, and returns
        the service's response.

        Args:
            data: The already serialized message_class data coming from outside of ROS

        Returns:
            service response
        """
        message_type = type(self.req)
        try:
            message = deserialize_message(data, message_type)
        except Exception as e:
            self.get_logger().error(
                "Could not deserialize request for {}: {}".format(self.service_topic, e)
            )
            return None

        if not self.cli.service_is_ready():
            self.get_logger().error(
                "Ignoring service call to {} - service is not ready.".format(self.service_topic)
            )
            return None

        try:
            self.future = self.cli.call_async(message)
        except Exception as e:
            self.get_logger().error(
                "Service call to {} failed to dispatch: {}".format(self.service_topic, e)
            )
            return None

        # Block on the future instead of spinning on future.done(): the old loop
        # was a bare `while rclpy.ok()` with no sleep, which burned a full core
        # on an executor thread and never terminated if no response arrived.
        completed = threading.Event()
        self.future.add_done_callback(lambda _future: completed.set())

        if not completed.wait(self.response_timeout):
            self.get_logger().error(
                "Service call to {} timed out after {}s.".format(
                    self.service_topic, self.response_timeout
                )
            )
            self.future.cancel()
            return None

        try:
            return self.future.result()
        except Exception as e:
            self.get_logger().error(f"Service call failed {e}")
            return None

    def unregister(self):
        """

        Returns:

        """
        self.destroy_client(self.cli)
        self.destroy_node()
