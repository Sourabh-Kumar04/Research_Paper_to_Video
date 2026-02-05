#!/usr/bin/env python3
"""
Enable Gemini-Only Mode: Disable all fallback systems
If Gemini is not available, system will fail with "system is down" message
"""

import sys
from pathlib import Path

def modify_production_video_generator():
    """Modify production_video_generator.py to be Gemini-only."""
    
    file_path = "production_video_generator.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Remove forced fallback script generation
    old_script_section = '''            # Step 2: Generate script (FORCED FALLBACK for comprehensive 20+ minute videos)
            print(f"[INFO] Job {self.job_id}: Using comprehensive fallback script (Gemini temporarily disabled for long videos)")
            script_data = self._create_fallback_script()'''
    
    new_script_section = '''            # Step 2: Generate script (GEMINI ONLY - NO FALLBACK)
            if not self.gemini_client:
                print(f"[ERROR] Job {self.job_id}: Gemini client not available - System is down")
                raise Exception("System is down: Gemini AI service is not available. Please try again later.")
            
            print(f"[INFO] Job {self.job_id}: Generating script with Gemini...")
            try:
                script_data = await self.gemini_client.generate_video_script(
                    self.paper_content, 
                    analysis, 
                    target_duration=1200  # 20 minutes
                )
                print(f"[OK] Job {self.job_id}: Gemini script generation completed")
            except Exception as e:
                print(f"[ERROR] Job {self.job_id}: Gemini script generation failed: {e}")
                raise Exception(f"System is down: Gemini AI service failed - {e}")'''
    
    content = content.replace(old_script_section, new_script_section)
    
    # 2. Remove fallback Manim code generation
    old_manim_section = '''            # If no Gemini code, create fallback Manim code and try
            print(f"    Using fallback Manim code for enhanced animations")
            fallback_code = self._create_fallback_manim_code(scene)
            scene['manim_code'] = fallback_code
            success = await self._generate_manim_video(scene, output_path)
            if success:
                return True'''
    
    new_manim_section = '''            # NO FALLBACK - Gemini required
            print(f"    No Gemini Manim code available - cannot generate video")
            return False'''
    
    content = content.replace(old_manim_section, new_manim_section)
    
    # 3. Modify Manim code generation to require Gemini
    old_manim_gen = '''            # Step 3: Generate Manim code for each scene and store in scene data
            if self.gemini_client:
                print(f"[INFO] Job {self.job_id}: Generating Manim animations with Gemini...")
                for i, scene in enumerate(scenes):
                    try:
                        manim_code = await self.gemini_client.generate_manim_code(
                            scene.get('title', f'Scene {i+1}'),
                            scene.get('visual_description', scene.get('narration', '')),
                            scene.get('duration', 10.0)
                        )
                        
                        # Store the Manim code in the scene for later use
                        scene['manim_code'] = manim_code
                        
                        # Save Manim code for reference
                        manim_file = self.output_dir / f"manim_scene_{i}_{scene.get('id', 'scene')}.py"
                        with open(manim_file, 'w') as f:
                            f.write(manim_code)
                        
                        print(f"[OK] Job {self.job_id}: Generated Manim code for scene {i+1}: {scene.get('title', 'Untitled')}")
                    except Exception as e:
                        print(f"[WARN] Job {self.job_id}: Manim generation failed for scene {i+1}: {e}")
                        scene['manim_code'] = None
            else:
                print(f"[WARN] Job {self.job_id}: Skipping Manim generation (no Gemini)")
                # Ensure all scenes have manim_code field
                for scene in scenes:
                    scene['manim_code'] = None'''
    
    new_manim_gen = '''            # Step 3: Generate Manim code for each scene (GEMINI REQUIRED)
            if not self.gemini_client:
                print(f"[ERROR] Job {self.job_id}: Cannot generate Manim code without Gemini")
                raise Exception("System is down: Gemini AI service required for video generation")
            
            print(f"[INFO] Job {self.job_id}: Generating Manim animations with Gemini...")
            failed_scenes = []
            
            for i, scene in enumerate(scenes):
                try:
                    manim_code = await self.gemini_client.generate_manim_code(
                        scene.get('title', f'Scene {i+1}'),
                        scene.get('visual_description', scene.get('narration', '')),
                        scene.get('duration', 10.0)
                    )
                    
                    if not manim_code or manim_code.strip() == "":
                        print(f"[ERROR] Job {self.job_id}: Empty Manim code for scene {i+1}")
                        failed_scenes.append(i+1)
                        continue
                    
                    # Store the Manim code in the scene for later use
                    scene['manim_code'] = manim_code
                    
                    # Save Manim code for reference
                    manim_file = self.output_dir / f"manim_scene_{i}_{scene.get('id', 'scene')}.py"
                    with open(manim_file, 'w') as f:
                        f.write(manim_code)
                    
                    print(f"[OK] Job {self.job_id}: Generated Manim code for scene {i+1}: {scene.get('title', 'Untitled')}")
                except Exception as e:
                    print(f"[ERROR] Job {self.job_id}: Manim generation failed for scene {i+1}: {e}")
                    failed_scenes.append(i+1)
            
            # If any scenes failed, abort the entire job
            if failed_scenes:
                print(f"[ERROR] Job {self.job_id}: Failed to generate Manim code for scenes: {failed_scenes}")
                raise Exception(f"System is down: Gemini AI failed to generate Manim code for {len(failed_scenes)} scenes")'''
    
    content = content.replace(old_manim_gen, new_manim_gen)
    
    # Write the modified content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Modified production_video_generator.py for Gemini-only mode")

def modify_gemini_client():
    """Modify Gemini client to remove fallback code generation."""
    
    file_path = "src/llm/gemini_client.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove fallback calls in generate_manim_code
    old_fallback_calls = [
        'return self._create_fallback_manim_code(scene_title, scene_description)',
        'return self._create_fallback_manim_code("Scene", "Animation")'
    ]
    
    for old_call in old_fallback_calls:
        new_call = 'raise Exception("Gemini AI service failed - no fallback available")'
        content = content.replace(old_call, new_call)
    
    # Write the modified content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Modified src/llm/gemini_client.py to remove fallback calls")

def create_system_status_check():
    """Create a system status check script."""
    
    status_check = '''#!/usr/bin/env python3
"""
System Status Check - Verify Gemini is available
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def check_system_status():
    """Check if system is operational (Gemini available)."""
    
    print("🔍 CHECKING SYSTEM STATUS")
    print("=" * 50)
    
    # Check Gemini API key
    gemini_api_key = os.getenv('RASO_GOOGLE_API_KEY')
    if not gemini_api_key:
        print("❌ SYSTEM DOWN: Gemini API key not configured")
        return False
    
    if not (gemini_api_key.startswith('AIza') or len(gemini_api_key) > 30):
        print("❌ SYSTEM DOWN: Invalid Gemini API key format")
        return False
    
    print(f"✅ Gemini API key configured: {gemini_api_key[:10]}...")
    
    # Try to import and initialize Gemini client
    try:
        from llm.gemini_client import GeminiClient, get_gemini_client
        client = get_gemini_client()
        print("✅ Gemini client initialized successfully")
        return True
    except Exception as e:
        print(f"❌ SYSTEM DOWN: Gemini client failed to initialize: {e}")
        return False

if __name__ == "__main__":
    is_operational = check_system_status()
    
    print("\\n" + "=" * 50)
    if is_operational:
        print("✅ SYSTEM OPERATIONAL: Gemini AI service is available")
        print("🎬 Video generation will use Gemini-generated Manim code")
    else:
        print("❌ SYSTEM DOWN: Gemini AI service is not available")
        print("🚫 Video generation is disabled until Gemini is restored")
    
    sys.exit(0 if is_operational else 1)
'''
    
    with open("check_system_status.py", 'w', encoding='utf-8') as f:
        f.write(status_check)
    
    print("✅ Created check_system_status.py")

def main():
    """Enable Gemini-only mode by removing all fallback systems."""
    
    print("🔧 ENABLING GEMINI-ONLY MODE")
    print("=" * 60)
    print("This will disable ALL fallback systems.")
    print("If Gemini is not available, video generation will fail with 'system is down' message.")
    print()
    
    try:
        # Step 1: Modify production video generator
        modify_production_video_generator()
        
        # Step 2: Modify Gemini client
        modify_gemini_client()
        
        # Step 3: Create system status check
        create_system_status_check()
        
        print()
        print("✅ GEMINI-ONLY MODE ENABLED")
        print("=" * 50)
        print("Changes made:")
        print("1. ✅ Removed forced fallback script generation")
        print("2. ✅ Removed fallback Manim code generation")
        print("3. ✅ Added Gemini requirement checks")
        print("4. ✅ Added proper error messages for system down")
        print("5. ✅ Created system status check script")
        print()
        print("🎬 System will now ONLY use Gemini-generated Manim code")
        print("🚫 No fallback systems will be used")
        print("❌ If Gemini fails, system will show 'system is down' message")
        print()
        print("To check system status, run: python check_system_status.py")
        
    except Exception as e:
        print(f"❌ ERROR: Failed to enable Gemini-only mode: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()