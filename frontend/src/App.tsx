import React, { useState } from 'react';
import { Container, Typography, Paper, TextField, Button, Box, LinearProgress } from '@mui/material';

interface JobStatus {
  job_id: string;
  status: string;
  progress: number;
  current_agent?: string;
  error_message?: string;
}

function App() {
  const [paperInput, setPaperInput] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [loading, setLoading] = useState(false);

  const submitJob = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          paper_input: {
            type: 'title',
            content: paperInput,
          },
        }),
      });
      
      const result = await response.json();
      setJobId(result.job_id);
      
      // Start polling for status
      pollJobStatus(result.job_id);
    } catch (error) {
      console.error('Failed to submit job:', error);
    } finally {
      setLoading(false);
    }
  };

  const pollJobStatus = async (id: string) => {
    try {
      const response = await fetch(`/api/jobs/${id}`);
      const status = await response.json();
      setJobStatus(status);
      
      if (status.status === 'processing' || status.status === 'queued') {
        setTimeout(() => pollJobStatus(id), 2000);
      }
    } catch (error) {
      console.error('Failed to get job status:', error);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom>
        RASO Platform
      </Typography>
      <Typography variant="subtitle1" gutterBottom>
        Research paper Automated Simulation & Orchestration Platform
      </Typography>
      
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h5" gutterBottom>
          Generate Video from Research Paper
        </Typography>
        
        <TextField
          fullWidth
          label="Paper Title or arXiv URL"
          value={paperInput}
          onChange={(e) => setPaperInput(e.target.value)}
          margin="normal"
          placeholder="Enter paper title or arXiv URL"
        />
        
        <Box sx={{ mt: 2 }}>
          <Button
            variant="contained"
            onClick={submitJob}
            disabled={!paperInput || loading}
            size="large"
          >
            Generate Video
          </Button>
        </Box>
        
        {jobStatus && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6">Job Status: {jobStatus.status}</Typography>
            {jobStatus.current_agent && (
              <Typography variant="body2">
                Current Agent: {jobStatus.current_agent}
              </Typography>
            )}
            
            <LinearProgress
              variant="determinate"
              value={jobStatus.progress}
              sx={{ mt: 2 }}
            />
            <Typography variant="body2" sx={{ mt: 1 }}>
              Progress: {Math.round(jobStatus.progress)}%
            </Typography>
            
            {jobStatus.status === 'completed' && jobId && (
              <Button
                variant="outlined"
                href={`/api/jobs/${jobId}/download`}
                sx={{ mt: 2 }}
              >
                Download Video
              </Button>
            )}
            
            {jobStatus.error_message && (
              <Typography color="error" sx={{ mt: 2 }}>
                Error: {jobStatus.error_message}
              </Typography>
            )}
          </Box>
        )}
      </Paper>
    </Container>
  );
}

export default App;