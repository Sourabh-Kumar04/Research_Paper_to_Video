import { Router } from 'express';
import templatesRouter from './templates';
import contentRouter from './content';
import renderRouter from './render';
import systemRouter from './system';
import jobsRouter from './jobs';

const router = Router();

// Mount route modules
router.use('/templates', templatesRouter);
router.use('/content', contentRouter);
router.use('/render', renderRouter);
router.use('/system', systemRouter);
router.use('/jobs', jobsRouter);

// API info endpoint
router.get('/', (req, res) => {
  res.json({
    name: 'Advanced Video Template Engine API',
    version: '1.0.0',
    description: 'API for creating and managing video templates with dynamic content',
    endpoints: {
      jobs: {
        base: '/api/v1/jobs',
        operations: [
          'POST / - Submit research paper job',
          'GET /:jobId - Get job status',
          'GET /:jobId/download - Download completed video'
        ]
      },
      templates: {
        base: '/api/v1/templates',
        operations: [
          'POST / - Create template',
          'GET /:id - Get template',
          'PUT /:id - Update template',
          'GET /:id/versions - Get template versions',
          'POST /:id/rollback - Rollback template',
          'POST /:id/share - Share template',
          'POST /validate - Validate template'
        ]
      },
      content: {
        base: '/api/v1/content',
        operations: [
          'POST /validate - Validate content',
          'POST /process - Process content',
          'POST /batch - Batch process content',
          'POST /optimize - Optimize content'
        ]
      },
      render: {
        base: '/api/v1/render',
        operations: [
          'POST / - Start render job',
          'GET /:jobId - Get render status',
          'DELETE /:jobId - Cancel render job',
          'POST /:jobId/retry - Retry failed job'
        ]
      },
      system: {
        base: '/api/v1/system',
        operations: [
          'GET /capabilities - Check system capabilities',
          'GET /health - System health check'
        ]
      }
    },
    features: [
      'Research paper video generation',
      'Template creation and management',
      'Version control and rollback',
      'Dynamic content processing',
      'Multi-format video rendering',
      'Interactive elements support',
      'Batch processing',
      'Real-time progress tracking',
      'Python-powered real video generation',
      'TTS audio generation',
      'FFmpeg-based animations',
      'System capability monitoring'
    ]
  });
});

export default router;