import { Router, Request, Response } from 'express';
import multer from 'multer';
import { ServiceFactory } from '../services';
import { ContentItem, SlotRequirements, ContentSet, OutputSpecs } from '../types';

const router = Router();
const contentService = ServiceFactory.getContentService();

// Configure multer for file uploads
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 100 * 1024 * 1024 // 100MB limit
  },
  fileFilter: (req, file, cb) => {
    // Allow common media formats
    const allowedMimes = [
      'image/jpeg', 'image/png', 'image/gif', 'image/webp',
      'video/mp4', 'video/webm', 'video/quicktime',
      'audio/mpeg', 'audio/wav', 'audio/aac', 'audio/ogg'
    ];
    
    if (allowedMimes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error(`Unsupported file type: ${file.mimetype}`));
    }
  }
});

// Validate content
router.post('/validate', async (req: Request, res: Response) => {
  try {
    const { slotId, content } = req.body;
    
    if (!slotId || !content) {
      return res.status(400).json({
        success: false,
        error: 'slotId and content are required'
      });
    }
    
    const validation = contentService.validateContent(slotId, content as ContentItem);
    
    res.json({
      success: true,
      data: validation
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to validate content'
    });
  }
});

// Process content
router.post('/process', upload.single('file'), async (req: Request, res: Response) => {
  try {
    const { slotId, type, requirements } = req.body;
    const file = req.file;
    
    if (!slotId || !type) {
      return res.status(400).json({
        success: false,
        error: 'slotId and type are required'
      });
    }
    
    let contentData: any;
    let metadata: any = {};
    
    if (file) {
      contentData = file.buffer;
      metadata = {
        filename: file.originalname,
        fileSize: file.size,
        mimeType: file.mimetype
      };
    } else if (req.body.data) {
      contentData = req.body.data;
    } else {
      return res.status(400).json({
        success: false,
        error: 'Either file upload or data field is required'
      });
    }
    
    const content: ContentItem = {
      slotId,
      type,
      data: contentData,
      metadata
    };
    
    const slotRequirements: SlotRequirements = requirements ? JSON.parse(requirements) : {
      type,
      constraints: { required: true },
      position: { x: 0, y: 0 },
      dimensions: { width: 1920, height: 1080 }
    };
    
    const processedContent = await contentService.processContent(content, slotRequirements);
    
    // Don't return the actual data in response (could be large)
    const response = {
      ...processedContent,
      data: '[BINARY_DATA]',
      optimizedData: '[BINARY_DATA]'
    };
    
    res.json({
      success: true,
      data: response,
      message: 'Content processed successfully'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to process content'
    });
  }
});

// Batch process content
router.post('/batch', async (req: Request, res: Response) => {
  try {
    const { contentSets } = req.body;
    
    if (!contentSets || !Array.isArray(contentSets)) {
      return res.status(400).json({
        success: false,
        error: 'contentSets array is required'
      });
    }
    
    const processedContent = await contentService.batchProcessContent(contentSets as ContentSet[]);
    
    // Don't return actual data in response
    const response = processedContent.map(content => ({
      ...content,
      data: '[BINARY_DATA]',
      optimizedData: '[BINARY_DATA]'
    }));
    
    res.json({
      success: true,
      data: response,
      message: `Processed ${processedContent.length} content items successfully`
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to batch process content'
    });
  }
});

// Optimize content
router.post('/optimize', upload.single('file'), async (req: Request, res: Response) => {
  try {
    const { slotId, type, targetSpecs } = req.body;
    const file = req.file;
    
    if (!slotId || !type || !targetSpecs) {
      return res.status(400).json({
        success: false,
        error: 'slotId, type, and targetSpecs are required'
      });
    }
    
    let contentData: any;
    let metadata: any = {};
    
    if (file) {
      contentData = file.buffer;
      metadata = {
        filename: file.originalname,
        fileSize: file.size,
        mimeType: file.mimetype
      };
    } else if (req.body.data) {
      contentData = req.body.data;
    } else {
      return res.status(400).json({
        success: false,
        error: 'Either file upload or data field is required'
      });
    }
    
    const content: ContentItem = {
      slotId,
      type,
      data: contentData,
      metadata
    };
    
    const specs: OutputSpecs = JSON.parse(targetSpecs);
    const optimizedContent = await contentService.optimizeContent(content, specs);
    
    // Don't return actual data in response
    const response = {
      ...optimizedContent,
      data: '[BINARY_DATA]',
      optimizedData: '[BINARY_DATA]'
    };
    
    res.json({
      success: true,
      data: response,
      message: 'Content optimized successfully'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to optimize content'
    });
  }
});

export default router;