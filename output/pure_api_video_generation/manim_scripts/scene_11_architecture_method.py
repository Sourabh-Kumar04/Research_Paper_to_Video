from manim import *

class TransformerArchitecture(Scene):
    def construct(self):
        # --- Title Slide ---
        title = Text("The Complete Transformer Architecture", font_size=36)
        title.scale_to_fit_width(12)
        subtitle = Text("Encoder and Decoder Explained", font_size=28)
        subtitle.scale_to_fit_width(12)
        self.play(Write(title))
        self.wait(3)
        self.play(Write(subtitle))
        self.wait(5)
        self.play(FadeOut(title, subtitle))

        # --- Encoder Stack ---
        encoder_title = Text("The Encoder Stack (🔵)", font_size=32)
        encoder_title.scale_to_fit_width(12)
        self.play(Write(encoder_title))
        self.wait(2)

        # Create a basic encoder block
        encoder_block = Rectangle(color=BLUE, width=2, height=1)
        encoder_block_text = Text("Encoder Block", font_size=24)
        encoder_block_text.scale_to_fit_width(1.5)
        encoder_block_text.move_to(encoder_block.get_center())
        self.play(Create(encoder_block), Write(encoder_block_text))
        self.wait(3)

        # Add residual connection
        residual_line = Line(encoder_block.get_right(), encoder_block.get_right() + RIGHT * 2, color=BLUE)
        residual_circle = Circle(color=BLUE, radius=0.2).move_to(residual_line.get_end())
        self.play(Create(residual_line), Create(residual_circle))
        self.wait(2)

        # Add attention mechanism
        attention_block = Rectangle(color=ORANGE, width=2, height=1).next_to(encoder_block, RIGHT * 3)
        attention_text = Text("Attention", font_size=24)
        attention_text.scale_to_fit_width(1.5)
        attention_text.move_to(attention_block.get_center())
        self.play(Create(attention_block), Write(attention_text))
        self.wait(3)

        # Add feed forward network
        ffn_block = Rectangle(color=BLUE, width=2, height=1).next_to(attention_block, RIGHT * 3)
        ffn_text = Text("Feed Forward", font_size=24)
        ffn_text.scale_to_fit_width(1.5)
        ffn_text.move_to(ffn_block.get_center())
        self.play(Create(ffn_block), Write(ffn_text))
        self.wait(3)

        # Stack multiple encoder blocks
        num_encoders = 6
        encoder_stack = VGroup(*[Rectangle(color=BLUE, width=2, height=1).move_to(DOWN * i * 2) for i in range(num_encoders)])
        encoder_stack_text = VGroup(*[Text("Encoder Block", font_size=24).scale_to_fit_width(1.5).move_to(DOWN * i * 2) for i in range(num_encoders)])
        self.play(FadeOut(encoder_block, residual_line, residual_circle, attention_block, attention_text, ffn_block, ffn_text, encoder_title))
        self.play(Create(encoder_stack), Write(encoder_stack_text))
        self.wait(5)

        # --- Decoder Stack ---
        decoder_title = Text("The Decoder Stack (🟢)", font_size=32)
        decoder_title.scale_to_fit_width(12)
        self.play(Write(decoder_title))
        self.wait(2)

        # Create a basic decoder block
        decoder_block = Rectangle(color=GREEN, width=2, height=1)
        decoder_block_text = Text("Decoder Block", font_size=24)
        decoder_block_text.scale_to_fit_width(1.5)
        decoder_block_text.move_to(decoder_block.get_center())
        self.play(Create(decoder_block), Write(decoder_block_text))
        self.wait(3)

        # Add masked attention
        masked_attention_block = Rectangle(color=ORANGE, width=2, height=1).next_to(decoder_block, RIGHT * 3)
        masked_attention_text = Text("Masked Attention", font_size=24)
        masked_attention_text.scale_to_fit_width(1.5)
        masked_attention_text.move_to(masked_attention_block.get_center())
        self.play(Create(masked_attention_block), Write(masked_attention_text))
        self.wait(3)

        # Add encoder-decoder attention
        encoder_decoder_attention_block = Rectangle(color=ORANGE, width=2, height=1).next_to(masked_attention_block, RIGHT * 3)
        encoder_decoder_attention_text = Text("Encoder-Decoder Attention", font_size=24)
        encoder_decoder_attention_text.scale_to_fit_width(1.5)
        encoder_decoder_attention_text.move_to(encoder_decoder_attention_block.get_center())
        self.play(Create(encoder_decoder_attention_block), Write(encoder_decoder_attention_text))
        self.wait(3)

        # Add feed forward network
        ffn_block_decoder = Rectangle(color=GREEN, width=2, height=1).next_to(encoder_decoder_attention_block, RIGHT * 3)
        ffn_text_decoder = Text("Feed Forward", font_size=24)
        ffn_text_decoder.scale_to_fit_width(1.5)
        ffn_text_decoder.move_to(ffn_block_decoder.get_center())
        self.play(Create(ffn_block_decoder), Write(ffn_text_decoder))
        self.wait(3)

        # Stack multiple decoder blocks
        num_decoders = 6
        decoder_stack = VGroup(*[Rectangle(color=GREEN, width=2, height=1).move_to(DOWN * i * 2) for i in range(num_decoders)])
        decoder_stack_text = VGroup(*[Text("Decoder Block", font_size=24).scale_to_fit_width(1.5).move_to(DOWN * i * 2) for i in range(num_decoders)])
        self.play(FadeOut(decoder_block, masked_attention_block, masked_attention_text, encoder_decoder_attention_block, encoder_decoder_attention_text, ffn_block_decoder, ffn_text_decoder, decoder_title))
        self.play(Create(decoder_stack), Write(decoder_stack_text))
        self.wait(5)

        # --- Complete Transformer ---
        complete_title = Text("The Complete Transformer", font_size=32)
        complete_title.scale_to_fit_width(12)
        self.play(Write(complete_title))
        self.wait(2)

        # Position encoder and decoder stacks
        encoder_stack.to_edge(LEFT)
        decoder_stack.to_edge(RIGHT)

        # Connect encoder and decoder with attention
        attention_line = Line(encoder_stack.get_right(), decoder_stack.get_left(), color=ORANGE)
        attention_text = Text("Encoder-Decoder Attention", font_size=24)
        attention_text.scale_to_fit_width(12)
        attention_text.move_to(attention_line.get_center())

        self.play(Create(attention_line), Write(attention_text))
        self.wait(5)

        # --- Summary ---
        summary_title = Text("Key Takeaways", font_size=32)
        summary_title.scale_to_fit_width(12)
        self.play(FadeOut(encoder_stack, decoder_stack, attention_line, attention_text, complete_title))
        self.play(Write(summary_title))
        self.wait(2)

        summary_points = VGroup(
            Text("• Encoder processes input sequence.", font_size=28).scale_to_fit_width(12),
            Text("• Decoder generates output sequence.", font_size=28).scale_to_fit_width(12),
            Text("• Attention connects encoder and decoder.", font_size=28).scale_to_fit_width(12)
        ).arrange(DOWN)
        summary_points.move_to(ORIGIN)
        self.play(Write(summary_points))
        self.wait(8)