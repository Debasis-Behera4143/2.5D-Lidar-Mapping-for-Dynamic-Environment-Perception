/**
 * Technical Configuration & Constants for Adaptive 2.5D LiDAR Mapping Workstation.
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// 10 Extended Visual/Dashboard Classes matching Reference Image
export const DISPLAY_TAXONOMY = [
  { id: 0, name: 'Road (Drivable)', color: '#2563eb', tag: 'Drivable', short: 'road' },
  { id: 1, name: 'Sidewalk (Drivable)', color: '#8b5cf6', tag: 'Drivable', short: 'sidewalk' },
  { id: 2, name: 'Building / Wall (Non-drivable)', color: '#ef4444', tag: 'Non-drivable', short: 'building' },
  { id: 3, name: 'Vegetation (Non-drivable)', color: '#10b981', tag: 'Non-drivable', short: 'vegetation' },
  { id: 4, name: 'Vehicle (Dynamic)', color: '#d946ef', tag: 'Dynamic', short: 'vehicle' },
  { id: 5, name: 'Pedestrian (Dynamic)', color: '#eab308', tag: 'Dynamic', short: 'pedestrian' },
  { id: 6, name: 'Pole / Sign (Non-drivable)', color: '#06b6d4', tag: 'Non-drivable', short: 'pole_sign' },
  { id: 7, name: 'Ground / Terrain (Drivable)', color: '#f97316', tag: 'Drivable', short: 'terrain' },
  { id: 8, name: 'Barrier (Non-drivable)', color: '#b45309', tag: 'Non-drivable', short: 'barrier' },
  { id: 9, name: 'Other', color: '#64748b', tag: 'Neutral', short: 'other' },
];

export const SEMANTIC_CLASSES = DISPLAY_TAXONOMY;

export const CLASS_COLORS = DISPLAY_TAXONOMY.reduce((acc, item) => {
  acc[item.id] = item.color;
  return acc;
}, {});

export const CLASS_NAMES = DISPLAY_TAXONOMY.reduce((acc, item) => {
  acc[item.id] = item.name;
  return acc;
}, {});

// Adaptive Grid Resolution Bands
export const RESOLUTION_BANDS = [
  { range: '0 – 10 m', res: '5 cm', level: 'Fine Detail', color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.15)' },
  { range: '10 – 25 m', res: '10 cm', level: 'Medium', color: '#a855f7', bg: 'rgba(168, 85, 247, 0.15)' },
  { range: '25 – 50 m', res: '25 cm', level: 'Coarse', color: '#eab308', bg: 'rgba(234, 179, 8, 0.15)' },
  { range: '50 – 100 m', res: '50 cm', level: 'Base Grid', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)' },
];

// Available Simulation Scenes
export const SIMULATION_FRAMES = [
  { id: '1248', name: '1248 (Urban Boulevard)', dataset: 'nuScenes (LiDAR)', points: 1284365, time: '14:32:17' },
  { id: '1249', name: '1249 (Dense Intersection)', dataset: 'nuScenes (LiDAR)', points: 1312980, time: '14:32:18' },
  { id: '1250', name: '1250 (Highway Overpass)', dataset: 'SemanticKITTI', points: 1245100, time: '14:32:19' },
];
