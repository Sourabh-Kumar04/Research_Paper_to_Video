import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';
import { Template, ContentSet, OutputSpecs, OutputFile } from '../types';

export interface PythonVideoGenerationRequest {
  template: Template;
  contentSet: ContentSet;
  outputSpecs: OutputSpecs;
  outputPath: string;
}

export interface PythonVideoGenerationResult {
  success: boolean;
  outputPath?: string;
  fileSize?: number;
  duration?: number;
  resolution?: [number, number];
  method?: string;
  errors: string[];
  warnings: string[];
}

export class PythonVideoBridge {
  private static instance: PythonVideoBridge;
  private pythonPath: string;
  private scriptsPath: string;

  private constructor() {
    this.pythonPath = process.env.PYTHON_PATH || 'python';
    this.scriptsPath = path.join(process.cwd(), 'src', 'agents');
  }

  public static getInstance(): PythonVideoBridge {
    if (!PythonVideoBridge.instance) {
      PythonVideoBridge.instance = new PythonVideoBridge();
    }
    return PythonVideoBridge.instance;
  }

  public async generateRealVideo(request: PythonVideoGenerationRequest): Promise<PythonVideoGenerationResult> {
    try {
      // Create temporary directory for this generation
      const tempDir = path.join(process.cwd(), 'temp', uuidv4());
      await fs.mkdir(tempDir, { recursive: true });

      // Step 1: Generate script from template and content
      const scriptResult = await this.generateScript(request.template, request.contentSet, tempDir);
      if (!scriptResult.success) {
        return {
          success: false,
          errors: [`Script generation failed: ${scriptResult.errors.join(', ')}`],
          warnings: []
        };
      }

      // Step 2: Generate audio from script
      const audioResult = await this.generateAudio(scriptResult.scriptPath!, tempDir);
      if (!audioResult.success) {
        return {
          success: false,
          errors: [`Audio generation failed: ${audioResult.errors.join(', ')}`],
          warnings: []
        };
      }

      // Step 3: Generate animations from script
      const animationResult = await this.generateAnimations(scriptResult.scriptPath!, tempDir);
      if (!animationResult.success) {
        return {
          success: false,
          errors: [`Animation generation failed: ${animationResult.errors.join(', ')}`],
          warnings: []
        };
      }

      // Step 4: Compose final video
      const videoResult = await this.composeVideo(
        audioResult.audioAssetsPath!,
        animationResult.animationAssetsPath!,
        request.outputPath,
        request.outputSpecs
      );

      // Clean up temporary directory
      await this.cleanupTempDir(tempDir);

      return videoResult;

    } catch (error) {
      return {
        success: false,
        errors: [`Video generation error: ${error instanceof Error ? error.message : 'Unknown error'}`],
        warnings: []
      };
    }
  }

  private async generateScript(template: Template, contentSet: ContentSet, tempDir: string): Promise<{
    success: boolean;
    scriptPath?: string;
    errors: string[];
  }> {
    try {
      // Create script data from template and content
      const scriptData = this.createScriptFromTemplate(template, contentSet);
      
      // Save script data to temporary file
      const scriptPath = path.join(tempDir, 'script.json');
      await fs.writeFile(scriptPath, JSON.stringify(scriptData, null, 2));

      return {
        success: true,
        scriptPath,
        errors: []
      };

    } catch (error) {
      return {
        success: false,
        errors: [error instanceof Error ? error.message : 'Script generation failed']
      };
    }
  }

  private createScriptFromTemplate(template: Template, contentSet: ContentSet): any {
    // Convert template and content to script format expected by Python agents
    const scenes = template.contentSlots.map((slot, index) => {
      const content = contentSet.content[slot.id] || { text: slot.placeholder };
      
      return {
        id: `scene_${index + 1}`,
        title: content.text.substring(0, 50) + (content.text.length > 50 ? '...' : ''),
        narration: content.text,
        duration: template.duration / template.contentSlots.length, // Distribute duration evenly
        concepts: slot.type === 'text' ? ['text', 'narration'] : ['visual', 'concept'],
        visual_type: this.mapVisualType(slot.type)
      };
    });

    return {
      scenes,
      total_duration: template.duration,
      word_count: scenes.reduce((total, scene) => total + scene.narration.split(' ').length, 0),
      target_audience: "general",
      language: "en"
    };
  }

  private mapVisualType(slotType: string): string {
    const mapping: Record<string, string> = {
      'text': 'remotion',
      'image': 'motion-canvas',
      'video': 'manim',
      'animation': 'manim'
    };
    return mapping[slotType] || 'remotion';
  }

  private async generateAudio(scriptPath: string, tempDir: string): Promise<{
    success: boolean;
    audioAssetsPath?: string;
    errors: string[];
  }> {
    return new Promise((resolve) => {
      const audioScript = path.join(this.scriptsPath, 'generate_audio_bridge.py');
      const audioOutputDir = path.join(tempDir, 'audio');
      
      const pythonProcess = spawn(this.pythonPath, [
        audioScript,
        '--script-path', scriptPath,
        '--output-dir', audioOutputDir
      ]);

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pythonProcess.on('close', (code) => {
        if (code === 0) {
          resolve({
            success: true,
            audioAssetsPath: path.join(audioOutputDir, 'audio_assets.json'),
            errors: []
          });
        } else {
          resolve({
            success: false,
            errors: [`Audio generation failed with code ${code}: ${stderr}`]
          });
        }
      });

      pythonProcess.on('error', (error) => {
        resolve({
          success: false,
          errors: [`Audio generation process error: ${error.message}`]
        });
      });
    });
  }

  private async generateAnimations(scriptPath: string, tempDir: string): Promise<{
    success: boolean;
    animationAssetsPath?: string;
    errors: string[];
  }> {
    return new Promise((resolve) => {
      const animationScript = path.join(this.scriptsPath, 'generate_animation_bridge.py');
      const animationOutputDir = path.join(tempDir, 'animations');
      
      const pythonProcess = spawn(this.pythonPath, [
        animationScript,
        '--script-path', scriptPath,
        '--output-dir', animationOutputDir
      ]);

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pythonProcess.on('close', (code) => {
        if (code === 0) {
          resolve({
            success: true,
            animationAssetsPath: path.join(animationOutputDir, 'animation_assets.json'),
            errors: []
          });
        } else {
          resolve({
            success: false,
            errors: [`Animation generation failed with code ${code}: ${stderr}`]
          });
        }
      });

      pythonProcess.on('error', (error) => {
        resolve({
          success: false,
          errors: [`Animation generation process error: ${error.message}`]
        });
      });
    });
  }

  private async composeVideo(
    audioAssetsPath: string,
    animationAssetsPath: string,
    outputPath: string,
    outputSpecs: OutputSpecs
  ): Promise<PythonVideoGenerationResult> {
    return new Promise((resolve) => {
      const composerScript = path.join(this.scriptsPath, 'compose_video_bridge.py');
      
      const pythonProcess = spawn(this.pythonPath, [
        composerScript,
        '--audio-assets', audioAssetsPath,
        '--animation-assets', animationAssetsPath,
        '--output-path', outputPath,
        '--format', outputSpecs.format,
        '--resolution', outputSpecs.resolution,
        '--quality', outputSpecs.quality
      ]);

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pythonProcess.on('close', async (code) => {
        if (code === 0) {
          try {
            // Parse result from stdout
            const result = JSON.parse(stdout.trim());
            
            // Get file stats
            const stats = await fs.stat(outputPath);
            
            resolve({
              success: true,
              outputPath,
              fileSize: stats.size,
              duration: result.duration || 0,
              resolution: result.resolution || [1280, 720],
              method: result.method_used || 'python_composer',
              errors: result.errors || [],
              warnings: result.warnings || []
            });
          } catch (error) {
            resolve({
              success: false,
              errors: [`Failed to parse video composition result: ${error instanceof Error ? error.message : 'Unknown error'}`],
              warnings: []
            });
          }
        } else {
          resolve({
            success: false,
            errors: [`Video composition failed with code ${code}: ${stderr}`],
            warnings: []
          });
        }
      });

      pythonProcess.on('error', (error) => {
        resolve({
          success: false,
          errors: [`Video composition process error: ${error.message}`],
          warnings: []
        });
      });
    });
  }

  private async cleanupTempDir(tempDir: string): Promise<void> {
    try {
      await fs.rm(tempDir, { recursive: true, force: true });
    } catch (error) {
      console.warn(`Failed to cleanup temp directory ${tempDir}:`, error);
    }
  }

  public async checkPythonEnvironment(): Promise<{
    available: boolean;
    capabilities: Record<string, boolean>;
    errors: string[];
  }> {
    return new Promise((resolve) => {
      const checkScript = path.join(this.scriptsPath, 'check_capabilities.py');
      
      const pythonProcess = spawn(this.pythonPath, [checkScript]);

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pythonProcess.on('close', (code) => {
        if (code === 0) {
          try {
            const capabilities = JSON.parse(stdout.trim());
            resolve({
              available: true,
              capabilities,
              errors: []
            });
          } catch (error) {
            resolve({
              available: false,
              capabilities: {},
              errors: [`Failed to parse capabilities: ${error instanceof Error ? error.message : 'Unknown error'}`]
            });
          }
        } else {
          resolve({
            available: false,
            capabilities: {},
            errors: [`Python environment check failed: ${stderr}`]
          });
        }
      });

      pythonProcess.on('error', (error) => {
        resolve({
          available: false,
          capabilities: {},
          errors: [`Python process error: ${error.message}`]
        });
      });
    });
  }
}