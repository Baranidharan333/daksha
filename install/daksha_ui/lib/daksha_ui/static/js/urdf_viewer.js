/**
 * urdf_viewer.js
 * Lightweight URDF parser + Three.js renderer for the Daksha web UI.
 * Parses the URDF XML, builds a Three.js scene, loads STL meshes (fast),
 * and handles interactive joint sliders.
 */

'use strict';

class URDFViewer {
  constructor(canvasId, containerId) {
    this.canvas    = document.getElementById(canvasId);
    this.container = document.getElementById(containerId);
    this.joints    = {};
    this.links     = {};
    this.rootObj   = null;
    this._wireframe= false;
    this._showGrid = true;
    this._meshCount= 0;
    this._meshLoaded = 0;
    this._fps = 0;
    this._frameCount = 0;
    this._lastFpsTime = performance.now();

    this._hoverCallback = null;
    this._hoveredJointName = null;
    this._highlightedMeshes = null;
    this.raycaster = new THREE.Raycaster();
    this._mouseNDC = new THREE.Vector2();

    this._initScene();
    this._initLights();
    this._initGrid();
    this._initHoverPicking();
    this._animate();
  }

  // ── Scene Setup ──────────────────────────────────────────────
  _initScene() {
    const W = this.container.clientWidth;
    const H = this.container.clientHeight;

    this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true, alpha: false });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(W, H);
    this.renderer.setClearColor(0x000000, 1);
    this.renderer.outputEncoding = THREE.sRGBEncoding;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type   = THREE.PCFSoftShadowMap;

    this.scene  = new THREE.Scene();
    // No fog — keep robot fully visible at all distances

    this.camera = new THREE.PerspectiveCamera(45, W / H, 0.01, 100);
    this.camera.position.set(0, 1.0, 2.5);
    this.camera.lookAt(0, 0.8, 0);

    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.target.set(0, 0.8, 0);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance   = 0.3;
    this.controls.maxDistance   = 12;
    this.controls.update();

    window.addEventListener('resize', () => this._onResize());
  }

  _initLights() {
    // Ambient
    this.ambientLight = new THREE.AmbientLight(0x6EE7F7, 0.25);
    this.scene.add(this.ambientLight);

    // Key light
    this.keyLight = new THREE.DirectionalLight(0xffffff, 0.9);
    this.keyLight.position.set(3, 5, 3);
    this.keyLight.castShadow = true;
    this.keyLight.shadow.mapSize.set(1024, 1024);
    this.scene.add(this.keyLight);

    // Fill light
    this.fillLight = new THREE.DirectionalLight(0xA78BFA, 0.3);
    this.fillLight.position.set(-3, 2, -2);
    this.scene.add(this.fillLight);

    // Rim light
    this.rimLight = new THREE.DirectionalLight(0x60A5FA, 0.2);
    this.rimLight.position.set(0, -2, -3);
    this.scene.add(this.rimLight);
  }

  _initGrid() {
    this.gridHelper = new THREE.GridHelper(6, 30, 0x1a3040, 0x0f2030);
    this.gridHelper.position.y = 0;
    this.gridHelper.visible = true;
    this.scene.add(this.gridHelper);

    // Floor shadow plane
    const floorGeo = new THREE.PlaneGeometry(6, 6);
    const floorMat = new THREE.MeshStandardMaterial({ color: 0x060b18, transparent: true, opacity: 0.6 });
    this.floor = new THREE.Mesh(floorGeo, floorMat);
    this.floor.rotation.x = -Math.PI / 2;
    this.floor.receiveShadow = true;
    this.scene.add(this.floor);
  }

  setDayMode(isDayMode) {
    if (isDayMode) {
      this.renderer.setClearColor(0xffffff, 1);
      this.floor.material.color.setHex(0xcbd5e1);
      this.floor.material.opacity = 0.35;
      this.ambientLight.color.setHex(0xffffff);
      this.ambientLight.intensity = 0.95;
      this.keyLight.intensity = 1.25;
      this.fillLight.color.setHex(0x38bdf8);
      this.fillLight.intensity = 0.25;
      this.rimLight.intensity = 0.15;
      if (this.gridHelper && this.gridHelper.material) {
        this.gridHelper.material.color.setHex(0x64748b);
      }
    } else {
      this.renderer.setClearColor(0x000000, 1);
      this.floor.material.color.setHex(0x0a0a0a);
      this.floor.material.opacity = 0.8;
      this.ambientLight.color.setHex(0xffffff);
      this.ambientLight.intensity = 0.45;
      this.keyLight.intensity = 1.0;
      this.fillLight.color.setHex(0xa1a1aa);
      this.fillLight.intensity = 0.35;
      this.rimLight.intensity = 0.25;
      if (this.gridHelper && this.gridHelper.material) {
        this.gridHelper.material.color.setHex(0x1a3040);
      }
    }
  }

  // ── Hover Picking ────────────────────────────────────────────
  _initHoverPicking() {
    this.canvas.addEventListener('pointermove', (e) => this._onPointerMove(e));
    this.canvas.addEventListener('pointerleave', () => {
      this._setHighlightedJoint(null);
      if (this._hoverCallback) this._hoverCallback(null, null);
    });
  }

  /** callback(jointName, {clientX, clientY}) — jointName is null on miss/leave. */
  onHover(callback) {
    this._hoverCallback = callback;
  }

  _onPointerMove(event) {
    if (!this.rootObj || !this._hoverCallback) return;
    const rect = this.canvas.getBoundingClientRect();
    this._mouseNDC.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this._mouseNDC.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this._mouseNDC, this.camera);
    const hits = this.raycaster.intersectObject(this.rootObj, true);
    if (!hits.length) {
      this._hoverCallback(null, null);
      return;
    }

    let obj = hits[0].object;
    let jointName = null;
    while (obj) {
      if (obj.userData && obj.userData.jointName) {
        jointName = obj.userData.jointName;
        break;
      }
      obj = obj.parent;
    }
    this._setHighlightedJoint(jointName);
    this._hoverCallback(jointName, { clientX: event.clientX, clientY: event.clientY });
  }

  _setHighlightedJoint(jointName) {
    if (this._hoveredJointName === jointName) return;
    this._clearHighlight();
    this._hoveredJointName = jointName;

    const joint = jointName && this.joints[jointName];
    if (!joint || !joint.obj) return;

    const meshes = [];
    joint.obj.traverse(o => { if (o.isMesh && o.material) meshes.push(o); });
    meshes.forEach(mesh => {
      const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      mats.forEach(mat => {
        if (!mat.emissive) return;
        mat.userData._preHoverEmissive = mat.emissive.getHex();
        mat.userData._preHoverEmissiveIntensity = mat.emissiveIntensity;
        mat.emissive.setHex(0xf59e0b);
        mat.emissiveIntensity = 0.55;
      });
    });
    this._highlightedMeshes = meshes;
  }

  _clearHighlight() {
    if (!this._highlightedMeshes) return;
    this._highlightedMeshes.forEach(mesh => {
      const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      mats.forEach(mat => {
        if (!mat.emissive || mat.userData._preHoverEmissive === undefined) return;
        mat.emissive.setHex(mat.userData._preHoverEmissive);
        mat.emissiveIntensity = mat.userData._preHoverEmissiveIntensity;
      });
    });
    this._highlightedMeshes = null;
  }

  _onResize() {
    const W = this.container.clientWidth;
    const H = this.container.clientHeight;
    this.camera.aspect = W / H;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(W, H);
  }

  _animate() {
    requestAnimationFrame(() => this._animate());
    this.controls.update();

    // FPS counter
    this._frameCount++;
    const now = performance.now();
    if (now - this._lastFpsTime >= 1000) {
      this._fps = this._frameCount;
      this._frameCount = 0;
      this._lastFpsTime = now;
      const el = document.getElementById('t-fps');
      if (el) el.textContent = this._fps;
    }

    this.renderer.render(this.scene, this.camera);
  }

  // ── Public API ────────────────────────────────────────────────
  resetCamera() {
    if (this.rootObj) {
      const box    = new THREE.Box3().setFromObject(this.rootObj);
      if (!box.isEmpty()) {
        const center = box.getCenter(new THREE.Vector3());
        const size   = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        // Generous zoom out multiplier so the full humanoid robot is elegantly framed
        const dist   = maxDim * 1.85;
        this.camera.position.set(center.x + dist * 0.8, center.y + dist * 0.25, center.z + dist * 1.2);
        this.controls.target.copy(center);
        this.controls.update();
        return;
      }
    }
    this.camera.position.set(1.6, 1.2, 2.8);
    this.controls.target.set(0, 0.8, 0);
    this.controls.update();
  }

  toggleGrid() {
    this._showGrid = !this._showGrid;
    this.gridHelper.visible = this._showGrid;
  }

  toggleWireframe() {
    this._wireframe = !this._wireframe;
    this.scene.traverse(obj => {
      if (obj.isMesh && obj.material) {
        const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
        mats.forEach(m => { m.wireframe = this._wireframe; });
      }
    });
  }

  setMode(mode) {
    document.getElementById('btn-visual').classList.toggle('active', mode === 'visual');
    document.getElementById('btn-collision').classList.toggle('active', mode === 'collision');
    // For now both modes use the same geometry; could filter by name
  }

  setJointValue(jointName, value, ignoreMimic = false) {
    const aliases = {
      'left_joint1': 'left_joint_1',
      'right_joint1': 'right_joint_1',
      'left_joint2': 'left_joint_2',
      'right_joint2': 'right_joint_2',
      'left_gripper': 'left_gripper_left_joint',
      'right_gripper': 'right_gripper_right_joint',
    };

    const actualName = aliases[jointName] || jointName;
    let joint = this.joints[actualName];
    if (!joint) return;

    this._updateSingleJoint(joint, value);

    if (!ignoreMimic) {
      // Update any joints that mimic this joint
      Object.entries(this.joints).forEach(([name, j]) => {
        if (j.mimic && j.mimic.targetJoint === actualName) {
          const mimicVal = value * j.mimic.multiplier + j.mimic.offset;
          this._updateSingleJoint(j, mimicVal);
        }
      });
    }
  }

  _updateSingleJoint(joint, value) {
    const axis = joint.axis || new THREE.Vector3(0, 0, 1);
    const obj  = joint.obj;
    if (!obj) return;

    if (joint.type === 'prismatic') {
      if (joint.basePos) {
        obj.position.copy(joint.basePos);
        obj.position.addScaledVector(axis, value);
      }
    } else {
      if (joint.baseQuat) {
        obj.quaternion.copy(joint.baseQuat);
        obj.rotateOnAxis(axis, value);
      }
    }
  }

  // ── URDF Parsing ──────────────────────────────────────────────
  async loadFromURL(urdfURL) {
    // Remove old robot
    if (this.rootObj) {
      this.scene.remove(this.rootObj);
      this.rootObj = null;
    }
    this.joints = {};
    this.links  = {};
    this._meshCount   = 0;
    this._meshLoaded  = 0;
    this._hoveredJointName = null;
    this._highlightedMeshes = null;

    document.getElementById('overlay-text').textContent = 'Fetching URDF…';
    const overlay = document.getElementById('viewer-overlay');
    overlay.classList.remove('hidden');

    try {
      const res  = await fetch(urdfURL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const xml  = await res.text();
      const parser = new DOMParser();
      const doc  = parser.parseFromString(xml, 'application/xml');
      if (doc.querySelector('parsererror')) throw new Error('URDF XML parse error');

      document.getElementById('overlay-text').textContent = 'Building robot…';
      await this._buildRobot(doc);

    } catch (err) {
      document.getElementById('overlay-text').textContent = `Error: ${err.message}`;
      console.error('[URDF Viewer]', err);
    }
  }

  async _buildRobot(doc) {
    this.rootObj = new THREE.Group();
    this.rootObj.name = 'robot';
    // ROS is Z-up, Three.js is Y-up. Rotate the root so the robot stands upright.
    this.rootObj.rotation.x = -Math.PI / 2;
    this.scene.add(this.rootObj);

    // Parse links
    const linkEls = doc.querySelectorAll('robot > link');
    const linkMap  = {};
    linkEls.forEach(el => {
      const name = el.getAttribute('name');
      const grp  = new THREE.Group();
      grp.name   = name;
      linkMap[name] = { el, grp, parent: null };
      this.links[name] = grp;
    });

    // Parse joints and build hierarchy
    const jointEls = doc.querySelectorAll('robot > joint');
    const roots    = new Set(Object.keys(linkMap));

    jointEls.forEach(jEl => {
      const jName  = jEl.getAttribute('name');
      const jType  = jEl.getAttribute('type');
      const parentName = jEl.querySelector('parent')?.getAttribute('link');
      const childName  = jEl.querySelector('child')?.getAttribute('link');
      const originEl   = jEl.querySelector('origin');
      const axisEl     = jEl.querySelector('axis');
      const limitEl    = jEl.querySelector('limit');
      const mimicEl    = jEl.querySelector('mimic');

      if (!parentName || !childName) return;
      if (!linkMap[parentName] || !linkMap[childName]) return;

      roots.delete(childName);

      const origin = this._parseOrigin(originEl);
      const childGrp = linkMap[childName].grp;
      childGrp.position.copy(origin.position);
      childGrp.quaternion.copy(origin.quaternion);

      linkMap[parentName].grp.add(childGrp);
      linkMap[childName].parent = parentName;

      if (jType === 'revolute' || jType === 'prismatic' || jType === 'continuous') {
        let axis = new THREE.Vector3(0, 0, 1);
        if (axisEl) {
          const xyz = axisEl.getAttribute('xyz')?.split(/\s+/).map(Number) || [0, 0, 1];
          axis.set(xyz[0], xyz[1], xyz[2]).normalize();
        }
        let mimic = null;
        if (mimicEl) {
          mimic = {
            targetJoint: mimicEl.getAttribute('joint'),
            multiplier: parseFloat(mimicEl.getAttribute('multiplier') || '1.0'),
            offset: parseFloat(mimicEl.getAttribute('offset') || '0.0'),
          };
        }
        this.joints[jName] = {
          type: jType,
          axis,
          obj: childGrp,
          baseQuat: childGrp.quaternion.clone(),
          basePos: childGrp.position.clone(),
          lower: limitEl ? parseFloat(limitEl.getAttribute('lower') || 0) : -Math.PI,
          upper: limitEl ? parseFloat(limitEl.getAttribute('upper') || 0) :  Math.PI,
          mimic,
        };
        // Tag the link's group so hover raycasts can walk up to the nearest
        // actuated joint (fixed sub-links between actuated joints stay untagged).
        childGrp.userData.jointName = jName;
      }
    });

    // Add root link(s)
    roots.forEach(rootName => {
      this.rootObj.add(linkMap[rootName].grp);
    });

    // Parse global materials defined at robot level
    const globalMaterials = {};
    doc.querySelectorAll('robot > material').forEach(mEl => {
      const matName = mEl.getAttribute('name');
      const colorEl = mEl.querySelector('color');
      if (matName && colorEl) {
        globalMaterials[matName] = this._parseColor(colorEl.getAttribute('rgba'));
      }
    });

    // Load visuals (STL only for speed; DAE support optional)
    const meshPromises = [];
    linkEls.forEach(lEl => {
      const name = lEl.getAttribute('name');
      lEl.querySelectorAll('visual').forEach(vEl => {
        const meshEl = vEl.querySelector('geometry mesh');
        if (!meshEl) {
          // Primitive shapes
          const promise = this._loadPrimitive(vEl, linkMap[name]?.grp);
          if (promise) meshPromises.push(promise);
          return;
        }
        const filename = meshEl.getAttribute('filename') || '';
        const scaleAttr = meshEl.getAttribute('scale');
        const scale    = scaleAttr ? scaleAttr.split(/\s+/).map(Number) : [1, 1, 1];
        
        const matEl = vEl.querySelector('material');
        let color = null;
        if (matEl) {
          const colorEl = matEl.querySelector('color');
          const matName = matEl.getAttribute('name');
          if (colorEl) {
            color = this._parseColor(colorEl.getAttribute('rgba'));
          } else if (matName && globalMaterials[matName] !== undefined) {
            color = globalMaterials[matName];
          }
        }

        const vOriginEl = vEl.querySelector('origin');
        const vOrigin  = this._parseOrigin(vOriginEl);

        // Visual origin is parsed directly from URDF XML (which cancels out CAD STL offsets naturally)

        // Convert package:// → /pkg/... (already done server-side, just use filename)
        const url = filename;
        if (!url || (!url.endsWith('.stl') && !url.endsWith('.STL') && !url.endsWith('.dae'))) return;

        this._meshCount++;
        const promise = this._loadMesh(url, scale, color, vOrigin, linkMap[name]?.grp);
        meshPromises.push(promise);
      });
    });


    document.getElementById('overlay-text').textContent = `Loading ${this._meshCount} meshes…`;

    // Update URDF meta
    const meta = document.getElementById('urdf-meta');
    if (meta) {
      meta.innerHTML = `Joints: ${Object.keys(this.joints).length}<br>Links: ${Object.keys(this.links).length}<br>Meshes: ${this._meshCount}`;
    }

    if (meshPromises.length === 0) {
      this._finishLoad();
    } else {
      // Load meshes with progress
      let done = 0;
      const checkDone = () => {
        done++;
        document.getElementById('overlay-text').textContent = `Loading meshes… ${done}/${this._meshCount}`;
        if (done >= meshPromises.length) this._finishLoad();
      };
      meshPromises.forEach(p => p.then(checkDone).catch(checkDone));
    }
  }

  _loadPrimitive(vEl, parentGrp) {
    if (!parentGrp) return null;
    const cylinder = vEl.querySelector('geometry cylinder');
    const box      = vEl.querySelector('geometry box');
    const sphere   = vEl.querySelector('geometry sphere');
    const vOriginEl = vEl.querySelector('origin');
    const vOrigin   = this._parseOrigin(vOriginEl);
    const materialEl = vEl.querySelector('material color');
    const color     = materialEl ? this._parseColor(materialEl.getAttribute('rgba')) : 0x556677;

    let geo, mesh;
    if (cylinder) {
      const r = parseFloat(cylinder.getAttribute('radius') || 0.05);
      const l = parseFloat(cylinder.getAttribute('length') || 0.1);
      geo  = new THREE.CylinderGeometry(r, r, l, 20);
      geo.rotateX(Math.PI / 2); // ROS primitives are Z-up; Three.js cylinder is Y-up.
    } else if (box) {
      const s = (box.getAttribute('size') || '0.1 0.1 0.1').split(/\s+/).map(Number);
      geo  = new THREE.BoxGeometry(s[0], s[1], s[2]);
    } else if (sphere) {
      const r = parseFloat(sphere.getAttribute('radius') || 0.05);
      geo  = new THREE.SphereGeometry(r, 16, 12);
    } else {
      return null;
    }

    const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.6, metalness: 0.4 });
    mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(vOrigin.position);
    mesh.quaternion.copy(vOrigin.quaternion);
    mesh.castShadow = true;
    parentGrp.add(mesh);
    return Promise.resolve();
  }

  _loadMesh(url, scale, color, origin, parentGrp) {
    return new Promise((resolve) => {
      if (!parentGrp) { resolve(); return; }
      const isSTL = url.toLowerCase().endsWith('.stl');
      const isDAE = url.toLowerCase().endsWith('.dae');

      const onLoaded = (geometry_or_scene) => {
        let grp = new THREE.Group();
        grp.position.copy(origin.position);
        grp.quaternion.copy(origin.quaternion);
        grp.scale.set(scale[0], scale[1], scale[2]);

        if (isSTL) {
          const matColor = (color !== null && color !== undefined) ? color : 0x7090A8;
          const mat = new THREE.MeshStandardMaterial({
            color: matColor,
            roughness: 0.55,
            metalness: 0.45,
            envMapIntensity: 0.8,
          });
          const mesh = new THREE.Mesh(geometry_or_scene, mat);
          mesh.castShadow = true;
          mesh.receiveShadow = true;
          grp.add(mesh);
        } else if (isDAE) {
          const scene3d = geometry_or_scene.scene || geometry_or_scene;
          
          // Three.js ColladaLoader automatically rotates the scene if up-axis is Z.
          // But URDF origins already account for transformations, so we must reset it.
          scene3d.rotation.set(0, 0, 0);
          scene3d.updateMatrix();

          scene3d.traverse(child => {
            if (child.isMesh) {
              if (color && child.material) {
                const mats = Array.isArray(child.material) ? child.material : [child.material];
                mats.forEach(m => m.color.set(color));
              }
              child.castShadow = true;
              child.receiveShadow = true;
            }
          });
          grp.add(scene3d);
        }

        parentGrp.add(grp);
        resolve();
      };

      const onError = () => resolve(); // silently skip failed meshes

      try {
        if (isSTL) {
          const loader = new THREE.STLLoader();
          loader.load(url, onLoaded, undefined, onError);
        } else if (isDAE) {
          const loader = new THREE.ColladaLoader();
          loader.load(url, onLoaded, undefined, onError);
        } else {
          resolve();
        }
      } catch(e) { resolve(); }
    });
  }

  _finishLoad() {
    // Auto-fit camera to frame full robot cleanly with generous margin
    const box = new THREE.Box3().setFromObject(this.rootObj);
    if (!box.isEmpty()) {
      const center = box.getCenter(new THREE.Vector3());
      const size   = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      const dist   = maxDim * 1.85;
      this.camera.position.set(
        center.x + dist * 0.8,
        center.y + dist * 0.25,
        center.z + dist * 1.2
      );
      this.controls.target.copy(center);
      this.controls.update();
    }

    const overlay = document.getElementById('viewer-overlay');
    overlay.classList.add('hidden');
  }

  // ── Parsing Utilities ─────────────────────────────────────────
  _parseOrigin(el) {
    let position    = new THREE.Vector3();
    let quaternion  = new THREE.Quaternion();
    if (!el) return { position, quaternion };

    const xyz = (el.getAttribute('xyz') || '0 0 0').split(/\s+/).map(Number);
    const rpy = (el.getAttribute('rpy') || '0 0 0').split(/\s+/).map(Number);

    position.set(xyz[0]||0, xyz[1]||0, xyz[2]||0);

    // ROS rpy is extrinsic XYZ, which is mathematically equivalent to intrinsic ZYX
    const euler = new THREE.Euler(rpy[0]||0, rpy[1]||0, rpy[2]||0, 'ZYX');
    quaternion.setFromEuler(euler);

    return { position, quaternion };
  }

  _parseColor(rgba) {
    if (!rgba) return 0x7090A8;
    const [r, g, b] = rgba.split(/\s+/).map(Number);
    return new THREE.Color(r, g, b);
  }
}

// Expose globally
window.URDFViewer = URDFViewer;
