#!/usr/bin/env python3
"""
Test script to verify MASSIVE text fix with NO SCALING
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from llm.gemini_client import GeminiClient

def test_fallback_manim_code():
    """Test that fallback Manim code has NO SCALING for content."""
    client = GeminiClient()
    
    # Test with long content
    long_content = "This is a very long piece of content that would normally be scaled down to fit the screen, making it unreadable. " * 5
    
    code = client._create_fallback_manim_code("Test Scene", long_content)
    
    print("=" * 80)
    print("GENERATED MANIM CODE:")
    print("=" * 80)
    print(code)
    print("=" * 80)
    
    # Verify NO SCALING in content
    assert "scale_to_fit_width" not in code or "# NO SCALING" in code, "❌ FAIL: Still has scaling!"
    assert "scale_to_fit_height" not in code or "# NO SCALING" in code, "❌ FAIL: Still has scaling!"
    assert "Paragraph" in code, "❌ FAIL: Not using Paragraph for wrapping!"
    assert "font_size=42" in code or "font_size=48" in code, "❌ FAIL: Font size too small!"
    
    print("\n✅ SUCCESS: Manim code has NO SCALING and uses Paragraph with large font!")
    print("✅ Content will be MASSIVE and readable!")
    
    return True

if __name__ == "__main__":
    try:
        test_fallback_manim_code()
        print("\n🎉 ALL TESTS PASSED!")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
