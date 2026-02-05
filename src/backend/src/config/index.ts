import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

export const config = {
  // Server Configuration
  port: parseInt(process.env.PORT || '3000', 10),
  nodeEnv: process.env.NODE_ENV || 'development',
  
  // Database Configuration
  mongodb: {
    uri: process.env.MONGODB_URI || 'mongodb://localhost:27017/video-template-engine',
  },
  redis: {
    url: process.env.REDIS_URL || 'redis://localhost:6379',
  },
  
  // File Storage Configuration
  storage: {
    path: process.env.STORAGE_PATH || './storage',
    maxFileSize: process.env.MAX_FILE_SIZE || '100MB',
  },
  
  // Video Processing Configuration
  video: {
    ffmpegPath: process.env.FFMPEG_PATH || '/usr/local/bin/ffmpeg',
    maxConcurrentJobs: parseInt(process.env.MAX_CONCURRENT_JOBS || '5', 10),
    renderTimeout: parseInt(process.env.RENDER_TIMEOUT || '300000', 10), // 5 minutes
  },
  
  // Authentication Configuration
  auth: {
    jwtSecret: process.env.JWT_SECRET || 'your-jwt-secret-here',
    jwtExpiresIn: process.env.JWT_EXPIRES_IN || '24h',
  },
  
  // External Services Configuration
  aws: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
    region: process.env.AWS_REGION || 'us-east-1',
    s3Bucket: process.env.S3_BUCKET || 'video-template-engine-storage',
  },
  
  // Logging Configuration
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    format: process.env.LOG_FORMAT || 'combined',
  },
  
  // Quality Presets
  qualityPresets: {
    '4k': {
      resolution: { width: 3840, height: 2160 },
      videoBitrate: 25000,
      audioBitrate: 320,
      codec: 'libx264',
      preset: 'medium'
    },
    '1080p': {
      resolution: { width: 1920, height: 1080 },
      videoBitrate: 8000,
      audioBitrate: 192,
      codec: 'libx264',
      preset: 'medium'
    },
    '720p': {
      resolution: { width: 1280, height: 720 },
      videoBitrate: 5000,
      audioBitrate: 128,
      codec: 'libx264',
      preset: 'fast'
    },
    'mobile': {
      resolution: { width: 854, height: 480 },
      videoBitrate: 2500,
      audioBitrate: 96,
      codec: 'libx264',
      preset: 'fast'
    }
  },
  
  // Supported Formats
  supportedFormats: {
    video: ['mp4', 'webm', 'mov', 'avi'],
    audio: ['mp3', 'wav', 'aac', 'ogg'],
    image: ['jpg', 'jpeg', 'png', 'gif', 'webp'],
    text: ['txt', 'srt', 'vtt']
  },
  
  // Cache Configuration
  cache: {
    templateTTL: 3600, // 1 hour
    contentTTL: 1800,  // 30 minutes
    renderJobTTL: 86400, // 24 hours
  }
};

export default config;