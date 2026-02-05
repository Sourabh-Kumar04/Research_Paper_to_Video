import { useState } from 'react';
import {
  Container,
  Typography,
  Paper,
  TextField,
  Button,
  Box,
  LinearProgress,
  Alert,
  Card,
  CardContent,
  Grid
} from '@mui/material';

interface JobStatus {
  job_id: string;
  status: string;
  progress: number;
  current_agent?: string;
  error_message?: string;
}

function App() {
  const [paperInput, setPaperInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submitJob = async () => {
    if (!paperInput.trim()) {
      setError('Please enter some paper content');
      return;
    }

    setLoading(true);
    setError(null);
    setJobStatus(null);

    try {
      const response = await fetch('/api/v1/jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          paper_input: {
            type: 'title',
            content: paperInput
          },
          options: {
            quality: 'medium',
            duration: 120
          }
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setJobStatus({
          job_id: result.job_id,
          status: result.status,
          progress: 0,
        });
        
        // Start polling for status
        pollJobStatus(result.job_id);
      } else {
        const errorData = await response.json();
        setError(`Failed to submit job: ${errorData.detail || response.statusText}`);
      }
    } catch (err) {
      setError(`Network error: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    const maxAttempts = 60; // 10 minutes max
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`/api/v1/jobs/${jobId}`);
        if (response.ok) {
          const status = await response.json();
          setJobStatus(status);

          if (status.status === 'completed' || status.status === 'failed') {
            return; // Stop polling
          }

          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(poll, 10000); // Poll every 10 seconds
          }
        }
      } catch (err) {
        console.error('Error polling job status:', err);
      }
    };

    setTimeout(poll, 2000); // Start polling after 2 seconds
  };

  const downloadVideo = async () => {
    if (!jobStatus?.job_id) return;

    try {
      const response = await fetch(`/api/v1/jobs/${jobStatus.job_id}/download`);
      if (response.ok) {
        // Get the video file as a blob
        const blob = await response.blob();
        
        // Create a download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `paper_video_${jobStatus.job_id}.mp4`;
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to download video');
      }
    } catch (err) {
      setError(`Download error: ${err}`);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          🎬 RASO Video Generator
        </Typography>
        <Typography variant="subtitle1" gutterBottom align="center" color="text.secondary">
          AI-Powered Research Paper to Video Conversion
        </Typography>

        <Box sx={{ mt: 4 }}>
          <TextField
            fullWidth
            multiline
            rows={6}
            label="Research Paper Content or Title"
            placeholder="Enter your research paper title, abstract, or full content here..."
            value={paperInput}
            onChange={(e) => setPaperInput(e.target.value)}
            variant="outlined"
            sx={{ mb: 3 }}
          />

          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
            <Button
              variant="contained"
              size="large"
              onClick={submitJob}
              disabled={loading || !paperInput.trim()}
              sx={{ minWidth: 200 }}
            >
              {loading ? 'Submitting...' : 'Generate Video'}
            </Button>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {jobStatus && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Job Status
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">
                      Job ID: {jobStatus.job_id}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">
                      Status: {jobStatus.status}
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Box sx={{ width: '100%', mr: 1 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={jobStatus.progress} 
                        />
                      </Box>
                      <Box sx={{ minWidth: 35 }}>
                        <Typography variant="body2" color="text.secondary">
                          {Math.round(jobStatus.progress)}%
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                  {jobStatus.current_agent && (
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">
                        Current Agent: {jobStatus.current_agent}
                      </Typography>
                    </Grid>
                  )}
                  {jobStatus.error_message && (
                    <Grid item xs={12}>
                      <Alert severity="error">
                        {jobStatus.error_message}
                      </Alert>
                    </Grid>
                  )}
                  {jobStatus.status === 'completed' && (
                    <Grid item xs={12}>
                      <Button
                        variant="contained"
                        color="success"
                        onClick={downloadVideo}
                        fullWidth
                      >
                        Download Video
                      </Button>
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Information
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • Backend API: Running on port 8000
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • Frontend UI: Running on port 3002
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • Video Generation: AI-powered with multiple agents
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • Cinematic Features: Enhanced visual processing
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Paper>
    </Container>
  );
}

export default App;