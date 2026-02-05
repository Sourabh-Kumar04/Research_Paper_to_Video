import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { DatabaseConfig } from './config/database';
import { ServiceFactory } from './services';
import apiRoutes from './routes';
import config from './config';

class VideoTemplateEngineApp {
  private app: express.Application;
  private dbConfig: DatabaseConfig;

  constructor() {
    this.app = express();
    this.dbConfig = DatabaseConfig.getInstance();
    this.initializeMiddleware();
    this.initializeRoutes();
  }

  private initializeMiddleware(): void {
    // Security middleware
    this.app.use(helmet());
    
    // CORS configuration
    this.app.use(cors({
      origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000', 'http://localhost:3001', 'http://localhost:3002'],
      credentials: true
    }));
    
    // Body parsing middleware
    this.app.use(express.json({ limit: '50mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '50mb' }));
    
    // Request logging
    this.app.use((req, res, next) => {
      console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
      next();
    });
  }

  private initializeRoutes(): void {
    // Health check endpoint
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        mode: 'production',
        services: {
          database: 'active',
          cache: 'active',
          queue: 'active',
          video_generation: 'active',
          llm_provider: 'google-gemini'
        },
        features: {
          real_video_generation: 'active',
          gemini_integration: 'active',
          manim_generation: 'active',
          audio_synthesis: 'active'
        }
      });
    });

    // API routes
    this.app.use('/api/v1', apiRoutes);

    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        error: 'Endpoint not found',
        path: req.originalUrl,
        method: req.method
      });
    });

    // Error handler
    this.app.use((error: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
      console.error('Unhandled error:', error);
      res.status(500).json({
        error: 'Internal server error',
        message: config.nodeEnv === 'development' ? error.message : 'Something went wrong'
      });
    });
  }

  public async start(): Promise<void> {
    try {
      // Initialize services for production
      console.log('🚀 Starting RASO Platform in production mode...');
      
      try {
        await ServiceFactory.initialize();
        console.log('✅ Services initialized successfully');
      } catch (error) {
        console.log('⚠️ Some services failed to initialize, continuing...');
      }

      // Start the server
      this.app.listen(config.port, () => {
        console.log(`🚀 RASO Platform started on port ${config.port}`);
        console.log(`📊 Environment: ${config.nodeEnv} (PRODUCTION MODE)`);
        console.log(`🔗 Health check: http://localhost:${config.port}/health`);
        console.log(`📚 API docs: http://localhost:${config.port}/api/v1`);
        console.log(`🎬 Jobs API: http://localhost:${config.port}/api/v1/jobs`);
        console.log(`🤖 LLM Provider: Google Gemini`);
        console.log(`🎥 Video Generation: Enhanced Production Pipeline`);
      });
    } catch (error) {
      console.error('Failed to start application:', error);
      process.exit(1);
    }
  }

  public getApp(): express.Application {
    return this.app;
  }
}

// Start the application if this file is run directly
if (require.main === module) {
  const app = new VideoTemplateEngineApp();
  app.start().catch(console.error);
}

export default VideoTemplateEngineApp;