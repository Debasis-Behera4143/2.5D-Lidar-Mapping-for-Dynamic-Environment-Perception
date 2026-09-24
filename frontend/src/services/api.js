/**
 * API Service for communicating with FastAPI Backend and fallback to Simulation.
 */

import { API_BASE_URL, SIMULATION_FRAMES } from '../config/constants';
import { generateSimulationFrame } from './simulationData';

class ApiService {
  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  async checkHealth() {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/health`, { method: 'GET' });
      if (res.ok) {
        const data = await res.json();
        return { online: true, ...data };
      }
      return { online: false, error: 'Non-200 response' };
    } catch {
      return { online: false, error: 'Failed to connect to backend' };
    }
  }

  async getClasses() {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/classes`);
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // ignore
    }
    return [];
  }

  async getSamples() {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/samples`);
      if (res.ok) {
        const data = await res.json();
        return data.samples || [];
      }
    } catch {
      // ignore
    }
    return [];
  }

  async getSimulationFrames() {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/simulation/frames`);
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // ignore
    }
    return SIMULATION_FRAMES;
  }

  async getFrameData(frameId, dataSource = 'Simulation') {
    if (dataSource === 'FastAPI') {
      try {
        const res = await fetch(`${this.baseUrl}/api/v1/simulation/frame/${frameId}`);
        if (res.ok) {
          const data = await res.json();
          return {
            ...data.perception,
            adaptive_map: data.adaptive_map,
            uniform_map: data.uniform_map,
            comparison: data.comparison,
            elevation_profile: data.elevation_profile,
            performance: data.performance,
            system_logs: data.logs,
            scene_objects: data.scene_objects,
            provenance: 'MEASURED (FastAPI)',
          };
        }
      } catch {
        console.warn('FastAPI unavailable, falling back to local simulation data.');
      }
    }

    // Default to deterministic simulation engine
    return generateSimulationFrame(frameId);
  }

  async runInference(payload) {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/inference`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      return { _success: false, error: e.message };
    }
  }
}

export const apiService = new ApiService();
