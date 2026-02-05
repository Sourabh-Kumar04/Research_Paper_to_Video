import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardContent,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Tabs,
  Tab,
  Alert,
  LinearProgress,
  Typography,
  Box,
  Grid
} from '@mui/material';
import { 
  Play, 
  Upload, 
  Eye, 
  Clock, 
  Target, 
  Zap, 
  CheckCircle, 
  AlertTriangle,
  Settings,
  Image as ImageIcon,
  Hash,
  FileText
} from 'lucide-react';

import { YouTubeOptimizationSettings, SEOMetadata, ThumbnailSuggestion, ChapterMarker } from '../../types/cinematic';
import { CinematicApiService } from '../../services/cinematicApi';

interface YouTubeOptimizerProps {
  videoMetadata: {
    title: string;
    description: string;
    duration: number;
    content_type: string;
    topics: string[];
  };
  onOptimizationChange: (optimization: YouTubeOptimizationSettings) => void;
  onPreviewGenerated: (previewUrl: string) => void;
}

export const YouTubeOptimizer: React.FC<YouTubeOptimizerProps> = ({
  videoMetadata,
  onOptimizationChange,
  onPreviewGenerated
}) => {
  const [optimization, setOptimization] = useState<YouTubeOptimizationSettings>({
    encoding_params: {
      video_codec: 'H.264',
      audio_codec: 'AAC',
      resolution: [1920, 1080],
      frame_rate: 30,
      video_bitrate: 8000,
      audio_bitrate: 128,
      pixel_format: 'yuv420p'
    },
    seo_metadata: {
      title: videoMetadata.title,
      description: videoMetadata.description,
      tags: videoMetadata.topics,
      category: 'Education',
      language: 'en',
      thumbnail_suggestions: [],
      chapter_markers: []
    },
    thumbnail_settings: {
      generate_thumbnails: true,
      thumbnail_count: 3,
      include_text_overlay: true,
      style: 'engaging'
    },
    intro_outro: {
      add_intro: false,
      add_outro: false,
      intro_duration: 3,
      outro_duration: 5,
      branding_elements: true
    },
    engagement_features: {
      add_end_screens: true,
      add_cards: true,
      optimize_for_retention: true,
      include_call_to_action: true
    }
  });

  const [seoMetadata, setSeoMetadata] = useState<SEOMetadata | null>(null);
  const [thumbnailSuggestions, setThumbnailSuggestions] = useState<ThumbnailSuggestion[]>([]);
  const [chapterMarkers, setChapterMarkers] = useState<ChapterMarker[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [optimizationScore, setOptimizationScore] = useState(0);
  const [complianceStatus, setComplianceStatus] = useState<'compliant' | 'minor_issues' | 'major_issues'>('compliant');

  // Generate SEO metadata using AI
  const generateSEOMetadata = useCallback(async () => {
    setIsGenerating(true);
    try {
      // TODO: Implement YouTube SEO generation API
      console.log('Generating SEO metadata for:', videoMetadata);
      
      // Mock implementation for now
      const mockSEO: SEOMetadata = {
        title: videoMetadata.title,
        description: videoMetadata.description,
        tags: videoMetadata.topics || [],
        category: 'Education',
        language: 'en',
        thumbnail_suggestions: [],
        chapter_markers: []
      };

      setSeoMetadata(mockSEO);
      setThumbnailSuggestions([]);
      setChapterMarkers([]);

      // Update optimization settings
      const updatedOptimization = {
        ...optimization,
        seo_metadata: {
          ...optimization.seo_metadata,
          ...mockSEO
        }
      };
      setOptimization(updatedOptimization);
      onOptimizationChange(updatedOptimization);

    } catch (error) {
      console.error('Failed to generate SEO metadata:', error);
    } finally {
      setIsGenerating(false);
    }
  }, [videoMetadata, optimization, onOptimizationChange]);

  // Validate YouTube compliance
  const validateCompliance = useCallback(async () => {
    try {
      // TODO: Implement YouTube compliance validation API
      console.log('Validating compliance for:', optimization, videoMetadata);
      
      // Mock implementation for now
      setOptimizationScore(85);
      setComplianceStatus('compliant');
    } catch (error) {
      console.error('Failed to validate compliance:', error);
    }
  }, [optimization, videoMetadata]);

  // Generate preview
  const generatePreview = useCallback(async () => {
    try {
      // TODO: Implement YouTube preview generation API
      console.log('Generating preview for:', optimization, videoMetadata);
      
      // Mock implementation for now
      const mockPreviewUrl = 'https://example.com/preview.mp4';
      onPreviewGenerated(mockPreviewUrl);
    } catch (error) {
      console.error('Failed to generate preview:', error);
    }
  }, [optimization, videoMetadata, onPreviewGenerated]);

  // Update optimization setting
  const updateOptimization = useCallback((updates: Partial<YouTubeOptimizationSettings>) => {
    const updatedOptimization = { ...optimization, ...updates };
    setOptimization(updatedOptimization);
    onOptimizationChange(updatedOptimization);
  }, [optimization, onOptimizationChange]);

  // Validate compliance when settings change
  useEffect(() => {
    const timer = setTimeout(validateCompliance, 500);
    return () => clearTimeout(timer);
  }, [validateCompliance]);

  const getComplianceColor = () => {
    switch (complianceStatus) {
      case 'compliant': return 'text-green-600';
      case 'minor_issues': return 'text-yellow-600';
      case 'major_issues': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getComplianceIcon = () => {
    switch (complianceStatus) {
      case 'compliant': return <CheckCircle className="h-4 w-4" />;
      case 'minor_issues': return <AlertTriangle className="h-4 w-4" />;
      case 'major_issues': return <AlertTriangle className="h-4 w-4" />;
      default: return <Settings className="h-4 w-4" />;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5 text-red-500" />
            YouTube Optimizer
          </CardTitle>
          <div className="flex items-center gap-2">
            <div className={`flex items-center gap-1 ${getComplianceColor()}`}>
              {getComplianceIcon()}
              <span className="text-sm font-medium">
                {complianceStatus.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            <Badge variant="outline">
              Score: {optimizationScore}%
            </Badge>
          </div>
        </div>
        <Progress value={optimizationScore} className="w-full" />
      </CardHeader>

      <CardContent>
        <Tabs defaultValue="encoding" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="encoding">Encoding</TabsTrigger>
            <TabsTrigger value="seo">SEO & Metadata</TabsTrigger>
            <TabsTrigger value="thumbnails">Thumbnails</TabsTrigger>
            <TabsTrigger value="branding">Branding</TabsTrigger>
            <TabsTrigger value="engagement">Engagement</TabsTrigger>
          </TabsList>

          {/* Encoding Settings */}
          <TabsContent value="encoding" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="resolution">Resolution</Label>
                <Select
                  value={`${optimization.encoding_params.resolution[0]}x${optimization.encoding_params.resolution[1]}`}
                  onValueChange={(value: string) => {
                    const [width, height] = value.split('x').map(Number);
                    updateOptimization({
                      encoding_params: {
                        ...optimization.encoding_params,
                        resolution: [width, height]
                      }
                    });
                  }}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1920x1080">1080p (1920x1080)</SelectItem>
                    <SelectItem value="1280x720">720p (1280x720)</SelectItem>
                    <SelectItem value="3840x2160">4K (3840x2160)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="framerate">Frame Rate</Label>
                <Select
                  value={optimization.encoding_params.frame_rate.toString()}
                  onValueChange={(value: string) => {
                    updateOptimization({
                      encoding_params: {
                        ...optimization.encoding_params,
                        frame_rate: parseInt(value)
                      }
                    });
                  }}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="24">24 fps</SelectItem>
                    <SelectItem value="30">30 fps</SelectItem>
                    <SelectItem value="60">60 fps</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="video-bitrate">Video Bitrate (kbps)</Label>
                <Input
                  id="video-bitrate"
                  type="number"
                  value={optimization.encoding_params.video_bitrate}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                    updateOptimization({
                      encoding_params: {
                        ...optimization.encoding_params,
                        video_bitrate: parseInt(e.target.value)
                      }
                    });
                  }}
                  min={1000}
                  max={50000}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="audio-bitrate">Audio Bitrate (kbps)</Label>
                <Input
                  id="audio-bitrate"
                  type="number"
                  value={optimization.encoding_params.audio_bitrate}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                    updateOptimization({
                      encoding_params: {
                        ...optimization.encoding_params,
                        audio_bitrate: parseInt(e.target.value)
                      }
                    });
                  }}
                  min={64}
                  max={320}
                />
              </div>
            </div>

            <Alert>
              <Target className="h-4 w-4" />
              <AlertDescription>
                YouTube recommends H.264 video codec with AAC audio for best compatibility.
                Higher bitrates improve quality but increase file size.
              </AlertDescription>
            </Alert>
          </TabsContent>

          {/* SEO & Metadata */}
          <TabsContent value="seo" className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">SEO Optimization</h3>
              <Button 
                onClick={generateSEOMetadata} 
                disabled={isGenerating}
                className="flex items-center gap-2"
              >
                <Zap className="h-4 w-4" />
                {isGenerating ? 'Generating...' : 'AI Generate'}
              </Button>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="seo-title">Optimized Title</Label>
                <Input
                  id="seo-title"
                  value={optimization.seo_metadata.title}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                    updateOptimization({
                      seo_metadata: {
                        ...optimization.seo_metadata,
                        title: e.target.value
                      }
                    });
                  }}
                  placeholder="Enter SEO-optimized title..."
                />
                <p className="text-sm text-gray-500">
                  {optimization.seo_metadata.title.length}/100 characters
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="seo-description">Description</Label>
                <Textarea
                  id="seo-description"
                  value={optimization.seo_metadata.description}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                    updateOptimization({
                      seo_metadata: {
                        ...optimization.seo_metadata,
                        description: e.target.value
                      }
                    });
                  }}
                  placeholder="Enter detailed description..."
                  rows={4}
                />
                <p className="text-sm text-gray-500">
                  {optimization.seo_metadata.description.length}/5000 characters
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="tags">Tags</Label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {optimization.seo_metadata.tags.map((tag, index) => (
                    <Badge key={index} variant="secondary" className="flex items-center gap-1">
                      <Hash className="h-3 w-3" />
                      {tag}
                      <button
                        onClick={() => {
                          const newTags = optimization.seo_metadata.tags.filter((_, i) => i !== index);
                          updateOptimization({
                            seo_metadata: {
                              ...optimization.seo_metadata,
                              tags: newTags
                            }
                          });
                        }}
                        className="ml-1 text-red-500 hover:text-red-700"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
                <Input
                  placeholder="Add tags (press Enter)"
                  onKeyPress={(e: React.KeyboardEvent<HTMLInputElement>) => {
                    if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                      const newTag = e.currentTarget.value.trim();
                      if (!optimization.seo_metadata.tags.includes(newTag)) {
                        updateOptimization({
                          seo_metadata: {
                            ...optimization.seo_metadata,
                            tags: [...optimization.seo_metadata.tags, newTag]
                          }
                        });
                      }
                      e.currentTarget.value = '';
                    }
                  }}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Select
                    value={optimization.seo_metadata.category}
                    onValueChange={(value: string) => {
                      updateOptimization({
                        seo_metadata: {
                          ...optimization.seo_metadata,
                          category: value
                        }
                      });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Education">Education</SelectItem>
                      <SelectItem value="Entertainment">Entertainment</SelectItem>
                      <SelectItem value="Science & Technology">Science & Technology</SelectItem>
                      <SelectItem value="How-to & Style">How-to & Style</SelectItem>
                      <SelectItem value="People & Blogs">People & Blogs</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="language">Language</Label>
                  <Select
                    value={optimization.seo_metadata.language}
                    onValueChange={(value: string) => {
                      updateOptimization({
                        seo_metadata: {
                          ...optimization.seo_metadata,
                          language: value
                        }
                      });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                      <SelectItem value="fr">French</SelectItem>
                      <SelectItem value="de">German</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* Chapter Markers */}
            {chapterMarkers.length > 0 && (
              <div className="space-y-2">
                <Label>Chapter Markers</Label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {chapterMarkers.map((chapter, index) => (
                    <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                      <Clock className="h-4 w-4 text-gray-500" />
                      <span className="text-sm font-mono">
                        {Math.floor(chapter.timestamp / 60)}:{(chapter.timestamp % 60).toString().padStart(2, '0')}
                      </span>
                      <span className="text-sm">{chapter.title}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>

          {/* Thumbnails */}
          <TabsContent value="thumbnails" className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Thumbnail Generation</h3>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={optimization.thumbnail_settings.generate_thumbnails}
                  onCheckedChange={(checked: boolean) => {
                    updateOptimization({
                      thumbnail_settings: {
                        ...optimization.thumbnail_settings,
                        generate_thumbnails: checked
                      }
                    });
                  }}
                />
                <Label>Generate Thumbnails</Label>
              </div>
            </div>

            {optimization.thumbnail_settings.generate_thumbnails && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="thumbnail-count">Number of Thumbnails</Label>
                    <Input
                      id="thumbnail-count"
                      type="number"
                      value={optimization.thumbnail_settings.thumbnail_count}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                        updateOptimization({
                          thumbnail_settings: {
                            ...optimization.thumbnail_settings,
                            thumbnail_count: parseInt(e.target.value)
                          }
                        });
                      }}
                      min={1}
                      max={10}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="thumbnail-style">Style</Label>
                    <Select
                      value={optimization.thumbnail_settings.style}
                      onValueChange={(value: string) => {
                        updateOptimization({
                          thumbnail_settings: {
                            ...optimization.thumbnail_settings,
                            style: value as 'engaging' | 'professional' | 'minimal'
                          }
                        });
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="engaging">Engaging</SelectItem>
                        <SelectItem value="professional">Professional</SelectItem>
                        <SelectItem value="minimal">Minimal</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    checked={optimization.thumbnail_settings.include_text_overlay}
                    onCheckedChange={(checked: boolean) => {
                      updateOptimization({
                        thumbnail_settings: {
                          ...optimization.thumbnail_settings,
                          include_text_overlay: checked
                        }
                      });
                    }}
                  />
                  <Label>Include Text Overlay</Label>
                </div>

                {/* Thumbnail Suggestions */}
                {thumbnailSuggestions.length > 0 && (
                  <div className="space-y-2">
                    <Label>AI Thumbnail Suggestions</Label>
                    <div className="grid grid-cols-3 gap-4">
                      {thumbnailSuggestions.map((suggestion, index) => (
                        <div key={index} className="border rounded-lg p-3 space-y-2">
                          <div className="aspect-video bg-gray-100 rounded flex items-center justify-center">
                            <ImageIcon className="h-8 w-8 text-gray-400" />
                          </div>
                          <p className="text-sm font-medium">{suggestion.title}</p>
                          <p className="text-xs text-gray-500">{suggestion.description}</p>
                          <div className="flex items-center gap-1">
                            <Eye className="h-3 w-3" />
                            <span className="text-xs">Score: {suggestion.engagement_score}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </TabsContent>

          {/* Branding */}
          <TabsContent value="branding" className="space-y-4">
            <h3 className="text-lg font-semibold">Intro & Outro</h3>
            
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <Switch
                  checked={optimization.intro_outro.add_intro}
                  onCheckedChange={(checked: boolean) => {
                    updateOptimization({
                      intro_outro: {
                        ...optimization.intro_outro,
                        add_intro: checked
                      }
                    });
                  }}
                />
                <Label>Add Intro Sequence</Label>
              </div>

              {optimization.intro_outro.add_intro && (
                <div className="ml-6 space-y-2">
                  <Label htmlFor="intro-duration">Intro Duration (seconds)</Label>
                  <Input
                    id="intro-duration"
                    type="number"
                    value={optimization.intro_outro.intro_duration}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                      updateOptimization({
                        intro_outro: {
                          ...optimization.intro_outro,
                          intro_duration: parseInt(e.target.value)
                        }
                      });
                    }}
                    min={1}
                    max={10}
                  />
                </div>
              )}

              <div className="flex items-center space-x-2">
                <Switch
                  checked={optimization.intro_outro.add_outro}
                  onCheckedChange={(checked: boolean) => {
                    updateOptimization({
                      intro_outro: {
                        ...optimization.intro_outro,
                        add_outro: checked
                      }
                    });
                  }}
                />
                <Label>Add Outro Sequence</Label>
              </div>

              {optimization.intro_outro.add_outro && (
                <div className="ml-6 space-y-2">
                  <Label htmlFor="outro-duration">Outro Duration (seconds)</Label>
                  <Input
                    id="outro-duration"
                    type="number"
                    value={optimization.intro_outro.outro_duration}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                      updateOptimization({
                        intro_outro: {
                          ...optimization.intro_outro,
                          outro_duration: parseInt(e.target.value)
                        }
                      });
                    }}
                    min={1}
                    max={20}
                  />
                </div>
              )}

              <div className="flex items-center space-x-2">
                <Switch
                  checked={optimization.intro_outro.branding_elements}
                  onCheckedChange={(checked: boolean) => {
                    updateOptimization({
                      intro_outro: {
                        ...optimization.intro_outro,
                        branding_elements: checked
                      }
                    });
                  }}
                />
                <Label>Include Branding Elements</Label>
              </div>
            </div>
          </TabsContent>

          {/* Engagement */}
          <TabsContent value="engagement" className="space-y-4">
            <h3 className="text-lg font-semibold">Engagement Features</h3>
            
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <Switch
                  checked={optimization.engagement_features.add_end_screens}
                  onCheckedChange={(checked: boolean) => {
                    updateOptimization({
                      engagement_features: {
                        ...optimization.engagement_features,
                        add_end_screens: checked
                      }
                    });
                  }}
                />
                <Label>Add End Screens</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  checked={optimization.engagement_features.add_cards}
                  onCheckedChange={(checked: boolean) => {
                    updateOptimization({
                      engagement_features: {
                        ...optimization.engagement_features,
                        add_cards: checked
                      }
                    });
                  }}
                />
                <Label>Add Info Cards</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  checked={optimization.engagement_features.optimize_for_retention}
                  onCheckedChange={(checked: boolean) => {
                    updateOptimization({
                      engagement_features: {
                        ...optimization.engagement_features,
                        optimize_for_retention: checked
                      }
                    });
                  }}
                />
                <Label>Optimize for Retention</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  checked={optimization.engagement_features.include_call_to_action}
                  onCheckedChange={(checked: boolean) => {
                    updateOptimization({
                      engagement_features: {
                        ...optimization.engagement_features,
                        include_call_to_action: checked
                      }
                    });
                  }}
                />
                <Label>Include Call-to-Action</Label>
              </div>
            </div>

            <Alert>
              <Target className="h-4 w-4" />
              <AlertDescription>
                Engagement features help increase viewer retention and channel growth.
                End screens and cards can promote related content and subscriptions.
              </AlertDescription>
            </Alert>
          </TabsContent>
        </Tabs>

        {/* Action Buttons */}
        <div className="flex justify-between items-center mt-6 pt-4 border-t">
          <Button variant="outline" onClick={generatePreview} className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Generate Preview
          </Button>
          
          <div className="flex gap-2">
            <Button variant="outline" onClick={validateCompliance}>
              Validate Compliance
            </Button>
            <Button className="flex items-center gap-2">
              <Upload className="h-4 w-4" />
              Apply Optimization
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
