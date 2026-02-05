import { v4 as uuidv4 } from 'uuid';
import sharp from 'sharp';
import { 
  ContentItem, 
  ProcessedContent, 
  ValidationResult, 
  SlotRequirements,
  ContentSet,
  OptimizedContent,
  OutputSpecs
} from '../types';

export class ContentService {
  private static instance: ContentService;

  private constructor() {}

  public static getInstance(): ContentService {
    if (!ContentService.instance) {
      ContentService.instance = new ContentService();
    }
    return ContentService.instance;
  }

  public validateContent(slotId: string, content: ContentItem): ValidationResult {
    const errors: string[] = [];

    // Basic validation
    if (!content.slotId || content.slotId !== slotId) {
      errors.push('Content slot ID mismatch');
    }

    if (!content.type || !['text', 'image', 'video', 'audio'].includes(content.type)) {
      errors.push('Invalid content type');
    }

    if (!content.data) {
      errors.push('Content data is required');
    }

    // Type-specific validation
    switch (content.type) {
      case 'text':
        if (typeof content.data !== 'string' || content.data.trim().length === 0) {
          errors.push('Text content must be a non-empty string');
        }
        break;
      case 'image':
        if (!content.metadata?.mimeType?.startsWith('image/')) {
          errors.push('Invalid image format');
        }
        break;
      case 'video':
        if (!content.metadata?.mimeType?.startsWith('video/')) {
          errors.push('Invalid video format');
        }
        break;
      case 'audio':
        if (!content.metadata?.mimeType?.startsWith('audio/')) {
          errors.push('Invalid audio format');
        }
        break;
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  public async processContent(content: ContentItem, requirements: SlotRequirements): Promise<ProcessedContent> {
    const startTime = Date.now();
    
    // Validate content first
    const validation = this.validateContent(requirements.type, content);
    if (!validation.isValid) {
      throw new Error(`Content validation failed: ${validation.errors.join(', ')}`);
    }

    let optimizedData = content.data;
    const optimizations: string[] = [];

    // Process based on content type
    switch (content.type) {
      case 'image':
        optimizedData = await this.processImage(content, requirements);
        optimizations.push('image_resize', 'format_optimization');
        break;
      case 'video':
        optimizedData = await this.processVideo(content, requirements);
        optimizations.push('video_resize', 'compression');
        break;
      case 'audio':
        optimizedData = await this.processAudio(content, requirements);
        optimizations.push('audio_compression');
        break;
      case 'text':
        optimizedData = this.processText(content, requirements);
        optimizations.push('text_formatting');
        break;
    }

    const processingTime = Date.now() - startTime;

    return {
      ...content,
      optimizedData,
      processingMetadata: {
        processedAt: new Date(),
        processingTime,
        optimizations
      },
      validationResult: validation
    };
  }

  public async batchProcessContent(contentSets: ContentSet[]): Promise<ProcessedContent[]> {
    const results: ProcessedContent[] = [];
    
    for (const contentSet of contentSets) {
      for (const [slotId, content] of contentSet.contentItems) {
        try {
          // Mock slot requirements - in real implementation, would fetch from template
          const requirements: SlotRequirements = {
            type: content.type,
            constraints: {
              maxFileSize: 10 * 1024 * 1024, // 10MB
              required: true
            },
            position: { x: 0, y: 0 },
            dimensions: { width: 1920, height: 1080 }
          };

          const processed = await this.processContent(content, requirements);
          results.push(processed);
        } catch (error) {
          console.error(`Failed to process content for slot ${slotId}:`, error);
          // Continue processing other content items
        }
      }
    }

    return results;
  }

  public async optimizeContent(content: ContentItem, targetSpecs: OutputSpecs): Promise<OptimizedContent> {
    const processed = await this.processContent(content, {
      type: content.type,
      constraints: { required: true },
      position: { x: 0, y: 0 },
      dimensions: targetSpecs.resolution
    });

    return {
      ...processed,
      optimizationLevel: this.calculateOptimizationLevel(targetSpecs),
      compressionRatio: this.calculateCompressionRatio(content, processed)
    };
  }

  private async processImage(content: ContentItem, requirements: SlotRequirements): Promise<any> {
    if (!Buffer.isBuffer(content.data)) {
      return content.data; // Return as-is if not a buffer
    }

    try {
      let image = sharp(content.data);
      
      // Resize if needed
      if (requirements.dimensions) {
        image = image.resize(
          requirements.dimensions.width,
          requirements.dimensions.height,
          { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } }
        );
      }

      // Optimize format
      const metadata = await image.metadata();
      if (metadata.format === 'png' && !metadata.hasAlpha) {
        image = image.jpeg({ quality: 85 });
      }

      return await image.toBuffer();
    } catch (error) {
      console.error('Image processing failed:', error);
      return content.data;
    }
  }

  private async processVideo(content: ContentItem, requirements: SlotRequirements): Promise<any> {
    // Video processing would use FFmpeg here
    // For now, return original data
    return content.data;
  }

  private async processAudio(content: ContentItem, requirements: SlotRequirements): Promise<any> {
    // Audio processing would use FFmpeg here
    // For now, return original data
    return content.data;
  }

  private processText(content: ContentItem, requirements: SlotRequirements): any {
    if (typeof content.data !== 'string') {
      return content.data;
    }

    // Basic text processing
    let text = content.data.trim();
    
    // Remove excessive whitespace
    text = text.replace(/\s+/g, ' ');
    
    // Ensure text fits within constraints
    if (requirements.constraints.maxDuration) {
      // Estimate reading time (average 200 words per minute)
      const wordCount = text.split(' ').length;
      const estimatedDuration = (wordCount / 200) * 60;
      
      if (estimatedDuration > requirements.constraints.maxDuration) {
        // Truncate text to fit duration
        const maxWords = Math.floor((requirements.constraints.maxDuration / 60) * 200);
        text = text.split(' ').slice(0, maxWords).join(' ') + '...';
      }
    }

    return text;
  }

  private calculateOptimizationLevel(specs: OutputSpecs): number {
    // Calculate optimization level based on quality preset
    const qualityLevels = {
      '4k': 0.9,
      '1080p': 0.7,
      '720p': 0.5,
      'mobile': 0.3
    };

    return qualityLevels[specs.quality] || 0.5;
  }

  private calculateCompressionRatio(original: ContentItem, processed: ProcessedContent): number {
    const originalSize = original.metadata?.fileSize || 0;
    const processedSize = processed.metadata?.fileSize || originalSize;
    
    if (originalSize === 0) return 1.0;
    
    return processedSize / originalSize;
  }
}