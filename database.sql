-- SQL-Skript zum Erstellen einer Datenbank für das Zwischenspeichern von Rezepten

-- Datenbank erstellen
CREATE DATABASE RecipeCache;

-- Verwende die erstellte Datenbank
USE RecipeCache;

-- Tabelle für Rezepte erstellen
CREATE TABLE recipes (
id INT AUTO_INCREMENT PRIMARY KEY,
name VARCHAR(255) NOT NULL,
Kochzeit VARCHAR(100),
is_vegetarian BOOLEAN,
blacklist BOOLEAN DEFAULT FALSE,
url VARCHAR(255) UNIQUE NOT NULL
);

-- Tabelle für Zutaten erstellen
CREATE TABLE ingredients (
id INT AUTO_INCREMENT PRIMARY KEY,
recipe_id INT,
Zutat VARCHAR(255) NOT NULL,
Menge VARCHAR(100),
FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);

-- Tabelle für Zubereitungsschritte erstellen
CREATE TABLE preparation_steps (
id INT AUTO_INCREMENT PRIMARY KEY,
recipe_id INT,
Schrittnummer INT,
Schrittbeschreibung TEXT,
FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);