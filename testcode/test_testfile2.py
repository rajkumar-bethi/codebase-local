import unittest
from testfile2 import generate_six_digit_random_number

class TestSixDigitRandomNumber(unittest.TestCase):
    def test_range(self):
        for _ in range(1000):  # Test multiple times for randomness
            num = generate_six_digit_random_number()
            self.assertTrue(100000 <= num <= 999999, f"Number {num} is not six digits")
            self.assertEqual(len(str(num)), 6, f"Number {num} does not have 6 digits")

if __name__ == "__main__":
    unittest.main()
