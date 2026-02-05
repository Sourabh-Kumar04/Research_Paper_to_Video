from manim import *

class AttentionIsAllYouNeed(Scene):
    def construct(self):
        # --- Opening Title Card (10 seconds) ---
        title = Text("Attention Is All You Need: The Transformer Revolution", font_size=36)
        title.scale_to_fit_width(12)
        author = Text("Vaswani et al. (2017)", font_size=28)
        author.scale_to_fit_width(12)
        author.next_to(title, DOWN, buff=0.5)

        self.play(Write(title))
        self.wait(5)
        self.play(Write(author))
        self.wait(5)
        self.play(FadeOut(title, author))

        # --- RNN Limitations - The Forgetting Problem (30 seconds) ---
        rnn_title = Text("The Problem with RNNs: Forgetting", font_size=32)
        rnn_title.scale_to_fit_width(12)
        self.play(Write(rnn_title))
        self.wait(2)

        sentence = Text("The quick brown fox jumps over the lazy dog.", font_size=24)
        sentence.scale_to_fit_width(12)
        sentence.next_to(rnn_title, DOWN, buff=0.5)
        self.play(Write(sentence))
        self.wait(3)

        # Visual metaphor: fading sentence
        fading_sentence = VGroup(sentence)
        self.play(ApplyMethod(fading_sentence.set_opacity, 0.2), run_time=5)
        self.wait(5)

        rnn_explanation = Text("RNNs process sequentially.  Long sentences become difficult to remember.", font_size=24)
        rnn_explanation.scale_to_fit_width(12)
        rnn_explanation.next_to(fading_sentence, DOWN, buff=0.5)
        self.play(Write(rnn_explanation))
        self.wait(7)

        self.play(FadeOut(rnn_title, sentence, fading_sentence, rnn_explanation))

        # --- Introducing the Transformer (30 seconds) ---
        transformer_title = Text("The Transformer: A New Approach", font_size=32)
        transformer_title.scale_to_fit_width(12)
        self.play(Write(transformer_title))
        self.wait(2)

        transformer_explanation = Text("The Transformer uses 'Attention' to focus on all parts of the input simultaneously.", font_size=24)
        transformer_explanation.scale_to_fit_width(12)
        transformer_explanation.next_to(transformer_title, DOWN, buff=0.5)
        self.play(Write(transformer_explanation))
        self.wait(5)

        # Visual metaphor: spotlight on sentence
        sentence_again = Text("The quick brown fox jumps over the lazy dog.", font_size=24)
        sentence_again.scale_to_fit_width(12)
        sentence_again.next_to(transformer_explanation, DOWN, buff=0.5)
        self.play(Write(sentence_again))

        spotlight = SurroundingRectangle(sentence_again, color=YELLOW, buff=0.2)
        self.play(Create(spotlight))
        self.wait(5)
        self.play(ApplyMethod(spotlight.set_fill, GREEN, color=GREEN), run_time=2)
        self.wait(5)
        self.play(FadeOut(spotlight))

        transformer_benefits = Text("No more forgetting!  Attention allows the model to 'see' the whole picture.", font_size=24)
        transformer_benefits.scale_to_fit_width(12)
        transformer_benefits.next_to(sentence_again, DOWN, buff=0.5)
        self.play(Write(transformer_benefits))
        self.wait(8)

        self.play(FadeOut(transformer_title, transformer_explanation, sentence_again, transformer_benefits))

        # --- Real-World Applications (20 seconds) ---
        applications_title = Text("Transformers in Action", font_size=32)
        applications_title.scale_to_fit_width(12)
        self.play(Write(applications_title))
        self.wait(2)

        # Images of applications
        google_translate = ImageMobject("google_translate.png").scale(0.5) # Replace with actual image path
        chatgpt = ImageMobject("chatgpt.png").scale(0.5) # Replace with actual image path

        google_translate.next_to(applications_title, DOWN, buff=0.5)
        chatgpt.next_to(google_translate, RIGHT, buff=1)

        self.play(FadeIn(google_translate, chatgpt))
        self.wait(5)

        applications_explanation = Text("Google Translate, ChatGPT, and many other AI tools are powered by Transformers!", font_size=24)
        applications_explanation.scale_to_fit_width(12)
        applications_explanation.next_to(chatgpt, DOWN, buff=0.5)
        self.play(Write(applications_explanation))
        self.wait(8)

        self.play(FadeOut(applications_title, google_translate, chatgpt, applications_explanation))