import { Router } from 'express';
import { RenderingService } from '../services/rendering-service';

const router = Router();
const renderingService = RenderingService.getInstance();

/**
 * GET /api/v1/system/capabilities
 * Check system capabilities for video generation
 */
router.get('/capabilities', async (req, res) => {
  try {
    const capabilities = await renderingService.checkPythonCapabilities();
    
    res.json({
      success: true,
      data: {
        typescript_engine: {
          available: true,
          template_processing: true,
          content_management: true,
          queue_processing: true
        },
        python_bridge: capabilities,
        overall_status: capabilities.available ? 'ready' : 'limited',
        recommendations: capabilities.available 
          ? ['System ready for full video generation']
          : [
              'Install Python dependencies for full video generation',
              'Current system limited to placeholder videos',
              ...capabilities.errors
            ]
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to check system capabilities',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * GET /api/v1/system/health
 * System health check
 */
router.get('/health', async (req, res) => {
  try {
    // Basic health checks
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        api: 'up',
        database: 'up', // Would check actual DB connection
        queue: 'up',    // Would check Redis connection
        python_bridge: 'unknown'
      }
    };

    // Check Python bridge
    try {
      const capabilities = await renderingService.checkPythonCapabilities();
      health.services.python_bridge = capabilities.available ? 'up' : 'degraded';
    } catch (error) {
      health.services.python_bridge = 'down';
    }

    // Determine overall status
    const serviceStatuses = Object.values(health.services);
    if (serviceStatuses.includes('down')) {
      health.status = 'unhealthy';
    } else if (serviceStatuses.includes('degraded')) {
      health.status = 'degraded';
    }

    const statusCode = health.status === 'healthy' ? 200 : 
                      health.status === 'degraded' ? 200 : 503;

    res.status(statusCode).json({
      success: true,
      data: health
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Health check failed',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router;