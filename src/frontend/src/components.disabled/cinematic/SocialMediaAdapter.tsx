import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { 
  Share2, 
  Instagram, 
  Play, 
  Linkedin, 
  Twitter,
  Facebook,
  Download,
  Eye,
  CheckCircle,
  AlertTriangle,
  Clock,
  FileSize,
  AspectRatio,
  Zap
} from 'lucide-react';

import { SocialPlatform, PlatformAdaptation, ContentOptimization } from '../../types/cinematic';
import { CinematicApiService } from '../../services/cinematicApi';

interface SocialMediaAdapterProps {
  videoMetadata: {
    title: string;
    description: string;
    duration: number;
    content_type: string;
    topics: string[];
    complexity_score?: number;
  };
  baseSettings: any;
  onAdaptationChange: (adaptations: Record<SocialPlatform, PlatformAdaptation>) => void;
  onExportRequested: (platforms: SocialPlatform[], adaptations: Record<SocialPlatform, PlatformAdaptation>) => void;
}

const PLATFORM_ICONS = {
  [SocialPlatform.YOUTUBE]: Play,
  [SocialPlatform.INSTAGRAM]: Instagram,
  [SocialPlatform.TIKTOK]: Play, // TikTok icon would be custom
  [SocialPlatform.LINKEDIN]: Linkedin,
  [SocialPlatform.TWITTER]: Twitter,
  [SocialPlatform.FACEBOOK]: Facebook,
};

const PLATFORM_COLORS = {
  [SocialPlatform.YOUTUBE]: 'text-red-500',
  [SocialPlatform.INSTAGRAM]: 'text-pink-500',
  [SocialPlatform.TIKTOK]: 'text-black',
  [SocialPlatform.LINKEDIN]: 'text-blue-600',
  [SocialPlatform.TWITTER]: 'text-blue-400',
  [SocialPlatform.FACEBOOK]: 'text-blue-700',
};

export const SocialMediaAdapter: React.FC<SocialMediaAdapterProps> = ({
  videoMetadata,
  baseSettings,
  onAdaptationChange,
  onExportRequested
}) => {
  const [selectedPlatforms, setSelectedPlatforms] = useState<SocialPlatform[]>([
    SocialPlatform.YOUTUBE,
    SocialPlatform.INSTAGRAM
  ]);
  const [adaptations, setAdaptations] = useState<Record<SocialPlatform, PlatformAdaptation>>({});
  const [isAdapting, setIsAdapting] = useState(false);
  const [contentAnalysis, setContentAnalysis] = useState<any>(null);
  const [comparisonView, setComparisonView] = useState(false);

  // Adapt content for selected platforms
  const adaptForPlatforms = useCallback(async () => {
    if (selectedPlatforms.length === 0) return;

    setIsAdapting(true);
    try {
      const response = await CinematicApiService.adaptForSocialPlatforms({
        base_settings: baseSettings,
        content_metadata: videoMetadata,
        target_platforms: selectedPlatforms
      });

      setAdaptations(response.adaptations);
      onAdaptationChange(response.adaptations);

      // Get content analysis
      const analysisResponse = await CinematicApiService.analyzeContentForPlatforms({
        content_metadata: videoMetadata,
        target_platforms: selectedPlatforms
      });
      setContentAnalysis(analysisResponse);

    } catch (error) {
      console.error('Failed to adapt for platforms:', error);
    } finally {
      setIsAdapting(false);
    }
  }, [selectedPlatforms, baseSettings, videoMetadata, onAdaptationChange]);

  // Handle platform selection
  const togglePlatform = useCallback((platform: SocialPlatform) => {
    setSelectedPlatforms(prev => {
      const newSelection = prev.includes(platform)
        ? prev.filter(p => p !== platform)
        : [...prev, platform];
      return newSelection;
    });
  }, []);

  // Export for selected platforms
  const handleExport = useCallback(() => {
    const exportPlatforms = selectedPlatforms.filter(p => adaptations[p]);
    onExportRequested(exportPlatforms, adaptations);
  }, [selectedPlatforms, adaptations, onExportRequested]);

  // Adapt when platforms or settings change
  useEffect(() => {
    if (selectedPlatforms.length > 0) {
      const timer = setTimeout(adaptForPlatforms, 500);
      return () => clearTimeout(timer);
    }
  }, [adaptForPlatforms]);

  const getComplianceColor = (status: string) => {
    switch (status) {
      case 'compliant': return 'text-green-600';
      case 'minor_issues': return 'text-yellow-600';
      case 'major_issues': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getComplianceIcon = (status: string) => {
    switch (status) {
      case 'compliant': return <CheckCircle className="h-4 w-4" />;
      case 'minor_issues': return <AlertTriangle className="h-4 w-4" />;
      case 'major_issues': return <AlertTriangle className="h-4 w-4" />;
      default: return <Clock className="h-4 w-4" />;
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatFileSize = (mb: number) => {
    if (mb < 1) return `${(mb * 1024).toFixed(0)} KB`;
    if (mb < 1024) return `${mb.toFixed(1)} MB`;
    return `${(mb / 1024).toFixed(1)} GB`;
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Share2 className="h-5 w-5 text-blue-500" />
            Multi-Platform Social Media Adapter
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setComparisonView(!comparisonView)}
            >
              {comparisonView ? 'List View' : 'Compare View'}
            </Button>
            <Button
              onClick={handleExport}
              disabled={Object.keys(adaptations).length === 0}
              className="flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Export ({selectedPlatforms.length})
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Platform Selection */}
        <div className="space-y-4 mb-6">
          <h3 className="text-lg font-semibold">Select Target Platforms</h3>
          <div className="grid grid-cols-3 gap-4">
            {Object.values(SocialPlatform).map((platform) => {
              const Icon = PLATFORM_ICONS[platform];
              const isSelected = selectedPlatforms.includes(platform);
              
              return (
                <div
                  key={platform}
                  className={`border rounded-lg p-4 cursor-pointer transition-all ${
                    isSelected 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => togglePlatform(platform)}
                >
                  <div className="flex items-center space-x-2">
                    <Checkbox checked={isSelected} readOnly />
                    <Icon className={`h-5 w-5 ${PLATFORM_COLORS[platform]}`} />
                    <Label className="capitalize cursor-pointer">
                      {platform.replace('_', ' ')}
                    </Label>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Content Analysis */}
        {contentAnalysis && (
          <div className="mb-6">
            <Alert>
              <Zap className="h-4 w-4" />
              <AlertDescription>
                <strong>Content Analysis:</strong> {contentAnalysis.content_classification} content
                {contentAnalysis.platform_ranking && (
                  <span>
                    {' '}• Best platforms: {contentAnalysis.platform_ranking.slice(0, 3).join(', ')}
                  </span>
                )}
              </AlertDescription>
            </Alert>
          </div>
        )}

        {/* Loading State */}
        {isAdapting && (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
              <p className="text-sm text-gray-600">Adapting content for platforms...</p>
            </div>
          </div>
        )}

        {/* Adaptations Display */}
        {Object.keys(adaptations).length > 0 && !isAdapting && (
          <div className="space-y-6">
            {comparisonView ? (
              /* Comparison View */
              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-gray-200">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="border border-gray-200 p-3 text-left">Platform</th>
                      <th className="border border-gray-200 p-3 text-left">Aspect Ratio</th>
                      <th className="border border-gray-200 p-3 text-left">Resolution</th>
                      <th className="border border-gray-200 p-3 text-left">File Size</th>
                      <th className="border border-gray-200 p-3 text-left">Performance</th>
                      <th className="border border-gray-200 p-3 text-left">Compliance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedPlatforms.map((platform) => {
                      const adaptation = adaptations[platform];
                      if (!adaptation) return null;

                      const Icon = PLATFORM_ICONS[platform];
                      
                      return (
                        <tr key={platform} className="hover:bg-gray-50">
                          <td className="border border-gray-200 p-3">
                            <div className="flex items-center gap-2">
                              <Icon className={`h-4 w-4 ${PLATFORM_COLORS[platform]}`} />
                              <span className="capitalize">{platform.replace('_', ' ')}</span>
                            </div>
                          </td>
                          <td className="border border-gray-200 p-3">
                            {adaptation.adapted_settings.aspect_ratio || 'N/A'}
                          </td>
                          <td className="border border-gray-200 p-3">
                            {adaptation.adapted_settings.resolution 
                              ? `${adaptation.adapted_settings.resolution[0]}×${adaptation.adapted_settings.resolution[1]}`
                              : 'N/A'
                            }
                          </td>
                          <td className="border border-gray-200 p-3">
                            {formatFileSize(adaptation.encoding_params.estimated_file_size_mb || 0)}
                          </td>
                          <td className="border border-gray-200 p-3">
                            <div className="flex items-center gap-2">
                              <Progress 
                                value={adaptation.estimated_performance_score} 
                                className="w-16 h-2" 
                              />
                              <span className="text-sm">{adaptation.estimated_performance_score.toFixed(0)}%</span>
                            </div>
                          </td>
                          <td className="border border-gray-200 p-3">
                            <div className={`flex items-center gap-1 ${getComplianceColor(adaptation.compliance_status)}`}>
                              {getComplianceIcon(adaptation.compliance_status)}
                              <span className="text-sm capitalize">
                                {adaptation.compliance_status.replace('_', ' ')}
                              </span>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              /* List View */
              <Tabs defaultValue={selectedPlatforms[0]} className="w-full">
                <TabsList className="grid w-full grid-cols-6">
                  {selectedPlatforms.map((platform) => {
                    const Icon = PLATFORM_ICONS[platform];
                    return (
                      <TabsTrigger key={platform} value={platform} className="flex items-center gap-1">
                        <Icon className={`h-4 w-4 ${PLATFORM_COLORS[platform]}`} />
                        <span className="hidden sm:inline capitalize">
                          {platform.replace('_', ' ')}
                        </span>
                      </TabsTrigger>
                    );
                  })}
                </TabsList>

                {selectedPlatforms.map((platform) => {
                  const adaptation = adaptations[platform];
                  if (!adaptation) return null;

                  return (
                    <TabsContent key={platform} value={platform} className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Platform Overview */}
                        <Card>
                          <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                              {React.createElement(PLATFORM_ICONS[platform], {
                                className: `h-5 w-5 ${PLATFORM_COLORS[platform]}`
                              })}
                              {platform.replace('_', ' ').toUpperCase()} Optimization
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-3">
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Performance Score</span>
                              <div className="flex items-center gap-2">
                                <Progress 
                                  value={adaptation.estimated_performance_score} 
                                  className="w-20 h-2" 
                                />
                                <Badge variant="outline">
                                  {adaptation.estimated_performance_score.toFixed(0)}%
                                </Badge>
                              </div>
                            </div>

                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Compliance</span>
                              <div className={`flex items-center gap-1 ${getComplianceColor(adaptation.compliance_status)}`}>
                                {getComplianceIcon(adaptation.compliance_status)}
                                <span className="text-sm capitalize">
                                  {adaptation.compliance_status.replace('_', ' ')}
                                </span>
                              </div>
                            </div>

                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Aspect Ratio</span>
                              <Badge variant="secondary" className="flex items-center gap-1">
                                <AspectRatio className="h-3 w-3" />
                                {adaptation.adapted_settings.aspect_ratio}
                              </Badge>
                            </div>

                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Resolution</span>
                              <span className="text-sm">
                                {adaptation.adapted_settings.resolution 
                                  ? `${adaptation.adapted_settings.resolution[0]}×${adaptation.adapted_settings.resolution[1]}`
                                  : 'N/A'
                                }
                              </span>
                            </div>

                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Estimated File Size</span>
                              <Badge variant="outline" className="flex items-center gap-1">
                                <FileSize className="h-3 w-3" />
                                {formatFileSize(adaptation.encoding_params.estimated_file_size_mb || 0)}
                              </Badge>
                            </div>
                          </CardContent>
                        </Card>

                        {/* Content Optimizations */}
                        <Card>
                          <CardHeader>
                            <CardTitle>Content Optimizations</CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-3">
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Pacing</span>
                              <span className="text-sm">
                                {adaptation.content_optimizations.pacing_multiplier}x speed
                              </span>
                            </div>

                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Visual Density</span>
                              <Badge variant="secondary">
                                {adaptation.content_optimizations.visual_density}
                              </Badge>
                            </div>

                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Text Size</span>
                              <Badge variant="secondary">
                                {adaptation.content_optimizations.text_size}
                              </Badge>
                            </div>

                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Subtitles</span>
                              <Badge variant={adaptation.content_optimizations.subtitles_required ? "default" : "secondary"}>
                                {adaptation.content_optimizations.subtitles_required ? "Required" : "Optional"}
                              </Badge>
                            </div>

                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Engagement Style</span>
                              <Badge variant="secondary">
                                {adaptation.content_optimizations.engagement_style}
                              </Badge>
                            </div>

                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Attention Span</span>
                              <span className="text-sm flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {adaptation.content_optimizations.attention_span_seconds}s
                              </span>
                            </div>
                          </CardContent>
                        </Card>
                      </div>

                      {/* Adaptations Applied */}
                      {adaptation.adaptations_applied.length > 0 && (
                        <Card>
                          <CardHeader>
                            <CardTitle>Applied Adaptations</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="space-y-2">
                              {adaptation.adaptations_applied.map((change, index) => (
                                <div key={index} className="flex items-start gap-2 p-2 bg-gray-50 rounded">
                                  <CheckCircle className="h-4 w-4 text-green-500 mt-0.5" />
                                  <div>
                                    <p className="text-sm font-medium capitalize">
                                      {change.type.replace('_', ' ')}
                                    </p>
                                    <p className="text-xs text-gray-600">{change.reason}</p>
                                    {change.original && change.adapted && (
                                      <p className="text-xs text-gray-500">
                                        {JSON.stringify(change.original)} → {JSON.stringify(change.adapted)}
                                      </p>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </CardContent>
                        </Card>
                      )}
                    </TabsContent>
                  );
                })}
              </Tabs>
            )}
          </div>
        )}

        {/* Export Options */}
        {Object.keys(adaptations).length > 0 && (
          <div className="mt-6 pt-4 border-t">
            <div className="flex justify-between items-center">
              <div className="text-sm text-gray-600">
                Ready to export {selectedPlatforms.length} platform{selectedPlatforms.length !== 1 ? 's' : ''}
              </div>
              <div className="flex gap-2">
                <Button variant="outline" className="flex items-center gap-2">
                  <Eye className="h-4 w-4" />
                  Preview All
                </Button>
                <Button onClick={handleExport} className="flex items-center gap-2">
                  <Download className="h-4 w-4" />
                  Export All Platforms
                </Button>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
