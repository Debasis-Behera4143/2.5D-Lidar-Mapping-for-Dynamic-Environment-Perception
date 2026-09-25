/**
 * Technical Configuration & Constants for Adaptive 2.5D LiDAR Mapping Workstation.
 * Exactly 8 Semantic Classes matching Project Pipeline & Reference UI.
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Exactly 8 Semantic Classes matching our pipeline
export const SEMANTIC_CLASSES_8 = [
  { id: 0, name: 'Road (Drivable)', color: '#1d64f2', short: 'road', tag: 'Drivable' },
  { id: 1, name: 'Sidewalk (Drivable)', color: '#7c3aed', short: 'sidewalk', tag: 'Drivable' },
  { id: 2, name: 'Building / Wall (Non-drivable)', color: '#ef4444', short: 'building', tag: 'Non-drivable' },
  { id: 3, name: 'Vegetation (Non-drivable)', color: '#10b981', short: 'vegetation', tag: 'Non-drivable' },
  { id: 4, name: 'Vehicle (Dynamic)', color: '#d946ef', short: 'vehicle', tag: 'Dynamic' },
  { id: 5, name: 'Pedestrian (Dynamic)', color: '#eab308', short: 'pedestrian', tag: 'Dynamic' },
  { id: 6, name: 'Pole / Sign (Non-drivable)', color: '#06b6d4', short: 'pole_sign', tag: 'Non-drivable' },
  { id: 7, name: 'Other', color: '#94a3b8', short: 'other', tag: 'Neutral' },
];

export const SEMANTIC_CLASSES = SEMANTIC_CLASSES_8;

export const CLASS_COLORS = {
  0: '#1d64f2',
  1: '#7c3aed',
  2: '#ef4444',
  3: '#10b981',
  4: '#d946ef',
  5: '#eab308',
  6: '#06b6d4',
  7: '#94a3b8',
};

export const CLASS_NAMES = {
  0: 'Road',
  1: 'Sidewalk',
  2: 'Building',
  3: 'Vegetation',
  4: 'Vehicle',
  5: 'Pedestrian',
  6: 'Pole / Sign',
  7: 'Other',
};

// Adaptive Grid Resolution Bands
export const RESOLUTION_BANDS = [
  { range: '0 - 10 m', res: '5 cm', level: 'Fine Detail', color: '#00d2ff' },
  { range: '10 - 25 m', res: '10 cm', level: 'Medium', color: '#9333ea' },
  { range: '25 - 50 m', res: '25 cm', level: 'Coarse', color: '#eab308' },
  { range: '50 - 100 m', res: '50 cm', level: 'Base Grid', color: '#ef4444' },
];
