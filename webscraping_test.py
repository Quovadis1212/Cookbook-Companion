#!/bin/env python
import pymysql
import requests
from bs4 import BeautifulSoup

def get_swissmilk_recipes(NumberofRecipes):
        
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

    # Return the recipe_list instead of printing it
    return recipe_list

def insert_into_database(recipe_data, connection):
    for recipe in recipe_data:
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

        # Commit to save changes
        connection.commit()

def main():
    number_of_recipes = 10  # Or any other number you choose
    recipe_data = get_swissmilk_recipes(number_of_recipes)

    # Database connection
    connection = pymysql.connect(host='192.168.1.242', user='dave', password='lustud', db='RecipeCache')

    try:
        insert_into_database(recipe_data, connection)
    finally:
        connection.close()

if __name__ == '__main__':
    main()