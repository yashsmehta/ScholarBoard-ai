"""Generate the ScholarBoard favicon set — a connected node-network icon.

Uses Pillow to draw a constellation of nodes with edges,
representing the research similarity map. Transparent background,
brand teal palette (#0d5c63 / #44a1a0).
"""

from pathlib import Path

from PIL import Image, ImageDraw

PUBLIC_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public"

# Brand colors
DARK = (13, 92, 99)    # #0d5c63
MID = (68, 161, 160)   # #44a1a0


def main():
    SIZE = 512
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Nodes: (x, y, radius, color_rgba)
    nodes = [
        (256, 200, 56, (*DARK, 255)),   # center-top, hero node
        (140, 310, 40, (*MID, 255)),    # bottom-left
        (370, 310, 40, (*MID, 255)),    # bottom-right
        (155, 150, 28, (*DARK, 230)),   # top-left
        (370, 140, 24, (*MID, 220)),    # top-right
        (256, 390, 30, (*DARK, 230)),   # bottom-center
    ]

    # Edges — connected graph
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4),
        (1, 2), (1, 3), (1, 5),
        (2, 4), (2, 5),
        (3, 4),
    ]

    for i, j in edges:
        x1, y1 = nodes[i][0], nodes[i][1]
        x2, y2 = nodes[j][0], nodes[j][1]
        draw.line([(x1, y1), (x2, y2)], fill=(*MID, 50), width=5)

    for x, y, r, color in nodes:
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)

    # Keep the 512px PNG as the canonical high-resolution browser icon.
    favicon_path = PUBLIC_DIR / "favicon.png"
    img.save(favicon_path, "PNG", optimize=True)

    # A multi-resolution .ico covers browsers and bookmarks that still prefer it.
    ico_path = PUBLIC_DIR / "favicon.ico"
    img.save(ico_path, "ICO", sizes=[(16, 16), (32, 32), (48, 48)])

    # iOS uses a dedicated opaque touch icon. The brand-tinted background keeps
    # the transparent network from being rendered on an unpredictable tile.
    touch_size = 180
    touch_background = Image.new("RGBA", (SIZE, SIZE), (245, 250, 249, 255))
    touch_background.alpha_composite(img)
    touch_icon = touch_background.resize(
        (touch_size, touch_size), Image.Resampling.LANCZOS
    ).convert("RGB")
    touch_path = PUBLIC_DIR / "apple-touch-icon.png"
    touch_icon.save(touch_path, "PNG", optimize=True)

    print(f"Saved favicon set to {PUBLIC_DIR}")


if __name__ == "__main__":
    main()
