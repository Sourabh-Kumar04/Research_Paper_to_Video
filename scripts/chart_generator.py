"""
Dynamic Chart and Diagram Generator for RASO Platform

This module provides dynamic chart and diagram generation capabilities using
matplotlib, seaborn, and other visualization libraries for data-driven content.
"""

import os
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging
import json
import numpy as np
import pandas as pd

# Import visualization libraries
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    sns = None

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

logger = logging.getLogger(__name__)


class ChartType(Enum):
    """Types of charts that can be generated."""
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    SCATTER_PLOT = "scatter_plot"
    HISTOGRAM = "histogram"
    PIE_CHART = "pie_chart"
    HEATMAP = "heatmap"
    BOX_PLOT = "box_plot"
    VIOLIN_PLOT = "violin_plot"
    NETWORK_DIAGRAM = "network_diagram"
    FLOWCHART = "flowchart"
    TIMELINE = "timeline"
    ANIMATED_CHART = "animated_chart"


class AnimationType(Enum):
    """Types of animations for charts."""
    GROW_FROM_ZERO = "grow_from_zero"
    FADE_IN = "fade_in"
    SLIDE_IN = "slide_in"
    SEQUENTIAL_REVEAL = "sequential_reveal"
    DATA_PROGRESSION = "data_progression"
    ROTATION_3D = "rotation_3d"


@dataclass
class ChartData:
    """Data structure for chart generation."""
    data: Union[Dict[str, Any], pd.DataFrame, List[Dict[str, Any]]]
    chart_type: ChartType
    title: str
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    categories: Optional[List[str]] = None
    values: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChartStyle:
    """Style configuration for charts."""
    color_palette: str = "viridis"
    background_color: str = "white"
    text_color: str = "black"
    font_family: str = "Arial"
    font_size: int = 12
    figure_size: Tuple[int, int] = (12, 8)
    dpi: int = 150
    style_theme: str = "default"  # seaborn themes: default, whitegrid, darkgrid, etc.


@dataclass
class AnimationConfig:
    """Configuration for chart animations."""
    animation_type: AnimationType
    duration: float
    fps: int = 30
    easing: str = "ease_in_out"
    delay_between_elements: float = 0.1
    show_progression: bool = True


class DynamicChartGenerator:
    """Generator for dynamic charts and diagrams."""
    
    def __init__(self):
        self.matplotlib_available = MATPLOTLIB_AVAILABLE
        self.networkx_available = NETWORKX_AVAILABLE
        self.temp_dir = None
        
    async def initialize(self) -> bool:
        """Initialize the chart generator."""
        try:
            if not self.matplotlib_available:
                logger.warning("❌ Matplotlib not available. Install with: pip install matplotlib seaborn")
                return False
            
            # Create temporary directory for chart generation
            self.temp_dir = Path(tempfile.mkdtemp(prefix="chart_gen_"))
            
            # Set up matplotlib defaults
            plt.style.use('default')
            sns.set_palette("husl")
            
            logger.info("✅ Dynamic Chart Generator initialized successfully")
            logger.info(f"   Matplotlib version: {matplotlib.__version__}")
            if self.networkx_available:
                logger.info(f"   NetworkX available for network diagrams")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Dynamic Chart Generator: {e}")
            return False
    
    async def generate_static_chart(
        self,
        chart_data: ChartData,
        style: ChartStyle,
        output_path: str
    ) -> Optional[str]:
        """Generate a static chart."""
        try:
            if not self.matplotlib_available:
                logger.error("Matplotlib not available for chart generation")
                return None
            
            # Set up the plot
            plt.figure(figsize=style.figure_size, dpi=style.dpi)
            
            # Apply style theme
            if style.style_theme != "default":
                sns.set_style(style.style_theme)
            
            # Generate chart based on type
            if chart_data.chart_type == ChartType.LINE_CHART:
                self._create_line_chart(chart_data, style)
            elif chart_data.chart_type == ChartType.BAR_CHART:
                self._create_bar_chart(chart_data, style)
            elif chart_data.chart_type == ChartType.SCATTER_PLOT:
                self._create_scatter_plot(chart_data, style)
            elif chart_data.chart_type == ChartType.HISTOGRAM:
                self._create_histogram(chart_data, style)
            elif chart_data.chart_type == ChartType.PIE_CHART:
                self._create_pie_chart(chart_data, style)
            elif chart_data.chart_type == ChartType.HEATMAP:
                self._create_heatmap(chart_data, style)
            elif chart_data.chart_type == ChartType.BOX_PLOT:
                self._create_box_plot(chart_data, style)
            elif chart_data.chart_type == ChartType.NETWORK_DIAGRAM:
                self._create_network_diagram(chart_data, style)
            elif chart_data.chart_type == ChartType.FLOWCHART:
                self._create_flowchart(chart_data, style)
            elif chart_data.chart_type == ChartType.TIMELINE:
                self._create_timeline(chart_data, style)
            else:
                logger.error(f"Unsupported chart type: {chart_data.chart_type}")
                return None
            
            # Apply common styling
            self._apply_common_styling(chart_data, style)
            
            # Save the chart
            plt.tight_layout()
            plt.savefig(output_path, dpi=style.dpi, bbox_inches='tight', 
                       facecolor=style.background_color)
            plt.close()
            
            logger.info(f"✅ Static chart generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating static chart: {e}")
            plt.close()  # Ensure plot is closed on error
            return None
    
    async def generate_animated_chart(
        self,
        chart_data: ChartData,
        style: ChartStyle,
        animation_config: AnimationConfig,
        output_path: str
    ) -> Optional[str]:
        """Generate an animated chart."""
        try:
            if not self.matplotlib_available:
                logger.error("Matplotlib not available for animated chart generation")
                return None
            
            # Set up the figure
            fig, ax = plt.subplots(figsize=style.figure_size, dpi=style.dpi)
            
            # Apply style theme
            if style.style_theme != "default":
                sns.set_style(style.style_theme)
            
            # Create animation based on chart type and animation type
            anim = None
            
            if chart_data.chart_type == ChartType.LINE_CHART:
                anim = self._create_animated_line_chart(fig, ax, chart_data, style, animation_config)
            elif chart_data.chart_type == ChartType.BAR_CHART:
                anim = self._create_animated_bar_chart(fig, ax, chart_data, style, animation_config)
            elif chart_data.chart_type == ChartType.SCATTER_PLOT:
                anim = self._create_animated_scatter_plot(fig, ax, chart_data, style, animation_config)
            elif chart_data.chart_type == ChartType.PIE_CHART:
                anim = self._create_animated_pie_chart(fig, ax, chart_data, style, animation_config)
            else:
                # For unsupported animated types, create static version
                logger.warning(f"Animation not supported for {chart_data.chart_type}, creating static version")
                plt.close()
                return await self.generate_static_chart(chart_data, style, output_path.replace('.mp4', '.png'))
            
            if anim:
                # Save animation
                writer = animation.FFMpegWriter(fps=animation_config.fps, bitrate=1800)
                anim.save(output_path, writer=writer)
                plt.close()
                
                logger.info(f"✅ Animated chart generated: {output_path}")
                return output_path
            else:
                plt.close()
                return None
                
        except Exception as e:
            logger.error(f"Error generating animated chart: {e}")
            plt.close()
            return None
    
    def _create_line_chart(self, chart_data: ChartData, style: ChartStyle):
        """Create a line chart."""
        if isinstance(chart_data.data, pd.DataFrame):
            df = chart_data.data
            for column in df.select_dtypes(include=[np.number]).columns:
                plt.plot(df.index, df[column], label=column, linewidth=2)
            plt.legend()
        elif isinstance(chart_data.data, dict):
            for key, values in chart_data.data.items():
                if isinstance(values, list):
                    plt.plot(values, label=key, linewidth=2)
            plt.legend()
        else:
            # Simple case with categories and values
            if chart_data.categories and chart_data.values:
                plt.plot(chart_data.categories, chart_data.values, linewidth=2, marker='o')
    
    def _create_bar_chart(self, chart_data: ChartData, style: ChartStyle):
        """Create a bar chart."""
        if isinstance(chart_data.data, pd.DataFrame):
            df = chart_data.data
            if len(df.columns) == 1:
                plt.bar(df.index, df.iloc[:, 0])
            else:
                df.plot(kind='bar', ax=plt.gca())
        elif isinstance(chart_data.data, dict):
            categories = list(chart_data.data.keys())
            values = list(chart_data.data.values())
            plt.bar(categories, values)
        else:
            if chart_data.categories and chart_data.values:
                plt.bar(chart_data.categories, chart_data.values)
    
    def _create_scatter_plot(self, chart_data: ChartData, style: ChartStyle):
        """Create a scatter plot."""
        if isinstance(chart_data.data, pd.DataFrame):
            df = chart_data.data
            if len(df.columns) >= 2:
                plt.scatter(df.iloc[:, 0], df.iloc[:, 1], alpha=0.7, s=60)
        elif isinstance(chart_data.data, dict):
            if 'x' in chart_data.data and 'y' in chart_data.data:
                plt.scatter(chart_data.data['x'], chart_data.data['y'], alpha=0.7, s=60)
    
    def _create_histogram(self, chart_data: ChartData, style: ChartStyle):
        """Create a histogram."""
        if isinstance(chart_data.data, pd.DataFrame):
            df = chart_data.data
            for column in df.select_dtypes(include=[np.number]).columns:
                plt.hist(df[column], alpha=0.7, label=column, bins=20)
            plt.legend()
        elif isinstance(chart_data.data, dict):
            if 'values' in chart_data.data:
                plt.hist(chart_data.data['values'], bins=20, alpha=0.7)
        elif chart_data.values:
            plt.hist(chart_data.values, bins=20, alpha=0.7)
    
    def _create_pie_chart(self, chart_data: ChartData, style: ChartStyle):
        """Create a pie chart."""
        if isinstance(chart_data.data, dict):
            labels = list(chart_data.data.keys())
            sizes = list(chart_data.data.values())
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        elif chart_data.categories and chart_data.values:
            plt.pie(chart_data.values, labels=chart_data.categories, autopct='%1.1f%%', startangle=90)
    
    def _create_heatmap(self, chart_data: ChartData, style: ChartStyle):
        """Create a heatmap."""
        if isinstance(chart_data.data, pd.DataFrame):
            sns.heatmap(chart_data.data, annot=True, cmap=style.color_palette)
        elif isinstance(chart_data.data, dict) and 'matrix' in chart_data.data:
            matrix = np.array(chart_data.data['matrix'])
            sns.heatmap(matrix, annot=True, cmap=style.color_palette)
    
    def _create_box_plot(self, chart_data: ChartData, style: ChartStyle):
        """Create a box plot."""
        if isinstance(chart_data.data, pd.DataFrame):
            df = chart_data.data
            df.boxplot()
        elif isinstance(chart_data.data, dict):
            data_to_plot = []
            labels = []
            for key, values in chart_data.data.items():
                if isinstance(values, list):
                    data_to_plot.append(values)
                    labels.append(key)
            plt.boxplot(data_to_plot, labels=labels)
    
    def _create_network_diagram(self, chart_data: ChartData, style: ChartStyle):
        """Create a network diagram."""
        if not self.networkx_available:
            logger.error("NetworkX not available for network diagrams")
            return
        
        # Create graph from data
        G = nx.Graph()
        
        if isinstance(chart_data.data, dict):
            if 'nodes' in chart_data.data and 'edges' in chart_data.data:
                # Add nodes
                for node in chart_data.data['nodes']:
                    if isinstance(node, dict):
                        G.add_node(node['id'], **node)
                    else:
                        G.add_node(node)
                
                # Add edges
                for edge in chart_data.data['edges']:
                    if isinstance(edge, dict):
                        G.add_edge(edge['from'], edge['to'], **edge)
                    else:
                        G.add_edge(edge[0], edge[1])
        
        # Layout and draw
        pos = nx.spring_layout(G, k=1, iterations=50)
        nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                node_size=1000, font_size=10, font_weight='bold')
    
    def _create_flowchart(self, chart_data: ChartData, style: ChartStyle):
        """Create a flowchart diagram."""
        if isinstance(chart_data.data, dict) and 'steps' in chart_data.data:
            steps = chart_data.data['steps']
            
            # Simple vertical flowchart
            fig, ax = plt.subplots(figsize=style.figure_size)
            
            y_positions = np.linspace(0.9, 0.1, len(steps))
            
            for i, (step, y_pos) in enumerate(zip(steps, y_positions)):
                # Draw box
                box = FancyBboxPatch((0.2, y_pos-0.05), 0.6, 0.08,
                                   boxstyle="round,pad=0.01",
                                   facecolor='lightblue',
                                   edgecolor='black')
                ax.add_patch(box)
                
                # Add text
                ax.text(0.5, y_pos, step, ha='center', va='center', 
                       fontsize=style.font_size, weight='bold')
                
                # Draw arrow to next step
                if i < len(steps) - 1:
                    ax.arrow(0.5, y_pos-0.05, 0, -0.05, head_width=0.02, 
                            head_length=0.01, fc='black', ec='black')
            
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
    
    def _create_timeline(self, chart_data: ChartData, style: ChartStyle):
        """Create a timeline diagram."""
        if isinstance(chart_data.data, dict) and 'events' in chart_data.data:
            events = chart_data.data['events']
            
            fig, ax = plt.subplots(figsize=style.figure_size)
            
            # Draw timeline line
            ax.plot([0, 1], [0.5, 0.5], 'k-', linewidth=3)
            
            # Add events
            x_positions = np.linspace(0.1, 0.9, len(events))
            
            for i, (event, x_pos) in enumerate(zip(events, x_positions)):
                # Draw event marker
                ax.plot(x_pos, 0.5, 'o', markersize=10, color='red')
                
                # Add event text
                y_text = 0.6 if i % 2 == 0 else 0.4
                ax.text(x_pos, y_text, event, ha='center', va='center',
                       fontsize=style.font_size, weight='bold',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
                
                # Draw line to timeline
                ax.plot([x_pos, x_pos], [0.5, y_text-0.05], 'k--', alpha=0.5)
            
            ax.set_xlim(-0.1, 1.1)
            ax.set_ylim(0.2, 0.8)
            ax.axis('off')
    
    def _create_animated_line_chart(self, fig, ax, chart_data: ChartData, 
                                  style: ChartStyle, animation_config: AnimationConfig):
        """Create animated line chart."""
        if not (chart_data.categories and chart_data.values):
            return None
        
        x_data = list(range(len(chart_data.categories)))
        y_data = chart_data.values
        
        line, = ax.plot([], [], linewidth=2, marker='o')
        ax.set_xlim(0, len(x_data)-1)
        ax.set_ylim(min(y_data)*0.9, max(y_data)*1.1)
        
        def animate(frame):
            # Reveal data progressively
            current_x = x_data[:frame+1]
            current_y = y_data[:frame+1]
            line.set_data(current_x, current_y)
            return line,
        
        frames = len(x_data)
        interval = (animation_config.duration * 1000) / frames
        
        return animation.FuncAnimation(fig, animate, frames=frames, 
                                     interval=interval, blit=True, repeat=False)
    
    def _create_animated_bar_chart(self, fig, ax, chart_data: ChartData,
                                 style: ChartStyle, animation_config: AnimationConfig):
        """Create animated bar chart."""
        if not (chart_data.categories and chart_data.values):
            return None
        
        categories = chart_data.categories
        values = chart_data.values
        
        bars = ax.bar(categories, [0] * len(categories))
        ax.set_ylim(0, max(values) * 1.1)
        
        def animate(frame):
            # Grow bars progressively
            progress = frame / (len(values) * animation_config.fps / animation_config.duration)
            for bar, target_height in zip(bars, values):
                current_height = min(target_height * progress, target_height)
                bar.set_height(current_height)
            return bars
        
        frames = int(animation_config.duration * animation_config.fps)
        
        return animation.FuncAnimation(fig, animate, frames=frames,
                                     interval=1000/animation_config.fps, 
                                     blit=False, repeat=False)
    
    def _create_animated_scatter_plot(self, fig, ax, chart_data: ChartData,
                                    style: ChartStyle, animation_config: AnimationConfig):
        """Create animated scatter plot."""
        if not isinstance(chart_data.data, dict) or 'x' not in chart_data.data or 'y' not in chart_data.data:
            return None
        
        x_data = chart_data.data['x']
        y_data = chart_data.data['y']
        
        scat = ax.scatter([], [], s=60, alpha=0.7)
        ax.set_xlim(min(x_data)*0.9, max(x_data)*1.1)
        ax.set_ylim(min(y_data)*0.9, max(y_data)*1.1)
        
        def animate(frame):
            # Reveal points progressively
            current_x = x_data[:frame+1]
            current_y = y_data[:frame+1]
            scat.set_offsets(np.column_stack((current_x, current_y)))
            return scat,
        
        frames = len(x_data)
        interval = (animation_config.duration * 1000) / frames
        
        return animation.FuncAnimation(fig, animate, frames=frames,
                                     interval=interval, blit=True, repeat=False)
    
    def _create_animated_pie_chart(self, fig, ax, chart_data: ChartData,
                                 style: ChartStyle, animation_config: AnimationConfig):
        """Create animated pie chart."""
        if not isinstance(chart_data.data, dict):
            return None
        
        labels = list(chart_data.data.keys())
        sizes = list(chart_data.data.values())
        
        def animate(frame):
            ax.clear()
            # Reveal slices progressively
            progress = frame / (animation_config.fps * animation_config.duration)
            current_sizes = [size * min(progress, 1.0) for size in sizes]
            
            ax.pie(current_sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.set_title(chart_data.title)
        
        frames = int(animation_config.duration * animation_config.fps)
        
        return animation.FuncAnimation(fig, animate, frames=frames,
                                     interval=1000/animation_config.fps,
                                     repeat=False)
    
    def _apply_common_styling(self, chart_data: ChartData, style: ChartStyle):
        """Apply common styling to charts."""
        plt.title(chart_data.title, fontsize=style.font_size + 4, weight='bold', color=style.text_color)
        
        if chart_data.x_label:
            plt.xlabel(chart_data.x_label, fontsize=style.font_size, color=style.text_color)
        
        if chart_data.y_label:
            plt.ylabel(chart_data.y_label, fontsize=style.font_size, color=style.text_color)
        
        # Set background color
        plt.gca().set_facecolor(style.background_color)
        plt.gcf().patch.set_facecolor(style.background_color)
        
        # Set text color for ticks
        plt.gca().tick_params(colors=style.text_color)
        
        # Grid styling
        plt.grid(True, alpha=0.3)
    
    def generate_sample_data(self, chart_type: ChartType, size: int = 20) -> ChartData:
        """Generate sample data for testing different chart types."""
        np.random.seed(42)  # For reproducible results
        
        if chart_type == ChartType.LINE_CHART:
            categories = [f"Point {i+1}" for i in range(size)]
            values = np.cumsum(np.random.randn(size)) + 100
            return ChartData(
                data={"values": values.tolist()},
                chart_type=chart_type,
                title="Sample Line Chart",
                x_label="Time",
                y_label="Value",
                categories=categories,
                values=values.tolist()
            )
        
        elif chart_type == ChartType.BAR_CHART:
            categories = [f"Category {chr(65+i)}" for i in range(min(size, 10))]
            values = np.random.randint(10, 100, len(categories))
            return ChartData(
                data=dict(zip(categories, values)),
                chart_type=chart_type,
                title="Sample Bar Chart",
                x_label="Categories",
                y_label="Values",
                categories=categories,
                values=values.tolist()
            )
        
        elif chart_type == ChartType.SCATTER_PLOT:
            x_data = np.random.randn(size)
            y_data = 2 * x_data + np.random.randn(size) * 0.5
            return ChartData(
                data={"x": x_data.tolist(), "y": y_data.tolist()},
                chart_type=chart_type,
                title="Sample Scatter Plot",
                x_label="X Values",
                y_label="Y Values"
            )
        
        elif chart_type == ChartType.PIE_CHART:
            categories = ["Category A", "Category B", "Category C", "Category D"]
            values = np.random.randint(10, 50, len(categories))
            return ChartData(
                data=dict(zip(categories, values)),
                chart_type=chart_type,
                title="Sample Pie Chart",
                categories=categories,
                values=values.tolist()
            )
        
        elif chart_type == ChartType.HISTOGRAM:
            values = np.random.randn(size) * 10 + 50  # Normal distribution
            return ChartData(
                data={"values": values.tolist()},
                chart_type=chart_type,
                title="Sample Histogram",
                x_label="Value",
                y_label="Frequency",
                values=values.tolist()
            )
        
        elif chart_type == ChartType.NETWORK_DIAGRAM:
            nodes = [{"id": f"Node{i}", "type": "default"} for i in range(6)]
            edges = [
                {"from": "Node0", "to": "Node1"},
                {"from": "Node1", "to": "Node2"},
                {"from": "Node2", "to": "Node3"},
                {"from": "Node0", "to": "Node4"},
                {"from": "Node4", "to": "Node5"},
                {"from": "Node2", "to": "Node5"}
            ]
            return ChartData(
                data={"nodes": nodes, "edges": edges},
                chart_type=chart_type,
                title="Sample Network Diagram"
            )
        
        elif chart_type == ChartType.FLOWCHART:
            steps = ["Start", "Process Data", "Make Decision", "Execute Action", "End"]
            return ChartData(
                data={"steps": steps},
                chart_type=chart_type,
                title="Sample Flowchart"
            )
        
        elif chart_type == ChartType.TIMELINE:
            events = ["Event 1", "Event 2", "Event 3", "Event 4", "Event 5"]
            return ChartData(
                data={"events": events},
                chart_type=chart_type,
                title="Sample Timeline"
            )
        
        else:
            # Default to line chart
            return self.generate_sample_data(ChartType.LINE_CHART, size)
    
    def get_system_requirements(self) -> Dict[str, Any]:
        """Get system requirements for chart generation."""
        return {
            "matplotlib_available": self.matplotlib_available,
            "networkx_available": self.networkx_available,
            "temp_directory": str(self.temp_dir) if self.temp_dir else None,
            "supported_chart_types": [t.value for t in ChartType],
            "supported_animations": [t.value for t in AnimationType],
            "requirements": {
                "matplotlib": "Required for all chart generation",
                "seaborn": "Required for advanced statistical plots",
                "networkx": "Required for network diagrams",
                "pandas": "Recommended for data manipulation",
                "numpy": "Required for numerical operations"
            }
        }


# Global instance for easy access
chart_generator = DynamicChartGenerator()