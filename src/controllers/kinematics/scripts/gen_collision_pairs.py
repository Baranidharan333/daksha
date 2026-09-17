#!/usr/bin/env python3
"""Generate the self-collision pair allowlist for the Daksha IK solver.

placo's RobotWrapper.load_collision_pairs() takes an ALLOWLIST: the JSON it
reads *replaces* the full set of pairs placo would otherwise check. That
matters for two reasons.

  Cost.   Checking all pairs of a 27-link model means 268 mesh-mesh distance
          queries per solve - ~365 ms, roughly 100x too slow for a control
          loop. Most of those pairs are kinematically incapable of touching.

  Sanity. Parent/child links overlap at their shared joint by construction,
          so they register as permanently colliding. A constraint told to
          separate them has no solution and will wreck the IK.

So the allowlist is built by exclusion, from the real mesh geometry:

  * drop parent-child pairs (structural, read from the URDF)
  * drop pairs that collide in essentially every sampled configuration -
    geometry that overlaps by design, not a collision worth avoiding
  * drop pairs that never come within APPROACH_THRESHOLD across the sweep -
    they cannot reach each other, so checking them is wasted time
  * keep the rest: pairs that are apart in some poses and close in others,
    which is exactly what "self-collision to avoid" means

Sampling is uniform over each joint's URDF limits, which over-covers the
real teleop workspace - a pair kept here may simply be unreachable in
practice, which is the safe direction to err.

    python3 gen_collision_pairs.py [--samples 400] [--out <path>]
"""

import argparse
import json
import os
import random
import xml.etree.ElementTree as ET

import numpy as np
import placo

# A pair is worth checking if the two links ever get this close (metres).
# Generous on purpose: the constraint needs to see a pair approaching well
# before contact to steer away smoothly.
APPROACH_THRESHOLD = 0.15

# Fraction of sampled configurations above which a colliding pair is treated
# as permanently overlapping geometry rather than a real collision.
ALWAYS_COLLIDING_FRACTION = 0.98


def parent_child_pairs(urdf_path):
    """Link pairs joined directly by a joint - always in contact."""
    root = ET.parse(urdf_path).getroot()
    pairs = set()
    for joint in root.iter("joint"):
        parent, child = joint.find("parent"), joint.find("child")
        if parent is not None and child is not None:
            pairs.add(frozenset((parent.get("link"), child.get("link"))))
    return pairs


def movable_joints(urdf_path):
    """Non-fixed joints with their limits, for sampling configurations."""
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


def _link(name):
    """placo suffixes collision object names with _<index>; strip it back
    to the URDF link name so pairs match what the URDF declares."""
    head, _, tail = name.rpartition("_")
    return head if tail.isdigit() else name


def geometry_link_names(robot):
    """Map each collision geometry index to its URDF link name.

    Distance.objA/objB index into collision_model.geometryObjects (the
    parentA/parentB fields are joint indices, not link names, and several
    geometries can share one joint)."""
    return [_link(g.name) for g in robot.collision_model.geometryObjects]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--urdf", default=os.path.join(
        os.path.dirname(__file__), "..", "..",
        "daksha_description_full_body", "urdf", "robot.urdf"))
    ap.add_argument("--samples", type=int, default=400)
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(__file__), "..", "config", "collision_pairs.json"))
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    urdf = os.path.abspath(args.urdf)
    robot = placo.RobotWrapper(urdf)
    robot.update_kinematics()

    adjacent = parent_child_pairs(urdf)
    joints = movable_joints(urdf)
    print(f"urdf:            {urdf}")
    print(f"movable joints:  {len(joints)}")
    print(f"parent-child:    {len(adjacent)} pairs (always excluded)")
    print(f"total pairs:     {len(robot.distances())}")
    print(f"sampling {args.samples} configurations...")

    rng = random.Random(args.seed)
    geom_link = geometry_link_names(robot)
    collides = {}   # pair -> how many sampled configs it collided in
    closest = {}    # pair -> smallest separation seen

    for n in range(args.samples):
        for name, (lo, hi) in joints.items():
            robot.set_joint(name, rng.uniform(lo, hi))
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
    keep = sorted(
        (sorted(p) for p in closest if p not in always and p not in unreachable),
        key=lambda p: (p[0], p[1]),
    )

    print(f"\nexcluded, parent-child:                 {len(adjacent)}")
    print(f"excluded, overlap in >={ALWAYS_COLLIDING_FRACTION:.0%} of poses: {len(always)}")
    for p in sorted(sorted(x) for x in always):
        print(f"    {p[0]} <-> {p[1]}")
    print(f"excluded, never within {APPROACH_THRESHOLD} m:        {len(unreachable)}")
    print(f"KEPT (checked every solve):             {len(keep)}")

    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(keep, f, indent=1)
    print(f"\nwrote {out}")

    # Prove the file loads and report the cost the solver will actually pay.
    import time
    verify = placo.RobotWrapper(urdf)
    verify.load_collision_pairs(out)
    verify.update_kinematics()
    times = []
    for _ in range(20):
        t = time.monotonic()
        verify.distances()
        times.append((time.monotonic() - t) * 1000)
    print(f"verified: {len(verify.distances())} pairs, "
          f"distances() {np.mean(times):.2f} ms -> {1000/np.mean(times):.0f} Hz")


if __name__ == "__main__":
    main()
