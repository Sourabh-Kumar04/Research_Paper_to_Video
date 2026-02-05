# Vision-Language Models Guide

## Overview

This comprehensive guide covers the integration and usage of vision-language models in the production video generation system, focusing on visual content understanding, diagram analysis, and multi-modal reasoning capabilities optimized for 16GB RAM systems.

## Table of Contents

1. [Vision-Language Model Overview](#vision-language-model-overview)
2. [Qwen2-VL Integration](#qwen2-vl-integration)
3. [LLaVA-NeXT Integration](#llava-next-integration)
4. [Image Processing Capabilities](#image-processing-capabilities)
5. [Scientific Content Analysis](#scientific-content-analysis)
6. [Performance Optimization](#performance-optimization)
7. [Use Case Examples](#use-case-examples)
8. [Troubleshooting](#troubleshooting)

## Vision-Language Model Overview

### Model Comparison Matrix

| Feature | Qwen2-VL | LLaVA-NeXT | Optimal Use Case |
|---------|----------|------------|------------------|
| **Image Resolution** | Up to 4K (4096x4096) | Variable (up to 2K) | High-res scientific figures |
| **Mathematical Understanding** | Excellent (LaTeX recognition) | Good | Equation extraction |
| **Multi-image Analysis** | Limited | Excellent | Comparative analysis |
| **Memory Usage (16GB)** | 12-15GB | 10-13GB | Memory-constrained systems |
| **Inference Speed** | 3-8 tok/s | 4-6 tok/s | Real-time applications |
| **Scientific Accuracy** | 92% | 88% | Research paper analysis |

### Architecture Overview

```mermaid
graph TD
    A[Input Image/Document] --> B{Image Preprocessor}
    B --> C[Resolution Optimizer]
    C --> D[Format Converter]
    
    D --> E{Model Router}
    E -->|High-res Scientific| F[Qwen2-VL]
    E -->|Multi-image Analysis| G[LLaVA-NeXT]
    E -->|General Vision| H[LLaVA-7B]
    
    F --> I[Vision Encoder]
    G --> I
    H --> I
    
    I --> J[Language Model]
    J --> K[Response Generator]
    K --> L[Output Formatter]
    
    M[Memory Manager] --> E
    M --> F
    M --> G
    M --> H
```

## Qwen2-VL Integration

### Model Specifications

#### Qwen2-VL-7B (Recommended for 16GB)
```json
{
  "model_name": "qwen2-vl:7b-q4_K_M",
  "parameters": "7B (quantized to 4-bit)",
  "memory_requirement": "12GB RAM",
  "max_resolution": "4096x4096",
  "supported_formats": ["PNG", "JPEG", "PDF", "SVG", "WebP"],
  "specializations": [
    "Mathematical equation recognition",
    "Scientific diagram analysis", 
    "Chart and graph interpretation",
    "Technical document processing"
  ],
  "performance": {
    "inference_speed": "3-8 tokens/second",
    "image_processing": "2-5 seconds per image",
    "accuracy": "92% on scientific content"
  }
}
```

### Installation and Setup

#### Ollama Integration
```bash
#!/bin/bash
# Install Qwen2-VL for 16GB systems

echo "Installing Qwen2-VL optimized for 16GB RAM..."
ollama pull qwen2-vl:7b-q4_K_M

echo "Testing image analysis capabilities..."
# Test with sample scientific figure
ollama run qwen2-vl:7b-q4_K_M "Analyze this scientific diagram and explain the key components" < sample_figure.png

echo "Testing equation recognition..."
# Test with mathematical equation image
ollama run qwen2-vl:7b-q4_K_M "Extract and explain the mathematical equations in this image" < equation_sample.png

echo "Qwen2-VL installation and testing complete!"
```

#### Python Integration
```python
import ollama
import base64
from PIL import Image
import io

class Qwen2VLIntegration:
    """Integration class for Qwen2-VL vision-language model."""
    
    def __init__(self, model_name: str = "qwen2-vl:7b-q4_K_M"):
        self.model_name = model_name
        self.client = ollama.Client()
        self.max_image_size = (2048, 2048)  # Optimized for 16GB RAM
        
    def analyze_image(self, image_path: str, prompt: str, 
                     optimize_for_memory: bool = True) -> dict:
        """Analyze image with Qwen2-VL model."""
        try:
            # Optimize image for memory efficiency
            if optimize_for_memory:
                image_data = self._optimize_image(image_path)
            else:
                with open(image_path, 'rb') as f:
                    image_data = f.read()
            
            # Perform analysis
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                images=[image_data],
                options={
                    'temperature': 0.2,  # Low temperature for factual analysis
                    'max_tokens': 1024,
                    'top_p': 0.9
                }
            )
            
            return {
                'analysis': response['response'],
                'model_used': self.model_name,
                'image_size': self._get_image_size(image_path),
                'processing_time': response.get('total_duration', 0) / 1e9
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'analysis': None,
                'model_used': self.model_name
            }
    
    def extract_equations(self, image_path: str) -> dict:
        """Extract mathematical equations from image."""
        prompt = """
        Analyze this image and extract all mathematical equations, formulas, and expressions.
        For each equation found:
        1. Provide the LaTeX representation
        2. Explain what the equation represents
        3. Identify any variables and their meanings
        4. Note the context or field of mathematics/science
        
        Format your response as:
        EQUATION 1: [LaTeX code]
        EXPLANATION: [What it represents]
        VARIABLES: [Variable definitions]
        CONTEXT: [Mathematical/scientific field]
        """
        
        return self.analyze_image(image_path, prompt)
    
    def analyze_scientific_figure(self, image_path: str) -> dict:
        """Analyze scientific figures and diagrams."""
        prompt = """
        Analyze this scientific figure or diagram. Provide:
        1. FIGURE TYPE: What type of scientific visualization this is
        2. KEY COMPONENTS: Main elements, labels, and structures
        3. DATA INTERPRETATION: What the data or diagram shows
        4. SCIENTIFIC CONTEXT: The field of science and specific concepts
        5. ANIMATION SUGGESTIONS: How this could be animated for educational content
        
        Be specific and technical in your analysis.
        """
        
        return self.analyze_image(image_path, prompt)
    
    def _optimize_image(self, image_path: str) -> bytes:
        """Optimize image for memory efficiency."""
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large
            if img.size[0] > self.max_image_size[0] or img.size[1] > self.max_image_size[1]:
                img.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85, optimize=True)
            return buffer.getvalue()
    
    def _get_image_size(self, image_path: str) -> tuple:
        """Get image dimensions."""
        with Image.open(image_path) as img:
            return img.size
```

### Advanced Usage Examples

#### Research Paper Figure Analysis
```python
class ResearchPaperAnalyzer:
    """Analyze research paper figures using Qwen2-VL."""
    
    def __init__(self):
        self.qwen_vl = Qwen2VLIntegration()
        
    def analyze_paper_figures(self, figure_paths: list) -> dict:
        """Analyze multiple figures from a research paper."""
        results = {
            'figures': [],
            'summary': '',
            'animation_suggestions': []
        }
        
        for i, figure_path in enumerate(figure_paths):
            print(f"Analyzing figure {i+1}/{len(figure_paths)}: {figure_path}")
            
            # Analyze individual figure
            analysis = self.qwen_vl.analyze_scientific_figure(figure_path)
            
            if analysis.get('analysis'):
                figure_result = {
                    'figure_number': i + 1,
                    'file_path': figure_path,
                    'analysis': analysis['analysis'],
                    'processing_time': analysis.get('processing_time', 0)
                }
                results['figures'].append(figure_result)
                
                # Extract animation suggestions
                if 'ANIMATION SUGGESTIONS:' in analysis['analysis']:
                    suggestions = analysis['analysis'].split('ANIMATION SUGGESTIONS:')[1].strip()
                    results['animation_suggestions'].append({
                        'figure': i + 1,
                        'suggestions': suggestions
                    })
        
        # Generate overall summary
        results['summary'] = self._generate_summary(results['figures'])
        
        return results
    
    def _generate_summary(self, figures: list) -> str:
        """Generate summary of all analyzed figures."""
        if not figures:
            return "No figures were successfully analyzed."
        
        summary = f"Analyzed {len(figures)} figures from the research paper.\n\n"
        
        # Categorize figures by type
        figure_types = {}
        for fig in figures:
            analysis = fig['analysis']
            if 'FIGURE TYPE:' in analysis:
                fig_type = analysis.split('FIGURE TYPE:')[1].split('\n')[0].strip()
                if fig_type not in figure_types:
                    figure_types[fig_type] = []
                figure_types[fig_type].append(fig['figure_number'])
        
        summary += "Figure Types Found:\n"
        for fig_type, numbers in figure_types.items():
            summary += f"- {fig_type}: Figures {', '.join(map(str, numbers))}\n"
        
        return summary
```

#### Mathematical Content Processor
```python
class MathematicalContentProcessor:
    """Process mathematical content from images."""
    
    def __init__(self):
        self.qwen_vl = Qwen2VLIntegration()
        
    def process_math_document(self, image_path: str) -> dict:
        """Process mathematical document or textbook page."""
        # Extract equations
        equations_result = self.qwen_vl.extract_equations(image_path)
        
        # Analyze mathematical concepts
        concepts_prompt = """
        Analyze this mathematical content and identify:
        1. MATHEMATICAL TOPICS: What areas of mathematics are covered
        2. DIFFICULTY LEVEL: Beginner, Intermediate, or Advanced
        3. KEY CONCEPTS: Main mathematical ideas presented
        4. PREREQUISITES: What knowledge is needed to understand this
        5. MANIM ANIMATION IDEAS: Specific suggestions for animating these concepts
        """
        
        concepts_result = self.qwen_vl.analyze_image(image_path, concepts_prompt)
        
        return {
            'equations': equations_result,
            'concepts': concepts_result,
            'manim_suggestions': self._extract_manim_suggestions(concepts_result)
        }
    
    def _extract_manim_suggestions(self, concepts_result: dict) -> list:
        """Extract Manim animation suggestions from analysis."""
        if not concepts_result.get('analysis'):
            return []
        
        analysis = concepts_result['analysis']
        if 'MANIM ANIMATION IDEAS:' not in analysis:
            return []
        
        suggestions_text = analysis.split('MANIM ANIMATION IDEAS:')[1].strip()
        suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
        
        return suggestions
```

## LLaVA-NeXT Integration

### Model Specifications

#### LLaVA-7B (Optimized for 16GB)
```json
{
  "model_name": "llava:7b-q4_K_M",
  "parameters": "7B (quantized to 4-bit)",
  "memory_requirement": "10GB RAM",
  "max_resolution": "2048x2048",
  "supported_formats": ["PNG", "JPEG", "BMP", "GIF"],
  "specializations": [
    "Multi-image comparative analysis",
    "Complex scene understanding",
    "Visual question answering",
    "General image description"
  ],
  "performance": {
    "inference_speed": "4-6 tokens/second",
    "multi_image_processing": "2-4 seconds per image",
    "accuracy": "88% on general visual tasks"
  }
}
```

### Python Integration
```python
class LLaVAIntegration:
    """Integration class for LLaVA-NeXT vision-language model."""
    
    def __init__(self, model_name: str = "llava:7b-q4_K_M"):
        self.model_name = model_name
        self.client = ollama.Client()
        
    def analyze_multiple_images(self, image_paths: list, prompt: str) -> dict:
        """Analyze multiple images for comparative analysis."""
        try:
            # Load and optimize images
            image_data = []
            for path in image_paths:
                with open(path, 'rb') as f:
                    image_data.append(f.read())
            
            # Perform multi-image analysis
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                images=image_data,
                options={
                    'temperature': 0.3,
                    'max_tokens': 1024
                }
            )
            
            return {
                'analysis': response['response'],
                'model_used': self.model_name,
                'image_count': len(image_paths),
                'processing_time': response.get('total_duration', 0) / 1e9
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'analysis': None,
                'model_used': self.model_name
            }
    
    def compare_experimental_setups(self, before_image: str, after_image: str) -> dict:
        """Compare before/after experimental setups."""
        prompt = """
        Compare these two experimental setups or results. Analyze:
        1. DIFFERENCES: What has changed between the images
        2. EXPERIMENTAL DESIGN: What type of experiment this appears to be
        3. VARIABLES: What variables might have been changed
        4. RESULTS INTERPRETATION: What the changes might indicate
        5. SCIENTIFIC SIGNIFICANCE: The importance of the observed changes
        
        Provide a detailed scientific analysis.
        """
        
        return self.analyze_multiple_images([before_image, after_image], prompt)
    
    def analyze_process_sequence(self, image_sequence: list) -> dict:
        """Analyze a sequence of images showing a process."""
        prompt = """
        Analyze this sequence of images showing a process or procedure. Describe:
        1. PROCESS OVERVIEW: What process is being shown
        2. STEP-BY-STEP ANALYSIS: What happens in each image
        3. KEY CHANGES: Important changes between steps
        4. SCIENTIFIC PRINCIPLES: What scientific concepts are demonstrated
        5. ANIMATION POTENTIAL: How this sequence could be animated
        
        Number your analysis for each step in the sequence.
        """
        
        return self.analyze_multiple_images(image_sequence, prompt)
```

## Image Processing Capabilities

### Supported Image Formats and Optimization

#### Format Support Matrix
```python
IMAGE_FORMAT_SUPPORT = {
    "qwen2_vl": {
        "supported_formats": ["PNG", "JPEG", "PDF", "SVG", "WebP"],
        "optimal_format": "PNG",
        "max_resolution": "4096x4096",
        "recommended_resolution": "2048x2048",
        "memory_per_megapixel": "1.2MB"
    },
    "llava_next": {
        "supported_formats": ["PNG", "JPEG", "BMP", "GIF"],
        "optimal_format": "JPEG",
        "max_resolution": "2048x2048", 
        "recommended_resolution": "1024x1024",
        "memory_per_megapixel": "0.8MB"
    }
}
```

#### Image Preprocessing Pipeline
```python
class ImagePreprocessor:
    """Preprocess images for optimal vision model performance."""
    
    def __init__(self, target_model: str = "qwen2-vl"):
        self.target_model = target_model
        self.config = IMAGE_FORMAT_SUPPORT[target_model]
        
    def preprocess_image(self, image_path: str, optimize_for_memory: bool = True) -> str:
        """Preprocess image for vision model analysis."""
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode not in ['RGB', 'L']:
                img = img.convert('RGB')
            
            # Resize if too large
            max_size = (2048, 2048) if optimize_for_memory else (4096, 4096)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                print(f"Resized image from {Image.open(image_path).size} to {img.size}")
            
            # Optimize quality vs size
            quality = 85 if optimize_for_memory else 95
            
            # Save optimized image
            output_path = f"optimized_{os.path.basename(image_path)}"
            img.save(output_path, format='JPEG', quality=quality, optimize=True)
            
            return output_path
    
    def batch_preprocess(self, image_paths: list) -> list:
        """Preprocess multiple images."""
        processed_paths = []
        
        for path in image_paths:
            try:
                processed_path = self.preprocess_image(path)
                processed_paths.append(processed_path)
                print(f"Processed: {path} -> {processed_path}")
            except Exception as e:
                print(f"Error processing {path}: {e}")
                processed_paths.append(path)  # Use original if processing fails
        
        return processed_paths
    
    def estimate_memory_usage(self, image_path: str) -> dict:
        """Estimate memory usage for image processing."""
        with Image.open(image_path) as img:
            width, height = img.size
            megapixels = (width * height) / 1_000_000
            
            estimated_memory = megapixels * self.config["memory_per_megapixel"]
            
            return {
                'image_size': img.size,
                'megapixels': megapixels,
                'estimated_memory_mb': estimated_memory,
                'recommended_resize': megapixels > 4.0,  # 4MP threshold
                'memory_warning': estimated_memory > 100  # 100MB warning
            }
```

## Scientific Content Analysis

### Research Paper Processing Pipeline

#### Complete Paper Analysis System
```python
class ScientificContentAnalyzer:
    """Comprehensive scientific content analysis system."""
    
    def __init__(self):
        self.qwen_vl = Qwen2VLIntegration()
        self.llava = LLaVAIntegration()
        self.preprocessor = ImagePreprocessor("qwen2_vl")
        
    def analyze_research_paper(self, paper_images: list) -> dict:
        """Analyze complete research paper from images."""
        results = {
            'paper_analysis': {},
            'figures': [],
            'equations': [],
            'tables': [],
            'animation_suggestions': [],
            'manim_code_suggestions': []
        }
        
        # Categorize images by content type
        categorized_images = self._categorize_images(paper_images)
        
        # Process each category
        for category, images in categorized_images.items():
            if category == 'figures':
                results['figures'] = self._analyze_figures(images)
            elif category == 'equations':
                results['equations'] = self._analyze_equations(images)
            elif category == 'tables':
                results['tables'] = self._analyze_tables(images)
        
        # Generate overall analysis
        results['paper_analysis'] = self._generate_paper_analysis(results)
        
        # Generate animation suggestions
        results['animation_suggestions'] = self._generate_animation_suggestions(results)
        
        return results
    
    def _categorize_images(self, image_paths: list) -> dict:
        """Categorize images by content type."""
        categories = {
            'figures': [],
            'equations': [],
            'tables': [],
            'text': []
        }
        
        for image_path in image_paths:
            # Use quick analysis to categorize
            category_prompt = """
            Quickly categorize this image as one of:
            - FIGURE: Scientific diagram, chart, graph, or illustration
            - EQUATION: Mathematical equations or formulas
            - TABLE: Data table or structured information
            - TEXT: Regular text content
            
            Respond with just the category name.
            """
            
            result = self.qwen_vl.analyze_image(image_path, category_prompt)
            
            if result.get('analysis'):
                category = result['analysis'].strip().lower()
                if 'figure' in category:
                    categories['figures'].append(image_path)
                elif 'equation' in category:
                    categories['equations'].append(image_path)
                elif 'table' in category:
                    categories['tables'].append(image_path)
                else:
                    categories['text'].append(image_path)
        
        return categories
    
    def _analyze_figures(self, figure_paths: list) -> list:
        """Analyze scientific figures."""
        figures = []
        
        for i, path in enumerate(figure_paths):
            analysis = self.qwen_vl.analyze_scientific_figure(path)
            
            if analysis.get('analysis'):
                figures.append({
                    'figure_number': i + 1,
                    'path': path,
                    'analysis': analysis['analysis'],
                    'type': self._extract_figure_type(analysis['analysis']),
                    'key_components': self._extract_key_components(analysis['analysis'])
                })
        
        return figures
    
    def _analyze_equations(self, equation_paths: list) -> list:
        """Analyze mathematical equations."""
        equations = []
        
        for i, path in enumerate(equation_paths):
            analysis = self.qwen_vl.extract_equations(path)
            
            if analysis.get('analysis'):
                equations.append({
                    'equation_set': i + 1,
                    'path': path,
                    'analysis': analysis['analysis'],
                    'latex_equations': self._extract_latex(analysis['analysis']),
                    'mathematical_field': self._extract_math_field(analysis['analysis'])
                })
        
        return equations
    
    def _generate_animation_suggestions(self, results: dict) -> list:
        """Generate comprehensive animation suggestions."""
        suggestions = []
        
        # Suggestions from figures
        for figure in results['figures']:
            if 'ANIMATION SUGGESTIONS:' in figure['analysis']:
                suggestion_text = figure['analysis'].split('ANIMATION SUGGESTIONS:')[1].strip()
                suggestions.append({
                    'type': 'figure_animation',
                    'source': f"Figure {figure['figure_number']}",
                    'suggestion': suggestion_text,
                    'complexity': self._assess_animation_complexity(suggestion_text)
                })
        
        # Suggestions from equations
        for equation_set in results['equations']:
            suggestions.append({
                'type': 'equation_animation',
                'source': f"Equation Set {equation_set['equation_set']}",
                'suggestion': f"Animate the derivation and application of equations in {equation_set['mathematical_field']}",
                'complexity': 'medium'
            })
        
        return suggestions
```

### Specialized Analysis Functions

#### Chart and Graph Analysis
```python
class ChartGraphAnalyzer:
    """Specialized analyzer for charts and graphs."""
    
    def __init__(self):
        self.qwen_vl = Qwen2VLIntegration()
        
    def analyze_data_visualization(self, image_path: str) -> dict:
        """Analyze charts, graphs, and data visualizations."""
        prompt = """
        Analyze this data visualization in detail. Provide:
        
        1. CHART TYPE: What type of chart/graph this is (bar, line, scatter, etc.)
        2. AXES INFORMATION: What the X and Y axes represent, including units
        3. DATA TRENDS: Key trends, patterns, or relationships shown
        4. DATA POINTS: Approximate values for key data points
        5. STATISTICAL INSIGHTS: What statistical conclusions can be drawn
        6. ANIMATION STRATEGY: How to animate this data for educational impact
        7. MANIM CODE OUTLINE: Basic structure for Manim animation code
        
        Be specific with numbers and trends.
        """
        
        result = self.qwen_vl.analyze_image(image_path, prompt)
        
        if result.get('analysis'):
            # Extract structured data
            analysis = result['analysis']
            
            return {
                'raw_analysis': analysis,
                'chart_type': self._extract_chart_type(analysis),
                'data_trends': self._extract_trends(analysis),
                'animation_strategy': self._extract_animation_strategy(analysis),
                'manim_outline': self._extract_manim_outline(analysis)
            }
        
        return {'error': 'Analysis failed'}
    
    def _extract_chart_type(self, analysis: str) -> str:
        """Extract chart type from analysis."""
        if 'CHART TYPE:' in analysis:
            return analysis.split('CHART TYPE:')[1].split('\n')[0].strip()
        return 'Unknown'
    
    def _extract_trends(self, analysis: str) -> list:
        """Extract data trends from analysis."""
        if 'DATA TRENDS:' in analysis:
            trends_text = analysis.split('DATA TRENDS:')[1].split('DATA POINTS:')[0].strip()
            return [trend.strip() for trend in trends_text.split('\n') if trend.strip()]
        return []
    
    def _extract_animation_strategy(self, analysis: str) -> str:
        """Extract animation strategy from analysis."""
        if 'ANIMATION STRATEGY:' in analysis:
            return analysis.split('ANIMATION STRATEGY:')[1].split('MANIM CODE OUTLINE:')[0].strip()
        return ''
    
    def _extract_manim_outline(self, analysis: str) -> str:
        """Extract Manim code outline from analysis."""
        if 'MANIM CODE OUTLINE:' in analysis:
            return analysis.split('MANIM CODE OUTLINE:')[1].strip()
        return ''
```

## Performance Optimization

### Memory Management for Vision Models

#### Optimized Processing Pipeline
```python
class VisionModelOptimizer:
    """Optimize vision model performance for 16GB systems."""
    
    def __init__(self):
        self.memory_monitor = MemoryMonitor()
        self.current_model = None
        self.model_cache = {}
        
    def process_images_optimized(self, image_paths: list, model_preference: str = "qwen2-vl") -> list:
        """Process multiple images with memory optimization."""
        results = []
        
        # Sort images by size (process smaller first)
        sorted_images = self._sort_by_size(image_paths)
        
        for i, image_path in enumerate(sorted_images):
            print(f"Processing image {i+1}/{len(sorted_images)}: {image_path}")
            
            # Check memory before processing
            if not self._check_memory_availability():
                print("Memory warning: Cleaning up before processing")
                self._cleanup_memory()
            
            # Process image
            result = self._process_single_image(image_path, model_preference)
            results.append(result)
            
            # Cleanup after each image for memory efficiency
            if i % 3 == 0:  # Cleanup every 3 images
                self._cleanup_memory()
        
        return results
    
    def _sort_by_size(self, image_paths: list) -> list:
        """Sort images by file size (smallest first)."""
        return sorted(image_paths, key=lambda x: os.path.getsize(x))
    
    def _check_memory_availability(self) -> bool:
        """Check if sufficient memory is available."""
        available_memory = self.memory_monitor.get_available_memory_gb()
        return available_memory > 4.0  # Need at least 4GB free
    
    def _cleanup_memory(self):
        """Cleanup memory by unloading models and forcing GC."""
        # Unload current model
        if self.current_model:
            del self.current_model
            self.current_model = None
        
        # Clear model cache
        self.model_cache.clear()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # Clear GPU cache if available
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
    
    def _process_single_image(self, image_path: str, model_preference: str) -> dict:
        """Process single image with optimal model selection."""
        # Estimate memory requirements
        memory_estimate = self._estimate_processing_memory(image_path)
        
        # Select appropriate model based on memory
        if memory_estimate > 12:  # High memory requirement
            model = "llava:7b-q4_K_M"  # Use lighter model
        else:
            model = f"{model_preference}:7b-q4_K_M"
        
        # Load model if not already loaded
        if self.current_model != model:
            self._load_model(model)
        
        # Process image
        if model_preference == "qwen2-vl":
            analyzer = Qwen2VLIntegration(model)
            return analyzer.analyze_scientific_figure(image_path)
        else:
            analyzer = LLaVAIntegration(model)
            return analyzer.analyze_multiple_images([image_path], "Analyze this image in detail")
    
    def _estimate_processing_memory(self, image_path: str) -> float:
        """Estimate memory requirements for processing image."""
        with Image.open(image_path) as img:
            width, height = img.size
            megapixels = (width * height) / 1_000_000
            
            # Base model memory + image processing memory
            base_memory = 8.0  # GB for base model
            image_memory = megapixels * 0.5  # GB per megapixel
            
            return base_memory + image_memory
```

### Batch Processing Optimization

#### Intelligent Batch Processing
```python
class BatchProcessor:
    """Intelligent batch processing for vision models."""
    
    def __init__(self, max_memory_gb: int = 12):
        self.max_memory = max_memory_gb
        self.batch_results = []
        
    def process_batch_intelligent(self, image_paths: list, analysis_type: str = "scientific") -> dict:
        """Process batch of images with intelligent memory management."""
        # Group images by estimated memory requirements
        batches = self._create_memory_aware_batches(image_paths)
        
        results = {
            'total_images': len(image_paths),
            'batches_processed': len(batches),
            'results': [],
            'processing_stats': {}
        }
        
        for i, batch in enumerate(batches):
            print(f"Processing batch {i+1}/{len(batches)} ({len(batch)} images)")
            
            batch_start_time = time.time()
            batch_results = self._process_batch(batch, analysis_type)
            batch_end_time = time.time()
            
            results['results'].extend(batch_results)
            results['processing_stats'][f'batch_{i+1}'] = {
                'images': len(batch),
                'processing_time': batch_end_time - batch_start_time,
                'avg_time_per_image': (batch_end_time - batch_start_time) / len(batch)
            }
            
            # Memory cleanup between batches
            self._cleanup_between_batches()
        
        return results
    
    def _create_memory_aware_batches(self, image_paths: list) -> list:
        """Create batches based on memory requirements."""
        batches = []
        current_batch = []
        current_memory = 0
        
        for image_path in image_paths:
            # Estimate memory for this image
            estimated_memory = self._estimate_image_memory(image_path)
            
            # Check if adding this image would exceed memory limit
            if current_memory + estimated_memory > self.max_memory and current_batch:
                # Start new batch
                batches.append(current_batch)
                current_batch = [image_path]
                current_memory = estimated_memory
            else:
                # Add to current batch
                current_batch.append(image_path)
                current_memory += estimated_memory
        
        # Add final batch
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _estimate_image_memory(self, image_path: str) -> float:
        """Estimate memory requirements for single image."""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                megapixels = (width * height) / 1_000_000
                return megapixels * 0.3  # Conservative estimate
        except Exception:
            return 1.0  # Default estimate if image can't be opened
```

## Use Case Examples

### Educational Content Creation

#### Complete Educational Pipeline
```python
class EducationalContentCreator:
    """Create educational content from scientific images."""
    
    def __init__(self):
        self.qwen_vl = Qwen2VLIntegration()
        self.llava = LLaVAIntegration()
        
    def create_educational_content(self, topic_images: list, target_audience: str = "undergraduate") -> dict:
        """Create comprehensive educational content from images."""
        content = {
            'topic_overview': '',
            'key_concepts': [],
            'visual_explanations': [],
            'animation_scripts': [],
            'assessment_questions': []
        }
        
        # Analyze all images to understand the topic
        topic_analysis = self._analyze_topic_scope(topic_images)
        content['topic_overview'] = topic_analysis
        
        # Process each image for educational content
        for i, image_path in enumerate(topic_images):
            print(f"Creating content for image {i+1}/{len(topic_images)}")
            
            # Generate educational explanation
            explanation = self._create_educational_explanation(image_path, target_audience)
            content['visual_explanations'].append(explanation)
            
            # Generate animation script
            animation_script = self._create_animation_script(image_path, explanation)
            content['animation_scripts'].append(animation_script)
            
            # Extract key concepts
            concepts = self._extract_key_concepts(explanation)
            content['key_concepts'].extend(concepts)
        
        # Remove duplicate concepts
        content['key_concepts'] = list(set(content['key_concepts']))
        
        # Generate assessment questions
        content['assessment_questions'] = self._generate_assessment_questions(content)
        
        return content
    
    def _create_educational_explanation(self, image_path: str, audience: str) -> dict:
        """Create educational explanation for specific audience."""
        prompt = f"""
        Create an educational explanation of this scientific image for {audience} students.
        
        Structure your response as:
        1. SIMPLE OVERVIEW: What this image shows in simple terms
        2. KEY CONCEPTS: Main scientific concepts illustrated
        3. DETAILED EXPLANATION: More detailed scientific explanation
        4. REAL-WORLD APPLICATIONS: How this relates to everyday life
        5. COMMON MISCONCEPTIONS: What students often get wrong about this topic
        6. LEARNING OBJECTIVES: What students should understand after studying this
        
        Adapt the complexity to the {audience} level.
        """
        
        result = self.qwen_vl.analyze_image(image_path, prompt)
        
        return {
            'image_path': image_path,
            'explanation': result.get('analysis', ''),
            'target_audience': audience,
            'processing_time': result.get('processing_time', 0)
        }
    
    def _create_animation_script(self, image_path: str, explanation: dict) -> dict:
        """Create animation script based on image and explanation."""
        prompt = f"""
        Based on this image and the educational explanation, create a detailed animation script.
        
        Include:
        1. SCENE BREAKDOWN: How to break this into animation scenes
        2. VISUAL ELEMENTS: What visual elements to animate
        3. TIMING: Suggested timing for each scene
        4. NARRATION SCRIPT: What to say during each scene
        5. MANIM CODE STRUCTURE: Basic Manim code structure for key animations
        
        Make it suitable for educational video production.
        
        Educational Context: {explanation.get('explanation', '')[:500]}...
        """
        
        result = self.qwen_vl.analyze_image(image_path, prompt)
        
        return {
            'image_path': image_path,
            'animation_script': result.get('analysis', ''),
            'complexity': self._assess_animation_complexity(result.get('analysis', '')),
            'estimated_duration': self._estimate_animation_duration(result.get('analysis', ''))
        }
```

This comprehensive vision-language models guide provides detailed integration instructions, optimization strategies, and practical examples for using visual AI models in the production video generation system, specifically optimized for 16GB RAM systems.