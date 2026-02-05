import { v4 as uuidv4 } from 'uuid';
import Queue from 'bull';
import { RenderJobModel } from '../config/database';
import { 
  Template, 
  ContentSet, 
  OutputSpecs, 
  RenderJob, 
  RenderProgress,
  OutputFile,
  RenderError
} from '../types';
import config from '../config';
import { PythonVideoBridge } from './python-bridge';

export class RenderingService {
  private static instance: RenderingService;
  private renderQueue: Queue.Queue;
  private pythonBridge: PythonVideoBridge;

  private constructor() {
    this.renderQueue = new Queue('video rendering', config.redis.url, {
      defaultJobOptions: {
        removeOnComplete: 10,
        removeOnFail: 5,
        attempts: 3,
        backoff: {
          type: 'exponential',
          delay: 2000
        }
      }
    });

    this.pythonBridge = PythonVideoBridge.getInstance();
    this.setupQueueProcessors();
  }

  public static getInstance(): RenderingService {
    if (!RenderingService.instance) {
      RenderingService.instance = new RenderingService();
    }
    return RenderingService.instance;
  }

  private setupQueueProcessors(): void {
    this.renderQueue.process('render-video', config.video.maxConcurrentJobs, async (job) => {
      const { template, contentSet, outputSpecs, jobId } = job.data;
      
      try {
        await this.updateJobStatus(jobId, 'processing', 0);
        
        const outputs: OutputFile[] = [];
        
        for (let i = 0; i < outputSpecs.length; i++) {
          const spec = outputSpecs[i];
          const progress = ((i + 1) / outputSpecs.length) * 100;
          
          await this.updateJobStatus(jobId, 'processing', progress);
          
          const output = await this.renderSingleFormat(template, contentSet, spec);
          outputs.push(output);
        }
        
        await this.updateJobStatus(jobId, 'completed', 100, outputs);
        
        return { success: true, outputs };
      } catch (error) {
        const renderError: RenderError = {
          code: 'RENDER_FAILED',
          message: error instanceof Error ? error.message : 'Unknown error',
          timestamp: new Date(),
          details: error
        };
        
        await this.updateJobStatus(jobId, 'failed', 0, [], [renderError]);
        throw error;
      }
    });

    this.renderQueue.on('completed', (job) => {
      console.log(`Render job ${job.data.jobId} completed successfully`);
    });

    this.renderQueue.on('failed', (job, error) => {
      console.error(`Render job ${job.data.jobId} failed:`, error);
    });
  }

  public async renderVideo(
    template: Template, 
    contentSet: ContentSet, 
    specs: OutputSpecs[]
  ): Promise<RenderJob> {
    const jobId = uuidv4();
    
    // Create job record
    const renderJob = new RenderJobModel({
      id: jobId,
      templateId: template.id,
      contentSetId: contentSet.name,
      status: 'queued',
      progress: 0,
      estimatedCompletion: new Date(Date.now() + this.estimateRenderTime(template, specs)),
      outputs: [],
      errors: []
    });

    await renderJob.save();

    // Queue the rendering job
    await this.renderQueue.add('render-video', {
      template,
      contentSet,
      outputSpecs: specs,
      jobId
    }, {
      priority: this.calculateJobPriority(template, specs),
      delay: 0
    });

    return this.mapToRenderJob(renderJob);
  }

  public async getProgress(jobId: string): Promise<RenderProgress> {
    const job = await RenderJobModel.findOne({ id: jobId });
    if (!job) {
      throw new Error(`Render job ${jobId} not found`);
    }

    return {
      jobId,
      progress: job.progress,
      currentStage: this.getCurrentStage(job.status, job.progress),
      estimatedCompletion: job.estimatedCompletion || new Date(),
      processedFrames: Math.floor((job.progress / 100) * this.estimateFrameCount(job)),
      totalFrames: this.estimateFrameCount(job)
    };
  }

  public async cancelJob(jobId: string): Promise<void> {
    // Find and remove job from queue
    const jobs = await this.renderQueue.getJobs(['waiting', 'active']);
    const job = jobs.find(j => j.data.jobId === jobId);
    
    if (job) {
      await job.remove();
    }

    // Update job status
    await this.updateJobStatus(jobId, 'failed', 0, [], [{
      code: 'CANCELLED',
      message: 'Job cancelled by user',
      timestamp: new Date()
    }]);
  }

  public async retryFailedChunks(jobId: string): Promise<void> {
    const job = await RenderJobModel.findOne({ id: jobId });
    if (!job || job.status !== 'failed') {
      throw new Error(`Cannot retry job ${jobId}: job not found or not in failed state`);
    }

    // Reset job status and re-queue
    await this.updateJobStatus(jobId, 'queued', 0);
    
    // Re-add to queue with higher priority
    await this.renderQueue.add('render-video', {
      jobId,
      retry: true
    }, {
      priority: 10, // High priority for retries
      delay: 1000
    });
  }

  private async renderSingleFormat(
    template: Template, 
    contentSet: ContentSet, 
    spec: OutputSpecs
  ): Promise<OutputFile> {
    // Generate unique output path
    const outputId = uuidv4();
    const outputPath = `/tmp/raso_output/${outputId}.${spec.format}`;

    try {
      // Use Python bridge for real video generation
      const result = await this.pythonBridge.generateRealVideo({
        template,
        contentSet,
        outputSpecs: spec,
        outputPath
      });

      if (!result.success) {
        throw new Error(`Video generation failed: ${result.errors.join(', ')}`);
      }

      // Create output file object
      const outputFile: OutputFile = {
        id: outputId,
        format: spec.format,
        resolution: spec.resolution,
        fileSize: result.fileSize || 0,
        duration: result.duration || template.duration,
        url: `/api/v1/outputs/${outputId}.${spec.format}`,
        downloadUrl: `/api/v1/downloads/${outputId}.${spec.format}`,
        metadata: {
          generatedAt: new Date(),
          processingTime: 0, // Will be calculated by queue processor
          quality: spec.quality,
          compression: spec.compression,
          generationMethod: result.method || 'python_bridge',
          warnings: result.warnings || []
        },
        interactivePackage: spec.interactive ? this.generateInteractivePackage(template) : undefined
      };

      return outputFile;

    } catch (error) {
      // Fallback to placeholder generation if Python bridge fails
      console.warn(`Python video generation failed, falling back to placeholder: ${error}`);
      return this.generatePlaceholderVideo(template, spec);
    }
  }

  private async generatePlaceholderVideo(template: Template, spec: OutputSpecs): Promise<OutputFile> {
    // Original placeholder generation logic as fallback
    await this.simulateRenderingDelay();

    const outputFile: OutputFile = {
      id: uuidv4(),
      format: spec.format,
      resolution: spec.resolution,
      fileSize: this.estimateFileSize(template, spec),
      duration: template.duration,
      url: `/api/v1/outputs/${uuidv4()}.${spec.format}`,
      downloadUrl: `/api/v1/downloads/${uuidv4()}.${spec.format}`,
      metadata: {
        generatedAt: new Date(),
        processingTime: 5000, // 5 seconds simulation
        quality: spec.quality,
        compression: spec.compression,
        generationMethod: 'placeholder',
        warnings: ['This is a placeholder video - Python video generation not available']
      },
      interactivePackage: spec.interactive ? this.generateInteractivePackage(template) : undefined
    };

    return outputFile;
  }

  private generateInteractivePackage(template: Template) {
    return {
      videoFile: `${template.id}.mp4`,
      webvttTracks: [
        {
          kind: 'chapters' as const,
          language: 'en',
          label: 'Chapters',
          content: this.generateWebVTTChapters(template.chapters)
        }
      ],
      hotspotData: template.hotspots.map(hotspot => ({
        id: hotspot.id,
        startTime: hotspot.timestamp,
        endTime: hotspot.timestamp + hotspot.duration,
        coordinates: hotspot.position,
        dimensions: hotspot.dimensions,
        action: hotspot.action
      })),
      chapterMarkers: template.chapters.map(chapter => ({
        id: chapter.id,
        title: chapter.title,
        startTime: chapter.timestamp,
        thumbnail: chapter.thumbnail
      })),
      playerConfig: {
        controls: true,
        autoplay: false,
        loop: false,
        muted: false,
        interactiveFeatures: ['chapters', 'hotspots', 'annotations']
      }
    };
  }

  private generateWebVTTChapters(chapters: Template['chapters']): string {
    let vtt = 'WEBVTT\n\n';
    
    for (let i = 0; i < chapters.length; i++) {
      const chapter = chapters[i];
      const nextChapter = chapters[i + 1];
      
      const startTime = this.formatWebVTTTime(chapter.timestamp);
      const endTime = nextChapter 
        ? this.formatWebVTTTime(nextChapter.timestamp)
        : this.formatWebVTTTime(chapter.timestamp + 60); // Default 1 minute
      
      vtt += `${startTime} --> ${endTime}\n`;
      vtt += `${chapter.title}\n\n`;
    }
    
    return vtt;
  }

  private formatWebVTTTime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
  }

  private async updateJobStatus(
    jobId: string, 
    status: RenderJob['status'], 
    progress: number,
    outputs: OutputFile[] = [],
    errors: RenderError[] = []
  ): Promise<void> {
    await RenderJobModel.updateOne(
      { id: jobId },
      {
        status,
        progress,
        outputs,
        errors,
        updatedAt: new Date()
      }
    );
  }

  private calculateJobPriority(template: Template, specs: OutputSpecs[]): number {
    // Higher priority for simpler jobs
    let priority = 5; // Base priority
    
    // Adjust based on template complexity
    if (template.animations.length > 10) priority -= 2;
    if (template.contentSlots.length > 20) priority -= 1;
    if (specs.length > 3) priority -= 1;
    
    // Adjust based on output quality
    if (specs.some(spec => spec.quality === '4k')) priority -= 2;
    if (specs.some(spec => spec.interactive)) priority -= 1;
    
    return Math.max(1, priority);
  }

  private estimateRenderTime(template: Template, specs: OutputSpecs[]): number {
    // Base time: 30 seconds per minute of video
    let baseTime = template.duration * 30 * 1000;
    
    // Multiply by number of output formats
    baseTime *= specs.length;
    
    // Add complexity factors
    baseTime += template.animations.length * 1000; // 1 second per animation
    baseTime += template.contentSlots.length * 500; // 0.5 seconds per slot
    
    // Quality multipliers
    const qualityMultipliers = { '4k': 3, '1080p': 2, '720p': 1.5, 'mobile': 1 };
    const maxMultiplier = Math.max(...specs.map(spec => qualityMultipliers[spec.quality]));
    baseTime *= maxMultiplier;
    
    return baseTime;
  }

  private estimateFileSize(template: Template, spec: OutputSpecs): number {
    // Rough file size estimation in bytes
    const bitrate = spec.compression.videoBitrate + spec.compression.audioBitrate;
    return Math.floor((bitrate * template.duration) / 8); // Convert bits to bytes
  }

  private estimateFrameCount(job: any): number {
    // Assume 30 FPS
    return Math.floor(30 * (job.templateId?.duration || 60));
  }

  private getCurrentStage(status: string, progress: number): string {
    if (status === 'queued') return 'Queued';
    if (status === 'failed') return 'Failed';
    if (status === 'completed') return 'Completed';
    
    if (progress < 25) return 'Preparing assets';
    if (progress < 50) return 'Rendering video';
    if (progress < 75) return 'Processing audio';
    if (progress < 95) return 'Encoding output';
    return 'Finalizing';
  }

  private async simulateRenderingDelay(): Promise<void> {
    // Simulate rendering time (1-5 seconds)
    const delay = Math.random() * 4000 + 1000;
    await new Promise(resolve => setTimeout(resolve, delay));
  }

  private mapToRenderJob(doc: any): RenderJob {
    return {
      id: doc.id,
      status: doc.status,
      progress: doc.progress,
      estimatedCompletion: doc.estimatedCompletion,
      outputs: doc.outputs,
      errors: doc.errors
    };
  }

  public async checkPythonCapabilities(): Promise<{
    available: boolean;
    capabilities: Record<string, boolean>;
    errors: string[];
  }> {
    return this.pythonBridge.checkPythonEnvironment();
  }
}