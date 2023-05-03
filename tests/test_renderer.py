from pyanimate.renderer import PILRenderer, RenderContext


class TestRenderer:
    def test_render_context(self):
        ctx = RenderContext(width=10, height=20, bit_width=2, dpi=(300, 300), scale=2)

        assert ctx.scale == 2
        assert ctx.w == 20
        assert ctx.h == 40
        assert ctx.cell_height == 200
        assert ctx.bit_width == 4
        assert ctx.dpi == (300, 300)

    def test_pil_renderer(self):
        ctx = RenderContext(width=10, height=20, bit_width=2, dpi=(300, 300), scale=2)
        renderer = PILRenderer(ctx)

        assert renderer.ctx == ctx
        assert renderer.image.mode == "RGBA"
        assert renderer.image.size == (20, 40)
