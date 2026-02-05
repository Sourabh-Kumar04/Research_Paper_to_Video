import mongoose from 'mongoose';
import { createClient } from 'redis';

export class DatabaseConfig {
  private static instance: DatabaseConfig;
  private mongoConnection?: mongoose.Connection;
  private redisClient?: ReturnType<typeof createClient>;

  private constructor() {}

  public static getInstance(): DatabaseConfig {
    if (!DatabaseConfig.instance) {
      DatabaseConfig.instance = new DatabaseConfig();
    }
    return DatabaseConfig.instance;
  }

  public async connectMongoDB(): Promise<void> {
    try {
      const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/video-template-engine';
      
      await mongoose.connect(mongoUri, {
        maxPoolSize: 10,
        serverSelectionTimeoutMS: 5000,
        socketTimeoutMS: 45000,
      });

      this.mongoConnection = mongoose.connection;
      
      this.mongoConnection.on('error', (error) => {
        console.error('MongoDB connection error:', error);
      });

      this.mongoConnection.on('disconnected', () => {
        console.log('MongoDB disconnected');
      });

      console.log('MongoDB connected successfully');
    } catch (error) {
      console.error('Failed to connect to MongoDB:', error);
      throw error;
    }
  }

  public async connectRedis(): Promise<void> {
    try {
      const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
      
      this.redisClient = createClient({
        url: redisUrl,
        socket: {
          connectTimeout: 5000,
          lazyConnect: true,
        },
      });

      this.redisClient.on('error', (error) => {
        console.error('Redis connection error:', error);
      });

      this.redisClient.on('connect', () => {
        console.log('Redis connected successfully');
      });

      await this.redisClient.connect();
    } catch (error) {
      console.error('Failed to connect to Redis:', error);
      throw error;
    }
  }

  public getRedisClient() {
    if (!this.redisClient) {
      throw new Error('Redis client not initialized');
    }
    return this.redisClient;
  }

  public async disconnect(): Promise<void> {
    if (this.mongoConnection) {
      await mongoose.disconnect();
    }
    
    if (this.redisClient) {
      await this.redisClient.quit();
    }
  }
}

// MongoDB Schemas
const templateSchema = new mongoose.Schema({
  name: { type: String, required: true },
  description: { type: String, required: true },
  version: { type: String, required: true, default: '1.0.0' },
  createdBy: { type: String, required: true },
  duration: { type: Number, required: true },
  resolution: {
    width: { type: Number, required: true },
    height: { type: Number, required: true }
  },
  frameRate: { type: Number, default: 30 },
  contentSlots: [{
    id: { type: String, required: true },
    type: { type: String, enum: ['text', 'image', 'video', 'audio'], required: true },
    position: {
      x: { type: Number, required: true },
      y: { type: Number, required: true }
    },
    dimensions: {
      width: { type: Number, required: true },
      height: { type: Number, required: true }
    },
    duration: Number,
    constraints: {
      maxFileSize: Number,
      allowedFormats: [String],
      maxDuration: Number,
      minDuration: Number,
      aspectRatio: Number,
      required: { type: Boolean, default: false }
    }
  }],
  staticAssets: [{
    id: { type: String, required: true },
    type: { type: String, enum: ['image', 'video', 'audio', 'font'], required: true },
    url: { type: String, required: true },
    metadata: {
      filename: String,
      fileSize: Number,
      mimeType: String,
      duration: Number,
      resolution: {
        width: Number,
        height: Number
      }
    }
  }],
  animations: [{
    id: { type: String, required: true },
    targetSlotId: { type: String, required: true },
    type: { type: String, enum: ['motion', 'scale', 'rotation', 'opacity', 'color'], required: true },
    keyframes: [{
      time: { type: Number, required: true },
      value: mongoose.Schema.Types.Mixed,
      easing: { type: String, enum: ['linear', 'ease-in', 'ease-out', 'ease-in-out', 'cubic-bezier'] }
    }],
    easing: { type: String, enum: ['linear', 'ease-in', 'ease-out', 'ease-in-out', 'cubic-bezier'], default: 'linear' },
    duration: { type: Number, required: true },
    delay: { type: Number, default: 0 }
  }],
  transitions: [{
    id: { type: String, required: true },
    type: { type: String, enum: ['fade', 'slide', 'zoom', 'wipe', 'custom'], required: true },
    duration: { type: Number, required: true },
    parameters: mongoose.Schema.Types.Mixed
  }],
  chapters: [{
    id: { type: String, required: true },
    title: { type: String, required: true },
    timestamp: { type: Number, required: true },
    thumbnail: String
  }],
  annotations: [{
    id: { type: String, required: true },
    text: { type: String, required: true },
    timestamp: { type: Number, required: true },
    duration: { type: Number, required: true },
    position: {
      x: { type: Number, required: true },
      y: { type: Number, required: true }
    },
    style: {
      fontSize: { type: Number, default: 16 },
      fontColor: { type: String, default: '#ffffff' },
      backgroundColor: { type: String, default: '#000000' },
      borderColor: String,
      opacity: { type: Number, default: 1.0 }
    }
  }],
  hotspots: [{
    id: { type: String, required: true },
    timestamp: { type: Number, required: true },
    duration: { type: Number, required: true },
    position: {
      x: { type: Number, required: true },
      y: { type: Number, required: true }
    },
    dimensions: {
      width: { type: Number, required: true },
      height: { type: Number, required: true }
    },
    action: {
      type: { type: String, enum: ['link', 'pause', 'seek', 'custom'], required: true },
      parameters: mongoose.Schema.Types.Mixed
    }
  }],
  tags: [String],
  category: { type: String, required: true },
  thumbnail: String,
  previewVideo: String
}, {
  timestamps: true,
  versionKey: 'version'
});

const renderJobSchema = new mongoose.Schema({
  templateId: { type: String, required: true },
  contentSetId: { type: String, required: true },
  status: { 
    type: String, 
    enum: ['queued', 'processing', 'completed', 'failed'], 
    default: 'queued' 
  },
  progress: { type: Number, default: 0 },
  estimatedCompletion: Date,
  outputs: [{
    id: { type: String, required: true },
    format: { type: String, required: true },
    resolution: {
      width: { type: Number, required: true },
      height: { type: Number, required: true }
    },
    fileSize: Number,
    duration: Number,
    url: String,
    downloadUrl: String,
    metadata: {
      generatedAt: Date,
      processingTime: Number,
      quality: { type: String, enum: ['4k', '1080p', '720p', 'mobile'] },
      compression: {
        videoBitrate: Number,
        audioBitrate: Number,
        codec: String,
        preset: String
      }
    },
    interactivePackage: {
      videoFile: String,
      webvttTracks: [{
        kind: { type: String, enum: ['subtitles', 'captions', 'chapters', 'metadata'] },
        language: String,
        label: String,
        content: String
      }],
      hotspotData: [mongoose.Schema.Types.Mixed],
      chapterMarkers: [mongoose.Schema.Types.Mixed],
      playerConfig: mongoose.Schema.Types.Mixed
    }
  }],
  errors: [{
    code: String,
    message: String,
    timestamp: { type: Date, default: Date.now },
    details: mongoose.Schema.Types.Mixed
  }]
}, {
  timestamps: true
});

export const TemplateModel = mongoose.model('Template', templateSchema);
export const RenderJobModel = mongoose.model('RenderJob', renderJobSchema);