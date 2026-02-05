from manim import *

class FutureDirectionsScene(Scene):
    def construct(self):
        # --- Opening Title Slide ---
        title = Text("Future Directions: Testing Gemma for Video Generation", font_size=36)
        title.scale_to_fit_width(12)
        subtitle = Text("Exploring Emerging Possibilities", font_size=28)
        subtitle.scale_to_fit_width(12)
        self.play(Write(title))
        self.wait(5)
        self.play(Write(subtitle))
        self.wait(10)
        self.play(FadeOut(title, subtitle))

        # --- Step 1: Conceptual Overview ---
        concept_title = Text("Step 1: The Big Picture", font_size=32)
        concept_title.scale_to_fit_width(12)
        self.play(Write(concept_title))
        self.wait(3)

        brain_image = ImageMobject("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Brain.svg/1200px-Brain.svg.png").scale(0.5)
        self.play(FadeIn(brain_image))
        self.wait(5)

        text1 = Text("AI models like Gemma are evolving rapidly.", font_size=28)
        text1.scale_to_fit_width(12)
        self.play(Write(text1.next_to(brain_image, DOWN)))
        self.wait(5)

        text2 = Text("Video generation is a key frontier.", font_size=28)
        text2.scale_to_fit_width(12)
        self.play(Write(text2.next_to(text1, DOWN)))
        self.wait(5)

        self.play(FadeOut(brain_image, concept_title, text1, text2))

        # --- Step 2: Detailed Component Analysis ---
        component_title = Text("Step 2: How it Works - Core Components", font_size=32)
        component_title.scale_to_fit_width(12)
        self.play(Write(component_title))
        self.wait(3)

        # Visualizing components
        data_box = Rectangle(color=BLUE, width=2, height=1)
        model_circle = Circle(color=ORANGE, radius=1)
        output_box = Rectangle(color=GREEN, width=2, height=1)

        data_box.move_to(LEFT * 3)
        model_circle.move_to(ORIGIN)
        output_box.move_to(RIGHT * 3)

        data_label = Text("Input Data", font_size=24)
        data_label.scale_to_fit_width(12)
        data_label.next_to(data_box, DOWN)

        model_label = Text("Gemma Model", font_size=24)
        model_label.scale_to_fit_width(12)
        model_label.next_to(model_circle, DOWN)

        output_label = Text("Generated Video", font_size=24)
        output_label.scale_to_fit_width(12)
        output_label.next_to(output_box, DOWN)

        self.play(Create(data_box), Create(model_circle), Create(output_box))
        self.play(Write(data_label), Write(model_label), Write(output_label))
        self.wait(8)

        arrow1 = Arrow(data_box.get_right(), model_circle.get_left(), buff=0.2)
        arrow2 = Arrow(model_circle.get_right(), output_box.get_left(), buff=0.2)

        self.play(Create(arrow1), Create(arrow2))
        self.wait(5)

        self.play(FadeOut(component_title, data_box, model_circle, output_box, data_label, model_label, output_label, arrow1, arrow2))

        # --- Step 3: Integration and Relationships ---
        integration_title = Text("Step 3: Connecting the Dots", font_size=32)
        integration_title.scale_to_fit_width(12)
        self.play(Write(integration_title))
        self.wait(3)

        # Visualizing integration
        cloud = ImageMobject("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Cloud_computing.svg/1200px-Cloud_computing.svg.png").scale(0.3)
        user_icon = ImageMobject("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/User-x-mark.svg/1200px-User-x-mark.svg.png").scale(0.2)
        gemma_icon = ImageMobject("https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Python-logo-v3-tm.svg/1200px-Python-logo-v3-tm.svg.png").scale(0.2) #Placeholder for Gemma Icon

        cloud.move_to(UP * 2)
        user_icon.move_to(LEFT * 3)
        gemma_icon.move_to(RIGHT * 3)

        self.play(FadeIn(cloud, user_icon, gemma_icon))
        self.wait(5)

        arrow_user_cloud = Arrow(user_icon.get_right(), cloud.get_left(), buff=0.2)
        arrow_cloud_gemma = Arrow(cloud.get_right(), gemma_icon.get_left(), buff=0.2)

        self.play(Create(arrow_user_cloud), Create(arrow_cloud_gemma))
        self.wait(8)

        text3 = Text("User requests -> Cloud processes -> Gemma generates", font_size=24)
        text3.scale_to_fit_width(12)
        self.play(Write(text3.next_to(cloud, DOWN)))
        self.wait(5)

        self.play(FadeOut(integration_title, cloud, user_icon, gemma_icon, arrow_user_cloud, arrow_cloud_gemma, text3))

        # --- Step 4: Practical Applications ---
        application_title = Text("Step 4: Real-World Impact", font_size=32)
        application_title.scale_to_fit_width(12)
        self.play(Write(application_title))
        self.wait(3)

        # Visualizing applications
        movie_icon = ImageMobject("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Video-icon.svg/1200px-Video-icon.svg.png").scale(0.3)
        education_icon = ImageMobject("https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Education_icon.svg/1200px-Education_icon.svg.png").scale(0.3)
        marketing_icon = ImageMobject("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/Marketing_icon.svg/1200px-Marketing_icon.svg.png").scale(0.3)

        movie_icon.move_to(LEFT * 3)
        education_icon.move_to(ORIGIN)
        marketing_icon.move_to(RIGHT * 3)

        self.play(FadeIn(movie_icon, education_icon, marketing_icon))
        self.wait(5)

        text4 = Text("Entertainment, Education, Marketing & More!", font_size=28)
        text4.scale_to_fit_width(12)
        self.play(Write(text4.next_to(education_icon, DOWN)))
        self.wait(10)

        self.play(FadeOut(application_title, movie_icon, education_icon, marketing_icon, text4))

        # --- Closing Summary ---
        summary_title = Text("Future is Bright!", font_size=36)
        summary_title.scale_to_fit_width(12)
        self.play(Write(summary_title))
        self.wait(5)

        summary_text = Text("Gemma and similar models are paving the way for a new era of video creation.", font_size=28)
        summary_text.scale_to_fit_width(12)
        self.play(Write(summary_text.next_to(summary_title, DOWN)))
        self.wait(10)

        self.play(FadeOut(summary_title, summary_text))