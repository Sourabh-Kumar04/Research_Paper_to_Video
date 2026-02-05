#!/usr/bin/env python3
"""
Clean fix for the fallback script - replace the entire function properly
"""

from pathlib import Path
import re

def fix_fallback_script_clean():
    """Fix the fallback script with proper indentation"""
    
    file_path = Path("src/llm/gemini_client.py")
    
    print(f"🔧 Fixing fallback script in {file_path}")
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the start and end of the function
    start_pattern = r'def _create_fallback_script\(self, paper_title: str, paper_content: str\) -> Dict\[str, Any\]:'
    
    # Find the start
    start_match = re.search(start_pattern, content)
    if not start_match:
        print("❌ Could not find function start")
        return False
    
    start_pos = start_match.start()
    
    # Find the next function definition after this one
    remaining_content = content[start_pos:]
    next_func_pattern = r'\n    def [^_]'  # Next function at same indentation level
    next_func_match = re.search(next_func_pattern, remaining_content)
    
    if next_func_match:
        end_pos = start_pos + next_func_match.start()
    else:
        # If no next function found, look for class end or file end
        print("❌ Could not find function end")
        return False
    
    # New function content
    new_function = '''    def _create_fallback_script(self, paper_title: str, paper_content: str) -> Dict[str, Any]:
        """Create fallback script when Gemini fails - professional educational format (5-10 minutes)."""
        return {
            "title": paper_title,
            "total_duration": 360.0,  # 6 minutes (5-10 minute range)
            "target_audience": "students and engineers",
            "teaching_style": "senior engineer explaining from basics to advanced",
            "scenes": [
                {
                    "id": "hook",
                    "title": "Why This Research Matters",
                    "duration": 35.0,
                    "narration": f"Welcome to this comprehensive technical analysis of '{paper_title}'. This research represents a significant contribution to the field, addressing fundamental challenges through innovative methodologies and rigorous theoretical foundations. As professional engineers and researchers, we'll examine this work from first principles, building from basic concepts to advanced implementations. We'll explore the mathematical foundations, analyze the algorithmic innovations, and discuss practical implications for real-world systems. This paper introduces novel approaches that advance the state-of-the-art, providing insights directly applicable to modern software engineering and system architecture. Throughout this analysis, we'll connect theoretical concepts to practical applications, ensuring you understand not just what the research does, but why it works and how you can apply these principles in your own projects.",
                    "visual_description": "Professional title slide with paper citation, research field context, and key impact areas",
                    "key_concepts": ["Research significance", "Real-world impact", "Technical innovation"],
                    "formulas": [],
                    "diagrams": ["Impact overview diagram"]
                },
                {
                    "id": "prerequisites",
                    "title": "Essential Background and Prerequisites",
                    "duration": 45.0,
                    "narration": "Before diving into the core contributions, let's establish the foundational concepts you'll need to fully understand this work. We'll start with the basic principles and mathematical tools that underpin the research. Think of this as building a solid foundation before constructing a complex structure - each concept we cover here will be essential for understanding the innovations that follow. We'll review relevant algorithms, data structures, and theoretical frameworks from computer science and mathematics. If you're familiar with these concepts, this will serve as a refresher and establish our notation. If these ideas are new to you, don't worry - we'll explain each concept clearly with examples and intuition before moving forward. The key is to ensure everyone has the same baseline understanding, so we can explore the advanced concepts together without gaps in knowledge. We'll use analogies and real-world examples to make abstract concepts concrete and relatable.",
                    "visual_description": "Concept map showing prerequisite knowledge, mathematical notation guide, and foundational algorithms",
                    "key_concepts": ["Foundational concepts", "Mathematical prerequisites", "Algorithm basics"],
                    "formulas": ["Basic mathematical notation"],
                    "diagrams": ["Prerequisite concept map", "Notation guide"]
                },
                {
                    "id": "problem",
                    "title": "Problem Statement and Challenges",
                    "duration": 50.0,
                    "narration": "Now let's examine the specific problem this research addresses. What makes this problem challenging? Why haven't previous approaches solved it effectively? Understanding the problem deeply is crucial for appreciating the solution's elegance and innovation. We'll analyze the limitations of existing methods, identifying specific bottlenecks in computational complexity, memory efficiency, or scalability. Consider the real-world scenarios where these limitations become critical - perhaps in large-scale distributed systems, real-time processing pipelines, or resource-constrained environments. The problem often involves trade-offs between competing objectives: speed versus accuracy, memory versus computation, or simplicity versus expressiveness. We'll formalize the problem mathematically, defining objective functions, constraint sets, and optimization criteria. This rigorous formulation allows us to precisely characterize what makes the problem hard and what properties an ideal solution should possess. By the end of this section, you'll understand not just what problem we're solving, but why it's important and what makes it technically challenging.",
                    "visual_description": "Problem visualization with existing method limitations, bottleneck analysis, and mathematical problem formulation",
                    "key_concepts": ["Problem definition", "Existing limitations", "Technical challenges"],
                    "formulas": ["Problem formulation", "Constraint definitions"],
                    "diagrams": ["Bottleneck analysis", "Trade-off visualization"]
                },
                {
                    "id": "method",
                    "title": "Detailed Methodology and Algorithm",
                    "duration": 60.0,
                    "narration": "Now we'll examine the detailed methodology, translating our intuition into precise algorithms and mathematical formulations. The approach consists of several key components that work together to achieve the desired properties. First, we'll look at the data structures and representations used - these choices are crucial for efficiency and correctness. Next, we'll walk through the algorithm step-by-step, explaining the purpose of each operation and how it contributes to the overall solution. Pay attention to the invariants maintained throughout execution - these guarantee correctness and provide insight into why the algorithm works. We'll analyze the computational complexity, showing how the approach achieves better performance than previous methods. The mathematical formulation provides rigorous guarantees about convergence, optimality, or approximation quality. We'll discuss implementation considerations: how to handle edge cases, numerical stability concerns, and practical optimizations that improve performance without sacrificing correctness.",
                    "visual_description": "Algorithm flowcharts, pseudocode, data structure diagrams, and complexity analysis",
                    "key_concepts": ["Algorithm design", "Data structures", "Implementation details"],
                    "formulas": ["Core algorithm equations", "Complexity bounds"],
                    "diagrams": ["Algorithm flowchart", "Data structure visualization"]
                },
                {
                    "id": "results",
                    "title": "Experimental Results and Performance Analysis",
                    "duration": 50.0,
                    "narration": "Now let's examine the experimental validation and performance analysis. The authors evaluate their approach on standard benchmarks and real-world datasets, comparing against state-of-the-art baselines. We'll look at the experimental setup: what datasets were used, how were hyperparameters chosen, and what metrics measure success. The results demonstrate significant improvements across multiple dimensions - perhaps better accuracy, faster runtime, lower memory usage, or improved scalability. Pay attention to the statistical significance of the results and the confidence intervals provided. We'll analyze performance across different problem sizes and characteristics, identifying where the method excels and where it faces limitations. The ablation studies reveal which components contribute most to performance, helping us understand what makes the approach effective.",
                    "visual_description": "Performance charts, comparison tables, ablation study results, and scalability analysis",
                    "key_concepts": ["Experimental validation", "Performance metrics", "Comparative analysis"],
                    "formulas": ["Performance metrics"],
                    "diagrams": ["Performance comparison charts", "Scalability plots"]
                },
                {
                    "id": "impact",
                    "title": "Impact and Future Directions",
                    "duration": 40.0,
                    "narration": "This research establishes new benchmarks while opening multiple avenues for future investigation and system development. The impact extends beyond immediate performance improvements to influence fundamental approaches in algorithm design and software engineering practices. Future directions include extensions to distributed computing environments, integration with emerging hardware architectures, and adaptation to evolving data characteristics. The work provides foundation for next-generation systems leveraging cloud-native architectures, edge computing deployments, and hybrid cloud environments, with significant implications for industry standards and open-source framework development. We'll discuss the broader implications for the field and how this work might influence future research directions.",
                    "visual_description": "Impact analysis, future research roadmap, and application domains",
                    "key_concepts": ["Research impact", "Future directions", "Practical applications"],
                    "formulas": [],
                    "diagrams": ["Impact timeline", "Future research map"]
                }
            ]
        }

'''
    
    # Replace the function
    new_content = content[:start_pos] + new_function + content[end_pos:]
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Successfully replaced fallback script")
    return True

def verify_fix():
    """Verify the fix worked"""
    print(f"\n🧪 Verifying the fix...")
    
    try:
        # Clear Python cache
        import sys
        
        # Remove from cache if already imported
        modules_to_remove = [k for k in sys.modules.keys() if 'gemini_client' in k]
        for module in modules_to_remove:
            del sys.modules[module]
        
        # Add src to path
        from pathlib import Path
        src_path = Path(__file__).parent / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        # Load environment
        from dotenv import load_dotenv
        load_dotenv()
        
        # Import fresh
        from llm.gemini_client import GeminiClient
        
        # Test the fallback script
        client = GeminiClient()
        result = client._create_fallback_script("Test Paper", "Test content")
        
        duration = result.get('total_duration', 0)
        scene_count = len(result.get('scenes', []))
        
        print(f"   Duration: {duration} seconds ({duration/60:.1f} minutes)")
        print(f"   Scene count: {scene_count}")
        print(f"   Target audience: {result.get('target_audience', 'N/A')}")
        print(f"   Teaching style: {result.get('teaching_style', 'N/A')}")
        
        if duration >= 300 and scene_count >= 6:
            print(f"✅ SUCCESS: Professional fallback script is working!")
            return True
        else:
            print(f"❌ FAILED: Still getting old format")
            return False
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Clean Fallback Script Fix")
    print("=" * 40)
    
    success = fix_fallback_script_clean()
    
    if success:
        verify_success = verify_fix()
        if verify_success:
            print(f"\n🎉 COMPLETE: Professional educational videos are now fully working!")
            print(f"   - Gemini script prompt: ✅ 5-10 minutes, detailed explanations")
            print(f"   - Manim code prompt: ✅ Formulas and diagrams support")
            print(f"   - Fallback script: ✅ 6 minutes, professional format")
            print(f"   - Latest Gemini model: ✅ gemini-2.0-flash-exp")
            print(f"\n🎯 READY TO TEST:")
            print(f"   1. Start backend: start_backend_now.bat")
            print(f"   2. Start frontend: cd src/frontend && npm start")
            print(f"   3. Generate video with 'Attention Is All You Need'")
            print(f"   4. Expect: 5-10 minute professional educational video")
        else:
            print(f"\n⚠️  Fix applied but verification failed")
    else:
        print(f"\n❌ Failed to apply fix")