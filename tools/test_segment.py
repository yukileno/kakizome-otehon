"""文字から離れた微小な墨を除き、点や濁点を残す回帰テスト。"""
import json
from pathlib import Path
import re
import unittest
from PIL import Image, ImageDraw
from segment import character_ink_bbox


class CharacterBoundsTest(unittest.TestCase):
    def test_noise_is_ignored_but_detached_marks_remain(self):
        ink = Image.new("L", (100, 100), 0)
        draw = ImageDraw.Draw(ink)
        draw.rectangle((20, 20, 60, 80), fill=255)
        draw.rectangle((70, 10, 73, 13), fill=255)
        draw.point((1, 95), fill=255)
        self.assertEqual(character_ink_bbox(ink), (20, 10, 74, 81))

    def test_thin_connected_stroke_is_preserved(self):
        ink = Image.new("L", (100, 100), 0)
        draw = ImageDraw.Draw(ink)
        draw.rectangle((20, 20, 60, 80), fill=255)
        draw.line((1, 50, 20, 50), fill=255)
        self.assertEqual(character_ink_bbox(ink), (1, 20, 61, 81))

    def test_empty_and_tiny_images(self):
        self.assertIsNone(character_ink_bbox(Image.new("L", (10, 10), 0)))
        ink = Image.new("L", (10, 10), 0)
        ink.putpixel((3, 4), 255)
        self.assertEqual(character_ink_bbox(ink), (3, 4, 4, 5))

    def test_reported_character_bounds(self):
        root = Path(__file__).resolve().parent.parent
        text = (root / "img/manifest.js").read_text(encoding="utf-8")
        images = json.loads(re.search(r"window\.GEN_IMAGES = (.*?);", text, re.S)[1])
        self.assertEqual(images["あかるい"]["segs"][3][2:], [15, 978])
        self.assertEqual(images["青い空"]["segs"][2][2:], [579, 1655])


if __name__ == "__main__":
    unittest.main()
