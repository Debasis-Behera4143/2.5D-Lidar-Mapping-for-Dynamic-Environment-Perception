/**
 * Backend API Client Service for LiDAR Perception & Mapping.
 * Integrates with FastAPI /api/v1 endpoints with robust error handling and fallback.
 */

import { API_BASE_URL } from '../app/config';

async function handleResponse(res) {
  if (!res.ok) {
    let errorMsg = `HTTP ${res.status} ${res.statusText}`;
    try {
      const data = await res.json();
      if (data.detail) errorMsg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      else if (data.message) errorMsg = data.message;
    } catch {
      // ignore json parse error
    }
    throw new Error(errorMsg);
  }
  return res.json();
}

export const api = {
  /**
   * Health & Device diagnostics
   */
  async getHealth() {
    const res = await fetch(`${API_BASE_URL}/api/v1/health`);
    return handleResponse(res);
  },

  /**
   * 8-Class Semantic Taxonomy
   */
  async getClasses() {
    const res = await fetch(`${API_BASE_URL}/api/v1/classes`);
    return handleResponse(res);
  },

  /**
   * Discovered KITTI LiDAR scan samples
   */
  async getSamples() {
    const res = await fetch(`${API_BASE_URL}/api/v1/samples`);
    return handleResponse(res);
  },

  /**
   * Single frame metadata
   */
  async getSample(sampleId) {
    const res = await fetch(`${API_BASE_URL}/api/v1/samples/${encodeURIComponent(sampleId)}`);
    return handleResponse(res);
  },

  /**
   * Run semantic segmentation inference on a .bin scan
   */
  async runInference({ binPath, labelPath = null, numPoints = null, interpolateToFull = false, previewPointsLimit = 3000 }) {
    const res = await fetch(`${API_BASE_URL}/api/v1/inference`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        bin_path: binPath,
        label_path: labelPath,
        num_points: numPoints,
        interpolate_to_full: interpolateToFull,
        preview_points_limit: previewPointsLimit,
      }),
    });
    return handleResponse(res);
  },

  /**
   * Generate 2.5D Uniform Grid Map
   */
  async generateUniformMap({ perception, resolution = 0.50, roiBounds = null }) {
    const res = await fetch(`${API_BASE_URL}/api/v1/map/uniform`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        perception,
        resolution,
        roi_bounds: roiBounds,
      }),
    });
    return handleResponse(res);
  },

  /**
   * Generate 2.5D Adaptive Variable-Resolution Grid Map
   */
  async generateAdaptiveMap({
    perception,
    previousPerception = null,
    baseResolution = 1.0,
    fineResolution = 0.25,
    importanceThreshold = 0.50,
    dynamicThreshold = 0.25,
    roiBounds = null,
  }) {
    const res = await fetch(`${API_BASE_URL}/api/v1/map/adaptive`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        perception,
        previous_perception: previousPerception,
        base_resolution: baseResolution,
        fine_resolution: fineResolution,
        importance_threshold: importanceThreshold,
        dynamic_threshold: dynamicThreshold,
        roi_bounds: roiBounds,
      }),
    });
    return handleResponse(res);
  },

  /**
   * Compare uniform vs adaptive maps
   */
  async compareMaps(uniformMap, adaptiveMap) {
    const res = await fetch(`${API_BASE_URL}/api/v1/map/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        uniform_map: uniformMap,
        adaptive_map: adaptiveMap,
      }),
    });
    return handleResponse(res);
  },

  /**
   * Simulation frames list
   */
  async getSimulationFrames() {
    const res = await fetch(`${API_BASE_URL}/api/v1/simulation/frames`);
    return handleResponse(res);
  },

  /**
   * Deterministic Simulation Frame bundle
   */
  async getSimulationFrame(frameId) {
    const res = await fetch(`${API_BASE_URL}/api/v1/simulation/frame/${encodeURIComponent(frameId)}`);
    return handleResponse(res);
  },
};
