from datetime import UTC, datetime, timezone
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont

DEFAULT_WIDTH = 900
DEFAULT_HEIGHT = 600


def _load_font(size: int, bold: bool = False):
    # Try common TTFs; fallback to default
    for name in ["DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", "arial.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _fetch_flag_image(url: str, size=(48, 32)):
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(url)
            r.raise_for_status()
            img = Image.open(BytesIO(r.content)).convert("RGBA")
            img.thumbnail(size, Image.Resampling.LANCZOS)
            return img
    except Exception:
        return None


def generate_summary_image(countries, filepath: str | None = None):
    try:
        base_dir = Path(__file__).resolve().parent
        cache_dir = base_dir / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        if filepath is None:
            filepath = cache_dir / "summary.png"
        else:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)

        print(f"Generating summary image at {filepath}...")

        top_5 = sorted(
            [c for c in countries if getattr(c, "estimated_gdp", None) is not None],
            key=lambda x: x.estimated_gdp,
            reverse=True,
        )[:5]

        width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT
        img = Image.new("RGB", (width, height), color="#f8fafc")
        draw = ImageDraw.Draw(img)

        # Fonts
        title_font = _load_font(36, bold=True)
        subtitle_font = _load_font(18)
        text_font = _load_font(16)

        # Header
        header_h = 110
        draw.rectangle([(0, 0), (width, header_h)], fill="#1e40af")
        draw.text((30, 28), "🌍 Country Summary Report", fill="white", font=title_font)

        # Stats
        total_text = f"Total Countries: {len(countries)}"
        # ✅ ISO 8601 UTC format (with Z suffix)
        date_text = (
            f"Last Refresh (UTC): {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}"
        )
        draw.text((30, header_h - 40), total_text, fill="white", font=subtitle_font)
        draw.text(
            (width - 400, header_h - 40), date_text, fill="white", font=subtitle_font
        )

        # Divider
        y_offset = header_h + 20
        draw.line([(30, y_offset), (width - 30, y_offset)], fill="#c7d2fe", width=2)

        # Top 5
        draw.text(
            (30, y_offset + 20),
            "🏆 Top 5 Countries by Estimated GDP",
            fill="#0f172a",
            font=subtitle_font,
        )

        start_y = y_offset + 60
        row_h = 56
        x_left = 30
        flag_size = (64, 40)

        if not top_5:
            draw.text(
                (30, start_y), "No GDP data available.", fill="#475569", font=text_font
            )
        else:
            for i, c in enumerate(top_5, start=1):
                top_y = start_y + (i - 1) * row_h
                draw.rectangle(
                    [(30, top_y - 6), (width - 30, top_y + row_h - 12)], fill="#ffffff"
                )

                # Flag
                flag_img = _fetch_flag_image(getattr(c, "flag_url", ""), size=flag_size)
                if flag_img:
                    img.paste(flag_img, (x_left, top_y - 4), flag_img)

                # Text
                text_x = x_left + flag_size[0] + 16
                name_text = f"{i}. {c.name}"
                gdp_text = f"Estimated GDP: ${c.estimated_gdp:,.2f}"
                draw.text((text_x, top_y), name_text, fill="#0b1226", font=text_font)
                draw.text(
                    (text_x, top_y + 22), gdp_text, fill="#334155", font=text_font
                )

        # Footer
        draw.line([(30, height - 60), (width - 30, height - 60)], fill="#e2e8f0")
        footer_text = "Generated automatically by Country Currency & Exchange API"
        draw.text((30, height - 40), footer_text, fill="#64748b", font=subtitle_font)

        img.save(filepath, format="PNG", optimize=True)
        print(f"✅ Summary image saved successfully at {filepath}")
        return str(filepath)

    except Exception as e:
        print(f"❌ Error generating summary image: {e}")
        return None
