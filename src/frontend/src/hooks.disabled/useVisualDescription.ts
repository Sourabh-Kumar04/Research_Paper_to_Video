/**
 * React hook for managing visual descriptions and AI-powered content analysis.
 * Provides description generation, scene analysis, and recommendations.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  VisualDescription,
  SceneAnalysis,
  CinematicSettings,
  VisualDescriptionRequest,
  SceneAnalysisRequest,
  VisualDescriptionState
} from '../types/cinematic';
import { CinematicApiService, withRetry, withTimeout, getErrorMessage } from '../services/cinematicApi';

interface UseVisualDescriptionOptions {
  sceneId: string;
  autoAnalyze?: boolean;
  debounceMs?: number;
  timeoutMs?: number;
}

interface UseVisualDescriptionReturn {
  // State
  content: string;
  description: string;
  sceneAnalysis: SceneAnalysis | null;
  recommendations: CinematicSettings | null;
  suggestions: string[];
  confidence: number;
  generatedBy: string;
  isGenerating: boolean;
  isAnalyzing: boolean;
  error: string | null;
  
  // Actions
  setContent: (content: string) => void;
  setDescription: (description: string) => void;
  generateDescription: (options?: { stylePreferences?: Record<string, any> }) => Promise<void>;
  analyzeScene: (existingDescription?: string) => Promise<void>;
  loadSavedDescription: () => Promise<void>;
  clearDescription: () => void;
  
  // Utility functions
  canGenerate: boolean;
  hasRecommendations: boolean;
  isContentChanged: boolean;
}

export const useVisualDescription = (
  options: UseVisualDescriptionOptions
): UseVisualDescriptionReturn => {
  const {
    sceneId,
    autoAnalyze = false,
    debounceMs = 1000,
    timeoutMs = 30000
  } = options;

  // State
  const [content, setContent] = useState('');
  const [originalContent, setOriginalContent] = useState('');
  const [description, setDescription] = useState('');
  const [sceneAnalysis, setSceneAnalysis] = useState<SceneAnalysis | null>(null);
  const [recommendations, setRecommendations] = useState<CinematicSettings | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [confidence, setConfidence] = useState(0);
  const [generatedBy, setGeneratedBy] = useState('user');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Computed values
  const canGenerate = useMemo(() => {
    return content.trim().length > 0 && !isGenerating;
  }, [content, isGenerating]);

  const hasRecommendations = useMemo(() => {
    return recommendations !== null && sceneAnalysis !== null;
  }, [recommendations, sceneAnalysis]);

  const isContentChanged = useMemo(() => {
    return content !== originalContent;
  }, [content, originalContent]);

  // Auto-analyze content changes
  useEffect(() => {
    if (!autoAnalyze || !content.trim() || isAnalyzing) return;

    const timeoutId = setTimeout(() => {
      analyzeScene();
    }, debounceMs);

    return () => clearTimeout(timeoutId);
  }, [content, autoAnalyze, debounceMs, isAnalyzing]);

  // Actions
  const generateDescription = useCallback(async (options: { stylePreferences?: Record<string, any> } = {}) => {
    if (!canGenerate) return;

    setIsGenerating(true);
    setError(null);

    try {
      const request: VisualDescriptionRequest = {
        scene_id: sceneId,
        content: content.trim(),
        scene_context: sceneAnalysis || undefined,
        style_preferences: options.stylePreferences
      };

      const result = await withTimeout(
        () => withRetry(() => CinematicApiService.generateVisualDescription(request)),
        timeoutMs
      );

      setDescription(result.description);
      setSceneAnalysis(result.scene_analysis);
      setRecommendations(result.cinematic_recommendations);
      setSuggestions(result.suggestions);
      setConfidence(result.confidence);
      setGeneratedBy(result.generated_by);
      setOriginalContent(content);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsGenerating(false);
    }
  }, [sceneId, content, canGenerate, sceneAnalysis, timeoutMs]);

  const analyzeScene = useCallback(async (existingDescription?: string) => {
    if (!content.trim()) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      const request: SceneAnalysisRequest = {
        content: content.trim(),
        existing_description: existingDescription || description || undefined
      };

      const result = await withTimeout(
        () => withRetry(() => CinematicApiService.analyzeScene(request)),
        timeoutMs
      );

      setSceneAnalysis(result.scene_analysis);
      setRecommendations(result.cinematic_recommendations);
      setConfidence(result.confidence);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsAnalyzing(false);
    }
  }, [content, description, timeoutMs]);

  const loadSavedDescription = useCallback(async () => {
    setError(null);

    try {
      const saved = await withRetry(() => 
        CinematicApiService.getVisualDescription(sceneId)
      );

      setDescription(saved.description);
      setSceneAnalysis(saved.scene_analysis);
      setRecommendations(saved.cinematic_recommendations);
      setSuggestions(saved.suggestions);
      setConfidence(saved.confidence);
      setGeneratedBy(saved.generated_by);
    } catch (err) {
      // Not finding a saved description is not an error
      if (getErrorMessage(err).includes('not found')) {
        return;
      }
      setError(getErrorMessage(err));
    }
  }, [sceneId]);

  const clearDescription = useCallback(() => {
    setDescription('');
    setSceneAnalysis(null);
    setRecommendations(null);
    setSuggestions([]);
    setConfidence(0);
    setGeneratedBy('user');
    setError(null);
  }, []);

  // Load saved description on mount
  useEffect(() => {
    loadSavedDescription();
  }, [loadSavedDescription]);

  return {
    // State
    content,
    description,
    sceneAnalysis,
    recommendations,
    suggestions,
    confidence,
    generatedBy,
    isGenerating,
    isAnalyzing,
    error,
    
    // Actions
    setContent,
    setDescription,
    generateDescription,
    analyzeScene,
    loadSavedDescription,
    clearDescription,
    
    // Computed
    canGenerate,
    hasRecommendations,
    isContentChanged
  };
};

// Hook for managing multiple visual descriptions
export const useVisualDescriptionBatch = () => {
  const [descriptions, setDescriptions] = useState<Map<string, VisualDescription>>(new Map());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateBatch = useCallback(async (requests: VisualDescriptionRequest[]) => {
    setIsLoading(true);
    setError(null);

    try {
      const results = await Promise.allSettled(
        requests.map(request => 
          withRetry(() => CinematicApiService.generateVisualDescription(request))
        )
      );

      const newDescriptions = new Map(descriptions);
      
      results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          newDescriptions.set(requests[index].scene_id, result.value);
        }
      });

      setDescriptions(newDescriptions);
      
      // Check for any failures
      const failures = results.filter(r => r.status === 'rejected');
      if (failures.length > 0) {
        setError(`${failures.length} descriptions failed to generate`);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }, [descriptions]);

  const getDescription = useCallback((sceneId: string): VisualDescription | null => {
    return descriptions.get(sceneId) || null;
  }, [descriptions]);

  const removeDescription = useCallback((sceneId: string) => {
    setDescriptions(current => {
      const newMap = new Map(current);
      newMap.delete(sceneId);
      return newMap;
    });
  }, []);

  const clearAll = useCallback(() => {
    setDescriptions(new Map());
    setError(null);
  }, []);

  return {
    descriptions: Array.from(descriptions.values()),
    isLoading,
    error,
    generateBatch,
    getDescription,
    removeDescription,
    clearAll
  };
};

// Hook for description templates and presets
export const useDescriptionTemplates = () => {
  const getEducationalTemplate = useCallback((subject: string) => ({
    style_preferences: {
      mood: 'analytical',
      pacing: 'medium',
      focus_type: 'educational',
      subject
    }
  }), []);

  const getPresentationTemplate = useCallback((audience: string) => ({
    style_preferences: {
      mood: 'professional',
      pacing: 'medium',
      focus_type: 'informational',
      audience
    }
  }), []);

  const getCreativeTemplate = useCallback((style: string) => ({
    style_preferences: {
      mood: 'creative',
      pacing: 'dynamic',
      focus_type: 'artistic',
      style
    }
  }), []);

  const getTechnicalTemplate = useCallback((complexity: string) => ({
    style_preferences: {
      mood: 'analytical',
      pacing: 'slow',
      focus_type: 'technical',
      complexity
    }
  }), []);

  return {
    getEducationalTemplate,
    getPresentationTemplate,
    getCreativeTemplate,
    getTechnicalTemplate
  };
};