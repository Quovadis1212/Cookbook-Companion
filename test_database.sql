-- SQL Script to Create a Database for Caching Recipes

-- Create Database (Uncomment if needed)
-- CREATE DATABASE RecipeCache;

-- Use the Created Database (Uncomment if needed)
USE RecipeCache;

-- Create a Table for Recipes
CREATE TABLE recipes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    cooking_time VARCHAR(100),
    is_vegetarian BOOLEAN,
    blacklist BOOLEAN DEFAULT FALSE,
    url VARCHAR(255) UNIQUE NOT NULL
);

-- Create a Table for Ingredients
CREATE TABLE ingredients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipe_id INT,
    ingredient VARCHAR(255) NOT NULL,
    amount VARCHAR(100),
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);

-- Create a Table for Preparation Steps
CREATE TABLE preparation_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipe_id INT,
    step_number INT,
    step_description TEXT,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);