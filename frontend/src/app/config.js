/**
 * Application Configuration & Project Taxonomy Standards.
 * Source of Truth aligned with backend /src/ai/label_mapping.py and /src/mapping/types.py
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const PROJECT_CLASSES = [
  { id: 0, name: 'road', label: 'Road', color: '#804080', rgb: [128, 64, 128], desc: 'Drivable road & markings' },
  { id: 1, name: 'sidewalk', label: 'Sidewalk', color: '#f52496', rgb: [245, 36, 150], desc: 'Pedestrian walk & curbs' },
  { id: 2, name: 'building', label: 'Building', color: '#595959', rgb: [89, 89, 89], desc: 'Structures & fences' },
  { id: 3, name: 'vegetation', label: 'Vegetation', color: '#389938', rgb: [56, 153, 56], desc: 'Trees, bushes, terrain' },
  { id: 4, name: 'vehicle', label: 'Vehicle', color: '#3380e6', rgb: [51, 128, 230], desc: 'Cars, trucks, cyclists' },
  { id: 5, name: 'pedestrian', label: 'Pedestrian', color: '#e62626', rgb: [230, 38, 38], desc: 'Walking humans' },
  { id: 6, name: 'pole_sign', label: 'Pole / Sign', color: '#ffd91a', rgb: [255, 217, 26], desc: 'Poles & traffic signs' },
  { id: 7, name: 'other', label: 'Other', color: '#a6a6a6', rgb: [166, 166, 166], desc: 'Unlabeled / outliers' },
];

export const CLASS_COLOR_MAP = Object.fromEntries(
  PROJECT_CLASSES.map((c) => [c.id, c.color])
);

export const DEFAULT_MAPPING_CONFIG = {
  baseResolution: 1.0,     // Coarse base cell size in meters
  fineResolution: 0.25,    // Fine subdivided cell size in meters
  importanceThreshold: 0.50, // Importance cutoff for subdivision
  dynamicThreshold: 0.25,  // Motion ratio threshold
  uniformResolution: 0.50, // Baseline uniform cell size
  roiBounds: [-40.0, 40.0, -40.0, 40.0, -3.0, 4.0],
};

export const COLOR_MODES = [
  { id: 'semantic', label: 'Semantic (8-Class)' },
  { id: 'elevation', label: 'Elevation (Z-Ramp)' },
  { id: 'intensity', label: 'Intensity (LiDAR)' },
  { id: 'confidence', label: 'Softmax Confidence' },
];

export const VIEW_MODES = [
  { id: 'orbit', label: '3D Orbit' },
  { id: 'top', label: 'Top (BEV)' },
  { id: 'front', label: 'Front' },
  { id: 'side', label: 'Side' },
  { id: 'ego', label: 'Ego POV' },
  { id: 'fit', label: 'Fit' },
];
