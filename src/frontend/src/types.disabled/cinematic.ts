/**
 * TypeScript types for cinematic features.
 * Defines interfaces for settings, profiles, and API responses.
 */

export enum CameraMovementType {
  STATIC = "static",
  PAN = "pan",
  ZOOM = "zoom",
  DOLLY = "dolly",
  CRANE = "crane",
  HANDHELD = "handheld"
}

export enum FilmEmulationType {
  NONE = "none",
  KODAK = "kodak",
  FUJI = "fuji",
  CINEMA = "cinema"
}

export enum QualityPresetType {
  STANDARD_HD = "standard_hd",
  CINEMATIC_4K = "cinematic_4k",
  CINEMATIC_8K = "cinematic_8k"
}

export interface CameraMovementSettings {
  enabled: boolean;
  allowed_types: CameraMovementType[];
  intensity: number; // 0-100
  auto_select: boolean;
}

export interface ColorGradingSettings {
  enabled: boolean;
  film_emulation: FilmEmulationType;
  temperature: number; // -100 to 100
  tint: number; // -100 to 100
  contrast: number; // -100 to 100
  saturation: number; // -100 to 100
  brightness: number; // -100 to 100
  shadows: number; // -100 to 100
  highlights: number; // -100 to 100
  auto_adjust: boolean;
}

export interface SoundDesignSettings {
  enabled: boolean;
  ambient_audio: boolean;
  music_scoring: boolean;
  spatial_audio: boolean;
  reverb_intensity: number; // 0-100
  eq_processing: boolean;
  dynamic_range_compression: boolean;
  auto_select_music: boolean;
}

export interface AdvancedCompositingSettings {
  enabled: boolean;
  film_grain: boolean;
  dynamic_lighting: boolean;
  depth_of_field: boolean;
  motion_blur: boolean;
  professional_transitions: boolean;
  lut_application: boolean;
}

export interface CinematicSettings {
  camera_movements: CameraMovementSettings;
  color_grading: ColorGradingSettings;
  sound_design: SoundDesignSettings;
  advanced_compositing: AdvancedCompositingSettings;
  quality_preset: QualityPresetType;
  auto_recommendations: boolean;
}

export interface CinematicProfile {
  id: string;
  name: string;
  description: string;
  settings: CinematicSettings;
  user_id: string;
  is_default: boolean;
  is_system: boolean;
  created_at: string;
  last_used: string;
  usage_count: number;
  validation: ValidationResult;
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface VisualDescription {
  scene_id: string;
  description: string;
  scene_analysis: Record<string, any>;
  cinematic_recommendations: CinematicSettings;
  suggestions: string[];
  confidence: number;
  generated_by: string;
}

export interface SceneAnalysis {
  mood?: string;
  complexity?: string;
  pacing?: string;
  focus_type?: string;
  confidence?: number;
}

export interface PreviewData {
  preview_url: string;
  thumbnail_url: string;
  estimated_size: string;
  estimated_duration: string;
  processing_time: string;
  effects_applied: string[];
}

export interface PreviewResponse {
  scene_id: string;
  preview_data: PreviewData;
  status: string;
  estimated_completion: string;
}

// API Request/Response types
export interface CreateProfileRequest {
  name: string;
  description: string;
  settings: CinematicSettings;
  user_id?: string;
  set_as_default?: boolean;
}

export interface VisualDescriptionRequest {
  scene_id: string;
  content: string;
  scene_context?: Record<string, any>;
  style_preferences?: Record<string, any>;
}

export interface SceneAnalysisRequest {
  content: string;
  existing_description?: string;
}

export interface PreviewRequest {
  scene_id: string;
  content: string;
  settings: CinematicSettings;
}

// UI State types
export interface CinematicUIState {
  selectedProfile: CinematicProfile | null;
  currentSettings: CinematicSettings;
  isLoading: boolean;
  error: string | null;
  previewMode: boolean;
  showAdvanced: boolean;
}

export interface ProfileManagerState {
  profiles: CinematicProfile[];
  selectedProfileId: string | null;
  isCreating: boolean;
  isEditing: boolean;
  searchQuery: string;
  sortBy: 'name' | 'last_used' | 'usage_count';
  sortOrder: 'asc' | 'desc';
}

export interface VisualDescriptionState {
  content: string;
  description: string;
  isGenerating: boolean;
  suggestions: string[];
  sceneAnalysis: SceneAnalysis | null;
  confidence: number;
  generatedBy: string;
}

// Component Props types
export interface CinematicControlPanelProps {
  initialSettings?: CinematicSettings;
  onSettingsChange?: (settings: CinematicSettings) => void;
  onPreview?: (settings: CinematicSettings) => void;
  disabled?: boolean;
  showPreview?: boolean;
  className?: string;
}

export interface CinematicProfileManagerProps {
  userId?: string;
  onProfileSelect?: (profile: CinematicProfile) => void;
  onProfileChange?: (profile: CinematicProfile) => void;
  selectedProfileId?: string;
  className?: string;
}

export interface VisualDescriptionEditorProps {
  sceneId: string;
  initialContent?: string;
  initialDescription?: string;
  onDescriptionChange?: (description: string) => void;
  onRecommendationsApply?: (settings: CinematicSettings) => void;
  disabled?: boolean;
  className?: string;
}

// Utility types
export type CinematicSettingsKey = keyof CinematicSettings;
export type CameraMovementSettingsKey = keyof CameraMovementSettings;
export type ColorGradingSettingsKey = keyof ColorGradingSettings;
export type SoundDesignSettingsKey = keyof SoundDesignSettings;
export type AdvancedCompositingSettingsKey = keyof AdvancedCompositingSettings;

// Default values
export const DEFAULT_CAMERA_MOVEMENT_SETTINGS: CameraMovementSettings = {
  enabled: true,
  allowed_types: [CameraMovementType.PAN, CameraMovementType.ZOOM],
  intensity: 50,
  auto_select: true
};

export const DEFAULT_COLOR_GRADING_SETTINGS: ColorGradingSettings = {
  enabled: true,
  film_emulation: FilmEmulationType.NONE,
  temperature: 0,
  tint: 0,
  contrast: 0,
  saturation: 0,
  brightness: 0,
  shadows: 0,
  highlights: 0,
  auto_adjust: true
};

export const DEFAULT_SOUND_DESIGN_SETTINGS: SoundDesignSettings = {
  enabled: true,
  ambient_audio: true,
  music_scoring: true,
  spatial_audio: false,
  reverb_intensity: 30,
  eq_processing: true,
  dynamic_range_compression: true,
  auto_select_music: true
};

export const DEFAULT_ADVANCED_COMPOSITING_SETTINGS: AdvancedCompositingSettings = {
  enabled: true,
  film_grain: true,
  dynamic_lighting: true,
  depth_of_field: false,
  motion_blur: false,
  professional_transitions: true,
  lut_application: true
};

export const DEFAULT_CINEMATIC_SETTINGS: CinematicSettings = {
  camera_movements: DEFAULT_CAMERA_MOVEMENT_SETTINGS,
  color_grading: DEFAULT_COLOR_GRADING_SETTINGS,
  sound_design: DEFAULT_SOUND_DESIGN_SETTINGS,
  advanced_compositing: DEFAULT_ADVANCED_COMPOSITING_SETTINGS,
  quality_preset: QualityPresetType.CINEMATIC_4K,
  auto_recommendations: true
};

// Validation helpers
export const validateCinematicSettings = (settings: CinematicSettings): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Validate camera movement intensity
  if (settings.camera_movements.intensity < 0 || settings.camera_movements.intensity > 100) {
    errors.push("Camera movement intensity must be between 0 and 100");
  }

  // Validate color grading values
  const colorFields: (keyof ColorGradingSettings)[] = [
    'temperature', 'tint', 'contrast', 'saturation', 'brightness', 'shadows', 'highlights'
  ];
  
  for (const field of colorFields) {
    const value = settings.color_grading[field] as number;
    if (typeof value === 'number' && (value < -100 || value > 100)) {
      errors.push(`Color grading ${field} must be between -100 and 100`);
    }
  }

  // Validate sound design reverb intensity
  if (settings.sound_design.reverb_intensity < 0 || settings.sound_design.reverb_intensity > 100) {
    errors.push("Sound design reverb intensity must be between 0 and 100");
  }

  // Generate warnings
  if (settings.camera_movements.intensity > 80 && settings.advanced_compositing.motion_blur) {
    warnings.push("High camera movement intensity with motion blur may cause excessive blur");
  }

  if (settings.color_grading.saturation > 50) {
    warnings.push("Very high saturation may cause unnatural colors");
  }

  if (settings.color_grading.contrast > 50) {
    warnings.push("Very high contrast may reduce detail visibility");
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
};

// Helper functions
export const cloneSettings = (settings: CinematicSettings): CinematicSettings => {
  return JSON.parse(JSON.stringify(settings));
};

export const mergeSettings = (base: CinematicSettings, override: Partial<CinematicSettings>): CinematicSettings => {
  return {
    ...base,
    ...override,
    camera_movements: { ...base.camera_movements, ...override.camera_movements },
    color_grading: { ...base.color_grading, ...override.color_grading },
    sound_design: { ...base.sound_design, ...override.sound_design },
    advanced_compositing: { ...base.advanced_compositing, ...override.advanced_compositing }
  };
};

// YouTube Optimization Types
export interface YouTubeEncodingParams {
  video_codec: string;
  audio_codec: string;
  resolution: [number, number];
  frame_rate: number;
  video_bitrate: number;
  audio_bitrate: number;
  pixel_format: string;
}

export interface SEOMetadata {
  title: string;
  description: string;
  tags: string[];
  category: string;
  language: string;
  thumbnail_suggestions: ThumbnailSuggestion[];
  chapter_markers: ChapterMarker[];
}

export interface ThumbnailSuggestion {
  title: string;
  description: string;
  engagement_score: number;
  style: string;
  timestamp?: number;
}

export interface ChapterMarker {
  timestamp: number;
  title: string;
  description?: string;
}

export interface ThumbnailSettings {
  generate_thumbnails: boolean;
  thumbnail_count: number;
  include_text_overlay: boolean;
  style: 'engaging' | 'professional' | 'minimal';
}

export interface IntroOutroSettings {
  add_intro: boolean;
  add_outro: boolean;
  intro_duration: number;
  outro_duration: number;
  branding_elements: boolean;
}

export interface EngagementFeatures {
  add_end_screens: boolean;
  add_cards: boolean;
  optimize_for_retention: boolean;
  include_call_to_action: boolean;
}

export interface YouTubeOptimizationSettings {
  encoding_params: YouTubeEncodingParams;
  seo_metadata: SEOMetadata;
  thumbnail_settings: ThumbnailSettings;
  intro_outro: IntroOutroSettings;
  engagement_features: EngagementFeatures;
}

// Social Media Types
export enum SocialPlatform {
  YOUTUBE = 'youtube',
  INSTAGRAM = 'instagram',
  TIKTOK = 'tiktok',
  LINKEDIN = 'linkedin',
  TWITTER = 'twitter',
  FACEBOOK = 'facebook'
}

export interface ContentOptimization {
  pacing_multiplier: number;
  visual_density: string;
  text_size: string;
  subtitles_required: boolean;
  engagement_style: string;
  attention_span_seconds: number;
}

export interface PlatformAdaptation {
  platform: SocialPlatform;
  original_settings: any;
  adapted_settings: any;
  encoding_params: any;
  content_optimizations: ContentOptimization;
  adaptations_applied: Array<{
    type: string;
    reason: string;
    original?: any;
    adapted?: any;
  }>;
  estimated_performance_score: number;
  compliance_status: string;
}

// Accessibility Types
export enum WCAGLevel {
  A = 'A',
  AA = 'AA',
  AAA = 'AAA'
}

export enum AccessibilityIssueType {
  COLOR_CONTRAST = 'color_contrast',
  FLASHING_CONTENT = 'flashing_content',
  AUDIO_DESCRIPTION = 'audio_description',
  CAPTIONS = 'captions',
  LANGUAGE_CLARITY = 'language_clarity',
  NAVIGATION = 'navigation',
  TIMING = 'timing'
}

export interface ColorContrastResult {
  foreground_color: string;
  background_color: string;
  contrast_ratio: number;
  wcag_aa_pass: boolean;
  wcag_aaa_pass: boolean;
  recommendations: string[];
}

export interface FlashingContentResult {
  has_flashing: boolean;
  flash_frequency: number;
  flash_duration: number;
  risk_level: string;
  recommendations: string[];
}

export interface CaptionSegment {
  start_time: number;
  end_time: number;
  text: string;
  confidence: number;
  speaker_id?: string;
}

export interface AudioDescriptionSegment {
  start_time: number;
  end_time: number;
  description: string;
  priority: string;
}

export interface AccessibilityReport {
  wcag_level: WCAGLevel;
  overall_compliance: boolean;
  compliance_score: number;
  issues: Array<{
    type: string;
    severity: string;
    description: string;
    location: string;
  }>;
  recommendations: string[];
  color_contrast_results: ColorContrastResult[];
  flashing_content_result?: FlashingContentResult;
  caption_segments: CaptionSegment[];
  audio_descriptions: AudioDescriptionSegment[];
  language_clarity_score: number;
  generated_at: string;
}