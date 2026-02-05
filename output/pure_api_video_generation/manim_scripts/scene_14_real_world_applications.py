from manim import *

class TransformersToday(Scene):
    def construct(self):
        # --- Opening Title Slide ---
        title = Text("Transformers Today: From Translation to Everything Else", font_size=36)
        title.scale_to_fit_width(10)
        subtitle = Text("A Beginner's Guide", font_size=28)
        subtitle.scale_to_fit_width(10)
        subtitle.next_to(title, DOWN, buff=0.5)
        self.play(Write(title))
        self.wait(3)
        self.play(Write(subtitle))
        self.wait(5)
        self.play(FadeOut(title, subtitle))

        # --- Introduction to the Problem: Traditional NLP ---
        problem_title = Text("The Old Way: Traditional NLP", font_size=32)
        problem_title.scale_to_fit_width(10)
        self.play(Write(problem_title))
        self.wait(2)

        problem_text = Text("Early NLP relied on hand-engineered features and complex rules.\nDifficult to scale and didn't understand context well.", font_size=24)
        problem_text.scale_to_fit_width(10)
        problem_text.next_to(problem_title, DOWN, buff=0.5)
        self.play(Write(problem_text))
        self.wait(8)  # Extended reading time

        # --- Introducing Transformers: The Breakthrough ---
        transformer_title = Text("Enter Transformers!", font_size=32)
        transformer_title.scale_to_fit_width(10)
        transformer_title.to_edge(UP)
        self.play(Transform(problem_title, transformer_title))
        self.wait(2)

        transformer_text = Text("Transformers use 'attention' to focus on relevant parts of the input.\nThey learn relationships between words without explicit rules.", font_size=24)
        transformer_text.scale_to_fit_width(10)
        transformer_text.next_to(transformer_title, DOWN, buff=0.5)
        self.play(Write(transformer_text))
        self.wait(8)

        # --- Visual Metaphor: Attention as a Spotlight ---
        spotlight = Circle(radius=0.5, color=YELLOW)
        sentence = Text("The cat sat on the mat.", font_size=28)
        sentence.scale_to_fit_width(10)
        sentence.next_to(transformer_text, DOWN, buff=1)

        self.play(Create(sentence))
        self.wait(1)

        words = VGroup(*[Text(word, font_size=24) for word in sentence.split()])
        words.arrange(RIGHT, aligned_edge=DOWN)
        words.next_to(sentence, DOWN, buff=0.5)
        self.play(Create(words))
        self.wait(1)

        # Animate spotlight moving across words
        for word in words:
            self.play(spotlight.move_to(word))
            self.wait(0.5)

        self.play(FadeOut(spotlight, words))
        self.wait(3)

        # --- Key Transformer Models: BERT, GPT-3, PaLM ---
        models_title = Text("Meet the Stars: BERT, GPT-3, and PaLM", font_size=32)
        models_title.scale_to_fit_width(10)
        models_title.to_edge(UP)
        self.play(Transform(transformer_title, models_title))
        self.wait(2)

        bert_image = ImageMobject("bert.png").scale(0.5) # Replace with actual image path
        gpt3_image = ImageMobject("gpt3.png").scale(0.5) # Replace with actual image path
        palm_image = ImageMobject("palm.png").scale(0.5) # Replace with actual image path

        bert_image.next_to(models_title, DOWN, buff=0.5)
        gpt3_image.next_to(bert_image, RIGHT, buff=1)
        palm_image.next_to(gpt3_image, RIGHT, buff=1)

        self.play(Create(bert_image))
        self.wait(2)
        self.play(Create(gpt3_image))
        self.wait(2)
        self.play(Create(palm_image))
        self.wait(5)

        # --- Applications: Green Color Coding ---
        applications_title = Text("What can they DO?", font_size=32)
        applications_title.scale_to_fit_width(10)
        applications_title.to_edge(UP)
        self.play(Transform(models_title, applications_title))
        self.wait(2)

        # Example Applications
        summarization_text = Text("Text Summarization", font_size=24, color=GREEN)
        qa_text = Text("Question Answering", font_size=24, color=GREEN)
        image_captioning_text = Text("Image Captioning", font_size=24, color=GREEN)

        summarization_text.next_to(applications_title, DOWN, buff=0.5)
        qa_text.next_to(summarization_text, RIGHT, buff=1)
        image_captioning_text.next_to(qa_text, RIGHT, buff=1)

        self.play(Write(summarization_text))
        self.wait(2)
        self.play(Write(qa_text))
        self.wait(2)
        self.play(Write(image_captioning_text))
        self.wait(5)

        # --- Summary and Future ---
        summary_title = Text("The Future is Transforming!", font_size=32)
        summary_title.scale_to_fit_width(10)
        summary_title.to_edge(UP)
        self.play(Transform(applications_title, summary_title))
        self.wait(2)

        summary_text = Text("Transformers are revolutionizing AI, with applications expanding rapidly.\nThey're the foundation for many exciting advancements.", font_size=24)
        summary_text.scale_to_fit_width(10)
        summary_text.next_to(summary_title, DOWN, buff=0.5)
        self.play(Write(summary_text))
        self.wait(8)

        self.play(FadeOut(summary_title, summary_text, bert_image, gpt3_image, palm_image, summarization_text, qa_text, image_captioning_text))
        self.wait(2)