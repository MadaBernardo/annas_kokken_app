from fastapi import FastAPI, Depends, HTTPException, status
from fastapi import UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List


import os
import shutil
import models
import schemas
import crud
from database import engine, get_db

#atualiza a pd com tableas novas criadas automaticamente
#models.Base.metadata.create_all(bind=engine)
#essa linha está comentada porque faz o trabalho do alembic antes dele

# Initialize the FastAPI application with clean metadata
app = FastAPI(
    title="Anna's Køkken",
    description="Backend REST API for Anna's Kitchen recipe management and shopping list system",
    version="1.0.0"
)

# FIXED: Registered and enabled Cross-Origin Resource Sharing (CORS) Middleware
# This permits incoming requests from different ports or domains securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits all origins for simplified development staging
    allow_credentials=True,
    allow_methods=["*"],  # Allows standard verbs: GET, POST, PUT, DELETE
    allow_headers=["*"],
)

# Ensure the local static upload infrastructure exists safely on startup
os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================
# CATEGORY ENDPOINTS
# ==========================================

@app.get("/categories", response_model=List[schemas.Category], tags=["Categories"])
def read_categories(db: Session = Depends(get_db)):
    """
    API endpoint to retrieve all available recipe categories.
    """
    return crud.get_categories(db)

@app.post("/categories", response_model=schemas.Category, status_code=status.HTTP_201_CREATED, tags=["Categories"])
def create_new_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    """
    API endpoint to create a new recipe category.
    """
    return crud.create_category(db=db, category=category)

@app.put("/categories/{category_id}", response_model=schemas.Category, tags=["Categories"])
def update_category(category_id: int, category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    """
    API endpoint to modify an existing category name.
    """
    db_category = crud.update_category(db=db, category_id=category_id, category=category)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

@app.delete("/categories/{category_id}", tags=["Categories"])
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """
    API endpoint to remove a category based on its ID.
    """
    success = crud.delete_category(db=db, category_id=category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}


# ==========================================
# RECIPE ENDPOINTS
# ==========================================

@app.post("/recipes/upload-image", tags=["Recipes"])
async def upload_image(file: UploadFile = File(...)):
    """
    Handles file upload streams and stores the image binary payload locally
    inside the managed static assets folder structure.
    """
    file_location = f"static/images/{file.filename}"
    
    # Copy file binary buffer systematically into local storage
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"image_url": f"http://localhost:8000/{file_location}"}

@app.get("/recipes", response_model=List[schemas.Recipe], tags=["Recipes"])
def read_recipes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    API endpoint to retrieve a paginated list of recipes.
    """
    return crud.get_recipes(db, skip=skip, limit=limit)

@app.get("/recipes/{recipe_id}", response_model=schemas.Recipe, tags=["Recipes"])
def read_single_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """
    API endpoint to fetch a specific recipe by its unique ID.
    Raises a 404 error if the recipe does not exist.
    """
    db_recipe = crud.get_recipe(db, recipe_id=recipe_id)
    if db_recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Recipe with ID {recipe_id} not found"
        )
    return db_recipe

@app.post("/recipes", response_model=schemas.Recipe, status_code=status.HTTP_201_CREATED, tags=["Recipes"])
def create_new_recipe(recipe: schemas.RecipeCreate, db: Session = Depends(get_db)):
    """
    API endpoint to create a new recipe alongside all its nested ingredients.
    """
    return crud.create_recipe(db=db, recipe=recipe)

@app.put("/recipes/{recipe_id}", response_model=schemas.Recipe, tags=["Recipes"])
def update_recipe(recipe_id: int, recipe: schemas.RecipeCreate, db: Session = Depends(get_db)):
    """
    API endpoint to update an existing recipe alongside all its nested ingredients.
    """
    db_recipe = crud.update_recipe(db=db, recipe_id=recipe_id, recipe=recipe)
    if not db_recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Recipe with ID {recipe_id} not found"
        )
    return db_recipe

@app.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Recipes"])
def delete_existing_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """
    API endpoint to permanently delete a recipe. 
    Cascade handling ensures ingredients are also removed.
    """
    success = crud.delete_recipe(db, recipe_id=recipe_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Recipe with ID {recipe_id} not found or could not be deleted"
        )
    return None
#terminou aqui antes da lista do supermaket table

# ==========================================
# SHOPPING LIST ENDPOINTS
# ==========================================

@app.get("/shopping-list", response_model=List[schemas.ShoppingListItem], tags=["Shopping List"])
def read_shopping_list(db: Session = Depends(get_db)):
    """
    API endpoint to retrieve the current active persistent shopping list items.
    """
    return crud.get_shopping_list(db)

@app.post("/shopping-list/generate", response_model=List[schemas.ShoppingListItem], tags=["Shopping List"])
def generate_new_list(payload: schemas.RecipeIdsRequest, db: Session = Depends(get_db)):
    """
    API endpoint to execute ingredient aggregation and populate the physical table layer.
    """
    return crud.generate_shopping_list(db=db, recipe_ids=payload.recipe_ids)

@app.put("/shopping-list/{item_id}", response_model=schemas.ShoppingListItem, tags=["Shopping List"])
def update_item_status(item_id: int, is_checked: bool, db: Session = Depends(get_db)):
    """
    API endpoint to update the checked or crossed-out state of a specific item.
    """
    db_item = crud.toggle_shopping_item(db=db, item_id=item_id, is_checked=is_checked)
    if not db_item:
        raise HTTPException(status_code=404, detail="Shopping item not found")
    return db_item

@app.delete("/shopping-list", tags=["Shopping List"])
def empty_list(db: Session = Depends(get_db)):
    """
    API endpoint to clear all records from the shopping list table.
    """
    crud.clear_shopping_list(db)
    return {"message": "Shopping list cleared successfully"}

# ==========================================
# RECIPE FEEDBACK ENDPOINTS
# ==========================================

@app.get("/recipes/{recipe_id}/feedbacks", response_model=List[schemas.RecipeFeedback], tags=["Feedbacks"])
def read_recipe_feedbacks(recipe_id: int, db: Session = Depends(get_db)):
    """
    API endpoint to retrieve all evaluations and reviews associated with a specific recipe.
    Verifies parent existence to prevent silent empty responses on invalid keys.
    """
    db_recipe = crud.get_recipe(db, recipe_id=recipe_id)
    if db_recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Recipe with ID {recipe_id} not found"
        )
    return crud.get_feedbacks_by_recipe(db, recipe_id=recipe_id)

@app.post("/recipes/{recipe_id}/feedbacks", response_model=schemas.RecipeFeedback, status_code=status.HTTP_201_CREATED, tags=["Feedbacks"])
def create_recipe_feedback(recipe_id: int, feedback: schemas.RecipeFeedbackCreate, db: Session = Depends(get_db)):
    """
    API endpoint to create a brand new feedback card (rating & comment) linked to an existing recipe.
    """
    db_recipe = crud.get_recipe(db, recipe_id=recipe_id)
    if db_recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Recipe with ID {recipe_id} not found"
        )
    return crud.create_feedback(db=db, feedback=feedback, recipe_id=recipe_id)

@app.put("/feedbacks/{feedback_id}", response_model=schemas.RecipeFeedback, tags=["Feedbacks"])
def update_existing_feedback(feedback_id: int, feedback: schemas.RecipeFeedbackUpdate, db: Session = Depends(get_db)):
    """
    API endpoint to handle updates on a specific evaluation record dynamically.
    """
    db_feedback = crud.update_feedback(db=db, feedback_id=feedback_id, feedback=feedback)
    if not db_feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Feedback record with ID {feedback_id} not found"
        )
    return db_feedback

@app.delete("/feedbacks/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Feedbacks"])
def delete_existing_feedback(feedback_id: int, db: Session = Depends(get_db)):
    """
    API endpoint to completely eliminate a feedback row using its unique framework ID.
    """
    success = crud.delete_feedback(db, feedback_id=feedback_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Feedback record with ID {feedback_id} not found or could not be deleted"
        )
    return None