/**
 * robot_viewer.js
 * URDF parser + Three.js renderer for the 3D robot view on the launch-control
 * dashboard. Fetches /api/urdf, builds the link/joint tree, loads the STL (or
 * DAE) meshes it references from /pkg/, and drives the joints from whatever
 * positions /api/joint_states reports.
 *
 * Depends on the three.js r128 globals the page loads ahead of it:
 * THREE, THREE.OrbitControls, THREE.STLLoader, THREE.ColladaLoader.
 */

'use strict';

class RobotViewer {
  /**
   * @param {HTMLCanvasElement} canvas  where the scene is drawn
   * @param {HTMLElement} container     sized element the canvas fills
   * @param {(text: string|null) => void} [onStatus]  loading/error text, null when loaded
   */
  constructor(canvas, container, onStatus) {
    this.canvas = canvas;
    this.container = container;
    this.onStatus = onStatus || (() => {});

    this.joints = {};
    this.links = {};
    this.rootObj = null;
    this.meshCount = 0;
    this._grid = true;

    this._hoverCallback = null;
    this._hoveredJoint = null;
    this._highlighted = null;
    this._raycaster = new THREE.Raycaster();
    this._pointerNDC = new THREE.Vector2();

    this._initScene();
    this._initLights();
    this._initGrid();
    this._initHover();
    this._animate();
  }

  // ── Hover picking ──────────────────────────────────────────────────────
  /** callback(jointName, {clientX, clientY}) — jointName is null off-robot. */
  onHover(callback) {
    this._hoverCallback = callback;
  }

  _initHover() {
    this.canvas.addEventListener('pointermove', e => this._onPointerMove(e));
    this.canvas.addEventListener('pointerleave', () => {
      this._highlight(null);
      if (this._hoverCallback) this._hoverCallback(null, null);
    });
  }

  _onPointerMove(event) {
    if (!this.rootObj || !this._hoverCallback) return;

    const rect = this.canvas.getBoundingClientRect();
    this._pointerNDC.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this._pointerNDC.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    this._raycaster.setFromCamera(this._pointerNDC, this.camera);

    const hits = this._raycaster.intersectObject(this.rootObj, true);
    if (!hits.length) {
      this._highlight(null);
      this._hoverCallback(null, null);
      return;
    }

    // Walk up from the mesh to the nearest actuated joint: the STL under the
    // cursor often belongs to a fixed sub-link (a gripper mount, a tcp frame)
    // that no motor drives, and the useful answer is the joint that carries
    // it.
    let obj = hits[0].object;
    let joint = null;
    while (obj) {
      if (obj.userData && obj.userData.jointName) {
        joint = obj.userData.jointName;
        break;
      }
      obj = obj.parent;
    }

    this._highlight(joint);
    this._hoverCallback(joint, { clientX: event.clientX, clientY: event.clientY });
  }

  _highlight(jointName) {
    if (this._hoveredJoint === jointName) return;
    this._clearHighlight();
    this._hoveredJoint = jointName;

    const joint = jointName && this.joints[jointName];
    if (!joint || !joint.obj) return;

    const meshes = [];
    // Only this joint's own links: traversing the whole subtree would light
    // up everything downstream of a shoulder.
    joint.obj.traverse(o => {
      if (!o.isMesh || !o.material) return;
      if (this._ownerJoint(o) === jointName) meshes.push(o);
    });

    meshes.forEach(mesh => {
      (Array.isArray(mesh.material) ? mesh.material : [mesh.material]).forEach(mat => {
        if (!mat.emissive) return;
        mat.userData._preHover = {
          emissive: mat.emissive.getHex(),
          intensity: mat.emissiveIntensity,
        };
        mat.emissive.setHex(0x1d6ff2);
        mat.emissiveIntensity = 0.45;
      });
    });
    this._highlighted = meshes;
  }

  _ownerJoint(obj) {
    let node = obj;
    while (node) {
      if (node.userData && node.userData.jointName) return node.userData.jointName;
      node = node.parent;
    }
    return null;
  }

  _clearHighlight() {
    if (!this._highlighted) return;
    this._highlighted.forEach(mesh => {
      (Array.isArray(mesh.material) ? mesh.material : [mesh.material]).forEach(mat => {
        const prev = mat.userData._preHover;
        if (!mat.emissive || !prev) return;
        mat.emissive.setHex(prev.emissive);
        mat.emissiveIntensity = prev.intensity;
        delete mat.userData._preHover;
      });
    });
    this._highlighted = null;
  }

  // ── Scene ──────────────────────────────────────────────────────────────
  _initScene() {
    const W = this.container.clientWidth || 1;
    const H = this.container.clientHeight || 1;

    this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true });
    // Cap at 2: a devicePixelRatio of 3 on a phone quadruples the fragment
    // work for no visible gain, and this also runs on the robot's Jetson.
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(W, H);
    this.renderer.setClearColor(0xf4f8fe, 1);
    this.renderer.outputEncoding = THREE.sRGBEncoding;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(45, W / H, 0.01, 100);
    this.camera.position.set(2.0, 1.2, 2.4);

    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.target.set(0, 0.8, 0);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance = 0.3;
    this.controls.maxDistance = 12;
    this.controls.update();

    window.addEventListener('resize', () => this.resize());
  }

  _initLights() {
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.85));

    const key = new THREE.DirectionalLight(0xffffff, 0.85);
    key.position.set(3, 5, 3);
    this.scene.add(key);

    const fill = new THREE.DirectionalLight(0xdce8fb, 0.35);
    fill.position.set(-3, 2, -2);
    this.scene.add(fill);

    const rim = new THREE.DirectionalLight(0xffffff, 0.2);
    rim.position.set(0, -2, -3);
    this.scene.add(rim);
  }

  _initGrid() {
    this.gridHelper = new THREE.GridHelper(6, 30, 0x9db6d6, 0xd7e3f3);
    this.scene.add(this.gridHelper);

    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(6, 6),
      new THREE.MeshStandardMaterial({ color: 0xe8eff9, transparent: true, opacity: 0.55 }),
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.001;  // under the grid, so the lines stay visible
    this.scene.add(floor);
  }

  _animate() {
    requestAnimationFrame(() => this._animate());
    // offsetParent is null while an ancestor is display:none, which is how the
    // sidebar hides a view. Rendering a view nobody is looking at would burn
    // the Jetson's GPU behind every other page.
    if (this.container.offsetParent === null) return;
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }

  // ── Public API ─────────────────────────────────────────────────────────
  resize() {
    const W = this.container.clientWidth;
    const H = this.container.clientHeight;
    if (!W || !H) return;
    this.camera.aspect = W / H;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(W, H);
    // The panel's aspect ratio can swing a lot (a narrow card vs. a
    // maximized wide window). Re-fitting keeps the robot filling the frame
    // instead of shrinking into a sea of empty canvas at wide aspects.
    if (this._lastFramedBox) this._frame(this._lastFramedBox);
  }

  toggleGrid() {
    this._grid = !this._grid;
    this.gridHelper.visible = this._grid;
    return this._grid;
  }

  resetCamera() {
    if (this.rootObj) {
      const box = new THREE.Box3().setFromObject(this.rootObj);
      if (!box.isEmpty()) {
        this._frame(box);
        return;
      }
    }
    this.camera.position.set(2.0, 1.2, 2.4);
    this.controls.target.set(0, 0.8, 0);
    this.controls.update();
  }

  _frame(box) {
    this._lastFramedBox = box.clone();

    const center = box.getCenter(new THREE.Vector3());
    const sphere = box.getBoundingSphere(new THREE.Sphere());

    // Fit the bounding sphere into whichever of the vertical/horizontal FOV
    // is tighter for the current aspect, so a wide (fullscreen) panel frames
    // the robot the same as a narrow (docked) one instead of leaving it
    // shrunk in the middle of a mostly-empty canvas.
    const vFov = THREE.MathUtils.degToRad(this.camera.fov);
    const hFov = 2 * Math.atan(Math.tan(vFov / 2) * this.camera.aspect);
    const dist = Math.max(
      sphere.radius / Math.sin(vFov / 2),
      sphere.radius / Math.sin(hFov / 2),
    ) * 1.15;

    const dir = new THREE.Vector3(0.8, 0.25, 1.2).normalize();
    this.camera.position.copy(center).addScaledVector(dir, dist);
    this.controls.target.copy(center);
    this.controls.update();
  }

  /** Apply a {jointName: position} map, following any mimic joints. */
  setJointPositions(positions) {
    for (const [name, value] of Object.entries(positions || {})) {
      this.setJointValue(name, value);
    }
  }

  setJointValue(name, value) {
    // hw_interface publishes the ros2_control joint names, which are the
    // URDF's own; the aliases only cover the older no-underscore spelling
    // some of the teleop stack still uses.
    const aliases = {
      left_joint1: 'left_joint_1', right_joint1: 'right_joint_1',
      left_joint2: 'left_joint_2', right_joint2: 'right_joint_2',
      left_gripper: 'left_gripper_left_joint',
      right_gripper: 'right_gripper_right_joint',
    };
    const actual = this.joints[name] ? name : (aliases[name] || name);
    const joint = this.joints[actual];
    if (!joint) return;

    this._moveJoint(joint, value);

    for (const other of Object.values(this.joints)) {
      if (other.mimic && other.mimic.joint === actual) {
        this._moveJoint(other, value * other.mimic.multiplier + other.mimic.offset);
      }
    }
  }

  _moveJoint(joint, value) {
    const obj = joint.obj;
    if (!obj) return;
    if (joint.type === 'prismatic') {
      obj.position.copy(joint.basePos).addScaledVector(joint.axis, value);
    } else {
      obj.quaternion.copy(joint.baseQuat);
      obj.rotateOnAxis(joint.axis, value);
    }
  }

  // ── Loading ────────────────────────────────────────────────────────────
  async load(urdfURL) {
    if (this.rootObj) {
      this.scene.remove(this.rootObj);
      this.rootObj = null;
    }
    this.joints = {};
    this.links = {};
    this.meshCount = 0;
    // The old robot's meshes are gone, so the saved emissive colours on them
    // are meaningless now.
    this._highlighted = null;
    this._hoveredJoint = null;

    this.onStatus('Fetching robot description…');
    let doc;
    try {
      const res = await fetch(urdfURL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      doc = new DOMParser().parseFromString(await res.text(), 'application/xml');
      if (doc.querySelector('parsererror')) throw new Error('URDF is not valid XML');
    } catch (err) {
      this.onStatus(`Could not load the robot model — ${err.message}`);
      console.error('[robot viewer]', err);
      return false;
    }

    // Viewer-only rotation-direction fixes from the automation package's
    // config/viewer_joint_overrides.yaml. Never fatal — a joint just keeps
    // whatever direction the URDF gives it if this can't be reached.
    let axisOverrides = [];
    try {
      const res = await fetch('/api/viewer_joint_overrides');
      if (res.ok) axisOverrides = (await res.json()).joints || [];
    } catch (err) {
      console.warn('[robot viewer] could not load viewer_joint_overrides', err);
    }

    this.onStatus('Building robot…');
    try {
      await this._build(doc, axisOverrides);
    } catch (err) {
      this.onStatus(`Could not build the robot — ${err.message}`);
      console.error('[robot viewer]', err);
      return false;
    }
    return true;
  }

  async _build(doc, axisOverrides) {
    const invertAxis = new Set(axisOverrides || []);
    this.rootObj = new THREE.Group();
    // ROS is Z-up, three.js is Y-up: rotating the root is what stands the
    // robot on the grid instead of laying it on its back.
    this.rootObj.rotation.x = -Math.PI / 2;
    this.scene.add(this.rootObj);

    const linkEls = doc.querySelectorAll('robot > link');
    const linkMap = {};
    linkEls.forEach(el => {
      const name = el.getAttribute('name');
      const grp = new THREE.Group();
      grp.name = name;
      linkMap[name] = grp;
      this.links[name] = grp;
    });

    // Every link starts as a candidate root; a link that some joint names as
    // its child is not one. What is left is the base of the tree.
    const roots = new Set(Object.keys(linkMap));

    doc.querySelectorAll('robot > joint').forEach(jEl => {
      const name = jEl.getAttribute('name');
      const type = jEl.getAttribute('type');
      const parent = jEl.querySelector('parent')?.getAttribute('link');
      const child = jEl.querySelector('child')?.getAttribute('link');
      if (!parent || !child || !linkMap[parent] || !linkMap[child]) return;

      roots.delete(child);

      const origin = this._origin(jEl.querySelector('origin'));
      const childGrp = linkMap[child];
      childGrp.position.copy(origin.position);
      childGrp.quaternion.copy(origin.quaternion);
      linkMap[parent].add(childGrp);

      if (type !== 'revolute' && type !== 'prismatic' && type !== 'continuous') return;

      const axis = new THREE.Vector3(0, 0, 1);
      const axisEl = jEl.querySelector('axis');
      if (axisEl) {
        const xyz = (axisEl.getAttribute('xyz') || '0 0 1').split(/\s+/).map(Number);
        axis.set(xyz[0] || 0, xyz[1] || 0, xyz[2] || 0).normalize();
      }
      // Viewer-only direction fix from config/viewer_joint_overrides.yaml —
      // the URDF axis is left untouched, we just flip which way the model
      // spins on screen.
      if (invertAxis.has(name)) axis.negate();

      const mimicEl = jEl.querySelector('mimic');
      const limitEl = jEl.querySelector('limit');
      this.joints[name] = {
        type, axis, obj: childGrp,
        baseQuat: childGrp.quaternion.clone(),
        basePos: childGrp.position.clone(),
        lower: limitEl ? parseFloat(limitEl.getAttribute('lower') || '0') : -Math.PI,
        upper: limitEl ? parseFloat(limitEl.getAttribute('upper') || '0') : Math.PI,
        mimic: mimicEl ? {
          joint: mimicEl.getAttribute('joint'),
          multiplier: parseFloat(mimicEl.getAttribute('multiplier') || '1'),
          offset: parseFloat(mimicEl.getAttribute('offset') || '0'),
        } : null,
      };
      // Tag the link this joint moves, so a hover raycast can walk up from
      // any mesh to the joint responsible for it.
      childGrp.userData.jointName = name;
    });

    roots.forEach(name => this.rootObj.add(linkMap[name]));

    // Materials declared once at robot level and referenced by name from a
    // <visual>.
    const palette = {};
    doc.querySelectorAll('robot > material').forEach(el => {
      const colorEl = el.querySelector('color');
      const name = el.getAttribute('name');
      if (name && colorEl) palette[name] = this._color(colorEl.getAttribute('rgba'));
    });

    const pending = [];
    linkEls.forEach(lEl => {
      const grp = linkMap[lEl.getAttribute('name')];
      lEl.querySelectorAll('visual').forEach(vEl => {
        const origin = this._origin(vEl.querySelector('origin'));
        const meshEl = vEl.querySelector('geometry mesh');

        let color = null;
        const matEl = vEl.querySelector('material');
        if (matEl) {
          const colorEl = matEl.querySelector('color');
          if (colorEl) color = this._color(colorEl.getAttribute('rgba'));
          else color = palette[matEl.getAttribute('name')] ?? null;
        }

        if (!meshEl) {
          this._addPrimitive(vEl, grp, origin, color);
          return;
        }
        const url = meshEl.getAttribute('filename') || '';
        if (!/\.(stl|dae)$/i.test(url)) return;
        const scaleAttr = meshEl.getAttribute('scale');
        const scale = scaleAttr ? scaleAttr.split(/\s+/).map(Number) : [1, 1, 1];

        this.meshCount++;
        pending.push(this._loadMesh(url, scale, color, origin, grp));
      });
    });

    if (!pending.length) {
      this._finish();
      return;
    }

    let done = 0;
    const tick = () => {
      done++;
      this.onStatus(`Loading meshes… ${done}/${pending.length}`);
      if (done >= pending.length) this._finish();
    };
    pending.forEach(p => p.then(tick, tick));
  }

  _addPrimitive(vEl, parent, origin, color) {
    if (!parent) return;
    const cylinder = vEl.querySelector('geometry cylinder');
    const box = vEl.querySelector('geometry box');
    const sphere = vEl.querySelector('geometry sphere');

    let geo;
    if (cylinder) {
      const r = parseFloat(cylinder.getAttribute('radius') || '0.05');
      const l = parseFloat(cylinder.getAttribute('length') || '0.1');
      geo = new THREE.CylinderGeometry(r, r, l, 20);
      geo.rotateX(Math.PI / 2);  // ROS cylinders are Z-up, three.js' are Y-up
    } else if (box) {
      const s = (box.getAttribute('size') || '0.1 0.1 0.1').split(/\s+/).map(Number);
      geo = new THREE.BoxGeometry(s[0], s[1], s[2]);
    } else if (sphere) {
      geo = new THREE.SphereGeometry(parseFloat(sphere.getAttribute('radius') || '0.05'), 16, 12);
    } else {
      return;
    }

    const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({
      color: color ?? 0x8fa6bd, roughness: 0.6, metalness: 0.35,
    }));
    mesh.position.copy(origin.position);
    mesh.quaternion.copy(origin.quaternion);
    parent.add(mesh);
  }

  _loadMesh(url, scale, color, origin, parent) {
    return new Promise(resolve => {
      if (!parent) { resolve(); return; }
      const isSTL = /\.stl$/i.test(url);

      const place = (loaded) => {
        const grp = new THREE.Group();
        grp.position.copy(origin.position);
        grp.quaternion.copy(origin.quaternion);
        grp.scale.set(scale[0], scale[1], scale[2]);

        if (isSTL) {
          grp.add(new THREE.Mesh(loaded, new THREE.MeshStandardMaterial({
            color: color ?? 0x93a7bd, roughness: 0.5, metalness: 0.45,
          })));
        } else {
          const scene3d = loaded.scene || loaded;
          // ColladaLoader applies the file's own up-axis conversion, but the
          // URDF origin already accounts for the mesh's orientation, so that
          // rotation has to go or the part lands on its side.
          scene3d.rotation.set(0, 0, 0);
          scene3d.updateMatrix();
          if (color !== null) {
            scene3d.traverse(o => {
              if (!o.isMesh || !o.material) return;
              (Array.isArray(o.material) ? o.material : [o.material])
                .forEach(m => m.color.set(color));
            });
          }
          grp.add(scene3d);
        }

        parent.add(grp);
        resolve();
      };

      try {
        const loader = isSTL ? new THREE.STLLoader() : new THREE.ColladaLoader();
        // A mesh that fails to load is skipped rather than failing the whole
        // robot: one missing STL should not leave the panel with no 3D view.
        loader.load(url, place, undefined, () => resolve());
      } catch (e) {
        resolve();
      }
    });
  }

  _finish() {
    const box = new THREE.Box3().setFromObject(this.rootObj);
    if (!box.isEmpty()) this._frame(box);
    this.resize();
    this.onStatus(null);
  }

  // ── Parsing helpers ────────────────────────────────────────────────────
  _origin(el) {
    const position = new THREE.Vector3();
    const quaternion = new THREE.Quaternion();
    if (!el) return { position, quaternion };

    const xyz = (el.getAttribute('xyz') || '0 0 0').split(/\s+/).map(Number);
    const rpy = (el.getAttribute('rpy') || '0 0 0').split(/\s+/).map(Number);
    position.set(xyz[0] || 0, xyz[1] || 0, xyz[2] || 0);
    // URDF rpy is extrinsic XYZ, which is the same rotation as intrinsic ZYX.
    quaternion.setFromEuler(new THREE.Euler(rpy[0] || 0, rpy[1] || 0, rpy[2] || 0, 'ZYX'));
    return { position, quaternion };
  }

  _color(rgba) {
    if (!rgba) return 0x93a7bd;
    const [r, g, b] = rgba.split(/\s+/).map(Number);
    return new THREE.Color(r, g, b);
  }
}

window.RobotViewer = RobotViewer;
