#!/usr/bin/env python3
"""Replace the URDF's mesh collision geometry with cylinder primitives.

robot.urdf uses the full-resolution visual STL as collision geometry for
every link. That costs ~133 ms per IK solve once the self-collision
constraint is active - roughly 8 Hz, far below the rate poses arrive at, so
the arm falls progressively behind the operator. Cylinders make the same
query ~2 ms.

Fitting has to account for two things the collision elements carry, both of
which are easy to miss and produce geometry in completely the wrong place:

  scale   every <mesh> has scale="0.001 0.001 0.001" (millimetres -> metres)
  origin  23 of the 24 <collision> elements have a non-zero <origin> xyz
          placing the mesh relative to the link frame

So vertices are taken into link frame as  origin * (scale * vertex)  before
anything is fitted, and the resulting primitive is written back with its own
origin expressed in that same link frame.

Each cylinder ENCLOSES its mesh: radius is the maximum radial distance from
the fitted axis and length the full axial extent. That direction of error is
deliberate. An enclosing primitive can report a collision the real geometry
would not (restrictive, visible, safe); an undersized one misses real
contacts (silent, unsafe). Use --shrink only if the conservative fit is too
restrictive in practice, and re-run --validate after.

    python3 gen_collision_primitives.py --validate
"""

import argparse
import os
import xml.etree.ElementTree as ET

import numpy as np
import trimesh
from scipy.spatial.transform import Rotation as R


def _rpy_to_matrix(rpy_str):
    if not rpy_str:
        return np.eye(3)
    return R.from_euler("xyz", [float(v) for v in rpy_str.split()]).as_matrix()


def _xyz(xyz_str):
    if not xyz_str:
        return np.zeros(3)
    return np.array([float(v) for v in xyz_str.split()])


def fit_box(vertices):
    """Oriented bounding box about the vertices' principal axes.

    Returns (size, centre, rpy). Chunky links (the base column, the wheel
    base) are badly served by a cylinder - fitting one to a wide flat body
    produces a radius that swallows everything mounted on it.
    """
    centroid = vertices.mean(axis=0)
    centred = vertices - centroid
    axes = np.linalg.svd(centred, full_matrices=False)[2]     # rows: principal axes
    if np.linalg.det(axes) < 0:                                # keep right-handed
        axes[2] = -axes[2]

    local = centred @ axes.T
    lo, hi = local.min(axis=0), local.max(axis=0)
    size = hi - lo
    centre = centroid + ((lo + hi) / 2.0) @ axes
    return size, centre, R.from_matrix(axes.T).as_euler("xyz")


def fit_cylinder(vertices, shrink=1.0):
    """Smallest enclosing-ish cylinder about the vertices' dominant axis.

    Returns (radius, length, centre, rpy) with everything in the same frame
    as `vertices`. The axis comes from PCA; radius and length are taken as
    the true extents about it, so the cylinder contains every vertex.
    """
    centroid = vertices.mean(axis=0)
    centred = vertices - centroid

    # Dominant axis of the point cloud - for a link this is its long axis.
    axis = np.linalg.svd(centred, full_matrices=False)[2][0]

    axial = centred @ axis
    radial = np.linalg.norm(centred - np.outer(axial, axis), axis=1)

    radius = float(radial.max()) * shrink
    length = float(axial.max() - axial.min())
    centre = centroid + axis * ((axial.max() + axial.min()) / 2.0)

    # URDF cylinders are aligned to +Z, so rotate +Z onto the fitted axis.
    z = np.array([0.0, 0.0, 1.0])
    v = np.cross(z, axis)
    s = np.linalg.norm(v)
    if s < 1e-9:
        rot = np.eye(3) if axis[2] > 0 else R.from_euler("x", np.pi).as_matrix()
    else:
        c = float(z @ axis)
        kmat = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        rot = np.eye(3) + kmat + kmat @ kmat * ((1 - c) / s**2)

    return radius, length, centre, R.from_matrix(rot).as_euler("xyz")


def slice_vertices(vertices, n_slices):
    """Split vertices into n_slices equal-width bins along the vertex
    cloud's dominant axis.

    A single primitive fit to a whole link is sized by that link's widest
    point and applied uniformly along its entire length - fine for a
    roughly-uniform arm segment, badly wrong for a tall, non-uniform link
    (e.g. a torso column that's wide at the wheelbase and narrow where the
    arms actually pass). Slicing lets each height-band get its own tightly
    fit primitive instead of inheriting the widest band's size everywhere.

    A small overlap at each bin edge keeps neighbouring slices touching
    rather than leaving a gap a real collision could hide in.
    """
    axis, centroid = _dominant_axis(vertices)
    axial = (vertices - centroid) @ axis
    lo, hi = float(axial.min()), float(axial.max())
    edges = np.linspace(lo, hi, n_slices + 1)
    pad = (hi - lo) / n_slices * 0.05

    bins = []
    for i in range(n_slices):
        mask = (axial >= edges[i] - pad) & (axial <= edges[i + 1] + pad)
        if mask.sum() >= 4:
            bins.append(vertices[mask])
    return bins or [vertices]


def _dominant_axis(vertices):
    centroid = vertices.mean(axis=0)
    axis = np.linalg.svd(vertices - centroid, full_matrices=False)[2][0]
    return axis, centroid


def _fit_one(vertices, shrink):
    """Fit both primitive types to `vertices` and keep whichever encloses
    them more tightly. Volume is the right tie-breaker: a slender arm
    link/slice wins with a cylinder, a wide flat one wins with a box, and
    no per-link naming rules are needed. Returns (shape, centre, rpy, dims)."""
    radius, length, c_centre, c_rpy = fit_cylinder(vertices, shrink)
    size, b_centre, b_rpy = fit_box(vertices)
    cyl_volume = np.pi * radius**2 * max(length, 1e-6)
    box_volume = float(np.prod(np.maximum(size, 1e-6)))

    if cyl_volume <= box_volume:
        return "cylinder", c_centre, c_rpy, {"radius": f"{radius:.6f}",
                                              "length": f"{max(length, 1e-4):.6f}"}, f"r={radius:.4f} l={length:.4f}"
    return "box", b_centre, b_rpy, {"size": " ".join(f"{max(v, 1e-4):.6f}" for v in size)}, \
        "x".join(f"{v:.3f}" for v in size)


def _set_origin(col, centre, rpy):
    origin = col.find("origin")
    if origin is None:
        origin = ET.SubElement(col, "origin")
    origin.set("xyz", " ".join(f"{v:.6f}" for v in centre))
    origin.set("rpy", " ".join(f"{v:.6f}" for v in rpy))


def build(urdf_path, mesh_dir, shrink, slices=None):
    tree = ET.parse(urdf_path)
    root = tree.getroot()
    report = []
    slices = slices or {}

    for link in root.iter("link"):
        for col in link.findall("collision"):
            geom = col.find("geometry")
            mesh_el = geom.find("mesh") if geom is not None else None
            if mesh_el is None:
                continue

            path = os.path.join(mesh_dir, os.path.basename(mesh_el.get("filename")))
            if not os.path.exists(path):
                raise FileNotFoundError(path)

            mesh = trimesh.load_mesh(path)
            verts = np.asarray(mesh.vertices, dtype=float)

            # mm -> m (or whatever the URDF declares)
            scale = mesh_el.get("scale")
            if scale:
                verts = verts * np.array([float(v) for v in scale.split()])

            # mesh frame -> link frame, using the collision element's origin
            origin = col.find("origin")
            if origin is not None:
                verts = verts @ _rpy_to_matrix(origin.get("rpy")).T + _xyz(origin.get("xyz"))

            n_slices = max(1, int(slices.get(link.get("name"), 1)))
            vertex_groups = slice_vertices(verts, n_slices) if n_slices > 1 else [verts]

            geom.remove(mesh_el)

            for i, group in enumerate(vertex_groups):
                target_col = col if i == 0 else ET.SubElement(link, "collision")
                target_geom = geom if i == 0 else ET.SubElement(target_col, "geometry")

                shape, centre, rpy, attrs, dims = _fit_one(group, shrink)
                el = ET.SubElement(target_geom, shape)
                for k, v in attrs.items():
                    el.set(k, v)
                _set_origin(target_col, centre, rpy)

                label = link.get("name") if len(vertex_groups) == 1 else f"{link.get('name')}[{i}]"
                report.append((label, shape, dims))

    return tree, report


def validate(mesh_urdf, prim_urdf, pairs, samples, seed):
    """Compare the primitive model against the mesh model, pose by pose.

    False negative = meshes collide but primitives do not. That is the
    dangerous direction and must be zero.
    """
    import random
    import placo

    mesh_robot = placo.RobotWrapper(mesh_urdf)
    prim_robot = placo.RobotWrapper(prim_urdf)
    for r in (mesh_robot, prim_robot):
        if pairs:
            r.load_collision_pairs(pairs)

    joints = {}
    for j in ET.parse(mesh_urdf).getroot().iter("joint"):
        if j.get("type") in ("revolute", "prismatic"):
            lim = j.find("limit")
            if lim is not None and lim.get("lower") is not None:
                joints[j.get("name")] = (float(lim.get("lower")), float(lim.get("upper")))

    def names(robot):
        objs = robot.collision_model.geometryObjects
        def strip(n):
            head, _, tail = n.rpartition("_")
            return head if tail.isdigit() else n
        return [strip(g.name) for g in objs]

    mesh_names, prim_names = names(mesh_robot), names(prim_robot)
    rng = random.Random(seed)
    fp = fn = agree = 0

    for _ in range(samples):
        q = {n: rng.uniform(lo, hi) for n, (lo, hi) in joints.items()}
        sets = []
        for robot, nm in ((mesh_robot, mesh_names), (prim_robot, prim_names)):
            for n, v in q.items():
                robot.set_joint(n, v)
            robot.update_kinematics()
            sets.append({frozenset((nm[c.objA], nm[c.objB])) for c in robot.self_collisions(False)})
        mesh_set, prim_set = sets
        fn += len(mesh_set - prim_set)
        fp += len(prim_set - mesh_set)
        agree += len(mesh_set & prim_set)

    return fp, fn, agree


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    desc = os.path.join(here, "..", "..", "daksha_description_full_body")
    ap = argparse.ArgumentParser()
    ap.add_argument("--urdf", default=os.path.join(desc, "urdf", "robot.urdf"))
    ap.add_argument("--meshes", default=os.path.join(desc, "meshes"))
    ap.add_argument("--out", default=os.path.join(desc, "urdf", "robot_collision.urdf"))
    ap.add_argument("--pairs", default=os.path.join(here, "..", "config", "collision_pairs.json"))
    ap.add_argument("--shrink", type=float, default=1.0,
                    help="scale factor on fitted radius; <1 is less conservative")
    ap.add_argument("--slices", nargs="*", default=[],
                    help="LINK=N pairs, e.g. --slices base_link=4, to fit N "
                         "primitives stacked along the link's dominant axis "
                         "instead of one - for tall/non-uniform links where a "
                         "single primitive is forced to the widest point's "
                         "size along the whole length")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--samples", type=int, default=200)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    slices = {}
    for spec in args.slices:
        name, _, n = spec.partition("=")
        if not n or not n.isdigit():
            raise SystemExit(f"--slices expects LINK=N (got '{spec}')")
        slices[name] = int(n)

    urdf = os.path.abspath(args.urdf)
    out = os.path.abspath(args.out)
    tree, report = build(urdf, os.path.abspath(args.meshes), args.shrink, slices)
    tree.write(out)

    print(f"{'link':26}{'shape':>10}   dimensions (m)")
    for name, shape, dims in report:
        print(f"{name:26}{shape:>10}   {dims}")
    print(f"\nwrote {out}")

    if args.validate:
        pairs = os.path.abspath(args.pairs) if os.path.exists(args.pairs) else None
        print(f"\nvalidating over {args.samples} random configurations"
              f"{' (allowlist applied)' if pairs else ''}...")
        fp, fn, agree = validate(urdf, out, pairs, args.samples, args.seed)
        print(f"  agreed collisions:            {agree}")
        print(f"  FALSE NEGATIVE (missed real): {fn}   <- must be 0")
        print(f"  false positive (over-strict): {fp}")
        if fn:
            print("\n  UNSAFE: primitives miss collisions the meshes detect.")


if __name__ == "__main__":
    main()
