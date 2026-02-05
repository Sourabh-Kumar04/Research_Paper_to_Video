"""
Detailed Content Generation Reporting System for RASO platform.

Provides comprehensive reporting on content generation success/failure
with detailed error analysis and recommendations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from utils.content_validator import ValidationResult


@dataclass
class ContentGenerationReport:
    """Comprehensive report of content generation process."""
    timestamp: str
    total_scenes: int
    script_status: str
    audio_status: str
    animation_status: str
    overall_success: bool
    quality_score: float
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]
    detailed_stats: Dict[str, Any]


class ContentReporter:
    """Detailed content generation reporter."""
    
    def __init__(self):
        """Initialize the content reporter."""
        self.reports_dir = Path("logs/content_reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_comprehensive_report(
        self,
        script_validation: Optional[ValidationResult],
        audio_validations: List[ValidationResult],
        video_validations: List[ValidationResult],
        generation_stats: Dict[str, Any]
    ) -> ContentGenerationReport:
        """Generate comprehensive content generation report."""
        
        timestamp = datetime.now().isoformat()
        total_scenes = len(audio_validations)
        
        # Analyze script status
        script_status = "MISSING"
        script_errors = []
        script_warnings = []
        
        if script_validation:
            if script_validation.valid:
                script_status = "VALID" if script_validation.score > 0.8 else "ACCEPTABLE"
            else:
                script_status = "INVALID"
            script_errors.extend(script_validation.errors)
            script_warnings.extend(script_validation.warnings)
        
        # Analyze audio status
        valid_audio = sum(1 for v in audio_validations if v.valid)
        if valid_audio == total_scenes:
            audio_status = "ALL_VALID"
        elif valid_audio > total_scenes * 0.7:
            audio_status = "MOSTLY_VALID"
        elif valid_audio > 0:
            audio_status = "PARTIALLY_VALID"
        else:
            audio_status = "INVALID"
        
        # Analyze animation status
        valid_animations = sum(1 for v in video_validations if v.valid)
        if valid_animations == total_scenes:
            animation_status = "ALL_VALID"
        elif valid_animations > total_scenes * 0.7:
            animation_status = "MOSTLY_VALID"
        elif valid_animations > 0:
            animation_status = "PARTIALLY_VALID"
        else:
            animation_status = "INVALID"
        
        # Collect all errors and warnings
        all_errors = script_errors.copy()
        all_warnings = script_warnings.copy()
        
        for i, validation in enumerate(audio_validations):
            all_errors.extend([f"Audio Scene {i}: {e}" for e in validation.errors])
            all_warnings.extend([f"Audio Scene {i}: {w}" for w in validation.warnings])
        
        for i, validation in enumerate(video_validations):
            all_errors.extend([f"Animation Scene {i}: {e}" for e in validation.errors])
            all_warnings.extend([f"Animation Scene {i}: {w}" for w in validation.warnings])
        
        # Calculate overall success and quality
        overall_success = (
            script_status in ["VALID", "ACCEPTABLE"] and
            audio_status in ["ALL_VALID", "MOSTLY_VALID"] and
            animation_status in ["ALL_VALID", "MOSTLY_VALID"] and
            len(all_errors) == 0
        )
        
        # Calculate quality score
        script_score = script_validation.score if script_validation else 0.0
        audio_score = sum(v.score for v in audio_validations) / len(audio_validations) if audio_validations else 0.0
        animation_score = sum(v.score for v in video_validations) / len(video_validations) if video_validations else 0.0
        
        quality_score = (script_score * 0.3 + audio_score * 0.4 + animation_score * 0.3)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            script_validation, audio_validations, video_validations, generation_stats
        )
        
        # Compile detailed stats
        detailed_stats = {
            "script": script_validation.stats if script_validation else {},
            "audio": [v.stats for v in audio_validations],
            "animations": [v.stats for v in video_validations],
            "generation": generation_stats,
            "summary": {
                "total_scenes": total_scenes,
                "valid_audio_scenes": valid_audio,
                "valid_animation_scenes": valid_animations,
                "script_quality": script_score,
                "audio_quality": audio_score,
                "animation_quality": animation_score,
                "error_count": len(all_errors),
                "warning_count": len(all_warnings)
            }
        }
        
        return ContentGenerationReport(
            timestamp=timestamp,
            total_scenes=total_scenes,
            script_status=script_status,
            audio_status=audio_status,
            animation_status=animation_status,
            overall_success=overall_success,
            quality_score=quality_score,
            errors=all_errors,
            warnings=all_warnings,
            recommendations=recommendations,
            detailed_stats=detailed_stats
        )
    
    def _generate_recommendations(
        self,
        script_validation: Optional[ValidationResult],
        audio_validations: List[ValidationResult],
        video_validations: List[ValidationResult],
        generation_stats: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []
        
        # Script recommendations
        if script_validation:
            if script_validation.score < 0.5:
                recommendations.append("Consider regenerating the script with more detailed content")
            if "empty_scenes" in script_validation.stats and script_validation.stats["empty_scenes"] > 0:
                recommendations.append("Some scenes have minimal content - add more detailed narration")
            if script_validation.stats.get("word_count", 0) < 100:
                recommendations.append("Script is very short - consider adding more explanatory content")
        
        # Audio recommendations
        silent_audio_count = sum(1 for v in audio_validations if v.stats.get("silence_ratio", 0) > 0.8)
        if silent_audio_count > 0:
            recommendations.append(f"{silent_audio_count} audio files are mostly silent - check TTS generation")
        
        low_quality_audio = sum(1 for v in audio_validations if v.score < 0.5)
        if low_quality_audio > 0:
            recommendations.append(f"{low_quality_audio} audio files have quality issues - consider regenerating")
        
        # Check if TTS engines are available
        if generation_stats.get("tts_engines_available", 0) == 0:
            recommendations.append("No TTS engines available - install pyttsx3 or configure system TTS")
        
        # Animation recommendations
        small_animations = sum(1 for v in video_validations if v.stats.get("file_size_bytes", 0) < 50000)
        if small_animations > 0:
            recommendations.append(f"{small_animations} animation files are very small - check FFmpeg generation")
        
        low_quality_animations = sum(1 for v in video_validations if v.score < 0.5)
        if low_quality_animations > 0:
            recommendations.append(f"{low_quality_animations} animation files have quality issues")
        
        # Check if FFmpeg is available
        if not generation_stats.get("ffmpeg_available", False):
            recommendations.append("FFmpeg not available - install FFmpeg for animation generation")
        
        # Overall recommendations
        if len(audio_validations) != len(video_validations):
            recommendations.append("Audio and animation scene counts don't match - check synchronization")
        
        total_errors = sum(len(v.errors) for v in audio_validations + video_validations)
        if script_validation:
            total_errors += len(script_validation.errors)
        
        if total_errors > 5:
            recommendations.append("Many validation errors detected - consider regenerating all content")
        
        return recommendations
    
    def save_report(self, report: ContentGenerationReport, job_id: str) -> str:
        """Save report to file and return file path."""
        report_filename = f"content_report_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.reports_dir / report_filename
        
        # Convert report to dictionary for JSON serialization
        report_dict = asdict(report)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        return str(report_path)
    
    def print_summary_report(self, report: ContentGenerationReport) -> None:
        """Print a human-readable summary of the report."""
        print("\n" + "="*60)
        print("📊 CONTENT GENERATION REPORT")
        print("="*60)
        
        print(f"⏰ Generated: {report.timestamp}")
        print(f"🎬 Total Scenes: {report.total_scenes}")
        print(f"📝 Script Status: {report.script_status}")
        print(f"🔊 Audio Status: {report.audio_status}")
        print(f"🎥 Animation Status: {report.animation_status}")
        print(f"✅ Overall Success: {'YES' if report.overall_success else 'NO'}")
        print(f"⭐ Quality Score: {report.quality_score:.2f}/1.00")
        
        if report.errors:
            print(f"\n❌ ERRORS ({len(report.errors)}):")
            for error in report.errors[:5]:  # Show first 5 errors
                print(f"  • {error}")
            if len(report.errors) > 5:
                print(f"  ... and {len(report.errors) - 5} more errors")
        
        if report.warnings:
            print(f"\n⚠️ WARNINGS ({len(report.warnings)}):")
            for warning in report.warnings[:3]:  # Show first 3 warnings
                print(f"  • {warning}")
            if len(report.warnings) > 3:
                print(f"  ... and {len(report.warnings) - 3} more warnings")
        
        if report.recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in report.recommendations:
                print(f"  • {rec}")
        
        # Detailed stats summary
        stats = report.detailed_stats.get("summary", {})
        if stats:
            print(f"\n📈 DETAILED STATS:")
            print(f"  • Valid Audio Scenes: {stats.get('valid_audio_scenes', 0)}/{report.total_scenes}")
            print(f"  • Valid Animation Scenes: {stats.get('valid_animation_scenes', 0)}/{report.total_scenes}")
            print(f"  • Script Quality: {stats.get('script_quality', 0):.2f}")
            print(f"  • Audio Quality: {stats.get('audio_quality', 0):.2f}")
            print(f"  • Animation Quality: {stats.get('animation_quality', 0):.2f}")
        
        print("="*60)
    
    def get_status_emoji(self, status: str) -> str:
        """Get emoji representation of status."""
        status_emojis = {
            "VALID": "✅",
            "ACCEPTABLE": "⚠️",
            "INVALID": "❌",
            "MISSING": "❓",
            "ALL_VALID": "✅",
            "MOSTLY_VALID": "⚠️",
            "PARTIALLY_VALID": "🔶",
        }
        return status_emojis.get(status, "❓")


# Global content reporter instance
content_reporter = ContentReporter()