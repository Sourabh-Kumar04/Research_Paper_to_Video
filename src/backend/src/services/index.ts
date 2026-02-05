// Import services
import { TemplateService } from './template-service';
import { ContentService } from './content-service';
import { RenderingService } from './rendering-service';

// Export all services
export { TemplateService, ContentService, RenderingService };

// Service factory for dependency injection
export class ServiceFactory {
  private static templateService: TemplateService;
  private static contentService: ContentService;
  private static renderingService: RenderingService;

  public static getTemplateService(): TemplateService {
    if (!this.templateService) {
      this.templateService = TemplateService.getInstance();
    }
    return this.templateService;
  }

  public static getContentService(): ContentService {
    if (!this.contentService) {
      this.contentService = ContentService.getInstance();
    }
    return this.contentService;
  }

  public static getRenderingService(): RenderingService {
    if (!this.renderingService) {
      this.renderingService = RenderingService.getInstance();
    }
    return this.renderingService;
  }

  // Initialize all services
  public static async initialize(): Promise<void> {
    console.log('Initializing services...');
    
    // Get instances to trigger initialization
    this.getTemplateService();
    this.getContentService();
    this.getRenderingService();
    
    console.log('All services initialized successfully');
  }
}