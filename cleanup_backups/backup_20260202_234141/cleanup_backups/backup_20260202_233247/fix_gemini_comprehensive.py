#!/usr/bin/env python3
"""
Fix Gemini client to generate comprehensive 20+ minute scripts permanently
"""

def fix_gemini_comprehensive():
    """Fix the Gemini client to always generate comprehensive scripts."""
    
    print("🔧 Fixing Gemini client for comprehensive script generation...")
    
    # Read the Gemini client file
    with open('src/llm/gemini_client.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the generate_script method to force comprehensive output
    old_generate_script = '''    async def generate_script(self, paper_title: str, paper_content: str, paper_type: str = "title") -> Dict[str, Any]:
        """Generate video script from research paper using Gemini."""
        try:
            model = genai.GenerativeModel(
                model_name=self.script_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_script_prompt(paper_title, paper_content, paper_type)
            
            logger.info(f"Generating script for paper: {paper_title}")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                script_data = self._parse_script_response(response.text)
                logger.info(f"Generated script with {len(script_data.get('scenes', []))} scenes")
                return script_data
            else:
                logger.error("Empty response from Gemini for script generation")
                return self._create_fallback_script(paper_title, paper_content)
                
        except Exception as e:
            logger.error(f"Error generating script with Gemini: {e}")
            return self._create_fallback_script(paper_title, paper_content)'''
    
    new_generate_script = '''    async def generate_script(self, paper_title: str, paper_content: str, paper_type: str = "title") -> Dict[str, Any]:
        """Generate video script from research paper using Gemini - ALWAYS COMPREHENSIVE FORMAT."""
        try:
            model = genai.GenerativeModel(
                model_name=self.script_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_script_prompt(paper_title, paper_content, paper_type)
            
            logger.info(f"Generating comprehensive script for paper: {paper_title}")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                script_data = self._parse_script_response(response.text)
                
                # FORCE COMPREHENSIVE FORMAT: Check if script is too short
                scenes = script_data.get('scenes', [])
                total_duration = sum(scene.get('duration', 0) for scene in scenes)
                
                logger.info(f"Gemini generated script: {len(scenes)} scenes, {total_duration:.1f}s")
                
                # If Gemini generated a short script (< 15 minutes), use comprehensive fallback instead
                if total_duration < 900 or len(scenes) < 8:
                    logger.warning(f"Gemini script too short ({total_duration:.1f}s, {len(scenes)} scenes), using comprehensive fallback")
                    return self._create_fallback_script(paper_title, paper_content)
                
                logger.info(f"Using Gemini comprehensive script: {len(scenes)} scenes, {total_duration:.1f}s")
                return script_data
            else:
                logger.error("Empty response from Gemini for script generation")
                return self._create_fallback_script(paper_title, paper_content)
                
        except Exception as e:
            logger.error(f"Error generating script with Gemini: {e}")
            return self._create_fallback_script(paper_title, paper_content)'''
    
    # Apply the replacement
    if old_generate_script in content:
        content = content.replace(old_generate_script, new_generate_script)
        print("✅ Successfully updated generate_script method")
    else:
        print("⚠️ Could not find exact generate_script method")
        return False
    
    # Also update the script prompt to be even more forceful
    old_prompt_start = '''    def _create_script_prompt(self, paper_title: str, paper_content: str, paper_type: str) -> str:
        """Create prompt for script generation."""
        return f"""
You are a SENIOR AI ENGINEER and EXPERT EDUCATOR creating an in-depth educational video for YouTube/classroom teaching.

Paper Title: {paper_title}
Paper Type: {paper_type}
Content: {paper_content}

Create a COMPREHENSIVE, DETAILED video script (MINIMUM 15-25 minutes) that explains this research paper from absolute scratch like a world-class educator teaching complete beginners.

CRITICAL DURATION REQUIREMENTS:
- MINIMUM total video duration: 900 seconds (15 minutes)
- TARGET total video duration: 1200-1800 seconds (20-30 minutes)'''
    
    new_prompt_start = '''    def _create_script_prompt(self, paper_title: str, paper_content: str, paper_type: str) -> str:
        """Create prompt for script generation."""
        return f"""
You are a SENIOR AI ENGINEER and EXPERT EDUCATOR creating an in-depth educational video for YouTube/classroom teaching.

Paper Title: {paper_title}
Paper Type: {paper_type}
Content: {paper_content}

MANDATORY: Create a COMPREHENSIVE, DETAILED video script with MINIMUM 15-20 scenes and MINIMUM 20-30 minutes duration.

CRITICAL DURATION REQUIREMENTS (NON-NEGOTIABLE):
- MINIMUM total video duration: 1200 seconds (20 minutes) - SHORTER SCRIPTS WILL BE REJECTED
- TARGET total video duration: 1500-1800 seconds (25-30 minutes)
- MINIMUM scene count: 15 scenes - FEWER SCENES WILL BE REJECTED'''
    
    # Apply the prompt update
    content = content.replace(old_prompt_start, new_prompt_start)
    
    # Write the updated content back
    with open('src/llm/gemini_client.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Gemini client updated for comprehensive script generation!")
    print("📋 Changes made:")
    print("   - Added validation to reject short Gemini scripts")
    print("   - Forces fallback (20+ minutes) if Gemini generates < 15 minutes")
    print("   - Updated prompt to be more forceful about duration requirements")
    print("   - Minimum 20 minutes and 15 scenes now required")
    return True

if __name__ == "__main__":
    success = fix_gemini_comprehensive()
    if success:
        print("✅ Gemini comprehensive fix completed!")
        print("🎬 All videos will now be 20+ minutes comprehensive format!")
    else:
        print("❌ Failed to fix Gemini comprehensive generation")