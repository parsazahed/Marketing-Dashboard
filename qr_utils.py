import re
from urllib.parse import unquote, urlparse

import qrcode


MIN_QUIET_ZONE = 4


def normalize_link(value):
    """Return a trimmed URL with a scheme suitable for QR scanners."""
    link = str(value).strip()
    if not link:
        return ""

    parsed = urlparse(link)
    if parsed.scheme:
        return link
    if link.startswith("//"):
        return f"https:{link}"
    return f"https://{link}"


def _hex_to_rgb(value):
    value = value.lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", value):
        raise ValueError("Colors must use the #RRGGBB format.")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def contrast_ratio(foreground, background):
    """Calculate the WCAG contrast ratio between two hex colors."""
    def relative_luminance(color):
        channels = []
        for channel in _hex_to_rgb(color):
            channel /= 255
            channels.append(
                channel / 12.92
                if channel <= 0.04045
                else ((channel + 0.055) / 1.055) ** 2.4
            )
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

    light, dark = sorted(
        (relative_luminance(foreground), relative_luminance(background)),
        reverse=True,
    )
    return (light + 0.05) / (dark + 0.05)


def generate_qr(link, fill_hex, back_hex_or_none, box, border):
    """Generate a QR image while enforcing the scanner-safe quiet zone."""
    normalized_link = normalize_link(link)
    if not normalized_link:
        raise ValueError("A link is required.")

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box,
        border=max(MIN_QUIET_ZONE, border),
    )
    qr.add_data(normalized_link)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    fill_rgb = _hex_to_rgb(fill_hex)
    background = _hex_to_rgb(back_hex_or_none) if back_hex_or_none else None

    pixels = []
    for pixel in image.getdata():
        if pixel[0] == 0:
            pixels.append(fill_rgb + (255,))
        elif background:
            pixels.append(background + (255,))
        else:
            pixels.append((255, 255, 255, 0))

    image.putdata(pixels)
    return image


def get_slug(url):
    """Create a safe, stable filename stem from a URL."""
    normalized_url = normalize_link(url)
    parsed = urlparse(normalized_url)
    candidate = unquote(parsed.path.rstrip("/").rsplit("/", 1)[-1])
    if not candidate:
        candidate = parsed.hostname or "qr_code"

    candidate = re.sub(r"[^\w.-]+", "_", candidate, flags=re.UNICODE).strip("._")
    return candidate[:100] or "qr_code"
