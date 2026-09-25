/**
 * Custom Hook: usePointCloud
 * Manages point buffer processing, visualization color modes, and slice filtering.
 */

import { useState, useMemo } from 'react';
import { dataAdapter } from '../services/dataAdapter';

export function usePointCloud(previewPoints = [], colorMode = 'semantic', activeClasses = {}) {
  const [pointSize, setPointSize] = useState(2.0);
  const [minZFilter, setMinZFilter] = useState(-3.0);
  const [maxZFilter, setMaxZFilter] = useState(4.0);

  // Filter points based on active class visibility and height slice
  const filteredPoints = useMemo(() => {
    if (!previewPoints || previewPoints.length === 0) return [];
    return previewPoints.filter((p) => {
      const clsId = p.predicted_label ?? 7;
      if (activeClasses[clsId] === false) return false;
      const z = p.z || 0;
      if (z < minZFilter || z > maxZFilter) return false;
      return true;
    });
  }, [previewPoints, activeClasses, minZFilter, maxZFilter]);

  // Convert to Three.js BufferAttribute arrays
  const bufferData = useMemo(() => {
    return dataAdapter.pointsToBufferData(filteredPoints, colorMode);
  }, [filteredPoints, colorMode]);

  return {
    filteredPoints,
    bufferData,
    pointSize,
    setPointSize,
    minZFilter,
    setMinZFilter,
    maxZFilter,
    setMaxZFilter,
  };
}
