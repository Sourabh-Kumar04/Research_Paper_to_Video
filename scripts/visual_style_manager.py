"""
Visual Style Manager for RASO Platform

This module provides consistent visual styling and branding across all
animation types (Manim, Motion Canvas, Remotion, Charts, 3D).
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import colorsys

logger = logging.getLogger(__name__)


class BrandTheme(Enum):
    """Available brand themes."""
    ACADEMIC = "academic"
    CORPORATE = "corporate"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    MINIMAL = "minimal"
    VIBRANT = "vibrant"
    DARK = "dark"
    LIGHT = "light"


class AnimationType(Enum):
    """Types of animations for styling."""
    MATHEMATICAL = "mathematical"
    CONCEPTUAL = "conceptual"
    PROCEDURAL = "procedural"
    DATA_VISUALIZATION = "data_visualization"
    SCIENTIFIC_3D = "scientific_3d"
    TITLE_SEQUENCE = "title_sequence"
    TRANSITION = "transition"


@dataclass
class ColorPalette:
    """Color palette definition."""
    primary: str
    secondary: str
    accent: str
    background: str
    text: str
    text_secondary: str
    success: str
    warning: str
    error: str
    info: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return asdict(self)
    
    def get_gradient(self, steps: int = 5) -> List[str]:
        """Generate gradient colors from primary to secondary."""
        return self._interpolate_colors(self.primary, self.secondary, steps)
    
    def get_complementary(self, color: str) -> str:
        """Get complementary color."""
        return self._get_complementary_color(color)
    
    def _interpolate_colors(self, color1: str, color2: str, steps: int) -> List[str]:
        """Interpolate between two colors."""
        # Convert hex to RGB
        rgb1 = tuple(int(color1.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        rgb2 = tuple(int(color2.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        
        colors = []
        for i in range(steps):
            ratio = i / (steps - 1) if steps > 1 else 0
            r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * ratio)
            g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * ratio)
            b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * ratio)
            colors.append(f"#{r:02x}{g:02x}{b:02x}")
        
        return colors
    
    def _get_complementary_color(self, color: str) -> str:
        """Get complementary color using color theory."""
        # Convert hex to RGB
        rgb = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        
        # Convert to HSV
        hsv = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        
        # Get complementary hue (opposite on color wheel)
        comp_hue = (hsv[0] + 0.5) % 1.0
        
        # Convert back to RGB
        comp_rgb = colorsys.hsv_to_rgb(comp_hue, hsv[1], hsv[2])
        
        # Convert to hex
        r, g, b = int(comp_rgb[0] * 255), int(comp_rgb[1] * 255), int(comp_rgb[2] * 255)
        return f"#{r:02x}{g:02x}{b:02x}"


@dataclass
class Typography:
    """Typography settings."""
    primary_font: str
    secondary_font: str
    monospace_font: str
    base_size: int
    scale_ratio: float
    line_height: float
    letter_spacing: float
    
    def get_font_sizes(self) -> Dict[str, int]:
        """Get font sizes for different elements."""
        return {
            'h1': int(self.base_size * (self.scale_ratio ** 3)),
            'h2': int(self.base_size * (self.scale_ratio ** 2)),
            'h3': int(self.base_size * (self.scale_ratio ** 1)),
            'body': self.base_size,
            'small': int(self.base_size / self.scale_ratio),
            'caption': int(self.base_size / (self.scale_ratio ** 2))
        }


@dataclass
class Spacing:
    """Spacing and layout settings."""
    base_unit: int
    scale_factor: float
    
    def get_spacing_values(self) -> Dict[str, int]:
        """Get spacing values for different elements."""
        return {
            'xs': int(self.base_unit * 0.25),
            'sm': int(self.base_unit * 0.5),
            'md': self.base_unit,
            'lg': int(self.base_unit * self.scale_factor),
            'xl': int(self.base_unit * (self.scale_factor ** 2)),
            'xxl': int(self.base_unit * (self.scale_factor ** 3))
        }


@dataclass
class AnimationSettings:
    """Animation timing and easing settings."""
    duration_fast: float
    duration_normal: float
    duration_slow: float
    easing_in: str
    easing_out: str
    easing_in_out: str
    
    def get_duration_for_complexity(self, complexity: str) -> float:
        """Get animation duration based on complexity."""
        duration_map = {
            'simple': self.duration_fast,
            'moderate': self.duration_normal,
            'complex': self.duration_slow,
            'advanced': self.duration_slow * 1.5
        }
        return duration_map.get(complexity, self.duration_normal)


@dataclass
class VisualEffects:
    """Visual effects settings."""
    shadow_enabled: bool
    shadow_blur: int
    shadow_offset: Tuple[int, int]
    shadow_color: str
    border_radius: int
    gradient_enabled: bool
    particle_effects: bool
    glow_effects: bool


@dataclass
class BrandStyle:
    """Complete brand style definition."""
    name: str
    theme: BrandTheme
    colors: ColorPalette
    typography: Typography
    spacing: Spacing
    animation: AnimationSettings
    effects: VisualEffects
    custom_properties: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'theme': self.theme.value,
            'colors': self.colors.to_dict(),
            'typography': asdict(self.typography),
            'spacing': asdict(self.spacing),
            'animation': asdict(self.animation),
            'effects': asdict(self.effects),
            'custom_properties': self.custom_properties
        }


class VisualStyleManager:
    """Manages visual styles and branding across all animation types."""
    
    def __init__(self):
        self.current_style: Optional[BrandStyle] = None
        self.available_styles: Dict[str, BrandStyle] = {}
        self.style_cache: Dict[str, Dict[str, Any]] = {}
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the visual style manager."""
        try:
            # Create default brand styles
            self._create_default_styles()
            
            # Set default style
            self.current_style = self.available_styles['academic']
            
            # Load custom styles if they exist
            await self._load_custom_styles()
            
            self.initialized = True
            logger.info("✅ Visual Style Manager initialized successfully")
            logger.info(f"   Available styles: {list(self.available_styles.keys())}")
            logger.info(f"   Current style: {self.current_style.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Visual Style Manager: {e}")
            return False
    
    def _create_default_styles(self):
        """Create default brand styles."""
        # Academic Style
        self.available_styles['academic'] = BrandStyle(
            name="Academic",
            theme=BrandTheme.ACADEMIC,
            colors=ColorPalette(
                primary="#1e3a8a",      # Deep blue
                secondary="#3b82f6",    # Blue
                accent="#f59e0b",       # Amber
                background="#ffffff",   # White
                text="#1f2937",         # Dark gray
                text_secondary="#6b7280", # Medium gray
                success="#10b981",      # Green
                warning="#f59e0b",      # Amber
                error="#ef4444",        # Red
                info="#3b82f6"          # Blue
            ),
            typography=Typography(
                primary_font="Times New Roman",
                secondary_font="Arial",
                monospace_font="Courier New",
                base_size=16,
                scale_ratio=1.25,
                line_height=1.6,
                letter_spacing=0.0
            ),
            spacing=Spacing(base_unit=16, scale_factor=1.5),
            animation=AnimationSettings(
                duration_fast=0.3,
                duration_normal=0.6,
                duration_slow=1.2,
                easing_in="ease-in",
                easing_out="ease-out",
                easing_in_out="ease-in-out"
            ),
            effects=VisualEffects(
                shadow_enabled=True,
                shadow_blur=4,
                shadow_offset=(2, 2),
                shadow_color="#00000020",
                border_radius=4,
                gradient_enabled=False,
                particle_effects=False,
                glow_effects=False
            ),
            custom_properties={}
        )
        
        # Corporate Style
        self.available_styles['corporate'] = BrandStyle(
            name="Corporate",
            theme=BrandTheme.CORPORATE,
            colors=ColorPalette(
                primary="#1f2937",      # Dark gray
                secondary="#4b5563",    # Medium gray
                accent="#3b82f6",       # Blue
                background="#f9fafb",   # Light gray
                text="#111827",         # Very dark gray
                text_secondary="#6b7280", # Medium gray
                success="#059669",      # Dark green
                warning="#d97706",      # Dark amber
                error="#dc2626",        # Dark red
                info="#1d4ed8"          # Dark blue
            ),
            typography=Typography(
                primary_font="Arial",
                secondary_font="Helvetica",
                monospace_font="Consolas",
                base_size=14,
                scale_ratio=1.2,
                line_height=1.5,
                letter_spacing=0.025
            ),
            spacing=Spacing(base_unit=12, scale_factor=1.4),
            animation=AnimationSettings(
                duration_fast=0.2,
                duration_normal=0.4,
                duration_slow=0.8,
                easing_in="ease-in",
                easing_out="ease-out",
                easing_in_out="ease-in-out"
            ),
            effects=VisualEffects(
                shadow_enabled=True,
                shadow_blur=8,
                shadow_offset=(0, 4),
                shadow_color="#00000015",
                border_radius=8,
                gradient_enabled=True,
                particle_effects=False,
                glow_effects=False
            ),
            custom_properties={}
        )
        
        # Creative Style
        self.available_styles['creative'] = BrandStyle(
            name="Creative",
            theme=BrandTheme.CREATIVE,
            colors=ColorPalette(
                primary="#7c3aed",      # Purple
                secondary="#ec4899",    # Pink
                accent="#f59e0b",       # Amber
                background="#fefefe",   # Off-white
                text="#1f2937",         # Dark gray
                text_secondary="#6b7280", # Medium gray
                success="#10b981",      # Green
                warning="#f59e0b",      # Amber
                error="#ef4444",        # Red
                info="#8b5cf6"          # Light purple
            ),
            typography=Typography(
                primary_font="Montserrat",
                secondary_font="Open Sans",
                monospace_font="Fira Code",
                base_size=16,
                scale_ratio=1.3,
                line_height=1.7,
                letter_spacing=0.05
            ),
            spacing=Spacing(base_unit=20, scale_factor=1.6),
            animation=AnimationSettings(
                duration_fast=0.4,
                duration_normal=0.8,
                duration_slow=1.6,
                easing_in="cubic-bezier(0.4, 0, 0.2, 1)",
                easing_out="cubic-bezier(0, 0, 0.2, 1)",
                easing_in_out="cubic-bezier(0.4, 0, 0.2, 1)"
            ),
            effects=VisualEffects(
                shadow_enabled=True,
                shadow_blur=12,
                shadow_offset=(0, 8),
                shadow_color="#7c3aed30",
                border_radius=16,
                gradient_enabled=True,
                particle_effects=True,
                glow_effects=True
            ),
            custom_properties={}
        )
        
        # Technical Style
        self.available_styles['technical'] = BrandStyle(
            name="Technical",
            theme=BrandTheme.TECHNICAL,
            colors=ColorPalette(
                primary="#0f172a",      # Very dark blue
                secondary="#1e293b",    # Dark blue-gray
                accent="#00d9ff",       # Cyan
                background="#020617",   # Very dark
                text="#f1f5f9",         # Light gray
                text_secondary="#94a3b8", # Medium gray
                success="#22c55e",      # Bright green
                warning="#eab308",      # Yellow
                error="#ef4444",        # Red
                info="#06b6d4"          # Cyan
            ),
            typography=Typography(
                primary_font="JetBrains Mono",
                secondary_font="Inter",
                monospace_font="Source Code Pro",
                base_size=14,
                scale_ratio=1.15,
                line_height=1.4,
                letter_spacing=0.1
            ),
            spacing=Spacing(base_unit=8, scale_factor=1.3),
            animation=AnimationSettings(
                duration_fast=0.15,
                duration_normal=0.3,
                duration_slow=0.6,
                easing_in="cubic-bezier(0.25, 0.46, 0.45, 0.94)",
                easing_out="cubic-bezier(0.25, 0.46, 0.45, 0.94)",
                easing_in_out="cubic-bezier(0.25, 0.46, 0.45, 0.94)"
            ),
            effects=VisualEffects(
                shadow_enabled=True,
                shadow_blur=6,
                shadow_offset=(0, 2),
                shadow_color="#00d9ff40",
                border_radius=2,
                gradient_enabled=False,
                particle_effects=False,
                glow_effects=True
            ),
            custom_properties={}
        )
        
        # Minimal Style
        self.available_styles['minimal'] = BrandStyle(
            name="Minimal",
            theme=BrandTheme.MINIMAL,
            colors=ColorPalette(
                primary="#000000",      # Black
                secondary="#666666",    # Medium gray
                accent="#ff6b6b",       # Coral red
                background="#ffffff",   # White
                text="#333333",         # Dark gray
                text_secondary="#888888", # Light gray
                success="#51cf66",      # Light green
                warning="#ffd43b",      # Light yellow
                error="#ff6b6b",        # Coral red
                info="#339af0"          # Light blue
            ),
            typography=Typography(
                primary_font="Helvetica Neue",
                secondary_font="Arial",
                monospace_font="Monaco",
                base_size=16,
                scale_ratio=1.2,
                line_height=1.5,
                letter_spacing=0.0
            ),
            spacing=Spacing(base_unit=24, scale_factor=1.5),
            animation=AnimationSettings(
                duration_fast=0.2,
                duration_normal=0.4,
                duration_slow=0.8,
                easing_in="ease",
                easing_out="ease",
                easing_in_out="ease"
            ),
            effects=VisualEffects(
                shadow_enabled=False,
                shadow_blur=0,
                shadow_offset=(0, 0),
                shadow_color="#00000000",
                border_radius=0,
                gradient_enabled=False,
                particle_effects=False,
                glow_effects=False
            ),
            custom_properties={}
        )
    
    async def _load_custom_styles(self):
        """Load custom styles from configuration files."""
        try:
            styles_dir = Path(".kiro/styles")
            if styles_dir.exists():
                for style_file in styles_dir.glob("*.json"):
                    try:
                        with open(style_file, 'r') as f:
                            style_data = json.load(f)
                        
                        # Parse and create custom style
                        custom_style = self._parse_style_data(style_data)
                        if custom_style:
                            self.available_styles[custom_style.name.lower()] = custom_style
                            logger.info(f"Loaded custom style: {custom_style.name}")
                    
                    except Exception as e:
                        logger.warning(f"Failed to load custom style {style_file}: {e}")
        
        except Exception as e:
            logger.warning(f"Failed to load custom styles: {e}")
    
    def _parse_style_data(self, data: Dict[str, Any]) -> Optional[BrandStyle]:
        """Parse style data from JSON."""
        try:
            # This is a simplified parser - in production, you'd want more validation
            colors = ColorPalette(**data['colors'])
            typography = Typography(**data['typography'])
            spacing = Spacing(**data['spacing'])
            animation = AnimationSettings(**data['animation'])
            effects = VisualEffects(**data['effects'])
            
            return BrandStyle(
                name=data['name'],
                theme=BrandTheme(data['theme']),
                colors=colors,
                typography=typography,
                spacing=spacing,
                animation=animation,
                effects=effects,
                custom_properties=data.get('custom_properties', {})
            )
        
        except Exception as e:
            logger.error(f"Failed to parse style data: {e}")
            return None
    
    def set_style(self, style_name: str) -> bool:
        """Set the current style."""
        if style_name.lower() in self.available_styles:
            self.current_style = self.available_styles[style_name.lower()]
            self.style_cache.clear()  # Clear cache when style changes
            logger.info(f"Style changed to: {self.current_style.name}")
            return True
        else:
            logger.warning(f"Style '{style_name}' not found")
            return False
    
    def get_style_for_animation_type(self, animation_type: AnimationType) -> Dict[str, Any]:
        """Get style configuration for specific animation type."""
        if not self.current_style:
            logger.warning("No current style set")
            return {}
        
        cache_key = f"{self.current_style.name}_{animation_type.value}"
        if cache_key in self.style_cache:
            return self.style_cache[cache_key]
        
        # Base style configuration
        base_config = {
            'colors': self.current_style.colors.to_dict(),
            'typography': self.current_style.typography.get_font_sizes(),
            'spacing': self.current_style.spacing.get_spacing_values(),
            'animation_duration': self.current_style.animation.duration_normal,
            'easing': self.current_style.animation.easing_in_out,
            'effects': asdict(self.current_style.effects)
        }
        
        # Animation-type specific adjustments
        if animation_type == AnimationType.MATHEMATICAL:
            base_config.update({
                'primary_font': self.current_style.typography.monospace_font,
                'equation_color': self.current_style.colors.primary,
                'highlight_color': self.current_style.colors.accent,
                'animation_duration': self.current_style.animation.duration_slow,
                'precision_mode': True
            })
        
        elif animation_type == AnimationType.DATA_VISUALIZATION:
            base_config.update({
                'chart_colors': self.current_style.colors.get_gradient(8),
                'grid_color': self.current_style.colors.text_secondary,
                'axis_color': self.current_style.colors.text,
                'animation_duration': self.current_style.animation.duration_normal,
                'data_point_size': 6
            })
        
        elif animation_type == AnimationType.CONCEPTUAL:
            base_config.update({
                'concept_color': self.current_style.colors.primary,
                'connection_color': self.current_style.colors.secondary,
                'highlight_color': self.current_style.colors.accent,
                'animation_duration': self.current_style.animation.duration_normal,
                'flow_style': 'smooth'
            })
        
        elif animation_type == AnimationType.PROCEDURAL:
            base_config.update({
                'step_color': self.current_style.colors.primary,
                'active_step_color': self.current_style.colors.accent,
                'completed_step_color': self.current_style.colors.success,
                'animation_duration': self.current_style.animation.duration_fast,
                'step_transition': 'slide'
            })
        
        elif animation_type == AnimationType.SCIENTIFIC_3D:
            base_config.update({
                'material_colors': {
                    'default': self.current_style.colors.primary,
                    'highlight': self.current_style.colors.accent,
                    'secondary': self.current_style.colors.secondary
                },
                'lighting': 'professional',
                'camera_movement': 'smooth',
                'animation_duration': self.current_style.animation.duration_slow
            })
        
        elif animation_type == AnimationType.TITLE_SEQUENCE:
            base_config.update({
                'title_font': self.current_style.typography.primary_font,
                'title_size': self.current_style.typography.get_font_sizes()['h1'],
                'subtitle_size': self.current_style.typography.get_font_sizes()['h2'],
                'animation_duration': self.current_style.animation.duration_slow,
                'dramatic_effects': self.current_style.effects.glow_effects
            })
        
        # Cache the result
        self.style_cache[cache_key] = base_config
        return base_config
    
    def get_manim_style_config(self) -> Dict[str, Any]:
        """Get Manim-specific style configuration."""
        if not self.current_style:
            return {}
        
        return {
            'background_color': self.current_style.colors.background,
            'default_mobject_color': self.current_style.colors.primary,
            'text_color': self.current_style.colors.text,
            'font_family': self.current_style.typography.primary_font,
            'font_size': self.current_style.typography.base_size,
            'stroke_width': 2,
            'fill_opacity': 0.8,
            'animation_run_time': self.current_style.animation.duration_normal
        }
    
    def get_motion_canvas_style_config(self) -> Dict[str, Any]:
        """Get Motion Canvas-specific style configuration."""
        if not self.current_style:
            return {}
        
        return {
            'colors': self.current_style.colors.to_dict(),
            'fonts': {
                'primary': self.current_style.typography.primary_font,
                'secondary': self.current_style.typography.secondary_font,
                'monospace': self.current_style.typography.monospace_font
            },
            'sizes': self.current_style.typography.get_font_sizes(),
            'spacing': self.current_style.spacing.get_spacing_values(),
            'borderRadius': self.current_style.effects.border_radius,
            'shadow': {
                'enabled': self.current_style.effects.shadow_enabled,
                'blur': self.current_style.effects.shadow_blur,
                'offset': self.current_style.effects.shadow_offset,
                'color': self.current_style.effects.shadow_color
            },
            'animation': {
                'duration': self.current_style.animation.duration_normal,
                'easing': self.current_style.animation.easing_in_out
            }
        }
    
    def get_chart_style_config(self) -> Dict[str, Any]:
        """Get chart-specific style configuration."""
        if not self.current_style:
            return {}
        
        return {
            'color_palette': self.current_style.colors.get_gradient(10),
            'background_color': self.current_style.colors.background,
            'text_color': self.current_style.colors.text,
            'grid_color': self.current_style.colors.text_secondary,
            'font_family': self.current_style.typography.secondary_font,
            'font_size': self.current_style.typography.base_size,
            'line_width': 2,
            'marker_size': 6,
            'border_radius': self.current_style.effects.border_radius,
            'shadow_enabled': self.current_style.effects.shadow_enabled
        }
    
    def get_blender_style_config(self) -> Dict[str, Any]:
        """Get Blender 3D-specific style configuration."""
        if not self.current_style:
            return {}
        
        return {
            'material_colors': {
                'primary': self.current_style.colors.primary,
                'secondary': self.current_style.colors.secondary,
                'accent': self.current_style.colors.accent
            },
            'lighting_setup': 'three_point' if self.current_style.theme == BrandTheme.ACADEMIC else 'studio',
            'background_color': self.current_style.colors.background,
            'camera_settings': {
                'fov': 50,
                'clip_start': 0.1,
                'clip_end': 1000
            },
            'render_quality': 'high' if self.current_style.effects.glow_effects else 'medium',
            'animation_interpolation': 'bezier'
        }
    
    def create_transition_style(self, from_type: AnimationType, to_type: AnimationType) -> Dict[str, Any]:
        """Create transition style between animation types."""
        if not self.current_style:
            return {}
        
        from_style = self.get_style_for_animation_type(from_type)
        to_style = self.get_style_for_animation_type(to_type)
        
        # Create smooth transition configuration
        return {
            'duration': self.current_style.animation.duration_normal * 0.5,
            'easing': self.current_style.animation.easing_in_out,
            'fade_color': self.current_style.colors.background,
            'transition_effect': 'crossfade' if self.current_style.effects.gradient_enabled else 'cut',
            'from_style': from_style,
            'to_style': to_style
        }
    
    def get_available_styles(self) -> List[str]:
        """Get list of available style names."""
        return list(self.available_styles.keys())
    
    def get_current_style_info(self) -> Dict[str, Any]:
        """Get information about the current style."""
        if not self.current_style:
            return {}
        
        return {
            'name': self.current_style.name,
            'theme': self.current_style.theme.value,
            'description': f"{self.current_style.theme.value.title()} style with {self.current_style.colors.primary} primary color",
            'features': {
                'shadows': self.current_style.effects.shadow_enabled,
                'gradients': self.current_style.effects.gradient_enabled,
                'particles': self.current_style.effects.particle_effects,
                'glow': self.current_style.effects.glow_effects
            },
            'colors': self.current_style.colors.to_dict(),
            'fonts': {
                'primary': self.current_style.typography.primary_font,
                'secondary': self.current_style.typography.secondary_font,
                'monospace': self.current_style.typography.monospace_font
            }
        }
    
    async def save_custom_style(self, style: BrandStyle) -> bool:
        """Save a custom style to disk."""
        try:
            styles_dir = Path(".kiro/styles")
            styles_dir.mkdir(parents=True, exist_ok=True)
            
            style_file = styles_dir / f"{style.name.lower().replace(' ', '_')}.json"
            
            with open(style_file, 'w') as f:
                json.dump(style.to_dict(), f, indent=2)
            
            # Add to available styles
            self.available_styles[style.name.lower()] = style
            
            logger.info(f"Custom style '{style.name}' saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save custom style: {e}")
            return False
    
    def generate_style_preview(self, style_name: str) -> Dict[str, Any]:
        """Generate a preview of a style."""
        if style_name.lower() not in self.available_styles:
            return {}
        
        style = self.available_styles[style_name.lower()]
        
        return {
            'name': style.name,
            'theme': style.theme.value,
            'color_swatches': [
                {'name': 'Primary', 'color': style.colors.primary},
                {'name': 'Secondary', 'color': style.colors.secondary},
                {'name': 'Accent', 'color': style.colors.accent},
                {'name': 'Background', 'color': style.colors.background},
                {'name': 'Text', 'color': style.colors.text}
            ],
            'typography_sample': {
                'font': style.typography.primary_font,
                'sizes': style.typography.get_font_sizes()
            },
            'effects_preview': {
                'shadow': style.effects.shadow_enabled,
                'gradient': style.effects.gradient_enabled,
                'glow': style.effects.glow_effects,
                'particles': style.effects.particle_effects
            }
        }


# Global instance for easy access
visual_style_manager = VisualStyleManager()