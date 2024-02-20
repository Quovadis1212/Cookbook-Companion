import unittest
from unittest.mock import MagicMock

from app import insert_into_database

class TestInsertIntoDatabase(unittest.TestCase):
    def setUp(self):
        # Create a mock connection object
        self.connection = MagicMock()

    def test_insert_into_database_success(self):
        # Define the recipe data to be inserted
        recipe_data = [
            {
                'Gerichtname': 'Spaghetti Bolognese',
                'Kochzeit': 30,
                'Vegetarisch': False,
                'URL': 'https://example.com/recipe1',
                'Zutaten': ['Spaghetti', 'Tomato Sauce', 'Ground Beef'],
                'Zubereitung': ['Cook spaghetti', 'Make bolognese sauce', 'Serve']
            },
            {
                'Gerichtname': 'Caesar Salad',
                'Kochzeit': 15,
                'Vegetarisch': True,
                'URL': 'https://example.com/recipe2',
                'Zutaten': ['Lettuce', 'Croutons', 'Caesar Dressing'],
                'Zubereitung': ['Chop lettuce', 'Add croutons', 'Toss with dressing']
            }
        ]

        # Call the function
        success_count = insert_into_database(recipe_data, self.connection)

        # Assert that the success count is equal to the number of recipes
        self.assertEqual(success_count, len(recipe_data))

        # Assert that the execute method of the cursor is called for each recipe
        self.assertEqual(self.connection.cursor().execute.call_count, len(recipe_data) * 3)

        # Assert that the commit method is called once
        self.assertEqual(self.connection.commit.call_count, 1)

    def test_insert_into_database_duplicate_recipe(self):
        # Define the recipe data to be inserted
        recipe_data = [
            {
                'Gerichtname': 'Spaghetti Bolognese',
                'Kochzeit': 30,
                'Vegetarisch': False,
                'URL': 'https://example.com/recipe1',
                'Zutaten': ['Spaghetti', 'Tomato Sauce', 'Ground Beef'],
                'Zubereitung': ['Cook spaghetti', 'Make bolognese sauce', 'Serve']
            },
            {
                'Gerichtname': 'Spaghetti Bolognese',
                'Kochzeit': 30,
                'Vegetarisch': False,
                'URL': 'https://example.com/recipe1',
                'Zutaten': ['Spaghetti', 'Tomato Sauce', 'Ground Beef'],
                'Zubereitung': ['Cook spaghetti', 'Make bolognese sauce', 'Serve']
            }
        ]

        # Call the function
        success_count = insert_into_database(recipe_data, self.connection)

        # Assert that the success count is equal to 1
        self.assertEqual(success_count, 1)

        # Assert that the execute method of the cursor is called once for the first recipe
        self.assertEqual(self.connection.cursor().execute.call_count, 3)

        # Assert that the commit method is called once
        self.assertEqual(self.connection.commit.call_count, 1)

        # Assert that the rollback method is called once
        self.assertEqual(self.connection.rollback.call_count, 1)

if __name__ == '__main__':
    unittest.main()