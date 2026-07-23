from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# ==========================================
# INGREDIENT SCHEMAS
# ==========================================

class RecipeIngredientBase(BaseModel):
    """
    Shared attributes for recipe ingredients validation.
    """
    ingredient_name: str
    quantity: float
    unit: str

class RecipeIngredientCreate(RecipeIngredientBase):
    """
    Schema used when creating a new ingredient. 
    Does not require ids since they are auto-generated.
    """
    pass

class RecipeIngredient(RecipeIngredientBase):
    """
    Schema used when returning ingredient data from the API.
    Includes the database primary keys.
    """
    id: int
    recipe_id: int

    # Enables Pydantic to parse SQLAlchemy ORM objects automatically
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# RECIPE SCHEMAS
# ==========================================

class RecipeBase(BaseModel):
    """
    Shared attributes for recipe validation.
    """
    title: str
    instructions: Optional[str] = None
    portions: int = 1
    category_id: int                 # 🟢 Mantém-se obrigatório (int)
    image_url: Optional[str] = None   # 👈 Adicionado como opcional para a foto

class RecipeCreate(RecipeBase):
    """
    Schema used when creating a recipe.
    Expects a nested list of ingredients to be created simultaneously.
    """
    ingredients: List[RecipeIngredientCreate] = []

class Recipe(RecipeBase):
    """
    Schema used when returning recipe data to the frontend.
    Includes the database id and the fully resolved list of ingredients.
    """
    id: int
    ingredients: List[RecipeIngredient] = []

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# CATEGORY SCHEMAS
# ==========================================

class CategoryBase(BaseModel):
    """
    Shared attributes for category validation.
    """
    name: str

class CategoryCreate(CategoryBase):
    """
    Schema used when creating a new category.
    """
    pass

class Category(CategoryBase):
    """
    Schema used when returning category data.
    """
    id: int

    model_config = ConfigDict(from_attributes=True)
    #permite ao fastApi ler os obj no SQLAlchemy e 
    #converte-los em JSON

# ==========================================
# SHOPPING LIST SCHEMAS
# ==========================================

class RecipeIdsRequest(BaseModel):
    """
    Schema used to accept an incoming payload containing an array of target recipe IDs.
    """
    recipe_ids: List[int]

class ShoppingListItemBase(BaseModel):
    """
    Shared attributes for persistent shopping list items.
    """
    ingredient_name: str
    quantity: float
    unit: str
    is_checked: bool = False

class ShoppingListItemCreate(ShoppingListItemBase):
    """
    Schema used during record initialization.
    """
    pass

class ShoppingListItem(ShoppingListItemBase):
    """
    Schema used to return saved shopping list rows from the API database layer.
    """
    id: int

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# FEEDBACK SCHEMAS
# ==========================================

class RecipeFeedbackBase(BaseModel):
    """
    Shared evaluation attributes utilized across schema variations.
    """
    rating: int
    comment: Optional[str] = None

class RecipeFeedbackCreate(RecipeFeedbackBase):
    """
    Schema deployed when injecting a brand new feedback record.
    """
    pass

class RecipeFeedbackUpdate(BaseModel):
    """
    Schema deployed when adjusting an existing feedback entry.
    Fields remain optional to handle partial property updates smoothly.
    """
    rating: Optional[int] = None
    comment: Optional[str] = None

class RecipeFeedback(RecipeFeedbackBase):
    """
    Schema deployed when returning feedback records downstream to the client.
    Includes auto-assigned framework primary identification nodes.
    """
    id: int
    recipe_id: int

    # Direct Pydantic to interface cleanly with SQLAlchemy ORM layers
    model_config = ConfigDict(from_attributes=True)