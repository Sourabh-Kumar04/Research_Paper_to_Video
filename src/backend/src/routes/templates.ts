import { Router, Request, Response } from 'express';
import { ServiceFactory } from '../services';
import { TemplateDefinition, SharingPermissions } from '../types';

const router = Router();
const templateService = ServiceFactory.getTemplateService();

// Create template
router.post('/', async (req: Request, res: Response) => {
  try {
    const templateDef: TemplateDefinition = req.body;
    const createdBy = req.headers['user-id'] as string || 'anonymous';
    
    const template = await templateService.createTemplate(templateDef, createdBy);
    
    res.status(201).json({
      success: true,
      data: template,
      message: 'Template created successfully'
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to create template'
    });
  }
});

// Get template
router.get('/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const { version } = req.query;
    
    const template = await templateService.getTemplate(id, version as string);
    
    if (!template) {
      return res.status(404).json({
        success: false,
        error: 'Template not found'
      });
    }
    
    res.json({
      success: true,
      data: template
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get template'
    });
  }
});

// Update template
router.put('/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const updates = req.body;
    const updatedBy = req.headers['user-id'] as string || 'anonymous';
    
    const template = await templateService.updateTemplate(id, updates, updatedBy);
    
    res.json({
      success: true,
      data: template,
      message: 'Template updated successfully'
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to update template'
    });
  }
});

// Get template versions
router.get('/:id/versions', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    
    const versions = await templateService.getTemplateVersions(id);
    
    res.json({
      success: true,
      data: versions
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get template versions'
    });
  }
});

// Rollback template
router.post('/:id/rollback', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const { targetVersion } = req.body;
    
    if (!targetVersion) {
      return res.status(400).json({
        success: false,
        error: 'Target version is required'
      });
    }
    
    const template = await templateService.rollbackTemplate(id, targetVersion);
    
    res.json({
      success: true,
      data: template,
      message: `Template rolled back to version ${targetVersion}`
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to rollback template'
    });
  }
});

// Share template
router.post('/:id/share', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const permissions: SharingPermissions = req.body;
    
    const shareLink = await templateService.shareTemplate(id, permissions);
    
    res.json({
      success: true,
      data: shareLink,
      message: 'Template shared successfully'
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to share template'
    });
  }
});

// Validate template
router.post('/validate', async (req: Request, res: Response) => {
  try {
    const templateDef: TemplateDefinition = req.body;
    
    const validation = templateService.validateTemplate(templateDef);
    
    res.json({
      success: true,
      data: validation
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to validate template'
    });
  }
});

export default router;