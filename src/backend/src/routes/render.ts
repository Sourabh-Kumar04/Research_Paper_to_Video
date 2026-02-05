import { Router, Request, Response } from 'express';
import { ServiceFactory } from '../services';
import { Template, ContentSet, OutputSpecs } from '../types';

const router = Router();
const renderingService = ServiceFactory.getRenderingService();
const templateService = ServiceFactory.getTemplateService();

// Start render job
router.post('/', async (req: Request, res: Response) => {
  try {
    const { templateId, contentSet, outputSpecs } = req.body;
    
    if (!templateId || !contentSet || !outputSpecs) {
      return res.status(400).json({
        success: false,
        error: 'templateId, contentSet, and outputSpecs are required'
      });
    }
    
    // Get template
    const template = await templateService.getTemplate(templateId);
    if (!template) {
      return res.status(404).json({
        success: false,
        error: 'Template not found'
      });
    }
    
    // Start rendering
    const renderJob = await renderingService.renderVideo(
      template,
      contentSet as ContentSet,
      outputSpecs as OutputSpecs[]
    );
    
    res.status(202).json({
      success: true,
      data: renderJob,
      message: 'Render job started successfully'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to start render job'
    });
  }
});

// Get render job status
router.get('/:jobId', async (req: Request, res: Response) => {
  try {
    const { jobId } = req.params;
    
    const progress = await renderingService.getProgress(jobId);
    
    res.json({
      success: true,
      data: progress
    });
  } catch (error) {
    res.status(404).json({
      success: false,
      error: error instanceof Error ? error.message : 'Render job not found'
    });
  }
});

// Cancel render job
router.delete('/:jobId', async (req: Request, res: Response) => {
  try {
    const { jobId } = req.params;
    
    await renderingService.cancelJob(jobId);
    
    res.json({
      success: true,
      message: 'Render job cancelled successfully'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to cancel render job'
    });
  }
});

// Retry failed render job
router.post('/:jobId/retry', async (req: Request, res: Response) => {
  try {
    const { jobId } = req.params;
    
    await renderingService.retryFailedChunks(jobId);
    
    res.json({
      success: true,
      message: 'Render job retry initiated successfully'
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to retry render job'
    });
  }
});

export default router;