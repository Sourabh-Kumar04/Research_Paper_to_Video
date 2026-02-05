import { v4 as uuidv4 } from 'uuid';
import Joi from 'joi';
import { TemplateModel } from '../config/database';
import { 
  Template, 
  TemplateDefinition, 
  ValidationResult, 
  SharingPermissions, 
  ShareLink,
  ContentSlot,
  Animation,
  InteractiveElement
} from '../types';

export class TemplateService {
  private static instance: TemplateService;

  private constructor() {}

  public static getInstance(): TemplateService {
    if (!TemplateService.instance) {
      TemplateService.instance = new TemplateService();
    }
    return TemplateService.instance;
  }

  // Validation schemas
  private readonly templateDefinitionSchema = Joi.object({
    name: Joi.string().min(1).max(100).required(),
    description: Joi.string().min(1).max(500).required(),
    duration: Joi.number().positive().required(),
    resolution: Joi.object({
      width: Joi.number().integer().min(320).max(7680).required(),
      height: Joi.number().integer().min(240).max(4320).required()
    }).required(),
    contentSlots: Joi.array().items(
      Joi.object({
        id: Joi.string().required(),
        type: Joi.string().valid('text', 'image', 'video', 'audio').required(),
        position: Joi.object({
          x: Joi.number().min(0).required(),
          y: Joi.number().min(0).required()
        }).required(),
        dimensions: Joi.object({
          width: Joi.number().positive().required(),
          height: Joi.number().positive().required()
        }).required(),
        duration: Joi.number().positive().optional(),
        constraints: Joi.object({
          maxFileSize: Joi.number().positive().optional(),
          allowedFormats: Joi.array().items(Joi.string()).optional(),
          maxDuration: Joi.number().positive().optional(),
          minDuration: Joi.number().positive().optional(),
          aspectRatio: Joi.number().positive().optional(),
          required: Joi.boolean().default(false)
        }).required()
      })
    ).required(),
    animations: Joi.array().items(
      Joi.object({
        id: Joi.string().required(),
        targetSlotId: Joi.string().required(),
        type: Joi.string().valid('motion', 'scale', 'rotation', 'opacity', 'color').required(),
        keyframes: Joi.array().items(
          Joi.object({
            time: Joi.number().min(0).max(1).required(),
            value: Joi.any().required(),
            easing: Joi.string().valid('linear', 'ease-in', 'ease-out', 'ease-in-out', 'cubic-bezier').optional()
          })
        ).min(2).required(),
        easing: Joi.string().valid('linear', 'ease-in', 'ease-out', 'ease-in-out', 'cubic-bezier').default('linear'),
        duration: Joi.number().positive().required(),
        delay: Joi.number().min(0).default(0)
      })
    ).default([]),
    interactiveElements: Joi.array().items(
      Joi.object({
        id: Joi.string().required(),
        type: Joi.string().valid('chapter', 'annotation', 'hotspot').required(),
        timestamp: Joi.number().min(0).required(),
        duration: Joi.number().positive().optional(),
        position: Joi.object({
          x: Joi.number().min(0).required(),
          y: Joi.number().min(0).required()
        }).optional(),
        data: Joi.any().required()
      })
    ).default([]),
    metadata: Joi.object({
      tags: Joi.array().items(Joi.string()).default([]),
      category: Joi.string().required(),
      description: Joi.string().optional(),
      thumbnail: Joi.string().optional()
    }).required()
  });

  public validateTemplate(template: TemplateDefinition): ValidationResult {
    const { error, value } = this.templateDefinitionSchema.validate(template, { 
      abortEarly: false,
      allowUnknown: false 
    });

    if (error) {
      return {
        isValid: false,
        errors: error.details.map(detail => detail.message)
      };
    }

    // Additional business logic validation
    const businessValidation = this.validateBusinessRules(value);
    if (!businessValidation.isValid) {
      return businessValidation;
    }

    return { isValid: true, errors: [] };
  }

  private validateBusinessRules(template: TemplateDefinition): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check for slot ID uniqueness
    const slotIds = template.contentSlots.map(slot => slot.id);
    const duplicateSlotIds = slotIds.filter((id, index) => slotIds.indexOf(id) !== index);
    if (duplicateSlotIds.length > 0) {
      errors.push(`Duplicate content slot IDs found: ${duplicateSlotIds.join(', ')}`);
    }

    // Validate animation target slots exist
    for (const animation of template.animations) {
      if (!slotIds.includes(animation.targetSlotId)) {
        errors.push(`Animation ${animation.id} targets non-existent slot ${animation.targetSlotId}`);
      }
    }

    // Check slot positions are within template bounds
    for (const slot of template.contentSlots) {
      if (slot.position.x + slot.dimensions.width > template.resolution.width) {
        errors.push(`Content slot ${slot.id} extends beyond template width`);
      }
      if (slot.position.y + slot.dimensions.height > template.resolution.height) {
        errors.push(`Content slot ${slot.id} extends beyond template height`);
      }
    }

    // Validate interactive element timestamps
    for (const element of template.interactiveElements) {
      if (element.timestamp > template.duration) {
        errors.push(`Interactive element ${element.id} timestamp exceeds template duration`);
      }
      if (element.duration && element.timestamp + element.duration > template.duration) {
        warnings.push(`Interactive element ${element.id} extends beyond template duration`);
      }
    }

    // Check for circular animation dependencies
    const animationGraph = this.buildAnimationDependencyGraph(template.animations);
    if (this.hasCircularDependencies(animationGraph)) {
      errors.push('Circular dependencies detected in animations');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings: warnings.length > 0 ? warnings : undefined
    };
  }

  private buildAnimationDependencyGraph(animations: Animation[]): Map<string, string[]> {
    const graph = new Map<string, string[]>();
    
    for (const animation of animations) {
      if (!graph.has(animation.id)) {
        graph.set(animation.id, []);
      }
      
      // Add dependencies based on animation timing and target slots
      const dependencies = animations
        .filter(other => 
          other.id !== animation.id && 
          other.targetSlotId === animation.targetSlotId &&
          other.delay + other.duration > animation.delay
        )
        .map(other => other.id);
      
      graph.set(animation.id, dependencies);
    }
    
    return graph;
  }

  private hasCircularDependencies(graph: Map<string, string[]>): boolean {
    const visited = new Set<string>();
    const recursionStack = new Set<string>();

    const hasCycle = (node: string): boolean => {
      if (recursionStack.has(node)) return true;
      if (visited.has(node)) return false;

      visited.add(node);
      recursionStack.add(node);

      const dependencies = graph.get(node) || [];
      for (const dependency of dependencies) {
        if (hasCycle(dependency)) return true;
      }

      recursionStack.delete(node);
      return false;
    };

    for (const node of graph.keys()) {
      if (hasCycle(node)) return true;
    }

    return false;
  }

  public async createTemplate(templateDef: TemplateDefinition, createdBy: string): Promise<Template> {
    // Validate template
    const validation = this.validateTemplate(templateDef);
    if (!validation.isValid) {
      throw new Error(`Template validation failed: ${validation.errors.join(', ')}`);
    }

    // Create template document
    const template = new TemplateModel({
      id: uuidv4(),
      name: templateDef.name,
      description: templateDef.description,
      version: '1.0.0',
      createdBy,
      duration: templateDef.duration,
      resolution: templateDef.resolution,
      frameRate: 30, // Default frame rate
      contentSlots: templateDef.contentSlots,
      staticAssets: [],
      animations: templateDef.animations,
      transitions: [],
      chapters: templateDef.interactiveElements
        .filter(el => el.type === 'chapter')
        .map(el => ({
          id: el.id,
          title: el.data.title || 'Untitled Chapter',
          timestamp: el.timestamp,
          thumbnail: el.data.thumbnail
        })),
      annotations: templateDef.interactiveElements
        .filter(el => el.type === 'annotation')
        .map(el => ({
          id: el.id,
          text: el.data.text || '',
          timestamp: el.timestamp,
          duration: el.duration || 5,
          position: el.position || { x: 0, y: 0 },
          style: el.data.style || {
            fontSize: 16,
            fontColor: '#ffffff',
            backgroundColor: '#000000',
            opacity: 1.0
          }
        })),
      hotspots: templateDef.interactiveElements
        .filter(el => el.type === 'hotspot')
        .map(el => ({
          id: el.id,
          timestamp: el.timestamp,
          duration: el.duration || 5,
          position: el.position || { x: 0, y: 0 },
          dimensions: el.data.dimensions || { width: 100, height: 100 },
          action: el.data.action || { type: 'pause', parameters: {} }
        })),
      tags: templateDef.metadata.tags,
      category: templateDef.metadata.category,
      thumbnail: templateDef.metadata.thumbnail || '',
      previewVideo: undefined
    });

    const savedTemplate = await template.save();
    return this.mapToTemplate(savedTemplate);
  }

  public async getTemplate(id: string, version?: string): Promise<Template | null> {
    const query: any = { id };
    if (version) {
      query.version = version;
    }

    const template = await TemplateModel.findOne(query).sort({ createdAt: -1 });
    return template ? this.mapToTemplate(template) : null;
  }

  public async updateTemplate(id: string, updates: Partial<TemplateDefinition>, updatedBy: string): Promise<Template> {
    const existingTemplate = await TemplateModel.findOne({ id }).sort({ createdAt: -1 });
    if (!existingTemplate) {
      throw new Error(`Template with id ${id} not found`);
    }

    // Create new version
    const newVersion = this.incrementVersion(existingTemplate.version);
    
    // Merge updates with existing template
    const updatedTemplate = {
      ...existingTemplate.toObject(),
      ...updates,
      id: existingTemplate.id, // Preserve original ID
      version: newVersion,
      updatedAt: new Date()
    };

    // Validate updated template
    if (updates.name || updates.contentSlots || updates.animations || updates.interactiveElements) {
      const validation = this.validateTemplate(updatedTemplate as TemplateDefinition);
      if (!validation.isValid) {
        throw new Error(`Template validation failed: ${validation.errors.join(', ')}`);
      }
    }

    const newTemplateDoc = new TemplateModel(updatedTemplate);
    const savedTemplate = await newTemplateDoc.save();
    
    return this.mapToTemplate(savedTemplate);
  }

  public async getTemplateVersions(id: string): Promise<Template[]> {
    const templates = await TemplateModel.find({ id }).sort({ createdAt: -1 });
    return templates.map(template => this.mapToTemplate(template));
  }

  public async rollbackTemplate(id: string, targetVersion: string): Promise<Template> {
    const targetTemplate = await TemplateModel.findOne({ id, version: targetVersion });
    if (!targetTemplate) {
      throw new Error(`Template version ${targetVersion} not found`);
    }

    // Create new version based on target
    const newVersion = this.incrementVersion(
      (await TemplateModel.findOne({ id }).sort({ createdAt: -1 }))?.version || '1.0.0'
    );

    const rolledBackTemplate = new TemplateModel({
      ...targetTemplate.toObject(),
      _id: undefined, // Remove MongoDB _id to create new document
      version: newVersion,
      updatedAt: new Date()
    });

    const savedTemplate = await rolledBackTemplate.save();
    return this.mapToTemplate(savedTemplate);
  }

  public async shareTemplate(id: string, permissions: SharingPermissions): Promise<ShareLink> {
    const template = await TemplateModel.findOne({ id }).sort({ createdAt: -1 });
    if (!template) {
      throw new Error(`Template with id ${id} not found`);
    }

    const shareLink: ShareLink = {
      id: uuidv4(),
      url: `${process.env.BASE_URL || 'http://localhost:3000'}/shared/templates/${id}?token=${uuidv4()}`,
      permissions,
      expiresAt: permissions.public ? undefined : new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days
    };

    // Store share link in cache/database
    // Implementation would depend on chosen storage mechanism

    return shareLink;
  }

  private incrementVersion(currentVersion: string): string {
    const parts = currentVersion.split('.').map(Number);
    parts[2] = (parts[2] || 0) + 1; // Increment patch version
    return parts.join('.');
  }

  private mapToTemplate(doc: any): Template {
    return {
      id: doc.id,
      name: doc.name,
      description: doc.description,
      version: doc.version,
      createdAt: doc.createdAt,
      updatedAt: doc.updatedAt,
      createdBy: doc.createdBy,
      duration: doc.duration,
      resolution: doc.resolution,
      frameRate: doc.frameRate,
      contentSlots: doc.contentSlots,
      staticAssets: doc.staticAssets,
      animations: doc.animations,
      transitions: doc.transitions,
      chapters: doc.chapters,
      annotations: doc.annotations,
      hotspots: doc.hotspots,
      tags: doc.tags,
      category: doc.category,
      thumbnail: doc.thumbnail,
      previewVideo: doc.previewVideo
    };
  }
}