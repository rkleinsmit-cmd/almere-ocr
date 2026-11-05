import unittest
from ocr_quality_benchmark import benchmark


class BenchmarkTests(unittest.TestCase):
    def test_exact_match(self):
        result = benchmark("Almere 2026", "Almere 2026")
        self.assertEqual(result["cer"], 0)
        self.assertEqual(result["wer"], 0)

    def test_single_character_error(self):
        result = benchmark("kat", "kas")
        self.assertEqual(result["cer"], 1 / 3)
        self.assertEqual(result["wer"], 1)

    def test_missing_word(self):
        result = benchmark("een twee drie", "een drie")
        self.assertEqual(result["word_errors"], 1)
        self.assertEqual(result["wer"], 1 / 3)

    def test_no_reference_is_invalid(self):
        with self.assertRaises(ValueError):
            benchmark("", "some OCR")


if __name__ == "__main__":
    unittest.main()
