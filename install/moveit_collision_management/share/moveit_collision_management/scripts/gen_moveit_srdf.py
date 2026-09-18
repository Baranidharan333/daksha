#!/usr/bin/env python3
"""Generate an SRDF <disable_collisions> allowlist-by-exclusion for daksha.

MoveIt2's collision pipeline (moveit_core/collision_detection_fcl) prunes
which link pairs even reach the FCL narrow phase using an
AllowedCollisionMatrix built from the robot's SRDF: every pair listed with
<disable_collisions> is skipped outright. daksha_description_full_body has
no SRDF yet, so without one MoveIt would check every possible link pair,
including parent/child links that overlap at their shared joint by
construction (see collision_detection/collision_env.hpp - this is exactly
the AllowedCollisionMatrix concept moveit_core/collision_detection uses).

This mirrors kinematics/scripts/gen_collision_pairs.py's exclusion logic
(same sampling approach, same categories) but emits the MoveIt-native
format instead of a JSON allowlist:

  * parent-child pairs           -> reason="Adjacent"
  * always-colliding (>=98%)     -> reason="Default"  (overlaps by design)
  * never within APPROACH_THRESHOLD -> reason="Never"
  * everything else stays enabled (real self-collision candidates)

Uses placo (already a project dependency) purely for its FCL-backed
distance queries during sampling - no MoveIt/placo coupling at runtime.

    python3 gen_moveit_srdf.py [--samples 400] [--out <path>]
"""

import argparse
import os
import random
import xml.etree.ElementTree as ET

import placo

APPROACH_THRESHOLD = 0.15
ALWAYS_COLLIDING_FRACTION = 0.98


def parent_child_pairs(urdf_path):
    root = ET.parse(urdf_path).getroot()
    pairs = set()
    for joint in root.iter("joint"):
        parent, child = joint.find("parent"), joint.find("child")
        if parent is not None and child is not None:
            pairs.add(frozenset((parent.get("link"), child.get("link"))))
    return pairs


def movable_joints(urdf_path):
    root = ET.parse(urdf_path).getroot()
    joints = {}
    for joint in root.iter("joint"):
        if joint.get("type") in ("revolute", "prismatic"):
            limit = joint.find("limit")
            if limit is not None and limit.get("lower") is not None:
                joints[joint.get("name")] = (
                    float(limit.get("lower")), float(limit.get("upper"))
                )
    return joints


def robot_name(urdf_path):
    return ET.parse(urdf_path).getroot().get("name")


def _link(name):
    head, _, tail = name.rpartition("_")
    return head if tail.isdigit() else name


def geometry_link_names(robot):
    return [_link(g.name) for g in robot.collision_model.geometryObjects]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--urdf", default=os.path.join(
        os.path.dirname(__file__), "..", "..",
        "daksha_description_full_body", "urdf", "robot_collision.urdf"))
    ap.add_argument("--samples", type=int, default=400)
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(__file__), "..", "..",
        "daksha_description_full_body", "srdf", "daksha.srdf"))
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    urdf = os.path.abspath(args.urdf)
    robot = placo.RobotWrapper(urdf)
    robot.update_kinematics()

    name = robot_name(urdf)
    adjacent = parent_child_pairs(urdf)
    joints = movable_joints(urdf)
    print(f"urdf:            {urdf}")
    print(f"robot name:      {name}")
    print(f"movable joints:  {len(joints)}")
    print(f"parent-child:    {len(adjacent)} pairs (Adjacent)")
    print(f"sampling {args.samples} configurations...")

    rng = random.Random(args.seed)
    geom_link = geometry_link_names(robot)
    collides = {}
    closest = {}

    for n in range(args.samples):
        for jname, (lo, hi) in joints.items():
            robot.set_joint(jname, rng.uniform(lo, hi))
        robot.update_kinematics()

        for d in robot.distances():
            pair = frozenset((geom_link[d.objA], geom_link[d.objB]))
            if pair in adjacent or len(pair) < 2:
                continue
            gap = float(d.min_distance)
            closest[pair] = min(closest.get(pair, 1e9), gap)
            if gap <= 0.0:
                collides[pair] = collides.get(pair, 0) + 1

        if (n + 1) % 100 == 0:
            print(f"  {n+1}/{args.samples}")

    always = {p for p, c in collides.items()
              if c >= args.samples * ALWAYS_COLLIDING_FRACTION}
    unreachable = {p for p, g in closest.items()
                   if g > APPROACH_THRESHOLD and p not in always}
    kept = {p for p in closest if p not in always and p not in unreachable}

    print(f"\nexcluded, parent-child (Adjacent):            {len(adjacent)}")
    print(f"excluded, overlap >={ALWAYS_COLLIDING_FRACTION:.0%} of poses (Default): {len(always)}")
    print(f"excluded, never within {APPROACH_THRESHOLD} m (Never):        {len(unreachable)}")
    print(f"KEPT (checked by MoveIt at runtime):          {len(kept)}")

    disabled = (
        [(p, "Adjacent", "parent/child link pair") for p in adjacent]
        + [(p, "Default", "always in contact across sampled configurations") for p in always]
        + [(p, "Never", f"never within {APPROACH_THRESHOLD} m across sampled configurations") for p in unreachable]
    )
    disabled.sort(key=lambda x: tuple(sorted(x[0])))

    root = ET.Element("robot", {"name": name})
    for pair, reason, _ in disabled:
        a, b = sorted(pair)
        ET.SubElement(root, "disable_collisions", {
            "link1": a, "link2": b, "reason": reason,
        })

    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(out, encoding="utf-8", xml_declaration=True)
    print(f"\nwrote {out} ({len(disabled)} disable_collisions entries)")


if __name__ == "__main__":
    main()
