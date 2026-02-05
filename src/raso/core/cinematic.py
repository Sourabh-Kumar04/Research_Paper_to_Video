"""
Backend API endpoints for cinematic features.
Provides REST API for cinematic settings management, visual descriptions, and scene analysis.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
import asyncio
import logging
from datetime import datetime

from ..models.cinematic_api import (
    CinematicSettingsRequest, CinematicSettingsResponse,
    CinematicProfileRequest, CinematicProfileResponse,
    VisualDescriptionRequest, VisualDescriptionResponse,
    SceneAnalysisRequest, SceneAnalysisResponse,
    PreviewRequest, PreviewResponse,
    ErrorResponse
)
from src.cinematic.settings_manager import get_settings_manager
from src.llm.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/cinematic", tags=["cinematic"])

# Dependencies
def get_cinematic_manager():
    """Get cinematic settings manager instance."""
    return get_settings_manager()

def get_gemini_client():
    """Get Gemini client instance."""
    return GeminiClient()


@router.get("/settings/profiles", response_model=List[CinematicProfileResponse])
async def list_profiles(
    user_id: str = "default",
    manager = Depends(get_cinematic_manager)
):
    """List all cinematic profiles for a user."""
    try:
        profiles = await manager.get_user_profiles(user_id)
        
        response_profiles = []
        for profile in profiles:
            response_profiles.append(CinematicProfileResponse(
                id=profile["id"],
                name=profile["name"],
                description=profile["description"],
                settings=profile["settings"],
                user_id=profile["user_id"],
                is_default=profile["is_default"],
                is_system=profile["is_system"],
                created_at=profile["created_at"],
                last_used=profile["last_used"],
                usage_count=profile["usage_count"],
                validation=profile["validation"]
            ))
        
        return response_profiles
        
    except Exception as e:
        logger.error(f"Error listing profiles for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/profiles", response_model=Dict[str, str])
async def create_profile(
    request: CinematicProfileRequest,
    manager = Depends(get_cinematic_manager)
):
    """Create a new cinematic profile."""
    try:
        from src.cinematic.models import CinematicSettingsModel
        
        # Convert settings dict to model
        settings = CinematicSettingsModel.from_dict(request.settings)
        
        # Create profile
        profile_id = await manager.save_profile(
            request.name,
            settings,
            request.user_id,
            request.description,
            request.set_as_default
        )
        
        return {"profile_id": profile_id, "status": "created"}
        
    except ValueError as e:
        logger.warning(f"Invalid profile data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings/profiles/{profile_id}", response_model=CinematicSettingsResponse)
async def get_profile(
    profile_id: str,
    user_id: str = "default",
    manager = Depends(get_cinematic_manager)
):
    """Get a specific cinematic profile."""
    try:
        settings = await manager.load_profile(profile_id, user_id)
        
        if settings is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return CinematicSettingsResponse(
            settings=settings.to_dict(),
            profile_id=profile_id,
            user_id=user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings/profiles/{profile_id}", response_model=Dict[str, str])
async def update_profile(
    profile_id: str,
    request: CinematicProfileRequest,
    manager = Depends(get_cinematic_manager)
):
    """Update an existing cinematic profile."""
    try:
        from src.cinematic.models import CinematicSettingsModel
        
        # Check if profile exists
        existing_settings = await manager.load_profile(profile_id, request.user_id)
        if existing_settings is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Delete old profile
        await manager.delete_profile(profile_id, request.user_id)
        
        # Create updated profile with same ID
        settings = CinematicSettingsModel.from_dict(request.settings)
        new_profile_id = await manager.save_profile(
            request.name,
            settings,
            request.user_id,
            request.description,
            request.set_as_default
        )
        
        return {"profile_id": new_profile_id, "status": "updated"}
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid profile data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/settings/profiles/{profile_id}", response_model=Dict[str, str])
async def delete_profile(
    profile_id: str,
    user_id: str = "default",
    manager = Depends(get_cinematic_manager)
):
    """Delete a cinematic profile."""
    try:
        success = await manager.delete_profile(profile_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found or cannot be deleted")
        
        return {"profile_id": profile_id, "status": "deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings/default", response_model=CinematicSettingsResponse)
async def get_default_settings(
    user_id: str = "default",
    manager = Depends(get_cinematic_manager)
):
    """Get default cinematic settings for a user."""
    try:
        settings = await manager.get_default_profile(user_id)
        
        return CinematicSettingsResponse(
            settings=settings.to_dict(),
            profile_id="default",
            user_id=user_id
        )
        
    except Exception as e:
        logger.error(f"Error getting default settings for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/validate", response_model=Dict[str, Any])
async def validate_settings(
    request: CinematicSettingsRequest,
    manager = Depends(get_cinematic_manager)
):
    """Validate cinematic settings."""
    try:
        from src.cinematic.models import CinematicSettingsModel
        
        settings = CinematicSettingsModel.from_dict(request.settings)
        validation = await manager.validate_settings(settings)
        
        return validation
        
    except Exception as e:
        logger.error(f"Error validating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visual-description", response_model=VisualDescriptionResponse)
async def generate_visual_description(
    request: VisualDescriptionRequest,
    background_tasks: BackgroundTasks,
    gemini_client = Depends(get_gemini_client),
    manager = Depends(get_cinematic_manager)
):
    """Generate AI-powered visual description for content."""
    try:
        # Generate description using Gemini
        description = await gemini_client.generate_detailed_visual_description(
            request.content,
            request.scene_context or {},
            request.style_preferences or {}
        )
        
        # Analyze scene for cinematic recommendations
        scene_analysis = await gemini_client.analyze_scene_for_cinematics(
            request.content,
            description
        )
        
        # Get cinematic recommendations
        recommendations = await manager.get_recommendations(scene_analysis)
        
        # Generate suggestions
        suggestions = await gemini_client.suggest_cinematic_improvements(
            request.content,
            description,
            recommendations.to_dict()
        )
        
        # Save visual description in background
        background_tasks.add_task(
            manager.save_visual_description,
            request.scene_id,
            request.content,
            description,
            "gemini",
            recommendations.to_dict(),
            scene_analysis,
            suggestions,
            0.9  # High confidence for Gemini-generated content
        )
        
        return VisualDescriptionResponse(
            scene_id=request.scene_id,
            description=description,
            scene_analysis=scene_analysis,
            cinematic_recommendations=recommendations.to_dict(),
            suggestions=suggestions,
            confidence=0.9,
            generated_by="gemini"
        )
        
    except Exception as e:
        logger.error(f"Error generating visual description: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visual-description/{scene_id}", response_model=VisualDescriptionResponse)
async def get_visual_description(
    scene_id: str,
    manager = Depends(get_cinematic_manager)
):
    """Get saved visual description for a scene."""
    try:
        description = await manager.load_visual_description(scene_id)
        
        if description is None:
            raise HTTPException(status_code=404, detail="Visual description not found")
        
        return VisualDescriptionResponse(
            scene_id=description.scene_id,
            description=description.description,
            scene_analysis=description.scene_analysis,
            cinematic_recommendations=description.cinematic_settings,
            suggestions=description.suggestions,
            confidence=description.confidence,
            generated_by=description.generated_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting visual description for scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scene-analysis", response_model=SceneAnalysisResponse)
async def analyze_scene(
    request: SceneAnalysisRequest,
    gemini_client = Depends(get_gemini_client),
    manager = Depends(get_cinematic_manager)
):
    """Analyze scene content for cinematic recommendations."""
    try:
        # Analyze scene using Gemini
        analysis = await gemini_client.analyze_scene_for_cinematics(
            request.content,
            request.existing_description
        )
        
        # Get cinematic recommendations based on analysis
        recommendations = await manager.get_recommendations(analysis)
        
        return SceneAnalysisResponse(
            scene_analysis=analysis,
            cinematic_recommendations=recommendations.to_dict(),
            confidence=analysis.get("confidence", 0.8)
        )
        
    except Exception as e:
        logger.error(f"Error analyzing scene: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview", response_model=PreviewResponse)
async def generate_preview(
    request: PreviewRequest,
    background_tasks: BackgroundTasks
):
    """Generate preview for cinematic settings."""
    try:
        from src.cinematic.models import CinematicSettingsModel
        
        # Convert settings
        settings = CinematicSettingsModel.from_dict(request.settings)
        
        # Validate settings
        validation = settings.validate()
        if validation:
            raise HTTPException(status_code=400, detail=f"Invalid settings: {validation}")
        
        # Generate preview (placeholder implementation)
        preview_data = {
            "preview_url": f"/api/v1/cinematic/preview/{request.scene_id}/render",
            "thumbnail_url": f"/api/v1/cinematic/preview/{request.scene_id}/thumbnail",
            "estimated_size": "2.5 MB",
            "estimated_duration": "15 seconds",
            "processing_time": "3-5 seconds",
            "effects_applied": _get_effects_summary(settings)
        }
        
        # Add background task for actual preview generation
        background_tasks.add_task(
            _generate_preview_background,
            request.scene_id,
            settings,
            request.content
        )
        
        return PreviewResponse(
            scene_id=request.scene_id,
            preview_data=preview_data,
            status="generating",
            estimated_completion=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/export/{profile_id}")
async def export_profile(
    profile_id: str,
    user_id: str = "default",
    manager = Depends(get_cinematic_manager)
):
    """Export a cinematic profile."""
    try:
        exported_data = await manager.export_profile(profile_id, user_id)
        
        if exported_data is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return JSONResponse(
            content={"exported_data": exported_data},
            headers={"Content-Disposition": f"attachment; filename=profile_{profile_id}.json"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/import", response_model=Dict[str, str])
async def import_profile(
    profile_data: str,
    user_id: str = "default",
    manager = Depends(get_cinematic_manager)
):
    """Import a cinematic profile."""
    try:
        profile_id = await manager.import_profile(profile_data, user_id)
        
        if profile_id is None:
            raise HTTPException(status_code=400, detail="Invalid profile data")
        
        return {"profile_id": profile_id, "status": "imported"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
def _get_effects_summary(settings) -> List[str]:
    """Get summary of effects that will be applied."""
    effects = []
    
    if settings.camera_movements.enabled:
        effects.append(f"Camera movement ({settings.camera_movements.intensity}% intensity)")
    
    if settings.color_grading.enabled:
        effects.append(f"Color grading ({settings.color_grading.film_emulation.value})")
    
    if settings.sound_design.enabled:
        effects.append("Sound design enhancement")
    
    if settings.advanced_compositing.enabled:
        compositing_effects = []
        if settings.advanced_compositing.film_grain:
            compositing_effects.append("film grain")
        if settings.advanced_compositing.dynamic_lighting:
            compositing_effects.append("dynamic lighting")
        if settings.advanced_compositing.depth_of_field:
            compositing_effects.append("depth of field")
        if settings.advanced_compositing.motion_blur:
            compositing_effects.append("motion blur")
        
        if compositing_effects:
            effects.append(f"Advanced compositing ({', '.join(compositing_effects)})")
    
    return effects


async def _generate_preview_background(scene_id: str, settings, content: str):
    """Background task for generating preview."""
    try:
        # Placeholder for actual preview generation
        logger.info(f"Generating preview for scene {scene_id} with settings")
        
        # Simulate processing time
        await asyncio.sleep(2)
        
        # In real implementation, this would:
        # 1. Apply cinematic settings to content
        # 2. Generate thumbnail
        # 3. Create preview video
        # 4. Store results
        
        logger.info(f"Preview generation completed for scene {scene_id}")
        
    except Exception as e:
        logger.error(f"Error in background preview generation for scene {scene_id}: {e}")


# YouTube and Social Media Optimization Endpoints

@router.post("/youtube-optimize", response_model=Dict[str, Any])
async def optimize_for_youtube(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    gemini_client = Depends(get_gemini_client)
):
    """Optimize video content for YouTube platform."""
    try:
        from src.cinematic.youtube_optimizer import YouTubeOptimizer
        
        optimizer = YouTubeOptimizer()
        
        # Extract request data
        video_metadata = request.get("video_metadata", {})
        content = request.get("content", "")
        optimization_settings = request.get("optimization_settings", {})
        
        # Optimize encoding parameters
        encoding_params = await optimizer.optimize_encoding_parameters(
            video_metadata,
            optimization_settings
        )
        
        # Generate SEO metadata using Gemini
        seo_metadata = await gemini_client.generate_youtube_seo_metadata(
            content,
            video_metadata.get("title", ""),
            video_metadata.get("description", "")
        )
        
        # Generate thumbnail suggestions
        thumbnail_suggestions = await optimizer.generate_thumbnail_suggestions(
            content,
            video_metadata
        )
        
        # Generate chapter markers
        chapter_markers = await optimizer.generate_chapter_markers(
            content,
            video_metadata.get("duration", 0)
        )
        
        # Create intro/outro sequences
        intro_outro = await optimizer.create_intro_outro_sequences(
            optimization_settings.get("branding", {}),
            video_metadata
        )
        
        return {
            "optimization_id": f"yt_opt_{datetime.utcnow().timestamp()}",
            "encoding_parameters": encoding_params,
            "seo_metadata": seo_metadata,
            "thumbnail_suggestions": thumbnail_suggestions,
            "chapter_markers": chapter_markers,
            "intro_outro_sequences": intro_outro,
            "estimated_upload_time": "5-10 minutes",
            "compliance_status": "youtube_ready"
        }
        
    except Exception as e:
        logger.error(f"Error optimizing for YouTube: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-platform-export", response_model=Dict[str, Any])
async def export_for_multiple_platforms(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Export video content optimized for multiple social media platforms."""
    try:
        from src.cinematic.social_media_adapter import SocialMediaAdapter
        
        adapter = SocialMediaAdapter()
        
        # Extract request data
        video_metadata = request.get("video_metadata", {})
        content = request.get("content", "")
        target_platforms = request.get("target_platforms", ["instagram", "tiktok", "linkedin"])
        adaptation_settings = request.get("adaptation_settings", {})
        
        platform_exports = {}
        
        for platform in target_platforms:
            # Adapt content for platform
            platform_adaptation = await adapter.adapt_for_platform(
                platform,
                video_metadata,
                content,
                adaptation_settings
            )
            
            # Optimize file size and compression
            compression_settings = await adapter.optimize_file_size(
                platform,
                video_metadata,
                adaptation_settings.get("quality_preference", "balanced")
            )
            
            # Generate platform-specific metadata
            platform_metadata = await adapter.generate_platform_metadata(
                platform,
                content,
                video_metadata
            )
            
            platform_exports[platform] = {
                "adaptation_settings": platform_adaptation,
                "compression_settings": compression_settings,
                "metadata": platform_metadata,
                "estimated_file_size": compression_settings.get("estimated_size", "Unknown"),
                "aspect_ratio": platform_adaptation.get("aspect_ratio", "16:9"),
                "duration_limit": platform_adaptation.get("max_duration", "No limit")
            }
        
        # Add background task for actual export processing
        background_tasks.add_task(
            _process_multi_platform_export,
            platform_exports,
            video_metadata,
            content
        )
        
        return {
            "export_id": f"multi_export_{datetime.utcnow().timestamp()}",
            "platform_exports": platform_exports,
            "total_platforms": len(target_platforms),
            "estimated_processing_time": f"{len(target_platforms) * 2}-{len(target_platforms) * 4} minutes",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error in multi-platform export: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/accessibility-analyze", response_model=Dict[str, Any])
async def analyze_accessibility_compliance(
    request: Dict[str, Any],
    gemini_client = Depends(get_gemini_client)
):
    """Analyze video content for accessibility compliance."""
    try:
        from src.cinematic.accessibility_manager import AccessibilityManager
        
        accessibility_manager = AccessibilityManager()
        
        # Extract request data
        video_metadata = request.get("video_metadata", {})
        cinematic_settings = request.get("cinematic_settings", {})
        target_wcag_level = request.get("target_wcag_level", "AA")
        
        # Analyze color contrast
        color_contrast_results = await accessibility_manager.analyze_color_contrast(
            cinematic_settings.get("color_grading", {}),
            target_wcag_level
        )
        
        # Analyze flashing content
        flashing_content_result = await accessibility_manager.analyze_flashing_content(
            cinematic_settings.get("camera_movements", {}),
            cinematic_settings.get("advanced_compositing", {})
        )
        
        # Generate captions using speech recognition
        caption_segments = await accessibility_manager.generate_captions(
            video_metadata.get("transcript", ""),
            video_metadata.get("duration", 0)
        )
        
        # Generate audio descriptions using Gemini
        audio_descriptions = await gemini_client.generate_audio_descriptions(
            video_metadata.get("content", ""),
            video_metadata.get("title", ""),
            cinematic_settings
        )
        
        # Analyze language clarity
        language_clarity_score = await accessibility_manager.analyze_language_clarity(
            video_metadata.get("transcript", ""),
            video_metadata.get("description", "")
        )
        
        # Generate accessibility issues
        issues = await accessibility_manager.identify_accessibility_issues(
            color_contrast_results,
            flashing_content_result,
            caption_segments,
            audio_descriptions,
            language_clarity_score,
            target_wcag_level
        )
        
        # Calculate compliance score
        compliance_score = await accessibility_manager.calculate_compliance_score(
            issues,
            target_wcag_level
        )
        
        # Generate recommendations
        recommendations = await accessibility_manager.generate_accessibility_recommendations(
            issues,
            target_wcag_level,
            cinematic_settings
        )
        
        return {
            "analysis_id": f"acc_analysis_{datetime.utcnow().timestamp()}",
            "wcag_level": target_wcag_level,
            "overall_compliance": compliance_score >= 80,
            "compliance_score": compliance_score,
            "color_contrast_results": color_contrast_results,
            "flashing_content_result": flashing_content_result,
            "caption_segments": caption_segments,
            "audio_descriptions": audio_descriptions,
            "language_clarity_score": language_clarity_score,
            "issues": issues,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in accessibility analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thumbnail-generate/{content_id}", response_model=Dict[str, Any])
async def generate_thumbnail(
    content_id: str,
    request: Dict[str, Any] = None,
    gemini_client = Depends(get_gemini_client)
):
    """Generate engaging thumbnail for video content."""
    try:
        from src.cinematic.youtube_optimizer import YouTubeOptimizer
        
        optimizer = YouTubeOptimizer()
        
        # Extract content and metadata
        content = request.get("content", "") if request else ""
        video_metadata = request.get("video_metadata", {}) if request else {}
        thumbnail_style = request.get("thumbnail_style", "engaging") if request else "engaging"
        
        # Generate thumbnail suggestions using Gemini
        thumbnail_suggestions = await gemini_client.generate_thumbnail_suggestions(
            content,
            video_metadata.get("title", ""),
            thumbnail_style
        )
        
        # Generate thumbnail images
        thumbnail_images = await optimizer.generate_thumbnail_images(
            thumbnail_suggestions,
            video_metadata
        )
        
        return {
            "content_id": content_id,
            "thumbnail_suggestions": thumbnail_suggestions,
            "thumbnail_images": thumbnail_images,
            "recommended_style": thumbnail_style,
            "generation_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating thumbnail for content {content_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seo-metadata", response_model=Dict[str, Any])
async def generate_seo_metadata(
    request: Dict[str, Any],
    gemini_client = Depends(get_gemini_client)
):
    """Generate SEO-optimized metadata for video content."""
    try:
        # Extract request data
        content = request.get("content", "")
        title = request.get("title", "")
        description = request.get("description", "")
        target_keywords = request.get("target_keywords", [])
        platform = request.get("platform", "youtube")
        
        # Generate SEO metadata using Gemini
        seo_metadata = await gemini_client.generate_seo_metadata(
            content,
            title,
            description,
            target_keywords,
            platform
        )
        
        # Generate hashtags and tags
        hashtags = await gemini_client.generate_hashtags(
            content,
            title,
            platform
        )
        
        # Generate optimized title variations
        title_variations = await gemini_client.generate_title_variations(
            title,
            content,
            platform
        )
        
        # Generate description variations
        description_variations = await gemini_client.generate_description_variations(
            description,
            content,
            platform
        )
        
        return {
            "seo_metadata": seo_metadata,
            "hashtags": hashtags,
            "title_variations": title_variations,
            "description_variations": description_variations,
            "target_platform": platform,
            "generation_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating SEO metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/platform-compliance", response_model=Dict[str, Any])
async def validate_platform_compliance(
    request: Dict[str, Any]
):
    """Validate content compliance with platform requirements."""
    try:
        from src.cinematic.social_media_adapter import SocialMediaAdapter
        
        adapter = SocialMediaAdapter()
        
        # Extract request data
        platform = request.get("platform", "youtube")
        video_metadata = request.get("video_metadata", {})
        content_settings = request.get("content_settings", {})
        
        # Validate platform compliance
        compliance_result = await adapter.validate_platform_compliance(
            platform,
            video_metadata,
            content_settings
        )
        
        # Check file size limits
        file_size_compliance = await adapter.check_file_size_limits(
            platform,
            video_metadata.get("estimated_file_size", 0)
        )
        
        # Check duration limits
        duration_compliance = await adapter.check_duration_limits(
            platform,
            video_metadata.get("duration", 0)
        )
        
        # Check aspect ratio compliance
        aspect_ratio_compliance = await adapter.check_aspect_ratio_compliance(
            platform,
            content_settings.get("aspect_ratio", "16:9")
        )
        
        return {
            "platform": platform,
            "overall_compliance": compliance_result.get("compliant", False),
            "compliance_details": compliance_result,
            "file_size_compliance": file_size_compliance,
            "duration_compliance": duration_compliance,
            "aspect_ratio_compliance": aspect_ratio_compliance,
            "validation_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error validating platform compliance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task helpers

async def _process_multi_platform_export(platform_exports: Dict, video_metadata: Dict, content: str):
    """Background task for processing multi-platform exports."""
    try:
        logger.info(f"Processing multi-platform export for {len(platform_exports)} platforms")
        
        # Simulate processing time
        await asyncio.sleep(5)
        
        # In real implementation, this would:
        # 1. Apply platform-specific adaptations
        # 2. Compress and optimize for each platform
        # 3. Generate platform-specific metadata
        # 4. Store export results
        
        logger.info("Multi-platform export processing completed")
        
    except Exception as e:
        logger.error(f"Error in background multi-platform export processing: {e}")


# Error handlers - These should be registered on the FastAPI app instance, not the router
# They are kept here for reference but should be moved to the main app configuration

def register_error_handlers(app):
    """Register error handlers on the FastAPI app instance."""
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        """Handle validation errors."""
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="validation_error",
                message=str(exc),
                details={"type": "ValueError"}
            ).dict()
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request, exc):
        """Handle general errors."""
        from fastapi.responses import JSONResponse
        logger.error(f"Unhandled error in cinematic API: {exc}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="internal_error",
                message="An internal error occurred",
                details={"type": type(exc).__name__}
            ).dict()
        )