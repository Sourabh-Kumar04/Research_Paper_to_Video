#!/usr/bin/env python3
"""
Add educational metadata to scenes for Task 3.3
"""

import re
from pathlib import Path

def add_educational_metadata():
    """Add educational metadata (key_concepts, formulas, diagrams, analogies, transitions) to all scenes."""
    
    print("🎓 Adding educational metadata to scenes")
    print("=" * 50)
    
    # Read the current production_video_generator.py
    file_path = Path("production_video_generator.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define educational metadata for each scene type
    educational_metadata = {
        "intro": {
            "key_concepts": ["Research significance", "Problem landscape", "Learning roadmap", "Impact areas"],
            "formulas": [],
            "diagrams": ["Research impact visualization", "Learning pathway diagram"],
            "analogies": ["Hammer vs precision screwdriver", "Personal guide analogy"],
            "transitions": ["Now let's understand what came before this breakthrough..."]
        },
        "historical_context": {
            "key_concepts": ["Previous approaches", "Limitations", "Evolution timeline", "Innovation need"],
            "formulas": [],
            "diagrams": ["Timeline visualization", "Traffic jam analogy", "Puzzle pieces diagram"],
            "analogies": ["Bustling city with traffic jams", "Narrow roads vs highway system", "Pipe leak fixes"],
            "transitions": ["With this context, let's build the foundations you need..."]
        },
        "prerequisites": {
            "key_concepts": ["Algorithms", "Data structures", "Mathematical concepts", "Computational building blocks"],
            "formulas": ["f(x) = y (basic function notation)"],
            "diagrams": ["Algorithm recipe visualization", "Data structure comparisons", "Mathematical notation guide"],
            "analogies": ["Cooking complex dish", "Filing cabinet vs library catalog", "Musical score precision"],
            "transitions": ["Now that we have our foundations, let's define the problem..."]
        },
        "problem_definition": {
            "key_concepts": ["Problem dimensions", "Accuracy requirements", "Efficiency needs", "Scalability challenges"],
            "formulas": [],
            "diagrams": ["Multi-dimensional problem space", "GPS accuracy comparison", "Scaling visualization"],
            "analogies": ["Complex puzzle with billions of pieces", "GPS neighborhood vs exact address", "Family dinner vs stadium feeding"],
            "transitions": ["Understanding the problem, let's explore the brilliant solution..."]
        },
        "intuitive_overview": {
            "key_concepts": ["Core insight", "Parallel processing", "Pattern recognition", "Relationship capture"],
            "formulas": [],
            "diagrams": ["Library organization system", "Sequential vs parallel comparison", "Maze navigation visualization"],
            "analogies": ["Massive library organization", "Reading word by word vs seeing patterns", "Maze path vs aerial view"],
            "transitions": ["This intuitive understanding leads us to the first building block..."]
        },
        "mathematical_foundations": {
            "key_concepts": ["Mathematical precision", "Theoretical guarantees", "Performance analysis", "Convergence properties"],
            "formulas": ["System Equation: S = F(C₁(x), C₂(y))", "Optimization: min L(θ) = Σᵢ ℓ(fθ(xᵢ),yᵢ)"],
            "diagrams": ["Mathematical framework visualization", "Equation breakdown", "Theoretical guarantee charts"],
            "analogies": ["Blueprint language", "Precise recipe for computers", "Quality control checkpoints"],
            "transitions": ["With mathematical precision established, let's see the implementation..."]
        },
        "implementation": {
            "key_concepts": ["Computational efficiency", "Memory management", "Numerical stability", "Production readiness"],
            "formulas": ["Complexity analysis: O(n²×d) vs O(n×d²)"],
            "diagrams": ["Implementation architecture", "Memory management visualization", "Performance optimization flow"],
            "analogies": ["Blueprint to engine building", "Expert mechanics optimization", "Smart warehouse system"],
            "transitions": ["From implementation, let's examine the impressive results..."]
        },
        "impact_applications": {
            "key_concepts": ["Industry transformation", "Cross-domain applications", "Production deployment", "Economic impact"],
            "formulas": [],
            "diagrams": ["Industry impact map", "Application domain visualization", "Production system examples"],
            "analogies": ["Transistor invention impact", "Aerodynamics principles adaptation"],
            "transitions": ["Looking at current impact, let's explore future possibilities..."]
        },
        "future_directions": {
            "key_concepts": ["Scale extensions", "Domain adaptations", "Theoretical advances", "Hybrid approaches"],
            "formulas": [],
            "diagrams": ["Research roadmap", "Future possibilities map", "Innovation ecosystem"],
            "analogies": ["Key unlocking multiple doors", "Computer room to smartphone evolution"],
            "transitions": ["With future directions mapped, let's connect all the pieces..."]
        },
        "conclusion": {
            "key_concepts": ["Complete synthesis", "Interconnected understanding", "Journey summary", "Practical implications"],
            "formulas": [],
            "diagrams": ["Complete concept map", "Journey visualization", "Impact synthesis"],
            "analogies": ["Completed puzzle view", "Stepping back from masterpiece"],
            "transitions": ["This completes our comprehensive journey through this groundbreaking research."]
        }
    }
    
    # Find all scene definitions and add metadata
    scene_pattern = r'(\{\s*"id": "([^"]+)",\s*"title": "[^"]*",\s*"narration": f?"[^"]*",\s*(?:"duration": [^,]+,\s*)?(?:"visual_description": """[^"]*""",?\s*)?)\}'
    
    def add_metadata_to_scene(match):
        scene_content = match.group(1)
        scene_id = match.group(2)
        
        # Get metadata for this scene type, or use default
        metadata = educational_metadata.get(scene_id, {
            "key_concepts": ["Core concepts", "Technical details", "Practical applications"],
            "formulas": [],
            "diagrams": ["Conceptual visualization", "Technical diagram"],
            "analogies": ["Real-world comparison", "Intuitive explanation"],
            "transitions": ["This leads us to the next important concept..."]
        })
        
        # Add the educational metadata
        metadata_str = f'''
                "key_concepts": {metadata["key_concepts"]},
                "formulas": {metadata["formulas"]},
                "diagrams": {metadata["diagrams"]},
                "analogies": {metadata["analogies"]},
                "transitions": {metadata["transitions"]}'''
        
        # Insert metadata before the closing brace
        enhanced_scene = scene_content + "," + metadata_str + "\n            }"
        
        return enhanced_scene
    
    # Apply the metadata additions
    enhanced_content = re.sub(scene_pattern, add_metadata_to_scene, content, flags=re.DOTALL)
    
    # Also add metadata to the scene templates in the while loop
    template_pattern = r'(additional_scene = \{\s*"id": f"extended_scene_\{len\(scenes\)\}",\s*"title": f"[^"]*",\s*"narration": f"[^"]*",\s*(?:"visual_description": f"""[^"]*""",?\s*)?)\}'
    
    def add_metadata_to_template(match):
        template_content = match.group(1)
        
        # Add generic educational metadata for extended scenes
        metadata_str = '''
                "key_concepts": ["Advanced analysis", "Technical depth", "Practical implications", "Research methodology"],
                "formulas": ["Technical equations as needed"],
                "diagrams": ["Advanced technical diagrams", "Performance analysis charts"],
                "analogies": ["Complex system analogies", "Real-world applications"],
                "transitions": ["This analysis connects to our broader understanding..."]'''
        
        enhanced_template = template_content + "," + metadata_str + "\n            }"
        
        return enhanced_template
    
    enhanced_content = re.sub(template_pattern, add_metadata_to_template, enhanced_content, flags=re.DOTALL)
    
    # Write the enhanced content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_content)
    
    print("✅ Added educational metadata to all scenes")
    print("   - key_concepts: Core learning objectives")
    print("   - formulas: Mathematical expressions and equations")
    print("   - diagrams: Visual elements and illustrations")
    print("   - analogies: Real-world comparisons and explanations")
    print("   - transitions: Connections to next concepts")
    print("\n🎉 Educational metadata addition complete!")
    print("All scenes now include comprehensive educational metadata.")

if __name__ == "__main__":
    add_educational_metadata()