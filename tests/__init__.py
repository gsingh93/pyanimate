def convert_to_ascii(image):
    ascii_pixels = []

    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    for x in range(image.width):
        for y in range(image.height):
            pixel = image.getpixel((x, y))[:3]
            # yapf: disable
            ascii_pixels.append(
                'R' if pixel == RED else
                'G' if pixel == GREEN else
                'B' if pixel == BLUE else
                'w' if pixel == WHITE else
                'b' if pixel == BLACK else
                '?'
            )
            # yapf: enable

    ascii_pixels = [
        "".join(ascii_pixels[i : i + image.width])
        for i in range(0, len(ascii_pixels), image.width)
    ]

    return ascii_pixels
