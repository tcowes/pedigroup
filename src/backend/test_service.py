import os
from django.test import TestCase

from backend.exceptions import WrongHeadersForCsv
from backend.models import Product, Restaurant
from backend.service import create_entities_through_csv

class TestCsvLoader(TestCase):
    
    def test_restaurants_and_products_get_created_with_csv(self):
        csv_path = os.path.join(os.path.dirname(__file__), 'test_data', 'eden.csv')
        with open(csv_path, "r") as csvfile:
            restaurants, products, omitted_rows = create_entities_through_csv(csvfile)
        self.assertEqual(Restaurant.objects.filter(name="Empanadas del Eden").count(), 1)
        self.assertEqual(Product.objects.filter(restaurant__name="Empanadas del Eden").count(), 5)
        self.assertEqual(restaurants, 1)
        self.assertEqual(products, 5)
        self.assertEqual(omitted_rows, 0)

    def test_rows_get_ommited_if_restaurant_or_product_are_blank(self):
        csv_path = os.path.join(os.path.dirname(__file__), 'test_data', 'eden_with_blanks.csv')
        with open(csv_path, "r") as csvfile:
            _, _, omitted_rows = create_entities_through_csv(csvfile)
        self.assertEqual(omitted_rows, 2)

    def test_product_price_defaults_to_zero(self):
        csv_path = os.path.join(os.path.dirname(__file__), 'test_data', 'eden_without_prices.csv')
        with open(csv_path, "r") as csvfile:
            _, _, omitted_rows = create_entities_through_csv(csvfile)
        self.assertEqual(Product.objects.filter(estimated_price=0.0, restaurant__name="Empanadas del Eden").count(), 2)
        self.assertEqual(omitted_rows, 0)

    def test_exception_gets_raised_if_the_columns_are_incorrect(self):
        csv_path = os.path.join(os.path.dirname(__file__), 'test_data', 'lowercase.csv')
        with open(csv_path, "r") as csvfile:
            with self.assertRaises(WrongHeadersForCsv):
                create_entities_through_csv(csvfile)

    def test_exception_gets_raised_if_we_receive_csv_with_too_much_columns(self):
        csv_path = os.path.join(os.path.dirname(__file__), 'test_data', 'exceeded_headers.csv')
        with open(csv_path, "r") as csvfile:
            with self.assertRaises(WrongHeadersForCsv):
                create_entities_through_csv(csvfile)