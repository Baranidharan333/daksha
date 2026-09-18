#!/usr/bin/env python3
import os
import sys
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage

class TopicDiagnosticNode(Node):
    def __init__(self):
        super().__init__('topic_diagnostic_node')
        
        self.topics = {
            'left_arm_left': '/left_arm/left/color/image_raw/compressed',
            'right_arm_right': '/right_arm/right/color/image_raw/compressed',
            'zed_left': '/zed/zed_node/left/color/raw/image/compressed',
            'zed_right': '/zed/zed_node/right/color/raw/image/compressed'
        }
        
        self.counts = {k: 0 for k in self.topics}
        self.sizes = {k: [] for k in self.topics}
        self.times = {k: [] for k in self.topics}
        self.subs = {}
        
        for key, topic in self.topics.items():
            self.get_logger().info(f"Subscribing to {key}: {topic}")
            # Use default binding to pass the key parameter to callback
            self.subs[key] = self.create_subscription(
                CompressedImage,
                topic,
                self.create_callback(key),
                10
            )
        
        self.start_time = time.time()
        
    def create_callback(self, key):
        def cb(msg):
            self.counts[key] += 1
            self.sizes[key].append(len(msg.data))
            self.times[key].append(time.time())
        return cb

def main():
    # Enforce ROS_DOMAIN_ID to 18
    os.environ['ROS_DOMAIN_ID'] = '18'
    
    rclpy.init()
    node = TopicDiagnosticNode()
    
    duration = 125  # Run for 125 seconds (slightly over 2 minutes)
    print("====================================================")
    print("STARTING ROS 2 TOPIC DIAGNOSTIC ON DOMAIN 18 (4 TOPICS)")
    print("====================================================")
    for k, t in node.topics.items():
        print(f"  - {k}: {t}")
    print("\nPlease wait for 2 minutes (120s) to complete the sample run...")
    
    start = time.time()
    try:
        while time.time() - start < duration:
            rclpy.spin_once(node, timeout_sec=0.1)
            elapsed = time.time() - start
            stats_str = " | ".join([f"{k}: {node.counts[k]}" for k in node.topics])
            print(f"Elapsed: {elapsed:.1f}s / {duration}s | {stats_str}", end='\r')
    except KeyboardInterrupt:
        pass
    
    print("\n\nDiagnostic complete! Generating report...\n")
    
    # Generate statistics
    report_lines = []
    report_lines.append("ROS 2 TOPIC DIAGNOSTIC REPORT")
    report_lines.append("====================================================")
    report_lines.append(f"Domain ID: 18")
    report_lines.append(f"Duration:  125 seconds")
    report_lines.append("====================================================\n")
    
    terminal_report = []
    terminal_report.append("====================================================")
    terminal_report.append("ROS 2 TOPIC DIAGNOSTIC REPORT (Domain 18)")
    terminal_report.append("====================================================")

    for idx, (key, topic) in enumerate(node.topics.items(), 1):
        count = node.counts[key]
        times = node.times[key]
        sizes = node.sizes[key]
        
        avg_hz = 0.0
        if len(times) > 1:
            avg_hz = len(times) / (times[-1] - times[0])
            
        avg_size = 0.0
        if sizes:
            avg_size = sum(sizes) / len(sizes) / 1024.0  # Convert to KB
            
        active_status = "YES" if count > 0 else "NO (No data received)"
        
        # Terminal print
        terminal_report.append(f"{idx}. {key} ({topic})")
        terminal_report.append(f"   - Active:      {active_status}")
        terminal_report.append(f"   - Msg Count:   {count} frames")
        terminal_report.append(f"   - Avg Freq:    {avg_hz:.2f} Hz")
        terminal_report.append(f"   - Avg Size:    {avg_size:.2f} KB\n")
        
        # File report
        report_lines.append(f"{idx}. {key}: {topic}")
        report_lines.append(f"   - Active:      {'YES' if count > 0 else 'NO'}")
        report_lines.append(f"   - Msg Count:   {count} frames")
        report_lines.append(f"   - Avg Freq:    {avg_hz:.2f} Hz")
        report_lines.append(f"   - Avg Size:    {avg_size:.2f} KB\n")
        
    terminal_report.append("====================================================")
    report_lines.append("====================================================")
    
    print("\n".join(terminal_report))
    
    # Save to report file (relative to workspace root)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
    report_path = os.path.join(workspace_root, 'topic_diagnostic_report.txt')
    with open(report_path, 'w') as f:
        f.write("\n".join(report_lines))
    print(f"Report saved to: {report_path}")
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
