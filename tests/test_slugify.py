import unittest

from app.utils.helpers import slugify


class SlugifyTests(unittest.TestCase):
    def test_slugify_preserves_uzbek_apostrophe_letters(self):
        cases = {
            "Oʻzbekiston gʻalabasi": 'ozbekiston-galabasi',
            "O‘zbekiston g‘alabasi": 'ozbekiston-galabasi',
            "O'zbekiston g'alabasi": 'ozbekiston-galabasi',
            "Gʻoya va Oʻquv": 'goya-va-oquv',
            "Oʻrnak boʻlsin": 'ornak-bolsin',
        }

        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(slugify(raw), expected)

    def test_slugify_removes_standalone_apostrophe_marks_without_breaking_words(self):
        self.assertEqual(slugify("Salom ʻ dunyo"), 'salom-dunyo')


if __name__ == '__main__':
    unittest.main()
