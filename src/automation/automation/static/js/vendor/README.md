# Vendored three.js (r128, MIT)

Dependencies of the dashboard's 3D View. Kept here rather than loaded from a
CDN because this panel is what comes up on the robot at boot, and the robot is
often on a network with no route to the internet — a CDN `<script>` there just
fails and the 3D view never appears.

| File | Source |
| --- | --- |
| `three.min.js` | `https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js` |
| `OrbitControls.js` | `https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js` |
| `STLLoader.js` | `https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/STLLoader.js` |
| `ColladaLoader.js` | `https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/ColladaLoader.js` |

These are the non-module `examples/js/` builds, which attach to the global
`THREE` namespace; they only work against a matching r128 core, so replace all
four together if you upgrade.
