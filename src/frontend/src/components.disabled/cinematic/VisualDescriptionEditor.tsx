/**
 * VisualDescriptionEditor Component
 * AI-powered visual description editor with scene analysis and recommendations.
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  VisualDescriptionEditorProps,
  CinematicSettings,
  SceneAnalysis
} from '../../types/cinematic';
import { useVisualDescription, useDescriptionTemplates } from '../../hooks/useVisualDescription';

interface TemplateButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

const TemplateButton: React.FC<TemplateButtonProps> = ({ label, onClick, disabled = false }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className="template-button"
  >
    {label}
  </button>
);

interface AnalysisDisplayProps {
  analysis: SceneAnalysis;
  confidence: number;
}

const AnalysisDisplay: React.FC<AnalysisDisplayProps> = ({ analysis, confidence }) => (
  <div className="analysis-display">
    <h4>Scene Analysis</h4>
    <div className="analysis-grid">
      {analysis.mood && (
        <div className="analysis-item">
          <label>Mood:</label>
          <span className="analysis-value">{analysis.mood}</span>
        </div>
      )}
      {analysis.complexity && (
        <div className="analysis-item">
          <label>Complexity:</label>
          <span className="analysis-value">{analysis.complexity}</span>
        </div>
      )}
      {analysis.pacing && (
        <div className="analysis-item">
          <label>Pacing:</label>
          <span className="analysis-value">{analysis.pacing}</span>
        </div>
      )}
      {analysis.focus_type && (
        <div className="analysis-item">
          <label>Focus Type:</label>
          <span className="analysis-value">{analysis.focus_type}</span>
        </div>
      )}
    </div>
    <div className="confidence-display">
      <label>Confidence:</label>
      <div className="confidence-bar">
        <div 
          className="confidence-fill" 
          style={{ width: `${confidence * 100}%` }}
        />
      </div>
      <span className="confidence-value">{Math.round(confidence * 100)}%</span>
    </div>
  </div>
);

interface SuggestionsDisplayProps {
  suggestions: string[];
  onApplySuggestion?: (suggestion: string) => void;
}

const SuggestionsDisplay: React.FC<SuggestionsDisplayProps> = ({ 
  suggestions, 
  onApplySuggestion 
}) => {
  if (suggestions.length === 0) return null;

  return (
    <div className="suggestions-display">
      <h4>AI Suggestions</h4>
      <ul className="suggestions-list">
        {suggestions.map((suggestion, index) => (
          <li key={index} className="suggestion-item">
            <span className="suggestion-text">{suggestion}</span>
            {onApplySuggestion && (
              <button
                onClick={() => onApplySuggestion(suggestion)}
                className="apply-suggestion-btn"
              >
                Apply
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};

interface RecommendationsDisplayProps {
  recommendations: CinematicSettings;
  onApplyRecommendations: (settings: CinematicSettings) => void;
  disabled?: boolean;
}

const RecommendationsDisplay: React.FC<RecommendationsDisplayProps> = ({
  recommendations,
  onApplyRecommendations,
  disabled = false
}) => (
  <div className="recommendations-display">
    <h4>Cinematic Recommendations</h4>
    <div className="recommendations-summary">
      <div className="recommendation-item">
        <label>Camera Movement:</label>
        <span>{recommendations.camera_movements.intensity}% intensity</span>
      </div>
      <div className="recommendation-item">
        <label>Color Grading:</label>
        <span>{recommendations.color_grading.film_emulation} emulation</span>
      </div>
      <div className="recommendation-item">
        <label>Quality:</label>
        <span>{recommendations.quality_preset.replace('_', ' ')}</span>
      </div>
    </div>
    <button
      onClick={() => onApplyRecommendations(recommendations)}
      disabled={disabled}
      className="apply-recommendations-btn primary"
    >
      Apply Recommendations
    </button>
  </div>
);

export const VisualDescriptionEditor: React.FC<VisualDescriptionEditorProps> = ({
  sceneId,
  initialContent = '',
  initialDescription = '',
  onDescriptionChange,
  onRecommendationsApply,
  disabled = false,
  className = ''
}) => {
  const {
    content,
    description,
    sceneAnalysis,
    recommendations,
    suggestions,
    confidence,
    generatedBy,
    isGenerating,
    isAnalyzing,
    error,
    setContent,
    setDescription,
    generateDescription,
    analyzeScene,
    clearDescription,
    canGenerate,
    hasRecommendations,
    isContentChanged
  } = useVisualDescription({ sceneId });

  const {
    getEducationalTemplate,
    getPresentationTemplate,
    getCreativeTemplate,
    getTechnicalTemplate
  } = useDescriptionTemplates();

  const [showTemplates, setShowTemplates] = useState(false);
  const [customTemplate, setCustomTemplate] = useState('');

  // Initialize with provided content and description
  useEffect(() => {
    if (initialContent && !content) {
      setContent(initialContent);
    }
    if (initialDescription && !description) {
      setDescription(initialDescription);
    }
  }, [initialContent, initialDescription, content, description, setContent, setDescription]);

  // Notify parent of description changes
  useEffect(() => {
    onDescriptionChange?.(description);
  }, [description, onDescriptionChange]);

  // Handle content change
  const handleContentChange = useCallback((newContent: string) => {
    setContent(newContent);
  }, [setContent]);

  // Handle description change
  const handleDescriptionChange = useCallback((newDescription: string) => {
    setDescription(newDescription);
  }, [setDescription]);

  // Handle template application
  const handleApplyTemplate = useCallback(async (templateOptions: any) => {
    if (!canGenerate) return;
    
    try {
      await generateDescription({ stylePreferences: templateOptions });
      setShowTemplates(false);
    } catch (err) {
      // Error is handled by the hook
    }
  }, [canGenerate, generateDescription]);

  // Handle custom template
  const handleCustomTemplate = useCallback(async () => {
    if (!customTemplate.trim() || !canGenerate) return;
    
    try {
      const templateOptions = { custom_style: customTemplate.trim() };
      await generateDescription({ stylePreferences: templateOptions });
      setCustomTemplate('');
      setShowTemplates(false);
    } catch (err) {
      // Error is handled by the hook
    }
  }, [customTemplate, canGenerate, generateDescription]);

  // Handle suggestion application
  const handleApplySuggestion = useCallback((suggestion: string) => {
    const currentDesc = description || '';
    const newDescription = currentDesc + (currentDesc ? '\n\n' : '') + suggestion;
    setDescription(newDescription);
  }, [description, setDescription]);

  // Handle recommendations application
  const handleApplyRecommendations = useCallback((settings: CinematicSettings) => {
    onRecommendationsApply?.(settings);
  }, [onRecommendationsApply]);

  // Render content input
  const renderContentInput = () => (
    <div className="content-input-section">
      <label htmlFor="content-input" className="section-label">
        Content to Analyze
        {isContentChanged && <span className="changed-indicator">*</span>}
      </label>
      <textarea
        id="content-input"
        value={content}
        onChange={(e) => handleContentChange(e.target.value)}
        placeholder="Enter the content you want to create a visual description for..."
        rows={4}
        disabled={disabled || isGenerating}
        className="content-textarea"
      />
      <div className="content-actions">
        <button
          onClick={() => analyzeScene()}
          disabled={!content.trim() || isAnalyzing || disabled}
          className="analyze-btn"
        >
          {isAnalyzing ? 'Analyzing...' : 'Analyze Scene'}
        </button>
        {content.trim() && (
          <button
            onClick={() => setContent('')}
            disabled={disabled || isGenerating}
            className="clear-content-btn"
          >
            Clear
          </button>
        )}
      </div>
    </div>
  );

  // Render description editor
  const renderDescriptionEditor = () => (
    <div className="description-editor-section">
      <div className="section-header">
        <label htmlFor="description-input" className="section-label">
          Visual Description
          {generatedBy !== 'user' && (
            <span className="generated-badge">Generated by {generatedBy}</span>
          )}
        </label>
        <div className="editor-actions">
          <button
            onClick={() => setShowTemplates(!showTemplates)}
            disabled={disabled}
            className="templates-btn"
          >
            Templates
          </button>
          <button
            onClick={() => generateDescription()}
            disabled={!canGenerate || disabled}
            className="generate-btn primary"
          >
            {isGenerating ? 'Generating...' : 'Generate Description'}
          </button>
        </div>
      </div>
      
      <textarea
        id="description-input"
        value={description}
        onChange={(e) => handleDescriptionChange(e.target.value)}
        placeholder="Visual description will appear here, or you can write your own..."
        rows={8}
        disabled={disabled || isGenerating}
        className="description-textarea"
      />
      
      <div className="description-actions">
        {description && (
          <button
            onClick={clearDescription}
            disabled={disabled || isGenerating}
            className="clear-description-btn"
          >
            Clear Description
          </button>
        )}
        <div className="description-stats">
          <span className="char-count">{description.length} characters</span>
          <span className="word-count">{description.split(/\s+/).filter(w => w).length} words</span>
        </div>
      </div>
    </div>
  );

  // Render templates panel
  const renderTemplatesPanel = () => {
    if (!showTemplates) return null;

    return (
      <div className="templates-panel">
        <h4>Description Templates</h4>
        <div className="template-categories">
          <div className="template-category">
            <h5>Educational</h5>
            <div className="template-buttons">
              <TemplateButton
                label="Mathematics"
                onClick={() => handleApplyTemplate(getEducationalTemplate('mathematics'))}
                disabled={!canGenerate || disabled}
              />
              <TemplateButton
                label="Science"
                onClick={() => handleApplyTemplate(getEducationalTemplate('science'))}
                disabled={!canGenerate || disabled}
              />
              <TemplateButton
                label="History"
                onClick={() => handleApplyTemplate(getEducationalTemplate('history'))}
                disabled={!canGenerate || disabled}
              />
            </div>
          </div>
          
          <div className="template-category">
            <h5>Presentation</h5>
            <div className="template-buttons">
              <TemplateButton
                label="Business"
                onClick={() => handleApplyTemplate(getPresentationTemplate('business'))}
                disabled={!canGenerate || disabled}
              />
              <TemplateButton
                label="Academic"
                onClick={() => handleApplyTemplate(getPresentationTemplate('academic'))}
                disabled={!canGenerate || disabled}
              />
              <TemplateButton
                label="Technical"
                onClick={() => handleApplyTemplate(getTechnicalTemplate('high'))}
                disabled={!canGenerate || disabled}
              />
            </div>
          </div>
          
          <div className="template-category">
            <h5>Creative</h5>
            <div className="template-buttons">
              <TemplateButton
                label="Artistic"
                onClick={() => handleApplyTemplate(getCreativeTemplate('artistic'))}
                disabled={!canGenerate || disabled}
              />
              <TemplateButton
                label="Cinematic"
                onClick={() => handleApplyTemplate(getCreativeTemplate('cinematic'))}
                disabled={!canGenerate || disabled}
              />
              <TemplateButton
                label="Documentary"
                onClick={() => handleApplyTemplate(getCreativeTemplate('documentary'))}
                disabled={!canGenerate || disabled}
              />
            </div>
          </div>
        </div>
        
        <div className="custom-template">
          <h5>Custom Style</h5>
          <div className="custom-template-input">
            <input
              type="text"
              value={customTemplate}
              onChange={(e) => setCustomTemplate(e.target.value)}
              placeholder="Describe your desired style..."
              disabled={!canGenerate || disabled}
            />
            <button
              onClick={handleCustomTemplate}
              disabled={!customTemplate.trim() || !canGenerate || disabled}
              className="apply-custom-btn"
            >
              Apply
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`visual-description-editor ${className} ${disabled ? 'disabled' : ''}`}>
      <div className="editor-header">
        <h3>Visual Description Editor</h3>
        <div className="editor-status">
          {isGenerating && <span className="status generating">Generating...</span>}
          {isAnalyzing && <span className="status analyzing">Analyzing...</span>}
          {error && <span className="status error">Error</span>}
        </div>
      </div>

      {error && (
        <div className="error-display">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="editor-content">
        <div className="editor-main">
          {renderContentInput()}
          {renderDescriptionEditor()}
          {renderTemplatesPanel()}
        </div>
        
        <div className="editor-sidebar">
          {sceneAnalysis && (
            <AnalysisDisplay
              analysis={sceneAnalysis}
              confidence={confidence}
            />
          )}
          
          <SuggestionsDisplay
            suggestions={suggestions}
            onApplySuggestion={handleApplySuggestion}
          />
          
          {hasRecommendations && recommendations && (
            <RecommendationsDisplay
              recommendations={recommendations}
              onApplyRecommendations={handleApplyRecommendations}
              disabled={disabled}
            />
          )}
        </div>
      </div>

      {(isGenerating || isAnalyzing) && (
        <div className="loading-overlay">
          <div className="loading-spinner">
            {isGenerating ? 'Generating description...' : 'Analyzing scene...'}
          </div>
        </div>
      )}
    </div>
  );
};