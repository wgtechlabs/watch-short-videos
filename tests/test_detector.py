import unittest
from engine.cli import detect_platform

class PlatformTests(unittest.TestCase):
    def test_supported(self):
        for url, expected in [
            ("https://www.facebook.com/reel/123", "facebook"),
            ("https://www.instagram.com/reel/123/", "instagram"),
            ("https://www.tiktok.com/@a/video/123", "tiktok"),
            ("https://www.youtube.com/shorts/123", "youtube"),
        ]:
            self.assertEqual(detect_platform(url), expected)

    def test_rejects_spoofed_domain(self):
        with self.assertRaises(ValueError):
            detect_platform("https://youtube.com.evil.test/shorts/123")

if __name__ == "__main__":
    unittest.main()
