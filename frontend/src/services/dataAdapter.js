/**
 * dataAdapter.js
 * Transforms real perception output payloads into high-performance Three.js Float32 buffer arrays.
 * Preserves exact coordinate geometry and 8-class taxonomy colors without synthetic artifacts.
 */

import { CLASS_COLOR_MAP, PROJECT_CLASSES } from '../app/config';

export const dataAdapter = {
  /**
   * Convert point cloud array to typed Float32Array buffers for WebGL rendering.
   */
  pointsToBufferData(points = [], colorMode = 'semantic') {
    const count = points.length;
    if (count === 0) {
      return { positions: new Float32Array(0), colors: new Float32Array(0), count: 0 };
    }

    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    let minZ = Infinity, maxZ = -Infinity;
    let minI = Infinity, maxI = -Infinity;

    // First pass: compute bounds for color ramps
    for (let i = 0; i < count; i++) {
      const p = points[i];
      const z = typeof p.z === 'number' ? p.z : (Array.isArray(p) ? p[2] : 0);
      const intensity = typeof p.intensity === 'number' ? p.intensity : (Array.isArray(p) && p.length > 3 ? p[3] : 0);

      if (z < minZ) minZ = z;
      if (z > maxZ) maxZ = z;
      if (intensity < minI) minI = intensity;
      if (intensity > maxI) maxI = intensity;
    }

    const rangeZ = Math.max(0.1, maxZ - minZ);
    const rangeI = Math.max(0.01, maxI - minI);

    for (let i = 0; i < count; i++) {
      const p = points[i];
      const i3 = i * 3;

      const x = typeof p.x === 'number' ? p.x : (Array.isArray(p) ? p[0] : 0);
      const y = typeof p.y === 'number' ? p.y : (Array.isArray(p) ? p[1] : 0);
      const z = typeof p.z === 'number' ? p.z : (Array.isArray(p) ? p[2] : 0);
      const intensity = typeof p.intensity === 'number' ? p.intensity : (Array.isArray(p) && p.length > 3 ? p[3] : 0);
      const clsId = typeof p.predicted_label === 'number' ? p.predicted_label : 7;
      const conf = typeof p.confidence === 'number' ? p.confidence : 0.85;

      // Coordinate mapping:
      // KITTI: X forward, Y left, Z up
      // Three.js: X right (-Y), Y up (+Z), Z back (-X)
      positions[i3] = -y;
      positions[i3 + 1] = z;
      positions[i3 + 2] = -x;

      let r = 0.6, g = 0.6, b = 0.6;

      if (colorMode === 'semantic') {
        const hex = CLASS_COLOR_MAP[clsId] || '#a6a6a6';
        const rgb = this.hexToRgb(hex);
        r = rgb[0] / 255;
        g = rgb[1] / 255;
        b = rgb[2] / 255;
      } else if (colorMode === 'elevation') {
        const normZ = Math.min(1.0, Math.max(0.0, (z - minZ) / rangeZ));
        const rgb = this.turboColormap(normZ);
        r = rgb[0]; g = rgb[1]; b = rgb[2];
      } else if (colorMode === 'intensity') {
        const normI = Math.min(1.0, Math.max(0.0, (intensity - minI) / rangeI));
        r = normI; g = normI; b = normI;
      } else if (colorMode === 'confidence') {
        const c = Math.min(1.0, Math.max(0.0, conf));
        if (c < 0.5) {
          r = 1.0; g = c * 2.0; b = 0.0;
        } else {
          r = (1.0 - c) * 2.0; g = 1.0; b = 0.1;
        }
      }

      colors[i3] = r;
      colors[i3 + 1] = g;
      colors[i3 + 2] = b;
    }

    return { positions, colors, count };
  },

  hexToRgb(hex) {
    const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
    const fullHex = hex.replace(shorthandRegex, (m, r, g, b) => r + r + g + g + b + b);
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(fullHex);
    return result ? [parseInt(result[1], 16), parseInt(result[2], 16), parseInt(result[3], 16)] : [128, 128, 128];
  },

  turboColormap(t) {
    let r, g, b;
    if (t < 0.25) {
      const f = t / 0.25;
      r = 0.1; g = f * 0.8; b = 1.0;
    } else if (t < 0.5) {
      const f = (t - 0.25) / 0.25;
      r = 0.0; g = 0.8 + f * 0.2; b = 1.0 - f;
    } else if (t < 0.75) {
      const f = (t - 0.5) / 0.25;
      r = f; g = 1.0; b = 0.0;
    } else {
      const f = (t - 0.75) / 0.25;
      r = 1.0; g = 1.0 - f * 0.8; b = 0.0;
    }
    return [r, g, b];
  },
};
