exports.getRecipes = (req, res) => {
    const recipes = [
        { id: 1, title: 'Spaghetti Bolognese', image: 'recipe1.jpg' },
        { id: 2, title: 'Chicken Curry', image: 'recipe2.jpg' },
        { id: 3, title: 'Beef Stew', image: 'recipe3.jpg' },
    ];
    res.json(recipes);
};

exports.swipeRecipe = (req, res) => {
    const { recipeId, action } = req.body;
    res.status(200).send({ message: `Recipe ${recipeId} ${action}ed successfully` });
};
