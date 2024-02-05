from flask import Flask, render_template, request, session
import requests
from bs4 import BeautifulSoup
import pymysql

def crawl_swissmilk_recipes(NumberofRecipes):
        
    # recipe-list-URL
    url = f'https://www.swissmilk.ch/de/rezepte-kochideen/neue-rezepte/?n={NumberofRecipes+1}'
    print(f"Requesting recipe links from: {url}")
    response = requests.get(url)
    html_content = response.text

    # BeautifulSoup initialisieren
    soup = BeautifulSoup(html_content, 'html.parser')
    recipe_links = soup.find_all('a', class_='ArticleTeaser')

    # Extract and print the href attribute of each link where the link is like "/de/rezepte-kochideen/rezepte/"
    recipe_url_list = []
    for link in recipe_links:
        recipe_url = link.get('href')
        if recipe_url.startswith('/de/rezepte-kochideen/rezepte/'):
            recipe_url = 'https://www.swissmilk.ch' + recipe_url
            recipe_url_list.append(recipe_url)
        else:
            continue

    recipe_list = []
    # start loop over recipe_url_list and extract recipe information
    for url in recipe_url_list:
        # Die Anfrage an die Webseite senden und den HTML-Code abrufen
        print(f"Requesting recipes from: {url}")
        response = requests.get(url)

        html_content = response.text

        # BeautifulSoup initialisieren
        soup = BeautifulSoup(html_content, 'html.parser')

        # Gerichtname finden
        gerichtname = soup.find('h1', class_='DetailPageHeader--title').string.strip()

        # Zutaten finden
        zutaten_table = soup.find('table', class_='IngredientsCalculator--groups')
        if zutaten_table:
            zutaten_rows = zutaten_table.find_all('tr')
            zutaten_liste = []
            for row in zutaten_rows:
                zutat = row.find('th', class_='Ingredient--text')
                menge = row.find('td', class_='Ingredient--amount')
                if zutat and menge:
                    zutaten_liste.append(f"{menge.text.strip().replace('\n', '')} {zutat.text.strip()}")
        else:
            # Return an error message instead of printing
            return f"Die Zutaten-Tabelle wurde nicht gefunden für {gerichtname}"

        # Kochzeit finden
        kochzeit_tag = soup.find('span', class_='RecipeFacts--fact--text')
        if kochzeit_tag:
            kochzeit = kochzeit_tag.text.strip()
        else:
            # Return an error message instead of printing
            return f'Kochzeit nicht gefunden für {gerichtname}'

        # Zubereitung finden
        zubereitung = soup.find('ol', class_='PreparationList--list')
        zubereitungsschritte = [step.string.strip() for step in zubereitung.find_all('span', itemprop='text')]

        vegi_span = soup.find('span', class_='RecipeFacts--fact--text', string='Vegi')

        # Check if Vegi span is found and if it is the second occurrence of the class 'RecipeFacts--fact--text'
        if vegi_span and soup.find_all('span', class_='RecipeFacts--fact--text').index(vegi_span) == 1:
            vegi = True
        else:
            vegi = False

        # Erstelle ein Objekt für die gefundenen Informationen
        recipe = {
            'Gerichtname': gerichtname,
            'Zutaten': zutaten_liste,
            'Kochzeit': kochzeit,
            'Zubereitung': zubereitungsschritte,
            'Vegetarisch': vegi,
            'URL': url
        }
        recipe_list.append(recipe)
    print(recipe_list)
    return recipe_list

def insert_into_database(recipe_data, connection):
    success_count = 0
    for recipe in recipe_data:
            try:
                with connection.cursor() as cursor:
                    # Insert recipe into recipes table
                    sql = "INSERT INTO recipes (name, cooking_time, is_vegetarian, url, blacklist) VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(sql, (recipe['Gerichtname'], recipe['Kochzeit'], recipe['Vegetarisch'], recipe['URL'], False))
                    
                    recipe_id = cursor.lastrowid  # Get the last inserted id
                    
                    # Insert ingredients
                    for ingredient in recipe['Zutaten']:
                        sql = "INSERT INTO ingredients (recipe_id, ingredient) VALUES (%s, %s)"
                        cursor.execute(sql, (recipe_id, ingredient))

                    # Insert preparation steps
                    for step_number, step in enumerate(recipe['Zubereitung'], start=1):
                        sql = "INSERT INTO preparation_steps (recipe_id, step_number, step_description) VALUES (%s, %s, %s)"
                        cursor.execute(sql, (recipe_id, step_number, step))
                    success_count += 1
                # Commit to save changes
                connection.commit()
            except pymysql.err.IntegrityError as e:
                print(f"Recipe {recipe['Gerichtname']} already exists in the database. Skipping...")
                connection.rollback()
                continue
    return success_count

def get_recipes_from_database(connection, filter_ingredients=None):
    complete_recipes = []
    with connection.cursor() as cursor:
        sql_recipe = "SELECT DISTINCT recipes.* FROM recipes"

        if filter_ingredients:
            # Calculate the threshold for 50% + 1 of the filter ingredients
            threshold = len(filter_ingredients) // 2 + 1
            
            # Start building the WHERE clause with parameter placeholders
            where_clause_parts = ["ingredient LIKE %s" for _ in filter_ingredients]
            where_clause = " OR ".join(where_clause_parts)
            print(f"Where Clause: {where_clause}")
            
            # Define the SQL for the subquery with placeholders for parameters
            matching_subquery = f"""
            SELECT recipe_id
            FROM ingredients
            WHERE {where_clause}
            GROUP BY recipe_id
            HAVING COUNT(DISTINCT ingredient) >= %s
            """
            
            # Add the calculated threshold to the end of the list of filter values
            filter_values = [f"%{ingredient}%" for ingredient in filter_ingredients] + [threshold]
            
            # Prepare the final SQL query with the subquery embedded
            sql_recipe = f"""
            SELECT recipes.* FROM recipes
            JOIN ({matching_subquery}) AS matching_recipes ON recipes.id = matching_recipes.recipe_id
            """
            
            # Execute the query with the filter values
            cursor.execute(sql_recipe, filter_values)
        else:
            cursor.execute(sql_recipe)

        recipes = cursor.fetchall()
        
        for recipe in recipes:
            # Assuming 'id' is the first column in the 'recipes' table
            recipe_id = recipe[0]

            sql_ingredients = "SELECT ingredient FROM ingredients WHERE recipe_id = %s"
            cursor.execute(sql_ingredients, (recipe_id,))
            ingredients = cursor.fetchall()
            
            # Convert each ingredient tuple to its first element
            ingredients = [ingredient[0] for ingredient in ingredients]

            sql_preparation_steps = "SELECT step_number, step_description FROM preparation_steps WHERE recipe_id = %s"
            cursor.execute(sql_preparation_steps, (recipe_id,))
            preparation_steps = cursor.fetchall()

            ingredients_string = ", ".join(ingredients)

            # Convert tuple data to dictionary format
            recipe_data = {
                'id': recipe_id,
                'name': recipe[1],  # Adjust these indices based on your table structure
                'cooking_time': recipe[2],
                'is_vegetarian': recipe[3],
                'blacklist': recipe[4],
                'url': recipe[5],
                'ingredients': ingredients_string,
                'preparation_steps': preparation_steps
            }
            complete_recipes.append(recipe_data)  # If you want to return a list of all recipes

    return complete_recipes



app = Flask(__name__)
app.secret_key = 'cccooking'
@app.route('/', methods=['GET', 'POST'])
def index():
    connection = pymysql.connect(host='HOST', user='YOURUSER', password='YOURPASS', db='RecipeCache')
    status = None

    # Initialize filter_criteria from session
    filter_criteria = session.get('filter_criteria', [])

    if request.method == 'POST':
        if 'Crawl_Recipes' in request.form:
            number_of_recipes = abs(int(request.form['number_of_recipes']))
            try:
                success_count = insert_into_database(crawl_swissmilk_recipes(number_of_recipes), connection)
                status = f"Inserted {success_count} new recipes into the database."
            finally:
                connection.close()
            return render_template('index.html', status=status, filter_criteria=filter_criteria)
        
        elif 'Filter_Recipes' in request.form:
            user_input = request.form['ingredient_filter']
            filter_ingredients = [ingredient.strip().lower() for ingredient in user_input.split(',')]
            filter_criteria = filter_ingredients
            session['filter_criteria'] = filter_criteria  # Store filter_criteria in session
            print(f"Filter Criteria (in Filter Recipes): {filter_criteria}")
        
        elif 'Show_Recipes' in request.form:
            try:
                print(f"Filter Criteria (in Show Recipes): {filter_criteria}")
                recipes = get_recipes_from_database(connection, filter_ingredients=filter_criteria) if filter_criteria else get_recipes_from_database(connection)
                print(f"Number of Recipes: {len(recipes)}")
            finally:
                connection.close()
            return render_template('index.html', recipes=recipes, filter_criteria=filter_criteria)

    return render_template('index.html', filter_criteria=filter_criteria)





if __name__ == '__main__':

    app.run(debug=True)
