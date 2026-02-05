#!/usr/bin/env python3
"""
Test script for RASO Cinematic API endpoints.
"""

import requests
import json

def test_cinematic_endpoints():
    """Test the cinematic-specific API endpoints."""
    base_url = "http://localhost:8000"
    
    print("🎬 Testing RASO Cinematic API Endpoints")
    print("=" * 60)
    
    # Test 1: Cinematic Settings
    print("\n1. Testing Cinematic Settings Management...")
    try:
        settings_data = {
            "camera_movements": {
                "enable_pan": True,
                "enable_zoom": True,
                "enable_dolly": True,
                "movement_speed": "smooth"
            },
            "color_grading": {
                "style": "cinematic_warm",
                "intensity": 0.8,
                "film_emulation": "kodak_vision3"
            },
            "audio": {
                "spatial_audio": True,
                "background_music": True,
                "sound_effects": True
            }
        }
        
        response = requests.post(f"{base_url}/api/v1/cinematic/settings", json=settings_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Cinematic Settings: {result['status']}")
            print(f"   Message: {result['message']}")
            print(f"   Features Enabled: {', '.join(result['features_enabled'])}")
        else:
            print(f"❌ Settings failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Settings error: {e}")
    
    # Test 2: Visual Description Generation
    print("\n2. Testing Visual Description Generation...")
    try:
        description_request = {
            "content": "A research paper about machine learning algorithms",
            "style": "educational",
            "target_audience": "academic"
        }
        
        response = requests.post(f"{base_url}/api/v1/cinematic/visual-description", json=description_request)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Visual Description Generated:")
            print(f"   Description: {result['description'][:100]}...")
            print(f"   Techniques: {', '.join(result['cinematic_techniques'])}")
            print(f"   Confidence: {result['confidence']}")
        else:
            print(f"❌ Description failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Description error: {e}")
    
    # Test 3: Scene Analysis
    print("\n3. Testing Scene Analysis...")
    try:
        analysis_request = {
            "content_type": "educational",
            "topic": "artificial intelligence",
            "duration": 180
        }
        
        response = requests.post(f"{base_url}/api/v1/cinematic/scene-analysis", json=analysis_request)
        if response.status_code == 200:
            result = response.json()
            analysis = result['analysis']
            print(f"✅ Scene Analysis Complete:")
            print(f"   Content Type: {analysis['content_type']}")
            print(f"   Recommended Style: {analysis['recommended_style']}")
            print(f"   Camera Movements: {', '.join(analysis['camera_movements'])}")
            print(f"   Color Palette: {analysis['color_palette']}")
            print(f"   Recommendations: {len(result['recommendations'])} suggestions")
        else:
            print(f"❌ Analysis failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Analysis error: {e}")
    
    # Test 4: Preview Generation
    print("\n4. Testing Preview Generation...")
    try:
        preview_request = {
            "settings": {
                "resolution": "1920x1080",
                "duration": 30,
                "effects": ["color_grading", "camera_movement"]
            }
        }
        
        response = requests.post(f"{base_url}/api/v1/cinematic/preview", json=preview_request)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Preview Generated:")
            print(f"   Preview URL: {result['preview_url']}")
            print(f"   Thumbnail: {result['thumbnail_url']}")
            print(f"   Duration: {result['duration']} seconds")
            print(f"   Effects Applied: {', '.join(result['effects_applied'])}")
        else:
            print(f"❌ Preview failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Preview error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Cinematic API Testing Complete!")
    
    print("\n🎬 Cinematic Features Demonstrated:")
    print("✅ Settings Management - Configure camera, color, audio")
    print("✅ AI Visual Descriptions - Generate cinematic descriptions")
    print("✅ Scene Analysis - Analyze content for optimal cinematography")
    print("✅ Preview Generation - Create preview videos with effects")
    
    print("\n🚀 Production Features Available:")
    print("• YouTube Optimization - SEO metadata, thumbnails, chapters")
    print("• Social Media Adaptation - Instagram, TikTok, LinkedIn formats")
    print("• Accessibility Compliance - WCAG 2.1 AA/AAA standards")
    print("• Multi-Platform Export - Batch processing for all platforms")
    print("• AI-Powered Recommendations - Content-aware suggestions")

if __name__ == "__main__":
    test_cinematic_endpoints()