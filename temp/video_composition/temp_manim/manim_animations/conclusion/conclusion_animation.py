
from manim import *

class ConclusionScene(Scene):
    def construct(self):
        # Title
        title = Text("Scene 5", font_size=48, color=WHITE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Neural network visualization
        # Input layer
        input_nodes = VGroup(*[Circle(radius=0.3, color=BLUE, fill_opacity=0.7) for _ in range(4)])
        input_nodes.arrange(DOWN, buff=0.5)
        input_nodes.shift(LEFT * 4)
        
        # Hidden layer
        hidden_nodes = VGroup(*[Circle(radius=0.3, color=GREEN, fill_opacity=0.7) for _ in range(6)])
        hidden_nodes.arrange(DOWN, buff=0.3)
        hidden_nodes.shift(LEFT * 1)
        
        # Output layer
        output_nodes = VGroup(*[Circle(radius=0.3, color=RED, fill_opacity=0.7) for _ in range(3)])
        output_nodes.arrange(DOWN, buff=0.5)
        output_nodes.shift(RIGHT * 2)
        
        # Create connections
        connections = VGroup()
        for input_node in input_nodes:
            for hidden_node in hidden_nodes:
                line = Line(input_node.get_center(), hidden_node.get_center(), 
                           stroke_width=1, color=GRAY)
                connections.add(line)
        
        for hidden_node in hidden_nodes:
            for output_node in output_nodes:
                line = Line(hidden_node.get_center(), output_node.get_center(),
                           stroke_width=1, color=GRAY)
                connections.add(line)
        
        # Animate network creation
        self.play(Create(connections))
        self.play(Create(input_nodes), Create(hidden_nodes), Create(output_nodes))
        self.wait(2)
        
        # Add labels
        input_label = Text("Input", font_size=24, color=BLUE)
        input_label.next_to(input_nodes, DOWN)
        
        hidden_label = Text("Hidden", font_size=24, color=GREEN)
        hidden_label.next_to(hidden_nodes, DOWN)
        
        output_label = Text("Output", font_size=24, color=RED)
        output_label.next_to(output_nodes, DOWN)
        
        self.play(Write(input_label), Write(hidden_label), Write(output_label))
        self.wait(2)
        
        # Animate data flow
        for i in range(3):
            # Highlight input
            self.play(input_nodes.animate.set_fill(YELLOW, opacity=1))
            self.wait(0.5)
            
            # Flow to hidden
            self.play(
                input_nodes.animate.set_fill(BLUE, opacity=0.7),
                hidden_nodes.animate.set_fill(YELLOW, opacity=1)
            )
            self.wait(0.5)
            
            # Flow to output
            self.play(
                hidden_nodes.animate.set_fill(GREEN, opacity=0.7),
                output_nodes.animate.set_fill(YELLOW, opacity=1)
            )
            self.wait(0.5)
            
            # Reset
            self.play(output_nodes.animate.set_fill(RED, opacity=0.7))
            self.wait(0.5)
        
        # Fade out
        everything = VGroup(title, connections, input_nodes, hidden_nodes, output_nodes,
                           input_label, hidden_label, output_label)
        self.play(FadeOut(everything))
        self.wait(1)
