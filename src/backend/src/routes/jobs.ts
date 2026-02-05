import { Router, Request, Response } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

const router = Router();

// In-memory job storage - in production, use database
interface Job {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  current_agent?: string;
  error_message?: string;
  paper_input?: {
    type: string;
    content: string;
  };
  video_path?: string;
  created_at: Date;
  updated_at: Date;
}

const jobs: Map<string, Job> = new Map();

// Submit a new job
router.post('/', async (req: Request, res: Response) => {
  try {
    const { paper_input } = req.body;
    
    if (!paper_input || !paper_input.type || !paper_input.content) {
      return res.status(400).json({
        success: false,
        error: 'paper_input with type and content is required'
      });
    }
    
    const jobId = uuidv4();
    const job: Job = {
      job_id: jobId,
      status: 'queued',
      progress: 0,
      paper_input,
      created_at: new Date(),
      updated_at: new Date()
    };
    
    jobs.set(jobId, job);
    
    // Start real video generation immediately
    setTimeout(() => {
      startRealVideoGeneration(jobId);
    }, 1000);
    
    res.status(201).json({
      success: true,
      job_id: jobId,
      message: 'Job submitted successfully'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to submit job'
    });
  }
});

// Get job status
router.get('/:jobId', async (req: Request, res: Response) => {
  try {
    const { jobId } = req.params;
    const job = jobs.get(jobId);
    
    if (!job) {
      return res.status(404).json({
        success: false,
        error: 'Job not found'
      });
    }
    
    res.json({
      job_id: job.job_id,
      status: job.status,
      progress: job.progress,
      current_agent: job.current_agent,
      error_message: job.error_message
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get job status'
    });
  }
});

// Download job result - serve actual video file
router.get('/:jobId/download', async (req: Request, res: Response) => {
  try {
    const { jobId } = req.params;
    const job = jobs.get(jobId);
    
    if (!job) {
      return res.status(404).json({
        success: false,
        error: 'Job not found'
      });
    }
    
    if (job.status !== 'completed') {
      return res.status(400).json({
        success: false,
        error: 'Job is not completed yet'
      });
    }
    
    if (!job.video_path || !fs.existsSync(job.video_path)) {
      return res.status(404).json({
        success: false,
        error: 'Video file not found'
      });
    }
    
    // Serve the actual video file
    const videoPath = job.video_path;
    const stat = fs.statSync(videoPath);
    const fileSize = stat.size;
    const range = req.headers.range;
    
    if (range) {
      // Support video streaming with range requests
      const parts = range.replace(/bytes=/, "").split("-");
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
      const chunksize = (end - start) + 1;
      const file = fs.createReadStream(videoPath, { start, end });
      const head = {
        'Content-Range': `bytes ${start}-${end}/${fileSize}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': chunksize,
        'Content-Type': 'video/mp4',
      };
      res.writeHead(206, head);
      file.pipe(res);
    } else {
      // Serve complete file
      const head = {
        'Content-Length': fileSize,
        'Content-Type': 'video/mp4',
        'Content-Disposition': `attachment; filename="paper_video_${jobId}.mp4"`
      };
      res.writeHead(200, head);
      fs.createReadStream(videoPath).pipe(res);
    }
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to download job result'
    });
  }
});

// Start real video generation using Python system
function startRealVideoGeneration(jobId: string) {
  const job = jobs.get(jobId);
  if (!job || !job.paper_input) return;
  
  console.log(`🎬 Starting REAL video generation for job ${jobId}...`);
  console.log(`📄 Paper: "${job.paper_input.content}" (${job.paper_input.type})`);
  
  // Update job status
  job.status = 'processing';
  job.current_agent = 'Paper Analysis Agent';
  job.progress = 5;
  job.updated_at = new Date();
  
  // Create output directory for this job
  const outputDir = path.join(process.cwd(), 'output', 'jobs', jobId);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  // Use the production video generation script
  const rootDir = path.resolve(process.cwd(), '..', '..');
  const scriptPath = path.join(rootDir, 'production_video_generator.py');
  
  // Set environment variables for the job
  const env = {
    ...process.env,
    RASO_JOB_ID: jobId,
    RASO_PAPER_CONTENT: job.paper_input.content,
    RASO_PAPER_TYPE: job.paper_input.type,
    RASO_OUTPUT_DIR: outputDir
  };
  
  // Execute the Python video generation system
  const pythonProcess = spawn('python', [scriptPath], {
    cwd: rootDir,
    env: env,
    stdio: ['pipe', 'pipe', 'pipe']
  });
  
  let outputBuffer = '';
  let errorBuffer = '';
  
  pythonProcess.stdout.on('data', (data) => {
    const output = data.toString();
    outputBuffer += output;
    console.log(`[Job ${jobId}] ${output.trim()}`);
    
    // Parse progress from Python output
    parseProgressFromOutput(jobId, output);
  });
  
  pythonProcess.stderr.on('data', (data) => {
    const error = data.toString();
    errorBuffer += error;
    console.error(`[Job ${jobId} ERROR] ${error.trim()}`);
  });
  
  pythonProcess.on('close', (code) => {
    const job = jobs.get(jobId);
    if (!job) return;
    
    if (code === 0) {
      // Success - find the generated video file
      const videoPath = findGeneratedVideo(outputDir);
      if (videoPath && fs.existsSync(videoPath)) {
        job.status = 'completed';
        job.progress = 100;
        job.current_agent = undefined;
        job.video_path = videoPath;
        job.updated_at = new Date();
        console.log(`✅ Job ${jobId} completed successfully! Video: ${videoPath}`);
      } else {
        job.status = 'failed';
        job.error_message = 'Video file not generated';
        job.updated_at = new Date();
        console.error(`❌ Job ${jobId} failed: Video file not found`);
      }
    } else {
      // Failure
      job.status = 'failed';
      job.error_message = `Video generation failed with code ${code}: ${errorBuffer.slice(-200)}`;
      job.updated_at = new Date();
      console.error(`❌ Job ${jobId} failed with exit code ${code}`);
    }
  });
  
  pythonProcess.on('error', (error) => {
    const job = jobs.get(jobId);
    if (!job) return;
    
    job.status = 'failed';
    job.error_message = `Process error: ${error.message}`;
    job.updated_at = new Date();
    console.error(`❌ Job ${jobId} process error:`, error);
  });
}

// Parse progress updates from Python output
function parseProgressFromOutput(jobId: string, output: string) {
  const job = jobs.get(jobId);
  if (!job) return;
  
  // Parse different progress indicators
  if (output.includes('Creating content') || output.includes('Creating test content')) {
    job.current_agent = 'Paper Analysis Agent';
    job.progress = 15;
  } else if (output.includes('Creating mock assets') || output.includes('Generating audio')) {
    job.current_agent = 'Audio Generation Agent';
    job.progress = 35;
  } else if (output.includes('Generated') && output.includes('audio files')) {
    job.progress = 50;
  } else if (output.includes('Generating video') || output.includes('Testing Enhanced Video Composition')) {
    job.current_agent = 'Video Composition Agent';
    job.progress = 65;
  } else if (output.includes('Enhanced video composition completed successfully')) {
    job.progress = 90;
  } else if (output.includes('Test Completed Successfully') || output.includes('SUCCESS:')) {
    job.progress = 100;
  }
  
  job.updated_at = new Date();
}

// Find the generated video file in the output directory
function findGeneratedVideo(outputDir: string): string | null {
  try {
    // Look for video files in the job output directory and subdirectories
    const searchDirs = [
      outputDir,
      path.join(outputDir, 'attention_paper_test'),
      path.join(outputDir, 'assets')
    ];
    
    for (const dir of searchDirs) {
      if (fs.existsSync(dir)) {
        const files = fs.readdirSync(dir);
        const videoFiles = files.filter(file => 
          file.endsWith('.mp4') && fs.statSync(path.join(dir, file)).size > 50000 // > 50KB
        );
        
        if (videoFiles.length > 0) {
          const videoPath = path.join(dir, videoFiles[0]);
          console.log(`Found video file: ${videoPath} (${fs.statSync(videoPath).size} bytes)`);
          return videoPath;
        }
      }
    }
    
    // Also check the main output directory for any mp4 files
    const outputPath = path.join(process.cwd(), 'output');
    if (fs.existsSync(outputPath)) {
      const findVideoRecursive = (dir: string): string | null => {
        const files = fs.readdirSync(dir);
        for (const file of files) {
          const fullPath = path.join(dir, file);
          const stat = fs.statSync(fullPath);
          
          if (stat.isDirectory()) {
            const found = findVideoRecursive(fullPath);
            if (found) return found;
          } else if (file.endsWith('.mp4') && stat.size > 50000) {
            console.log(`Found video file: ${fullPath} (${stat.size} bytes)`);
            return fullPath;
          }
        }
        return null;
      };
      
      return findVideoRecursive(outputPath);
    }
    
    return null;
  } catch (error) {
    console.error('Error finding video file:', error);
    return null;
  }
}

export default router;