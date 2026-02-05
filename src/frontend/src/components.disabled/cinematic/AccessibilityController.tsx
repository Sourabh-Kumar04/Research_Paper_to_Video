import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Shield, 
  Eye, 
  Ear, 
  Type, 
  Zap, 
  CheckCircle, 
  AlertTriangle, 
  XCircle,
  Clock,
  Volume2,
  Palette,
  FileText,
  Download,
  Play
} from 'lucide-react';

import { WCAGLevel, AccessibilityReport, AccessibilityIssueType } from '../../types/cinematic';
import { CinematicApiService } from '../../services/cinematicApi';

interface AccessibilityControllerProps {
  videoMetadata: {
    title: string;
    description: string;
    duration: number;
    content_type: string;
    transcript?: string;
  };
  cinematicSettings: any;
  onAccessibilityChange: (settings: any) => void;
  onReportGenerated: (report: AccessibilityReport) => void;
}

const WCAG_LEVEL_DESCRIPTIONS = {
  [WCAGLevel.A]: 'Basic accessibility compliance',
  [WCAGLevel.AA]: 'Standard accessibility compliance (recommended)',
  [WCAGLevel.AAA]: 'Enhanced accessibility compliance'
};

const ISSUE_TYPE_ICONS = {
  [AccessibilityIssueType.COLOR_CONTRAST]: Palette,
  [AccessibilityIssueType.FLASHING_CONTENT]: Zap,
  [AccessibilityIssueType.AUDIO_DESCRIPTION]: Volume2,
  [AccessibilityIssueType.CAPTIONS]: FileText,
  [AccessibilityIssueType.LANGUAGE_CLARITY]: Type,
  [AccessibilityIssueType.NAVIGATION]: Eye,
  [AccessibilityIssueType.TIMING]: Clock,
};

const SEVERITY_COLORS = {
  low: 'text-blue-600',
  medium: 'text-yellow-600',
  high: 'text-orange-600',
  critical: 'text-red-600'
};

const SEVERITY_ICONS = {
  low: CheckCircle,
  medium: AlertTriangle,
  high: AlertTriangle,
  critical: XCircle
};

export const AccessibilityController: React.FC<AccessibilityControllerProps> = ({
  videoMetadata,
  cinematicSettings,
  onAccessibilityChange,
  onReportGenerated
}) => {
  const [targetWCAGLevel, setTargetWCAGLevel] = useState<WCAGLevel>(WCAGLevel.AA);
  const [accessibilityReport, setAccessibilityReport] = useState<AccessibilityReport | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [accessibilitySettings, setAccessibilitySettings] = useState({
    generate_captions: true,
    generate_audio_descriptions: true,
    high_contrast_mode: false,
    large_text_mode: false,
    reduce_motion: false,
    auto_play_disabled: true,
    keyboard_navigation: true,
    screen_reader_optimized: true
  });

  // Analyze accessibility compliance
  const analyzeAccessibility = useCallback(async () => {
    setIsAnalyzing(true);
    try {
      const response = await CinematicApiService.analyzeAccessibility({
        video_metadata: videoMetadata,
        cinematic_settings: cinematicSettings,
        target_wcag_level: targetWCAGLevel
      });

      setAccessibilityReport(response);
      onReportGenerated(response);
    } catch (error) {
      console.error('Failed to analyze accessibility:', error);
    } finally {
      setIsAnalyzing(false);
    }
  }, [videoMetadata, cinematicSettings, targetWCAGLevel, onReportGenerated]);

  // Update accessibility setting
  const updateAccessibilitySetting = useCallback((key: string, value: any) => {
    const updatedSettings = { ...accessibilitySettings, [key]: value };
    setAccessibilitySettings(updatedSettings);
    onAccessibilityChange(updatedSettings);
  }, [accessibilitySettings, onAccessibilityChange]);

  // Auto-analyze when settings change
  useEffect(() => {
    const timer = setTimeout(analyzeAccessibility, 1000);
    return () => clearTimeout(timer);
  }, [analyzeAccessibility]);

  const getComplianceColor = (compliance: boolean) => {
    return compliance ? 'text-green-600' : 'text-red-600';
  };

  const getComplianceIcon = (compliance: boolean) => {
    return compliance ? CheckCircle : XCircle;
  };

  const getSeverityIcon = (severity: string) => {
    const Icon = SEVERITY_ICONS[severity as keyof typeof SEVERITY_ICONS] || AlertTriangle;
    return Icon;
  };

  const groupIssuesByType = (issues: any[]) => {
    return issues.reduce((groups, issue) => {
      const type = issue.type;
      if (!groups[type]) {
        groups[type] = [];
      }
      groups[type].push(issue);
      return groups;
    }, {} as Record<string, any[]>);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-green-500" />
            Accessibility Controller
          </CardTitle>
          <div className="flex items-center gap-2">
            {accessibilityReport && (
              <div className={`flex items-center gap-1 ${getComplianceColor(accessibilityReport.overall_compliance)}`}>
                {React.createElement(getComplianceIcon(accessibilityReport.overall_compliance), {
                  className: "h-4 w-4"
                })}
                <span className="text-sm font-medium">
                  {accessibilityReport.overall_compliance ? 'COMPLIANT' : 'NON-COMPLIANT'}
                </span>
              </div>
            )}
            {accessibilityReport && (
              <Badge variant="outline">
                Score: {accessibilityReport.compliance_score.toFixed(0)}%
              </Badge>
            )}
          </div>
        </div>
        {accessibilityReport && (
          <Progress value={accessibilityReport.compliance_score} className="w-full" />
        )}
      </CardHeader>

      <CardContent>
        <Tabs defaultValue="settings" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="settings">Settings</TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
            <TabsTrigger value="issues">Issues</TabsTrigger>
            <TabsTrigger value="captions">Captions</TabsTrigger>
          </TabsList>

          {/* Accessibility Settings */}
          <TabsContent value="settings" className="space-y-6">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="wcag-level">WCAG Compliance Level</Label>
                <Select
                  value={targetWCAGLevel}
                  onValueChange={(value) => setTargetWCAGLevel(value as WCAGLevel)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.values(WCAGLevel).map((level) => (
                      <SelectItem key={level} value={level}>
                        WCAG {level} - {WCAG_LEVEL_DESCRIPTIONS[level]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <FileText className="h-4 w-4" />
                      Content Accessibility
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="generate-captions">Generate Captions</Label>
                      <Switch
                        id="generate-captions"
                        checked={accessibilitySettings.generate_captions}
                        onCheckedChange={(checked: boolean) => updateAccessibilitySetting('generate_captions', checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label htmlFor="generate-audio-descriptions">Audio Descriptions</Label>
                      <Switch
                        id="generate-audio-descriptions"
                        checked={accessibilitySettings.generate_audio_descriptions}
                        onCheckedChange={(checked: boolean) => updateAccessibilitySetting('generate_audio_descriptions', checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label htmlFor="screen-reader-optimized">Screen Reader Optimized</Label>
                      <Switch
                        id="screen-reader-optimized"
                        checked={accessibilitySettings.screen_reader_optimized}
                        onCheckedChange={(checked: boolean) => updateAccessibilitySetting('screen_reader_optimized', checked)}
                      />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Eye className="h-4 w-4" />
                      Visual Accessibility
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="high-contrast-mode">High Contrast Mode</Label>
                      <Switch
                        id="high-contrast-mode"
                        checked={accessibilitySettings.high_contrast_mode}
                        onCheckedChange={(checked: boolean) => updateAccessibilitySetting('high_contrast_mode', checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label htmlFor="large-text-mode">Large Text Mode</Label>
                      <Switch
                        id="large-text-mode"
                        checked={accessibilitySettings.large_text_mode}
                        onCheckedChange={(checked: boolean) => updateAccessibilitySetting('large_text_mode', checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label htmlFor="reduce-motion">Reduce Motion</Label>
                      <Switch
                        id="reduce-motion"
                        checked={accessibilitySettings.reduce_motion}
                        onCheckedChange={(checked: boolean) => updateAccessibilitySetting('reduce_motion', checked)}
                      />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Volume2 className="h-4 w-4" />
                      Audio Accessibility
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="auto-play-disabled">Disable Auto-play</Label>
                      <Switch
                        id="auto-play-disabled"
                        checked={accessibilitySettings.auto_play_disabled}
                        onCheckedChange={(checked: boolean) => updateAccessibilitySetting('auto_play_disabled', checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label htmlFor="keyboard-navigation">Keyboard Navigation</Label>
                      <Switch
                        id="keyboard-navigation"
                        checked={accessibilitySettings.keyboard_navigation}
                        onCheckedChange={(checked: boolean) => updateAccessibilitySetting('keyboard_navigation', checked)}
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>

            <div className="flex justify-between items-center pt-4 border-t">
              <Button variant="outline" onClick={analyzeAccessibility} disabled={isAnalyzing}>
                {isAnalyzing ? 'Analyzing...' : 'Re-analyze Accessibility'}
              </Button>
              <Button className="flex items-center gap-2">
                <Download className="h-4 w-4" />
                Export Accessibility Report
              </Button>
            </div>
          </TabsContent>

          {/* Analysis Overview */}
          <TabsContent value="analysis" className="space-y-4">
            {isAnalyzing ? (
              <div className="flex items-center justify-center py-8">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
                  <p className="text-sm text-gray-600">Analyzing accessibility compliance...</p>
                </div>
              </div>
            ) : accessibilityReport ? (
              <div className="space-y-6">
                {/* Overall Compliance */}
                <Card>
                  <CardHeader>
                    <CardTitle>WCAG {accessibilityReport.wcag_level} Compliance</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center">
                        <div className={`text-2xl font-bold ${getComplianceColor(accessibilityReport.overall_compliance)}`}>
                          {accessibilityReport.overall_compliance ? 'PASS' : 'FAIL'}
                        </div>
                        <p className="text-sm text-gray-600">Overall Compliance</p>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">
                          {accessibilityReport.compliance_score.toFixed(0)}%
                        </div>
                        <p className="text-sm text-gray-600">Compliance Score</p>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-orange-600">
                          {accessibilityReport.issues.length}
                        </div>
                        <p className="text-sm text-gray-600">Issues Found</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Color Contrast Analysis */}
                {accessibilityReport.color_contrast_results.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Palette className="h-4 w-4" />
                        Color Contrast Analysis
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {accessibilityReport.color_contrast_results.map((result, index) => (
                          <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                            <div className="flex items-center gap-2">
                              <div 
                                className="w-4 h-4 rounded border"
                                style={{ backgroundColor: result.foreground_color }}
                              ></div>
                              <span className="text-sm">on</span>
                              <div 
                                className="w-4 h-4 rounded border"
                                style={{ backgroundColor: result.background_color }}
                              ></div>
                              <span className="text-sm font-mono">
                                {result.contrast_ratio.toFixed(2)}:1
                              </span>
                            </div>
                            <div className="flex gap-1">
                              <Badge variant={result.wcag_aa_pass ? "default" : "destructive"}>
                                AA {result.wcag_aa_pass ? 'PASS' : 'FAIL'}
                              </Badge>
                              <Badge variant={result.wcag_aaa_pass ? "default" : "secondary"}>
                                AAA {result.wcag_aaa_pass ? 'PASS' : 'FAIL'}
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Flashing Content Analysis */}
                {accessibilityReport.flashing_content_result && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Zap className="h-4 w-4" />
                        Flashing Content Analysis
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">Flashing Detected</span>
                          <Badge variant={accessibilityReport.flashing_content_result.has_flashing ? "destructive" : "default"}>
                            {accessibilityReport.flashing_content_result.has_flashing ? 'YES' : 'NO'}
                          </Badge>
                        </div>
                        {accessibilityReport.flashing_content_result.has_flashing && (
                          <>
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Frequency</span>
                              <span className="text-sm">
                                {accessibilityReport.flashing_content_result.flash_frequency.toFixed(1)} Hz
                              </span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Risk Level</span>
                              <Badge variant={
                                accessibilityReport.flashing_content_result.risk_level === 'high' ? 'destructive' :
                                accessibilityReport.flashing_content_result.risk_level === 'medium' ? 'secondary' : 'default'
                              }>
                                {accessibilityReport.flashing_content_result.risk_level.toUpperCase()}
                              </Badge>
                            </div>
                          </>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Language Clarity */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Type className="h-4 w-4" />
                      Language Clarity
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Clarity Score</span>
                      <div className="flex items-center gap-2">
                        <Progress 
                          value={accessibilityReport.language_clarity_score * 100} 
                          className="w-20 h-2" 
                        />
                        <Badge variant="outline">
                          {(accessibilityReport.language_clarity_score * 100).toFixed(0)}%
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Recommendations */}
                {accessibilityReport.recommendations.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Recommendations</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {accessibilityReport.recommendations.map((recommendation, index) => (
                          <div key={index} className="flex items-start gap-2 p-2 bg-blue-50 rounded">
                            <CheckCircle className="h-4 w-4 text-blue-500 mt-0.5" />
                            <p className="text-sm">{recommendation}</p>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            ) : (
              <Alert>
                <Shield className="h-4 w-4" />
                <AlertDescription>
                  Click "Analyze Accessibility" to generate a comprehensive accessibility report.
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>

          {/* Issues Detail */}
          <TabsContent value="issues" className="space-y-4">
            {accessibilityReport && accessibilityReport.issues.length > 0 ? (
              <div className="space-y-4">
                {Object.entries(groupIssuesByType(accessibilityReport.issues)).map(([type, issues]) => {
                  const Icon = ISSUE_TYPE_ICONS[type as AccessibilityIssueType] || AlertTriangle;
                  
                  return (
                    <Card key={type}>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-base">
                          <Icon className="h-4 w-4" />
                          {type.replace('_', ' ').toUpperCase()} Issues ({issues.length})
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {issues.map((issue, index) => {
                            const SeverityIcon = getSeverityIcon(issue.severity);
                            
                            return (
                              <div key={index} className="flex items-start gap-2 p-3 border rounded">
                                <SeverityIcon className={`h-4 w-4 mt-0.5 ${SEVERITY_COLORS[issue.severity as keyof typeof SEVERITY_COLORS]}`} />
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <Badge variant={
                                      issue.severity === 'critical' ? 'destructive' :
                                      issue.severity === 'high' ? 'secondary' : 'outline'
                                    }>
                                      {issue.severity.toUpperCase()}
                                    </Badge>
                                  </div>
                                  <p className="text-sm font-medium">{issue.description}</p>
                                  <p className="text-xs text-gray-600 mt-1">Location: {issue.location}</p>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            ) : (
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  {accessibilityReport 
                    ? "No accessibility issues found! Your content meets the selected WCAG compliance level."
                    : "Run accessibility analysis to see detailed issues and recommendations."
                  }
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>

          {/* Captions & Audio Descriptions */}
          <TabsContent value="captions" className="space-y-4">
            {accessibilityReport ? (
              <div className="space-y-6">
                {/* Caption Segments */}
                {accessibilityReport.caption_segments.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        Generated Captions ({accessibilityReport.caption_segments.length})
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 max-h-60 overflow-y-auto">
                        {accessibilityReport.caption_segments.map((caption, index) => (
                          <div key={index} className="flex items-start gap-2 p-2 bg-gray-50 rounded">
                            <Clock className="h-4 w-4 text-gray-500 mt-0.5" />
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-xs font-mono text-gray-600">
                                  {Math.floor(caption.start_time / 60)}:{(caption.start_time % 60).toFixed(1).padStart(4, '0')} - 
                                  {Math.floor(caption.end_time / 60)}:{(caption.end_time % 60).toFixed(1).padStart(4, '0')}
                                </span>
                                <Badge variant="outline" className="text-xs">
                                  {(caption.confidence * 100).toFixed(0)}% confidence
                                </Badge>
                              </div>
                              <p className="text-sm">{caption.text}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Audio Descriptions */}
                {accessibilityReport.audio_descriptions.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Volume2 className="h-4 w-4" />
                        Audio Descriptions ({accessibilityReport.audio_descriptions.length})
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 max-h-60 overflow-y-auto">
                        {accessibilityReport.audio_descriptions.map((description, index) => (
                          <div key={index} className="flex items-start gap-2 p-2 bg-gray-50 rounded">
                            <Volume2 className="h-4 w-4 text-gray-500 mt-0.5" />
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-xs font-mono text-gray-600">
                                  {Math.floor(description.start_time / 60)}:{(description.start_time % 60).toFixed(1).padStart(4, '0')} - 
                                  {Math.floor(description.end_time / 60)}:{(description.end_time % 60).toFixed(1).padStart(4, '0')}
                                </span>
                                <Badge variant={
                                  description.priority === 'essential' ? 'default' :
                                  description.priority === 'important' ? 'secondary' : 'outline'
                                }>
                                  {description.priority}
                                </Badge>
                              </div>
                              <p className="text-sm">{description.description}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Export Options */}
                <div className="flex justify-between items-center pt-4 border-t">
                  <div className="text-sm text-gray-600">
                    {accessibilityReport.caption_segments.length} captions, {accessibilityReport.audio_descriptions.length} audio descriptions
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" className="flex items-center gap-2">
                      <Play className="h-4 w-4" />
                      Preview with Accessibility
                    </Button>
                    <Button className="flex items-center gap-2">
                      <Download className="h-4 w-4" />
                      Export Captions & Descriptions
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              <Alert>
                <FileText className="h-4 w-4" />
                <AlertDescription>
                  Run accessibility analysis to generate captions and audio descriptions for your content.
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};
