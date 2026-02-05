/**
 * React hook for managing cinematic settings state.
 * Provides settings management, validation, and persistence.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  CinematicSettings,
  ValidationResult,
  DEFAULT_CINEMATIC_SETTINGS,
  QualityPresetType,
  FilmEmulationType,
  validateCinematicSettings,
  cloneSettings,
  mergeSettings
} from '../types/cinematic';
import { CinematicApiService, withRetry, getErrorMessage } from '../services/cinematicApi';

interface UseCinematicSettingsOptions {
  userId?: string;
  autoValidate?: boolean;
  autoSave?: boolean;
  debounceMs?: number;
}

interface UseCinematicSettingsReturn {
  settings: CinematicSettings;
  validation: ValidationResult;
  isLoading: boolean;
  error: string | null;
  isDirty: boolean;
  
  // Actions
  updateSettings: (newSettings: Partial<CinematicSettings>) => void;
  resetSettings: () => void;
  loadDefaultSettings: () => Promise<void>;
  validateSettings: () => Promise<ValidationResult>;
  
  // Specific setting updaters
  updateCameraMovements: (updates: Partial<CinematicSettings['camera_movements']>) => void;
  updateColorGrading: (updates: Partial<CinematicSettings['color_grading']>) => void;
  updateSoundDesign: (updates: Partial<CinematicSettings['sound_design']>) => void;
  updateAdvancedCompositing: (updates: Partial<CinematicSettings['advanced_compositing']>) => void;
  
  // Utility functions
  exportSettings: () => string;
  importSettings: (settingsJson: string) => boolean;
}

export const useCinematicSettings = (
  initialSettings?: CinematicSettings,
  options: UseCinematicSettingsOptions = {}
): UseCinematicSettingsReturn => {
  const {
    userId = 'default',
    autoValidate = true,
    autoSave = false,
    debounceMs = 500
  } = options;

  // State
  const [settings, setSettings] = useState<CinematicSettings>(
    initialSettings || DEFAULT_CINEMATIC_SETTINGS
  );
  const [originalSettings, setOriginalSettings] = useState<CinematicSettings>(
    initialSettings || DEFAULT_CINEMATIC_SETTINGS
  );
  const [validation, setValidation] = useState<ValidationResult>({ valid: true, errors: [], warnings: [] });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Computed values
  const isDirty = useMemo(() => {
    return JSON.stringify(settings) !== JSON.stringify(originalSettings);
  }, [settings, originalSettings]);

  // Debounced validation
  useEffect(() => {
    if (!autoValidate) return;

    const timeoutId = setTimeout(() => {
      const validationResult = validateCinematicSettings(settings);
      setValidation(validationResult);
    }, debounceMs);

    return () => clearTimeout(timeoutId);
  }, [settings, autoValidate, debounceMs]);

  // Auto-save functionality
  useEffect(() => {
    if (!autoSave || !isDirty) return;

    const timeoutId = setTimeout(async () => {
      try {
        await withRetry(() => CinematicApiService.validateSettings(settings));
      } catch (err) {
        setError(getErrorMessage(err));
      }
    }, debounceMs * 2);

    return () => clearTimeout(timeoutId);
  }, [settings, autoSave, isDirty, debounceMs]);

  // Actions
  const updateSettings = useCallback((newSettings: Partial<CinematicSettings>) => {
    setSettings(current => mergeSettings(current, newSettings));
    setError(null);
  }, []);

  const resetSettings = useCallback(() => {
    setSettings(cloneSettings(originalSettings));
    setError(null);
  }, [originalSettings]);

  const loadDefaultSettings = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const defaultSettings = await withRetry(() => 
        CinematicApiService.getDefaultSettings(userId)
      );
      setSettings(defaultSettings);
      setOriginalSettings(cloneSettings(defaultSettings));
    } catch (err) {
      setError(getErrorMessage(err));
      // Fallback to built-in defaults
      setSettings(DEFAULT_CINEMATIC_SETTINGS);
      setOriginalSettings(cloneSettings(DEFAULT_CINEMATIC_SETTINGS));
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  const validateSettings = useCallback(async (): Promise<ValidationResult> => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await withRetry(() => 
        CinematicApiService.validateSettings(settings)
      );
      setValidation(result);
      return result;
    } catch (err) {
      const errorMsg = getErrorMessage(err);
      setError(errorMsg);
      // Fallback to client-side validation
      const clientValidation = validateCinematicSettings(settings);
      setValidation(clientValidation);
      return clientValidation;
    } finally {
      setIsLoading(false);
    }
  }, [settings]);

  // Specific setting updaters
  const updateCameraMovements = useCallback((updates: Partial<CinematicSettings['camera_movements']>) => {
    updateSettings({
      camera_movements: { ...settings.camera_movements, ...updates }
    });
  }, [settings.camera_movements, updateSettings]);

  const updateColorGrading = useCallback((updates: Partial<CinematicSettings['color_grading']>) => {
    updateSettings({
      color_grading: { ...settings.color_grading, ...updates }
    });
  }, [settings.color_grading, updateSettings]);

  const updateSoundDesign = useCallback((updates: Partial<CinematicSettings['sound_design']>) => {
    updateSettings({
      sound_design: { ...settings.sound_design, ...updates }
    });
  }, [settings.sound_design, updateSettings]);

  const updateAdvancedCompositing = useCallback((updates: Partial<CinematicSettings['advanced_compositing']>) => {
    updateSettings({
      advanced_compositing: { ...settings.advanced_compositing, ...updates }
    });
  }, [settings.advanced_compositing, updateSettings]);

  // Utility functions
  const exportSettings = useCallback((): string => {
    return JSON.stringify(settings, null, 2);
  }, [settings]);

  const importSettings = useCallback((settingsJson: string): boolean => {
    try {
      const importedSettings = JSON.parse(settingsJson) as CinematicSettings;
      
      // Validate imported settings
      const validationResult = validateCinematicSettings(importedSettings);
      if (!validationResult.valid) {
        setError(`Invalid settings: ${validationResult.errors.join(', ')}`);
        return false;
      }

      setSettings(importedSettings);
      setError(null);
      return true;
    } catch (err) {
      setError('Invalid JSON format');
      return false;
    }
  }, []);

  // Initialize with default settings on mount
  useEffect(() => {
    if (!initialSettings) {
      loadDefaultSettings();
    }
  }, [initialSettings, loadDefaultSettings]);

  return {
    settings,
    validation,
    isLoading,
    error,
    isDirty,
    
    // Actions
    updateSettings,
    resetSettings,
    loadDefaultSettings,
    validateSettings,
    
    // Specific updaters
    updateCameraMovements,
    updateColorGrading,
    updateSoundDesign,
    updateAdvancedCompositing,
    
    // Utilities
    exportSettings,
    importSettings
  };
};

// Hook for managing settings presets
export const useSettingsPresets = () => {
  const getStandardPreset = useCallback((): CinematicSettings => ({
    ...DEFAULT_CINEMATIC_SETTINGS,
    quality_preset: QualityPresetType.STANDARD_HD,
    camera_movements: {
      ...DEFAULT_CINEMATIC_SETTINGS.camera_movements,
      intensity: 30
    },
    color_grading: {
      ...DEFAULT_CINEMATIC_SETTINGS.color_grading,
      film_emulation: FilmEmulationType.NONE
    }
  }), []);

  const getCinematicPreset = useCallback((): CinematicSettings => ({
    ...DEFAULT_CINEMATIC_SETTINGS,
    quality_preset: QualityPresetType.CINEMATIC_4K,
    camera_movements: {
      ...DEFAULT_CINEMATIC_SETTINGS.camera_movements,
      intensity: 70
    },
    color_grading: {
      ...DEFAULT_CINEMATIC_SETTINGS.color_grading,
      film_emulation: FilmEmulationType.KODAK,
      contrast: 15,
      saturation: 10
    },
    advanced_compositing: {
      ...DEFAULT_CINEMATIC_SETTINGS.advanced_compositing,
      film_grain: true
    }
  }), []);

  const getPremiumPreset = useCallback((): CinematicSettings => ({
    ...DEFAULT_CINEMATIC_SETTINGS,
    quality_preset: QualityPresetType.CINEMATIC_8K,
    camera_movements: {
      ...DEFAULT_CINEMATIC_SETTINGS.camera_movements,
      intensity: 80
    },
    color_grading: {
      ...DEFAULT_CINEMATIC_SETTINGS.color_grading,
      film_emulation: FilmEmulationType.CINEMA,
      contrast: 20,
      saturation: 5
    },
    advanced_compositing: {
      ...DEFAULT_CINEMATIC_SETTINGS.advanced_compositing,
      film_grain: true,
      depth_of_field: true,
      motion_blur: true
    }
  }), []);

  return {
    getStandardPreset,
    getCinematicPreset,
    getPremiumPreset
  };
};