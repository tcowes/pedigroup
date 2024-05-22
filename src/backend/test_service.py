import os
import random

from django.test import TestCase

from backend.exceptions import WrongHeadersForCsv
from backend.models import Product, Restaurant, Group
from backend.service import create_entities_through_csv


def create_group() -> Group:
    group = Group.objects.create(name='Test group', id_app=random.randint(1, 100))
    return group


class TestCsvLoader(TestCase):
    
    def test_restaurants_and_products_get_created_with_csv(self):
        group = create_group()
        csv_path = os.path.join(os.path.dirname(__file__), 'test_data', 'eden.csv')
        with open(csv_path, "r") as csvfile:
            restaurants, products, omitted_rows = create_entities_through_csv(csvfile, group.id_app)
        self.assertEqual(Restaurant.objects.filter(name="Empanadas Del Eden").count(), 1)
        self.assertEqual(Product.objects.filter(restaurant__name="Empanadas Del Eden").count(), 5)
        self.assertEqual(restaurants, 1)
        self.assertEqual(products, 5)
        self.assertEqual(omitted_rows, 0)

    def test_rows_get_ommited_if_restaurant_or_product_are_blank(self):
        group = create_group()
        csv_path = os.path.join(os.path.dirname(__file__), 'test_data', 'eden_with_blanks.csv')
        with open(csv_path, "r") as csvfile:
            _, _, omitted_rows = create_entities_through_csv(csvfile, group.id_app)
        self.assertEqual(omitted_rows, 2)

    def test_product_price_defaults_to_zero(self):
        group = create_group()
        csv_path = os.path.join(os.path.dirname(__file__), 'test_data', 'eden_without_prices.csv')
        with open(csv_path, "r") as csvfile:
            _, _, omitted_rows = create_entities_through_csv(csvfile, group.id_app)
        self.assertEqual(Product.objects.filter(estimated_price=0.0, restaurant__name="Empanadas Del Eden").count(), 2)
        self.assertEqual(omitted_rows, 0)

    def test_exception_gets_raised_if_the_columns_are_incorrect(self):
        group = create_group()
        csv_path = os.path.join(os.path.dirname(__file__), 'test_data', 'lowercase.csv')
        with open(csv_path, "r") as csvfile:
            with self.assertRaises(WrongHeadersForCsv):
                create_entities_through_csv(csvfile, group.id_app)

    def test_exception_gets_raised_if_we_receive_csv_with_too_much_columns(self):
        group = create_group()
        csv_path = os.path.join(os.path.dirname(__file__), 'test_data', 'exceeded_headers.csv')
        with open(csv_path, "r") as csvfile:
            with self.assertRaises(WrongHeadersForCsv):
                create_entities_through_csv(csvfile, group.id_app)

    def test_two_groups_create_different_entities_with_the_same_csv(self):
        group_1 = create_group()
        group_2 = create_group()
        csv_path = os.path.join(os.path.dirname(__file__), 'test_data', 'eden.csv')
        with open(csv_path, "r") as csvfile:
            create_entities_through_csv(csvfile, group_1.id_app)
        with open(csv_path, "r") as csvfile:
            create_entities_through_csv(csvfile, group_2.id_app)

        # Primero validamos que en el sistema se crearon las entidades repetidas:
        self.assertEqual(Restaurant.objects.filter(name="Empanadas Del Eden").count(), 2)
        self.assertEqual(Product.objects.filter(restaurant__name="Empanadas Del Eden").count(), 10)
        # Despues validamos que pertenecen a grupos distintos:
        self.assertEqual(group_1.restaurants.count(), 1)
        self.assertEqual(group_2.restaurants.count(), 1)
        self.assertEqual(group_1.restaurants.first().name, group_2.restaurants.first().name)
        self.assertNotEqual(group_1.restaurants.first().id, group_2.restaurants.first().id)
