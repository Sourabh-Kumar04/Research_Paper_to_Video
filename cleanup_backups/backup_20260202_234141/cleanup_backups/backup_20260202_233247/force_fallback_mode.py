#!/usr/bin/env python3
"""
Force the system to use fallback mode to get comprehensive 20+ minute videos
"""

def force_fallback_mode():
    """Temporarily disable Gemini to force fallback mode."""
    
    print("🔧 Forcing fallback mode for comprehensive videos...")
    
    # Read the production video generator
    with open('production_video_generator.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and comment out the Gemini usage in the generate_video method
    # This will force it to always use the fallback script
    
    # Replace the Gemini script generation with immediate fallback
    old_gemini_section = '''            # Step 2: Generate script (Gemini or fallback)
            if self.gemini_client:
                print(f"[INFO] Job {self.job_id}: Generating script with Gemini...")
                try:
                    script_data = await self.gemini_client.generate_script(
                        analysis.get('title', self.paper_content),
                        self.paper_content,
                        "title"
                    )
                    print(f"[OK] Job {self.job_id}: Gemini generated script with {len(script_data.get('scenes', []))} scenes")
                except Exception as e:
                    print(f"[WARN] Job {self.job_id}: Gemini script generation failed: {e}, using fallback")
                    script_data = self._create_fallback_script()
            else:
                print(f"[INFO] Job {self.job_id}: Using fallback script generation")
                script_data = self._create_fallback_script()'''
    
    new_fallback_section = '''            # Step 2: Generate script (FORCED FALLBACK for comprehensive videos)
            print(f"[INFO] Job {self.job_id}: Using comprehensive fallback script generation (Gemini temporarily disabled)")
            script_data = self._create_fallback_script()'''
    
    # Apply the replacement
    if old_gemini_section in content:
        content = content.replace(old_gemini_section, new_fallback_section)
        print("✅ Successfully forced fallback mode")
    else:
        print("⚠️ Could not find exact Gemini section, trying alternative approach...")
        
        # Alternative approach - just replace the Gemini check
        content = content.replace(
            'if self.gemini_client:',
            'if False:  # Temporarily disabled for comprehensive videos'
        )
        print("✅ Applied alternative fallback forcing")
    
    # Write the modified content back
    with open('production_video_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fallback mode forced! Now all videos will be 20+ minutes comprehensive format.")
    print("📝 To re-enable Gemini later, change 'if False:' back to 'if self.gemini_client:'")
    return True

if __name__ == "__main__":
    success = force_fallback_mode()
    if success:
        print("✅ Fallback mode activation completed!")
        print("🎬 Generate a video now - it will be 20+ minutes comprehensive format!")
    else:
        print("❌ Failed to force fallback mode")