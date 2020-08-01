import unittest
from helpers.spain_geography import get_impact_string


class SpainGeographyUnitTest(unittest.TestCase):

    def test_given_ccaa_and_negative_number_when_get_impact_string_then_empty_string_returned(self):
        self.assertEqual("", get_impact_string(-1, "Madrid"))

    def test_given_ccaa_and_zero_when_get_impact_string_then_empty_string_returned(self):
        self.assertEqual("", get_impact_string(0, "Madrid"))

    def test_given_ccaa_and_positive_when_get_impact_string_then_impact_returned(self):
        self.assertEqual("(0,15/millón)", get_impact_string(1, "Madrid"))

    def test_given_no_ccaa_and_positive_when_get_impact_string_then_spain_impact_returned(self):
        self.assertEqual("(0,02/millón)", get_impact_string(1))
