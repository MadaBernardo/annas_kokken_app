from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from database import Base

class Category(Base):
    """
    Represents the 'categories' table in the MySQL database.
    Stores recipe categories like 'Desserts', 'Main Course', etc.
    """
    __tablename__ = "categories" #tablename garante que o SQLAlchemy se liga com a tabelas no xamp

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    # Relationship linking Category to multiple Recipe instances
    recipes = relationship("Recipe", back_populates="category")
    # relationship/ back_populates fazem os joins automaticamente


class Recipe(Base):
    """
    Represents the 'recipes' table in the MySQL database.
    Stores the core information of a recipe.
    """
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    instructions = Column(Text, nullable=True)
    portions = Column(Integer, default=1, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    image_url = Column(String(255), nullable=True)

    # ORM Relationships
    category = relationship("Category", back_populates="recipes")
    
    # cascade="all, delete-orphan" ensures that if a recipe is deleted, 
    # its ingredients are automatically removed from the database as well
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")

    # Cascade deletes to feedback records if the parent recipe is dropped
    feedbacks = relationship("RecipeFeedback", back_populates="recipe", cascade="all, delete-orphan")


class RecipeIngredient(Base):
    """
    Represents the 'recipe_ingredients' table in the MySQL database.
    Acts as the bridge linking ingredients, quantities, and their specific recipe.
    """
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    ingredient_name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)  # e.g., 'g', 'ml', 'spoons'

    # ORM Relationship linking back to the parent Recipe
    recipe = relationship("Recipe", back_populates="ingredients")

class ShoppingListItem(Base):
    """
    Represents the 'shopping_list' table in the MySQL database.
    Persists the aggregated weekly shopping items and their interactive checked status.
    """
    __tablename__ = "shopping_list"

    id = Column(Integer, primary_key=True, index=True)
    ingredient_name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    is_checked = Column(Boolean, default=False, nullable=False)

class RecipeFeedback(Base):
    """
    Represents the 'recipe_feedbacks' table in the MySQL database.
    Stores user-submitted ratings and notes for individual recipes.
    """
    __tablename__ = "recipe_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    rating = Column(Integer, nullable=False) # Stores score scale, e.g., 1 to 5 stars
    comment = Column(Text, nullable=True)    # Optional text notes or cooking feedback

    # ORM Relationship pointing back to the specific parent Recipe object
    recipe = relationship("Recipe", back_populates="feedbacks")