import unittest

from qr_utils import (
    MIN_QUIET_ZONE,
    contrast_ratio,
    generate_qr,
    get_slug,
    normalize_link,
)


class QRUtilsTests(unittest.TestCase):
    def test_normalize_link_adds_https(self):
        self.assertEqual(normalize_link(" janebi.com/product "), "https://janebi.com/product")

    def test_normalize_link_preserves_existing_scheme(self):
        self.assertEqual(normalize_link("mailto:test@example.com"), "mailto:test@example.com")

    def test_generate_qr_enforces_four_module_quiet_zone(self):
        box_size = 10
        image = generate_qr("janebi.com", "#000000", "#FFFFFF", box_size, 0)
        minimum_size = (21 + (2 * MIN_QUIET_ZONE)) * box_size
        self.assertGreaterEqual(image.width, minimum_size)
        self.assertEqual(image.getpixel((0, 0)), (255, 255, 255, 255))

    def test_generate_qr_supports_transparency(self):
        image = generate_qr("https://janebi.com", "#000000", None, 10, 4)
        self.assertEqual(image.getpixel((0, 0))[3], 0)
        self.assertIn(255, image.getchannel("A").getextrema())

    def test_contrast_ratio_flags_similar_colors(self):
        self.assertLess(contrast_ratio("#777777", "#888888"), 4.5)
        self.assertGreater(contrast_ratio("#000000", "#FFFFFF"), 4.5)

    def test_slug_is_safe_for_zip_filename(self):
        self.assertEqual(get_slug("https://example.com/a product/?ref=1"), "a_product")


if __name__ == "__main__":
    unittest.main()
