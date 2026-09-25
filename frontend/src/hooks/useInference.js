/**
 * Custom Hook: useInference
 * Manages semantic segmentation perception state, API requests, and metrics.
 */

import { useState, useCallback } from 'react';
import { api } from '../services/api';

export function useInference() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inferenceData, setInferenceData] = useState(null);
  const [lastLatencyMs, setLastLatencyMs] = useState(0);

  const runInference = useCallback(async ({ binPath, labelPath, numPoints = 4096, previewLimit = 3000 }) => {
    setLoading(true);
    setError(null);
    const start = performance.now();
    try {
      const data = await api.runInference({
        binPath,
        labelPath,
        numPoints,
        interpolateToFull: false,
        previewPointsLimit: previewLimit,
      });
      const latency = Math.round(performance.now() - start);
      setLastLatencyMs(latency);
      setInferenceData(data);
      return data;
    } catch (err) {
      setError(err.message || 'Inference failed');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    inferenceData,
    setInferenceData,
    lastLatencyMs,
    runInference,
  };
}
