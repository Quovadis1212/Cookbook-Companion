USE RecipeCache;
SELECT recipe_id, COUNT(DISTINCT ingredient) as matching_ingredients
FROM ingredients
WHERE ingredient LIKE '%Zucker%' OR ingredient LIKE '%Mehl%'
GROUP BY recipe_id
HAVING COUNT(DISTINCT ingredient) >= 2; -- Adjust the threshold for testing
