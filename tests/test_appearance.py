import unittest
from kiki.ui.appearance import PALETTES
from kiki.infrastructure.settings import Settings


def luminance(color):
    channels = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    channels = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return sum(c * weight for c, weight in zip(channels, (0.2126, 0.7152, 0.0722)))


class AppearanceTests(unittest.TestCase):
    def test_reading_and_button_contrast(self):
        for name, palette in PALETTES.items():
            for foreground, background in [('TEXT', 'BG'), ('MUTED', 'BG'), ('MUTED', 'SIDEBAR'),
                                           ('TEXT', 'SELECTED'), ('TEXT', 'SURFACE'), ('ON_BUTTON', 'BUTTON')]:
                high, low = sorted([luminance(palette[foreground]), luminance(palette[background])], reverse=True)
                with self.subTest(theme=name, pair=(foreground, background)):
                    self.assertGreaterEqual((high + 0.05) / (low + 0.05), 4.5)

    def test_invalid_reading_preferences_rejected(self):
        for kwargs in [{'theme': 'blue'}, {'font_size': 10}, {'font_size': 19}, {'font_size': True}, {'font_family': ''}]:
            with self.assertRaises(ValueError):
                Settings(**kwargs)
