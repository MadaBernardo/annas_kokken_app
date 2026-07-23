from sqlalchemy.orm import Session
import models
import schemas

# ==========================================
# CATEGORY CRUD OPERATIONS
# ==========================================

def get_categories(db: Session):
    """
    Fetches all recipe categories from the database.
    """
    return db.query(models.Category).all()

def create_category(db: Session, category: schemas.CategoryCreate):
    """
    Creates a new recipe category in the database.
    """
    db_category = models.Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_category(db: Session, category_id: int, category: schemas.CategoryCreate):
    """
    Updates an existing category's name based on its unique primary key ID.
    Returns the updated category object or None if not found.
    """
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if db_category:
        db_category.name = category.name
        db.commit()
        db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int):
    """
    Deletes a specific category from the database using its ID.
    Returns True if deletion was successful, False otherwise.
    """
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if db_category:
        db.delete(db_category)
        db.commit()
        return True
    return False

# ==========================================
# RECIPE CRUD OPERATIONS
# ==========================================

def get_recipes(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieves a list of recipes with optional pagination parameters.
    """
    return db.query(models.Recipe).offset(skip).limit(limit).all()

def get_recipe(db: Session, recipe_id: int):
    """
    Retrieves a single recipe by its primary key ID.
    """
    return db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()

def create_recipe(db: Session, recipe: schemas.RecipeCreate):
    """
    Creates a new recipe along with its nested ingredients.
    Uses database transactions to ensure atomicity.
    """
    # 1. Create and insert the core recipe object 
    # FIXED: Added image_url tracking so it maps correctly from schema to the model layer
    db_recipe = models.Recipe(
        title=recipe.title,
        instructions=recipe.instructions,
        portions=recipe.portions,
        category_id=recipe.category_id,
        image_url=recipe.image_url  
    )
    db.add(db_recipe)
    db.commit()       # Committing here generates the db_recipe.id via AUTO_INCREMENT
    db.refresh(db_recipe)

    # 2. Iterate through the nested ingredients list and link them to the new recipe ID
    # Complex mapping logic: unrolls the schema list into separate rows linking to db_recipe.id
    for ing in recipe.ingredients:
        db_ingredient = models.RecipeIngredient(
            recipe_id=db_recipe.id,
            ingredient_name=ing.ingredient_name,
            quantity=ing.quantity,
            unit=ing.unit
        )
        db.add(db_ingredient)
    
    db.commit()
    db.refresh(db_recipe)  # Refresh to populate the ORM relationship with the added ingredients
    return db_recipe

def delete_recipe(db: Session, recipe_id: int):
    """
    Deletes a recipe from the database by its ID.
    Associated ingredients are auto-deleted due to cascade setup in models.py.
    """
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if db_recipe:
        db.delete(db_recipe)
        db.commit()
        return True
    return False

def update_recipe(db: Session, recipe_id: int, recipe: schemas.RecipeCreate):
    """
    Updates an existing recipe and its nested ingredients.
    To avoid primary key conflicts or orphaned rows, it clears old ingredients 
    and reconstructs the list within a single atomic database transaction.
    """
    # 1. Find the existing recipe core record
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    
    if db_recipe:
        # 2. Update the core metadata fields
        db_recipe.title = recipe.title
        db_recipe.instructions = recipe.instructions
        db_recipe.portions = recipe.portions
        db_recipe.category_id = recipe.category_id
        
        # Only update image if a new URL stream was generated
        if recipe.image_url:
            db_recipe.image_url = recipe.image_url

        # 3. Purge old linked ingredients to prepare for the new payload structure
        db.query(models.RecipeIngredient).filter(models.RecipeIngredient.recipe_id == recipe_id).delete()
        
        # 4. Re-populate the ingredients table with updated values
        for ing in recipe.ingredients:
            db_ingredient = models.RecipeIngredient(
                recipe_id=recipe_id,
                ingredient_name=ing.ingredient_name,
                quantity=ing.quantity,
                unit=ing.unit
            )
            db.add(db_ingredient)
            
        db.commit()
        db.refresh(db_recipe)
        return db_recipe
        
    return None
#terminou aqui antes da nova tabela para lista do supermercado

# ==========================================
# SHOPPING LIST CRUD OPERATIONS
# ==========================================

def get_shopping_list(db: Session):
    """
    Retrieves all records currently stored inside the shopping list table.
    """
    return db.query(models.ShoppingListItem).all()

def generate_shopping_list(db: Session, recipe_ids: list[int]):
    """
    Aggregates ingredients from selected recipe IDs case-insensitively, 
    purges old shopping list rows, and saves the newly consolidated rows.
    """
    # 1. Fetch raw ingredient blocks linked to the chosen recipe primary keys
    ingredients = db.query(models.RecipeIngredient).filter(models.RecipeIngredient.recipe_id.in_(recipe_ids)).all()
    
    # 2. Perform case-insensitive aggregation mapping in memory
    aggregated = {}
    for ing in ingredients:
        key = (ing.ingredient_name.strip().lower(), ing.unit.strip().lower())
        if key in aggregated:
            aggregated[key]["quantity"] += ing.quantity
        else:
            aggregated[key] = {
                "ingredient_name": ing.ingredient_name,
                "quantity": ing.quantity,
                "unit": ing.unit
            }
            
    # 3. Purge the existing shopping list table records to clear old state safely
    db.query(models.ShoppingListItem).delete()
    
    # 4. Populate table rows with the freshly aggregated ingredient payload entries
    inserted_items = []
    for item in aggregated.values():
        db_item = models.ShoppingListItem(
            ingredient_name=item["ingredient_name"],
            quantity=item["quantity"],
            unit=item["unit"],
            is_checked=False
        )
        db.add(db_item)
        inserted_items.append(db_item)
        
    db.commit()
    return inserted_items

def toggle_shopping_item(db: Session, item_id: int, is_checked: bool):
    """
    Updates the 'is_checked' boolean field of a specific shopping item by its unique ID.
    """
    db_item = db.query(models.ShoppingListItem).filter(models.ShoppingListItem.id == item_id).first()
    if db_item:
        db_item.is_checked = is_checked
        db.commit()
        db.refresh(db_item)
    return db_item

def clear_shopping_list(db: Session):
    """
    Truncates/deletes all records from the shopping list table.
    """
    db.query(models.ShoppingListItem).delete()
    db.commit()
    return True

# ==========================================
# RECIPE FEEDBACK CRUD OPERATIONS
# ==========================================

def get_feedbacks_by_recipe(db: Session, recipe_id: int):
    """
    Retrieves all persistent feedback records linked to a specific recipe ID.
    """
    return db.query(models.RecipeFeedback).filter(models.RecipeFeedback.recipe_id == recipe_id).all()

def create_feedback(db: Session, feedback: schemas.RecipeFeedbackCreate, recipe_id: int):
    """
    Creates a new evaluation feedback entry systematically tied to a target recipe.
    """
    db_feedback = models.RecipeFeedback(
        recipe_id=recipe_id,
        rating=feedback.rating,
        comment=feedback.comment
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

def update_feedback(db: Session, feedback_id: int, feedback: schemas.RecipeFeedbackUpdate):
    """
    Updates an existing feedback entry. 
    Fields are checked for None to allow clean partial property updates (rating or comment).
    """
    db_feedback = db.query(models.RecipeFeedback).filter(models.RecipeFeedback.id == feedback_id).first()
    
    if db_feedback:
        if feedback.rating is not None:
            db_feedback.rating = feedback.rating
        if feedback.comment is not None:
            db_feedback.comment = feedback.comment
            
        db.commit()
        db.refresh(db_feedback)
        return db_feedback
        
    return None

def delete_feedback(db: Session, feedback_id: int):
    """
    Permanently deletes a targeted feedback record from the database layer by its unique ID.
    """
    db_feedback = db.query(models.RecipeFeedback).filter(models.RecipeFeedback.id == feedback_id).first()
    if db_feedback:
        db.delete(db_feedback)
        db.commit()
        return True
    return False

