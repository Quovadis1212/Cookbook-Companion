from flask import Flask, render_template, request, session
import requests
from bs4 import BeautifulSoup
import pymysql
import os


def crawl_swissmilk_recipes(NumberofRecipes):
    """
    Extrahiert eine angegebene Anzahl von Rezepten von der Swissmilk-Website.
    
    Parameter:
    - NumberofRecipes: Die Anzahl der Rezepte, die abgerufen werden sollen.
    
    Gibt eine Liste von Rezepten zurück, wobei jedes Rezept als ein Dictionary von Details dargestellt wird.
    """
    # URL für die Rezeptliste
    url = f'https://www.swissmilk.ch/de/rezepte-kochideen/neue-rezepte/?n={NumberofRecipes+1}'
    print(f"Requesting recipe links from: {url}")
    response = requests.get(url)
    html_content = response.text

    # BeautifulSoup initialisieren, um HTML-Inhalte zu parsen
    soup = BeautifulSoup(html_content, 'html.parser')
    recipe_links = soup.find_all('a', class_='ArticleTeaser')

    # Extrahiere und sammle die URL jedes Rezepts
    recipe_url_list = []
    for link in recipe_links:
        recipe_url = link.get('href')
        if recipe_url.startswith('/de/rezepte-kochideen/rezepte/'):
            recipe_url = 'https://www.swissmilk.ch' + recipe_url
            recipe_url_list.append(recipe_url)

    recipe_list = []
    # Durchlaufe die gesammelten URLs, um Rezeptdetails zu extrahieren
    for url in recipe_url_list:
        print(f"Requesting recipes from: {url}")
        response = requests.get(url)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extrahiere Rezeptdetails wie Namen, Zutaten, Kochzeit, etc.
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
            return f"Die Zutaten-Tabelle wurde nicht gefunden für {gerichtname}"

        # Kochzeit finden
        kochzeit_tag = soup.find('span', class_='RecipeFacts--fact--text')
        hours, minutes = 0, 0
        if kochzeit_tag:
            kochzeit_string = kochzeit_tag.text.strip()
            if 'h' in kochzeit_string:
                parts = kochzeit_string.split('h')
                hours = int(parts[0])
                kochzeit_string = parts[1] if len(parts) > 1 else '0'
            if 'min' in kochzeit_string:
                minutes = int(kochzeit_string.replace('min', ''))
            kochzeit = hours * 60 + minutes  
        else:
            return f'Kochzeit nicht gefunden für {gerichtname}'

        # Zubereitung finden
        zubereitung = soup.find('ol', class_='PreparationList--list')
        zubereitungsschritte = [step.string.strip() for step in zubereitung.find_all('span', itemprop='text')]

        vegi_span = soup.find('span', class_='RecipeFacts--fact--text', string='Vegi')

        # Vegetarisch finden
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
    """
    Fügt die extrahierten Rezeptdaten in eine Datenbank ein.
    
    Parameter:
    - recipe_data: Liste von Rezepten, die eingefügt werden sollen.
    - connection: Eine Verbindung zur Datenbank.
    
    Gibt die Anzahl der erfolgreich eingefügten Rezepte zurück.
    """
    success_count = 0
    for recipe in recipe_data:
            try:

                with connection.cursor() as cursor:
                    # SQL-Anweisungen zum Einfügen von Rezeptdetails
                    sql = "INSERT INTO recipes (name, cooking_time, is_vegetarian, url, blacklist) VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(sql, (recipe['Gerichtname'], recipe['Kochzeit'], recipe['Vegetarisch'], recipe['URL'], False))
                    recipe_id = cursor.lastrowid  
                    
                    # Zutaten einfügen
                    for ingredient in recipe['Zutaten']:
                        sql = "INSERT INTO ingredients (recipe_id, ingredient) VALUES (%s, %s)"
                        cursor.execute(sql, (recipe_id, ingredient))

                    # Kochschritte einfügen
                    for step_number, step in enumerate(recipe['Zubereitung'], start=1):
                        sql = "INSERT INTO preparation_steps (recipe_id, step_number, step_description) VALUES (%s, %s, %s)"
                        cursor.execute(sql, (recipe_id, step_number, step))
                # Commit, um die Änderungen in der Datenbank zu speichern
                connection.commit()
                success_count += 1
            except pymysql.err.IntegrityError as e:
                # Wenn das Rezept bereits in der Datenbank vorhanden ist, überspringen Sie es
                print(f"Recipe {recipe['Gerichtname']} already exists in the database. Skipping...")
                connection.rollback()
                continue
    return success_count

def get_recipes_from_database(connection, filter_ingredients=None, filter_cooking_time=None, filter_is_vegetarian=None):
    """
    Ruft Rezepte aus der Datenbank basierend auf den übergebenen Filterkriterien ab.

    Parameter:
    - connection: Eine Verbindung zur Datenbank.
    - filter_ingredients: Eine Liste von Zutaten, nach denen gefiltert werden soll. Optional.
    - filter_cooking_time: Maximale Kochzeit in Minuten, nach der gefiltert werden soll. Optional.
    - filter_is_vegetarian: Ein Boolscher Wert, der angibt, ob nur vegetarische Rezepte abgerufen werden sollen. Optional.

    Gibt eine Liste von Rezepten zurück, wobei jedes Rezept als Dictionary mit Details dargestellt wird.
    """
    complete_recipes = []
    with connection.cursor() as cursor:
        # Vorbereitung der Filterkriterien für die SQL-Abfrage
        where_clause_parts = []
        filter_values = []
        join_clause = ""

        # Filterung nach Zutaten, wenn angegeben
        if filter_ingredients is not None:
            where_clause_parts.extend(["ingredients.ingredient LIKE %s" for _ in filter_ingredients])
            filter_values.extend([f"%{ingredient}%" for ingredient in filter_ingredients])
            join_clause = " JOIN ingredients ON recipes.id = ingredients.recipe_id"

        # Aufbau des SQL-Queries mit optionalen Filtern
        sql_recipe = "SELECT DISTINCT recipes.* FROM recipes" + join_clause

        # Weitere Filter hinzufügen
        additional_filters = []
        if filter_cooking_time is not None:
            additional_filters.append("recipes.cooking_time <= %s")
            filter_values.append(filter_cooking_time)
        
        if filter_is_vegetarian is not None:
            additional_filters.append("recipes.is_vegetarian = %s")
            filter_values.append(1 if filter_is_vegetarian else 0)

        # Zusammenstellung der WHERE-Klausel
        if where_clause_parts:
            ingredients_where_clause = " OR ".join(where_clause_parts)
            additional_where_clause = " AND ".join(additional_filters)
            if additional_where_clause:
                where_clause = f"({ingredients_where_clause}) AND {additional_where_clause}"
            else:
                where_clause = ingredients_where_clause
            sql_recipe += " WHERE " + where_clause
            sql_recipe += " GROUP BY recipes.id ORDER BY COUNT(DISTINCT ingredients.ingredient) DESC LIMIT 10"
        
        # Ausführung der SQL-Abfrage und Sammeln der Ergebnisse
        print(f"Final SQL Query: {sql_recipe}")
        print(f"Filter Values: {filter_values}")
        cursor.execute(sql_recipe, filter_values)
        recipes = cursor.fetchall()
        print(f"Recipes: {recipes}")

        # Verarbeitung der Rezeptdaten und Rückgabe
        for recipe in recipes:
            # Annahme, dass 'id' die erste Spalte in der 'recipes'-Tabelle ist
            recipe_id = recipe[0]

            # Abrufen der Zutaten und Zubereitungsschritte für jedes Rezept
            sql_ingredients = "SELECT ingredient FROM ingredients WHERE recipe_id = %s"
            cursor.execute(sql_ingredients, (recipe_id,))
            ingredients = cursor.fetchall()
            ingredients = [ingredient[0] for ingredient in ingredients]
            sql_preparation_steps = "SELECT step_number, step_description FROM preparation_steps WHERE recipe_id = %s"
            cursor.execute(sql_preparation_steps, (recipe_id,))
            preparation_steps = cursor.fetchall()
            ingredients_string = ", ".join([str(ingredient) for ingredient in ingredients])

            # Zusammenstellung der Rezeptdaten als Dictionary
            recipe_data = {
                'id': recipe_id,
                'name': recipe[1],
                'cooking_time': recipe[2],
                'is_vegetarian': recipe[3],
                'blacklist': recipe[4],
                'url': recipe[5],
                'ingredients': ingredients_string,
                'preparation_steps': preparation_steps
            }
            complete_recipes.append(recipe_data)
    return complete_recipes


# Initialisierung der Flask-Anwendung mit einem geheimen Schlüssel für die Sessionverwaltung
app = Flask(__name__)
app.secret_key = 'cccooking'
@app.route('/', methods=['GET', 'POST'])

def index():
    """
    Hauptansicht der Webanwendung, die sowohl GET- als auch POST-Anfragen verarbeitet.
    Ermöglicht das Crawlen neuer Rezepte, das Filtern von Rezepten nach bestimmten Kriterien und das Anzeigen gefilterter Rezepte.
    """

    # Verbindung zur Datenbank initialisieren
    connection = pymysql.connect(
    host=os.environ.get('DATABASE_HOST'),
    user=os.environ.get('DATABASE_USER'),
    password=os.environ.get('DATABASE_PASSWORD'),
    db="RecipeCache")
    status = None

    # Initialisierung der Filterkriterien aus der Sitzung
    filter_criteria = session.get('filter_criteria', {})

    
    if request.method == 'POST':
        # Verarbeitung der Formularanfrage zum Crawlen neuer Rezepte
        if 'Crawl_Recipes' in request.form:
            if request.form['number_of_recipes']:
                number_of_recipes = abs(int(request.form['number_of_recipes']))
            else:
                number_of_recipes = 10
                try:
                    success_count = insert_into_database(crawl_swissmilk_recipes(number_of_recipes), connection)
                    status = f"Inserted {success_count} new recipes into the database."
                finally:
                    connection.close()
                return render_template('index.html', status=status, filter_criteria=filter_criteria)
           
        # Verarbeitung der Filteranfrage aus dem Formular
        elif 'Filter_Recipes' in request.form:
            user_input = request.form['ingredient_filter']
            filter_ingredients = [ingredient.strip().lower() for ingredient in user_input.split(',')]
            
            is_vegetarian = 'is_vegetarian' in request.form
            cooking_time = request.form.get('cooking_time_filter', None)
            
            
            filter_criteria = {
                'filter_ingredients': filter_ingredients,
                'filter_is_vegetarian': True if is_vegetarian else None, 
                'filter_cooking_time': int(cooking_time) if cooking_time.isdigit() else None 
            }
            
            session['filter_criteria'] = filter_criteria  
            

        # Zurücksetzen der Filterkriterien
        elif 'Reset_Filter' in request.form:
            session.pop('filter_criteria', None)
            filter_criteria = {}
            
        # Anzeigen von Rezepten basierend auf den Filterkriterien
        elif 'Show_Recipes' in request.form:
            try:
                
                recipes = get_recipes_from_database(connection, **filter_criteria) if filter_criteria else get_recipes_from_database(connection)
                print(f"Number of Recipes: {len(recipes)}")
            finally:
                connection.close()
            return render_template('index.html', recipes=recipes, filter_criteria=filter_criteria)
        
    # Standard-Rückgabe, wenn keine POST-Anfrage bearbeitet wird
    return render_template('index.html', filter_criteria=filter_criteria)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)