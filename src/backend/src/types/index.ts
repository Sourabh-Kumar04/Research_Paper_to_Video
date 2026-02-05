// Core Types for Advanced Video Template Engine

export interface Position {
  x: number;
  y: number;
}

export interface Dimensions {
  width: number;
  height: number;
}

export interface Resolution {
  width: number;
  height: number;
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings?: string[];
}

// Template Types
export interface Template {
  id: string;
  name: string;
  description: string;
  version: string;
  createdAt: Date;
  updatedAt: Date;
  createdBy: string;
  
  // Template Structure
  duration: number;
  resolution: Resolution;
  frameRate: number;
  
  // Content Definition
  contentSlots: ContentSlot[];
  staticAssets: StaticAsset[];
  
  // Animation Definition
  animations: Animation[];
  transitions: Transition[];
  
  // Interactive Elements
  chapters: Chapter[];
  annotations: Annotation[];
  hotspots: Hotspot[];
  
  // Metadata
  tags: string[];
  category: string;
  thumbnail: string;
  previewVideo?: string;
}

export interface TemplateDefinition {
  name: string;
  description: string;
  duration: number;
  resolution: Resolution;
  contentSlots: ContentSlot[];
  animations: Animation[];
  interactiveElements: InteractiveElement[];
  metadata: TemplateMetadata;
}

export interface ContentSlot {
  id: string;
  type: 'text' | 'image' | 'video' | 'audio';
  position: Position;
  dimensions: Dimensions;
  duration?: number;
  constraints: SlotConstraints;
}

export interface SlotConstraints {
  maxFileSize?: number;
  allowedFormats?: string[];
  maxDuration?: number;
  minDuration?: number;
  aspectRatio?: number;
  required: boolean;
}

export interface StaticAsset {
  id: string;
  type: 'image' | 'video' | 'audio' | 'font';
  url: string;
  metadata: AssetMetadata;
}

export interface AssetMetadata {
  filename: string;
  fileSize: number;
  mimeType: string;
  duration?: number;
  resolution?: Resolution;
}

// Animation Types
export interface Animation {
  id: string;
  targetSlotId: string;
  type: 'motion' | 'scale' | 'rotation' | 'opacity' | 'color';
  keyframes: Keyframe[];
  easing: EasingFunction;
  duration: number;
  delay: number;
}

export interface Keyframe {
  time: number; // 0-1 normalized time
  value: any; // Animation-specific value
  easing?: EasingFunction;
}

export type EasingFunction = 'linear' | 'ease-in' | 'ease-out' | 'ease-in-out' | 'cubic-bezier';

export interface Transition {
  id: string;
  type: 'fade' | 'slide' | 'zoom' | 'wipe' | 'custom';
  duration: number;
  parameters: Record<string, any>;
}

// Interactive Elements
export interface InteractiveElement {
  id: string;
  type: 'chapter' | 'annotation' | 'hotspot';
  timestamp: number;
  duration?: number;
  position?: Position;
  data: any;
}

export interface Chapter {
  id: string;
  title: string;
  timestamp: number;
  thumbnail?: string;
}

export interface Annotation {
  id: string;
  text: string;
  timestamp: number;
  duration: number;
  position: Position;
  style: AnnotationStyle;
}

export interface AnnotationStyle {
  fontSize: number;
  fontColor: string;
  backgroundColor: string;
  borderColor?: string;
  opacity: number;
}

export interface Hotspot {
  id: string;
  timestamp: number;
  duration: number;
  position: Position;
  dimensions: Dimensions;
  action: HotspotAction;
}

export interface HotspotAction {
  type: 'link' | 'pause' | 'seek' | 'custom';
  parameters: Record<string, any>;
}

// Content Types
export interface ContentSet {
  templateId: string;
  name: string;
  contentItems: Map<string, ContentItem>;
  metadata: ContentMetadata;
}

export interface ContentItem {
  slotId: string;
  type: 'text' | 'image' | 'video' | 'audio';
  data: any;
  metadata: ItemMetadata;
}

export interface ProcessedContent extends ContentItem {
  optimizedData: any;
  processingMetadata: ProcessingMetadata;
  validationResult: ValidationResult;
}

export interface ContentMetadata {
  createdAt: Date;
  createdBy: string;
  version: string;
}

export interface ItemMetadata {
  filename?: string;
  fileSize?: number;
  mimeType?: string;
  duration?: number;
  resolution?: Resolution;
}

export interface ProcessingMetadata {
  processedAt: Date;
  processingTime: number;
  optimizations: string[];
}

// Output Types
export interface OutputSpecs {
  format: 'mp4' | 'webm' | 'mov';
  resolution: Resolution;
  quality: QualityPreset;
  compression: CompressionSettings;
  interactive: boolean;
}

export type QualityPreset = '4k' | '1080p' | '720p' | 'mobile';

export interface CompressionSettings {
  videoBitrate: number;
  audioBitrate: number;
  codec: string;
  preset: string;
}

export interface OutputFile {
  id: string;
  format: string;
  resolution: Resolution;
  fileSize: number;
  duration: number;
  url: string;
  downloadUrl: string;
  metadata: OutputMetadata;
  interactivePackage?: InteractivePackage;
}

export interface OutputMetadata {
  generatedAt: Date;
  processingTime: number;
  quality: QualityPreset;
  compression: CompressionSettings;
}

export interface InteractivePackage {
  videoFile: string;
  webvttTracks: WebVTTTrack[];
  hotspotData: HotspotData[];
  chapterMarkers: ChapterMarker[];
  playerConfig: PlayerConfiguration;
}

export interface WebVTTTrack {
  kind: 'subtitles' | 'captions' | 'chapters' | 'metadata';
  language: string;
  label: string;
  content: string;
}

export interface HotspotData {
  id: string;
  startTime: number;
  endTime: number;
  coordinates: Position;
  dimensions: Dimensions;
  action: HotspotAction;
}

export interface ChapterMarker {
  id: string;
  title: string;
  startTime: number;
  thumbnail?: string;
}

export interface PlayerConfiguration {
  controls: boolean;
  autoplay: boolean;
  loop: boolean;
  muted: boolean;
  interactiveFeatures: string[];
}

// Rendering Types
export interface RenderJob {
  id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  estimatedCompletion: Date;
  outputs: OutputFile[];
  errors?: RenderError[];
}

export interface RenderError {
  code: string;
  message: string;
  timestamp: Date;
  details?: any;
}

export interface RenderProgress {
  jobId: string;
  progress: number;
  currentStage: string;
  estimatedCompletion: Date;
  processedFrames: number;
  totalFrames: number;
}

// Service Interfaces
export interface TemplateMetadata {
  tags: string[];
  category: string;
  description: string;
  thumbnail?: string;
}

export interface SharingPermissions {
  public: boolean;
  allowedUsers: string[];
  allowModification: boolean;
  attribution: string;
}

export interface ShareLink {
  id: string;
  url: string;
  expiresAt?: Date;
  permissions: SharingPermissions;
}

export interface SlotRequirements {
  type: ContentSlot['type'];
  constraints: SlotConstraints;
  position: Position;
  dimensions: Dimensions;
}

export interface OptimizedContent extends ProcessedContent {
  optimizationLevel: number;
  compressionRatio: number;
}