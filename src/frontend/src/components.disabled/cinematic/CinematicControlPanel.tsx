/**
 * CinematicControlPanel Component
 * Main control panel for cinematic settings with feature toggles and real-time preview.
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  CinematicSettings,
  CinematicControlPanelProps,
  CameraMovementType,
  FilmEmulationType,
  QualityPresetType
} from '../../types/cinematic';
import { useCinematicSettings, useSettingsPresets } from '../../hooks/useCinematicSettings';

interface ControlSectionProps {
  title: string;
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  children: React.ReactNode;
  tooltip?: string;
}

const ControlSection: React.FC<ControlSectionProps> = ({ 
  title, 
  enabled, 
  onToggle, 
  children, 
  tooltip 
}) => (
  <div className="cinematic-control-section">
    <div className="section-header">
      <label className="section-toggle">
        <input
          type="checkbox"
          checked={enabled}
          onChange={(e) => onToggle(e.target.checked)}
        />
        <span className="section-title">{title}</span>
        {tooltip && <span className="tooltip" title={tooltip}>?</span>}
      </label>
    </div>
    <div className={`section-content ${enabled ? 'enabled' : 'disabled'}`}>
      {children}
    </div>
  </div>
);

interface SliderControlProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (value: number) => void;
  disabled?: boolean;
  tooltip?: string;
  unit?: string;
}

const SliderControl: React.FC<SliderControlProps> = ({
  label,
  value,
  min,
  max,
  step = 1,
  onChange,
  disabled = false,
  tooltip,
  unit = ''
}) => (
  <div className="slider-control">
    <label className="slider-label">
      {label}
      {tooltip && <span className="tooltip" title={tooltip}>?</span>}
    </label>
    <div className="slider-container">
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        disabled={disabled}
        className="slider"
      />
      <span className="slider-value">{value}{unit}</span>
    </div>
  </div>
);

interface SelectControlProps {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
  disabled?: boolean;
  tooltip?: string;
}

const SelectControl: React.FC<SelectControlProps> = ({
  label,
  value,
  options,
  onChange,
  disabled = false,
  tooltip
}) => (
  <div className="select-control">
    <label className="select-label">
      {label}
      {tooltip && <span className="tooltip" title={tooltip}>?</span>}
    </label>
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className="select"
    >
      {options.map(option => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  </div>
);

export const CinematicControlPanel: React.FC<CinematicControlPanelProps> = ({
  initialSettings,
  onSettingsChange,
  onPreview,
  disabled = false,
  showPreview = true,
  className = ''
}) => {
  const {
    settings,
    validation,
    isLoading,
    error,
    updateCameraMovements,
    updateColorGrading,
    updateSoundDesign,
    updateAdvancedCompositing,
    updateSettings
  } = useCinematicSettings(initialSettings);

  const { getStandardPreset, getCinematicPreset, getPremiumPreset } = useSettingsPresets();
  
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);

  // Notify parent of settings changes
  useEffect(() => {
    onSettingsChange?.(settings);
  }, [settings, onSettingsChange]);

  // Camera Movement Controls
  const renderCameraMovementControls = () => (
    <ControlSection
      title="Camera Movements"
      enabled={settings.camera_movements.enabled}
      onToggle={(enabled) => updateCameraMovements({ enabled })}
      tooltip="Add dynamic camera movements to enhance visual engagement"
    >
      <SliderControl
        label="Movement Intensity"
        value={settings.camera_movements.intensity}
        min={0}
        max={100}
        onChange={(intensity) => updateCameraMovements({ intensity })}
        disabled={!settings.camera_movements.enabled}
        tooltip="Controls how pronounced camera movements will be"
        unit="%"
      />
      
      <div className="checkbox-group">
        <label>Movement Types:</label>
        {Object.values(CameraMovementType).map(type => (
          <label key={type} className="checkbox-item">
            <input
              type="checkbox"
              checked={settings.camera_movements.allowed_types.includes(type)}
              onChange={(e) => {
                const types = e.target.checked
                  ? [...settings.camera_movements.allowed_types, type]
                  : settings.camera_movements.allowed_types.filter(t => t !== type);
                updateCameraMovements({ allowed_types: types });
              }}
              disabled={!settings.camera_movements.enabled}
            />
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </label>
        ))}
      </div>

      <label className="checkbox-item">
        <input
          type="checkbox"
          checked={settings.camera_movements.auto_select}
          onChange={(e) => updateCameraMovements({ auto_select: e.target.checked })}
          disabled={!settings.camera_movements.enabled}
        />
        Auto-select movement types based on content
      </label>
    </ControlSection>
  );

  // Color Grading Controls
  const renderColorGradingControls = () => (
    <ControlSection
      title="Color Grading"
      enabled={settings.color_grading.enabled}
      onToggle={(enabled) => updateColorGrading({ enabled })}
      tooltip="Professional color correction and film-like color grading"
    >
      <SelectControl
        label="Film Emulation"
        value={settings.color_grading.film_emulation}
        options={Object.values(FilmEmulationType).map(type => ({
          value: type,
          label: type.charAt(0).toUpperCase() + type.slice(1)
        }))}
        onChange={(film_emulation) => updateColorGrading({ film_emulation: film_emulation as FilmEmulationType })}
        disabled={!settings.color_grading.enabled}
        tooltip="Apply film stock emulation for cinematic look"
      />

      <SliderControl
        label="Temperature"
        value={settings.color_grading.temperature}
        min={-100}
        max={100}
        onChange={(temperature) => updateColorGrading({ temperature })}
        disabled={!settings.color_grading.enabled}
        tooltip="Adjust color temperature (warm/cool)"
      />

      <SliderControl
        label="Contrast"
        value={settings.color_grading.contrast}
        min={-100}
        max={100}
        onChange={(contrast) => updateColorGrading({ contrast })}
        disabled={!settings.color_grading.enabled}
        tooltip="Adjust overall contrast"
      />

      <SliderControl
        label="Saturation"
        value={settings.color_grading.saturation}
        min={-100}
        max={100}
        onChange={(saturation) => updateColorGrading({ saturation })}
        disabled={!settings.color_grading.enabled}
        tooltip="Adjust color saturation"
      />

      {showAdvanced && (
        <>
          <SliderControl
            label="Brightness"
            value={settings.color_grading.brightness}
            min={-100}
            max={100}
            onChange={(brightness) => updateColorGrading({ brightness })}
            disabled={!settings.color_grading.enabled}
            tooltip="Adjust overall brightness"
          />

          <SliderControl
            label="Shadows"
            value={settings.color_grading.shadows}
            min={-100}
            max={100}
            onChange={(shadows) => updateColorGrading({ shadows })}
            disabled={!settings.color_grading.enabled}
            tooltip="Adjust shadow areas"
          />

          <SliderControl
            label="Highlights"
            value={settings.color_grading.highlights}
            min={-100}
            max={100}
            onChange={(highlights) => updateColorGrading({ highlights })}
            disabled={!settings.color_grading.enabled}
            tooltip="Adjust highlight areas"
          />
        </>
      )}

      <label className="checkbox-item">
        <input
          type="checkbox"
          checked={settings.color_grading.auto_adjust}
          onChange={(e) => updateColorGrading({ auto_adjust: e.target.checked })}
          disabled={!settings.color_grading.enabled}
        />
        Auto-adjust based on content analysis
      </label>
    </ControlSection>
  );

  // Sound Design Controls
  const renderSoundDesignControls = () => (
    <ControlSection
      title="Sound Design"
      enabled={settings.sound_design.enabled}
      onToggle={(enabled) => updateSoundDesign({ enabled })}
      tooltip="Enhanced audio processing and music scoring"
    >
      <div className="checkbox-group">
        <label className="checkbox-item">
          <input
            type="checkbox"
            checked={settings.sound_design.ambient_audio}
            onChange={(e) => updateSoundDesign({ ambient_audio: e.target.checked })}
            disabled={!settings.sound_design.enabled}
          />
          Ambient Audio Enhancement
        </label>

        <label className="checkbox-item">
          <input
            type="checkbox"
            checked={settings.sound_design.music_scoring}
            onChange={(e) => updateSoundDesign({ music_scoring: e.target.checked })}
            disabled={!settings.sound_design.enabled}
          />
          Background Music Scoring
        </label>

        <label className="checkbox-item">
          <input
            type="checkbox"
            checked={settings.sound_design.spatial_audio}
            onChange={(e) => updateSoundDesign({ spatial_audio: e.target.checked })}
            disabled={!settings.sound_design.enabled}
          />
          Spatial Audio Processing
        </label>
      </div>

      <SliderControl
        label="Reverb Intensity"
        value={settings.sound_design.reverb_intensity}
        min={0}
        max={100}
        onChange={(reverb_intensity) => updateSoundDesign({ reverb_intensity })}
        disabled={!settings.sound_design.enabled}
        tooltip="Control reverb effect intensity"
        unit="%"
      />

      {showAdvanced && (
        <div className="checkbox-group">
          <label className="checkbox-item">
            <input
              type="checkbox"
              checked={settings.sound_design.eq_processing}
              onChange={(e) => updateSoundDesign({ eq_processing: e.target.checked })}
              disabled={!settings.sound_design.enabled}
            />
            EQ Processing
          </label>

          <label className="checkbox-item">
            <input
              type="checkbox"
              checked={settings.sound_design.dynamic_range_compression}
              onChange={(e) => updateSoundDesign({ dynamic_range_compression: e.target.checked })}
              disabled={!settings.sound_design.enabled}
            />
            Dynamic Range Compression
          </label>

          <label className="checkbox-item">
            <input
              type="checkbox"
              checked={settings.sound_design.auto_select_music}
              onChange={(e) => updateSoundDesign({ auto_select_music: e.target.checked })}
              disabled={!settings.sound_design.enabled}
            />
            Auto-select Music Based on Content
          </label>
        </div>
      )}
    </ControlSection>
  );

  // Advanced Compositing Controls
  const renderAdvancedCompositingControls = () => (
    <ControlSection
      title="Advanced Compositing"
      enabled={settings.advanced_compositing.enabled}
      onToggle={(enabled) => updateAdvancedCompositing({ enabled })}
      tooltip="Professional visual effects and compositing"
    >
      <div className="checkbox-group">
        <label className="checkbox-item">
          <input
            type="checkbox"
            checked={settings.advanced_compositing.film_grain}
            onChange={(e) => updateAdvancedCompositing({ film_grain: e.target.checked })}
            disabled={!settings.advanced_compositing.enabled}
          />
          Film Grain
        </label>

        <label className="checkbox-item">
          <input
            type="checkbox"
            checked={settings.advanced_compositing.dynamic_lighting}
            onChange={(e) => updateAdvancedCompositing({ dynamic_lighting: e.target.checked })}
            disabled={!settings.advanced_compositing.enabled}
          />
          Dynamic Lighting
        </label>

        <label className="checkbox-item">
          <input
            type="checkbox"
            checked={settings.advanced_compositing.depth_of_field}
            onChange={(e) => updateAdvancedCompositing({ depth_of_field: e.target.checked })}
            disabled={!settings.advanced_compositing.enabled}
          />
          Depth of Field
        </label>

        <label className="checkbox-item">
          <input
            type="checkbox"
            checked={settings.advanced_compositing.motion_blur}
            onChange={(e) => updateAdvancedCompositing({ motion_blur: e.target.checked })}
            disabled={!settings.advanced_compositing.enabled}
          />
          Motion Blur
        </label>

        <label className="checkbox-item">
          <input
            type="checkbox"
            checked={settings.advanced_compositing.professional_transitions}
            onChange={(e) => updateAdvancedCompositing({ professional_transitions: e.target.checked })}
            disabled={!settings.advanced_compositing.enabled}
          />
          Professional Transitions
        </label>

        <label className="checkbox-item">
          <input
            type="checkbox"
            checked={settings.advanced_compositing.lut_application}
            onChange={(e) => updateAdvancedCompositing({ lut_application: e.target.checked })}
            disabled={!settings.advanced_compositing.enabled}
          />
          LUT Application
        </label>
      </div>
    </ControlSection>
  );

  // Quality and General Settings
  const renderGeneralSettings = () => (
    <div className="general-settings">
      <SelectControl
        label="Quality Preset"
        value={settings.quality_preset}
        options={Object.values(QualityPresetType).map(preset => ({
          value: preset,
          label: preset.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
        }))}
        onChange={(quality_preset) => updateSettings({ quality_preset: quality_preset as QualityPresetType })}
        disabled={disabled}
        tooltip="Overall quality and resolution preset"
      />

      <label className="checkbox-item">
        <input
          type="checkbox"
          checked={settings.auto_recommendations}
          onChange={(e) => updateSettings({ auto_recommendations: e.target.checked })}
          disabled={disabled}
        />
        Enable AI-powered recommendations
      </label>
    </div>
  );

  // Preset buttons
  const renderPresetButtons = () => (
    <div className="preset-buttons">
      <button
        onClick={() => updateSettings(getStandardPreset())}
        disabled={disabled || isLoading}
        className="preset-button standard"
      >
        Standard
      </button>
      <button
        onClick={() => updateSettings(getCinematicPreset())}
        disabled={disabled || isLoading}
        className="preset-button cinematic"
      >
        Cinematic
      </button>
      <button
        onClick={() => updateSettings(getPremiumPreset())}
        disabled={disabled || isLoading}
        className="preset-button premium"
      >
        Premium
      </button>
    </div>
  );

  // Validation display
  const renderValidation = () => {
    if (validation.valid && validation.warnings.length === 0) return null;

    return (
      <div className="validation-display">
        {validation.errors.length > 0 && (
          <div className="validation-errors">
            <h4>Errors:</h4>
            <ul>
              {validation.errors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </div>
        )}
        
        {validation.warnings.length > 0 && (
          <div className="validation-warnings">
            <h4>Warnings:</h4>
            <ul>
              {validation.warnings.map((warning, index) => (
                <li key={index}>{warning}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`cinematic-control-panel ${className} ${disabled ? 'disabled' : ''}`}>
      <div className="panel-header">
        <h2>Cinematic Controls</h2>
        <div className="panel-actions">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="toggle-advanced"
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced
          </button>
          {showPreview && (
            <button
              onClick={() => {
                setPreviewMode(!previewMode);
                if (!previewMode) {
                  onPreview?.(settings);
                }
              }}
              disabled={disabled || isLoading || !validation.valid}
              className={`preview-button ${previewMode ? 'active' : ''}`}
            >
              {previewMode ? 'Stop Preview' : 'Preview'}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="error-display">
          <strong>Error:</strong> {error}
        </div>
      )}

      {renderPresetButtons()}
      {renderGeneralSettings()}
      {renderCameraMovementControls()}
      {renderColorGradingControls()}
      {renderSoundDesignControls()}
      {renderAdvancedCompositingControls()}
      {renderValidation()}

      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-spinner">Loading...</div>
        </div>
      )}
    </div>
  );
};