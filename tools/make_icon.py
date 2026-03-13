from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def build_icon(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Notebook page background (high contrast border so it reads at 16x16)
    draw.rounded_rectangle(
        (24, 24, size - 24, size - 24),
        radius=32,
        fill=(255, 255, 255, 255),
        outline=(47, 111, 235, 255),
        width=10,
    )

    # Simplified dark spiral binding on the left
    for i in range(6):
        y = 60 + i * 28
        draw.rounded_rectangle(
            (32, y, 56, y + 18),
            radius=6,
            fill=(43, 45, 49, 255),
        )

    # Big "S" in the middle (oversized so it survives downscaling)
    try:
        font = ImageFont.truetype("Segoe UI Bold", 190)
    except Exception:
        font = ImageFont.load_default()

    text = "S"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2 + 6
    ty = (size - th) // 2 - 12
    draw.text((tx, ty), text, font=font, fill=(47, 111, 235, 255))

    # Save multi-size ICO
    img.save(output, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / "assets" / "SafeNote.ico"
    build_icon(out)


if __name__ == "__main__":
    main()

