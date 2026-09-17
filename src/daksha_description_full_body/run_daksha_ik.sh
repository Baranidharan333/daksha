#!/bin/bash
export ROS_PACKAGE_PATH=/home/thunder/gen2/gen2_full/src:$ROS_PACKAGE_PATH
export PYTHONNOUSERSITE=1
cd /home/thunder/gen2/gen2_full/src/daksha_description_full_body
/home/thunder/MD/isaac_sim/isaac-simulation/python.sh daksha_placo_ik_sim.py "$@"
