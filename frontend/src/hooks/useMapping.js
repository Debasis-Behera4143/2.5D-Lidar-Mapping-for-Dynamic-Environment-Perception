/**
 * Custom Hook: useMapping
 * Manages Uniform vs Adaptive 2.5D Mapping, comparisons, and configuration.
 */

import { useState, useCallback } from 'react';
import { api } from '../services/api';
import { DEFAULT_MAPPING_CONFIG } from '../app/config';

export function useMapping() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mappingConfig, setMappingConfig] = useState(DEFAULT_MAPPING_CONFIG);
  const [adaptiveMap, setAdaptiveMap] = useState(null);
  const [uniformMap, setUniformMap] = useState(null);
  const [comparison, setComparison] = useState(null);

  const updateConfig = useCallback((newConfig) => {
    setMappingConfig((prev) => ({ ...prev, ...newConfig }));
  }, []);

  const generateMaps = useCallback(async (perceptionPayload) => {
    if (!perceptionPayload) return;
    setLoading(true);
    setError(null);
    try {
      // 1. Generate Uniform Map
      const uni = await api.generateUniformMap({
        perception: perceptionPayload,
        resolution: mappingConfig.uniformResolution,
        roiBounds: mappingConfig.roiBounds,
      });
      setUniformMap(uni);

      // 2. Generate Adaptive Map
      const ada = await api.generateAdaptiveMap({
        perception: perceptionPayload,
        baseResolution: mappingConfig.baseResolution,
        fineResolution: mappingConfig.fineResolution,
        importanceThreshold: mappingConfig.importanceThreshold,
        dynamicThreshold: mappingConfig.dynamicThreshold,
        roiBounds: mappingConfig.roiBounds,
      });
      setAdaptiveMap(ada);

      // 3. Generate Benchmark Comparison
      const comp = await api.compareMaps(uni, ada);
      setComparison(comp);

      return { uniformMap: uni, adaptiveMap: ada, comparison: comp };
    } catch (err) {
      setError(err.message || 'Mapping generation failed');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [mappingConfig]);

  return {
    loading,
    error,
    mappingConfig,
    updateConfig,
    adaptiveMap,
    setAdaptiveMap,
    uniformMap,
    setUniformMap,
    comparison,
    setComparison,
    generateMaps,
  };
}
