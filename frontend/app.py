import streamlit as st
import requests
import urllib.parse

# Define your API base URL here (adjust to your actual variable name)
API_BASE_URL = "http://127.0.0.1:8000" 

# --- BACKEND HEALTH CHECK ---
# Verify API availability before rendering the application state
backend_online = True
try:
    # Quick lightweight ping to the backend (adjust endpoint if needed)
    requests.get(API_BASE_URL, timeout=2)
except requests.exceptions.RequestException:
    backend_online = False

if not backend_online:
    st.error("⚠️ **Backend Server Offline:** The FastAPI server is currently unreachable. Please ensure the backend is running and try again.")
    st.stop() # Gracefully halts Streamlit execution to prevent downstream UI crashes

# --- 1. PAGE SETUP ---
st.set_page_config(
    page_title="Anna's Køkken", 
    page_icon="🍳", 
    layout="centered"
)

# Helper function to inject clean, separate CSS from the new path
def local_css(file_name):
    with open(file_name, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Helper function to inject clean, separate CSS from the new path
def local_css(file_name):
    with open(file_name, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- NEW: RECIPE FEEDBACK API INTEGRATION ---
def get_recipe_feedbacks(recipe_id: int):
    """Fetch all comments and ratings for a specific recipe."""
    try:
        response = requests.get(f"{API_URL}/{recipe_id}/feedbacks", timeout=3)
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        return []

def submit_recipe_feedback(recipe_id: int, rating: int, comment: str):
    """Send a new rating and comment to the backend."""
    payload = {
        "rating": rating,
        "comment": comment
    }
    try:
        response = requests.post(f"{API_URL}/{recipe_id}/feedbacks", json=payload, timeout=3)
        return response.status_code == 201
    except requests.exceptions.RequestException:
        return False

# Load the external stylesheet from the dedicated css/ folder safely
try:
    local_css("frontend/css/style.css")
except FileNotFoundError:
    try:
        local_css("css/style.css")
    except FileNotFoundError:
        st.warning("CSS configuration file not found at frontend/css/style.css. Using defaults.")

# --- 2. GLOBAL HEADER & BRANDING LOGO ---
st.markdown("<h1 class='main-title'>🍳 Anna's Køkken</h1>", unsafe_allow_html=True)
st.markdown("<p class='hygge-subtitle'>Få det hyggeligt i køkkenet</p>", unsafe_allow_html=True)

st.markdown("---")

API_URL = "http://127.0.0.1:8000/recipes"

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("Menu")
page = st.sidebar.radio(
    "Go to:",
    [
        "📖 Anna's Køkken (Digital Recipe Book)", 
        "⚖️ The Scale Master (Danish Calculator)", 
        "🛒 Mad & Market (Smart Shopping List)"
    ]
)

# Initialize session state for dynamic ingredient rows in the form
if "ingredient_rows" not in st.session_state:
    st.session_state.ingredient_rows = 1

# --- SCREEN 1: DIGITAL RECIPE BOOK ---
if page == "📖 Anna's Køkken (Digital Recipe Book)":
    st.header("📖 Digital Recipe Book")
    
    # Dynamic Category Fetching with safe fallback setup
    categories_from_api = []
    try:
        cat_url = API_URL.replace("/recipes", "/categories") if "/recipes" in API_URL else f"{API_URL}/categories"
        cat_response = requests.get(cat_url, timeout=3)
        if cat_response.status_code == 200:
            categories_from_api = cat_response.json()
    except Exception:
        pass  # Silent failure prevents rendering interruptions

    # If database context has no categories yet or backend is offline, build fallback infrastructure
    if not categories_from_api:
        categories_from_api = [{"id": 1, "name": "General"}]

    # --- FORM TO MANAGE CATEGORIES ---
    with st.expander("📁 Manage Categories (Ny Kategori)", expanded=False):
        tab_create, tab_edit_delete = st.tabs(["✨ Create", "🛠️ Edit / Delete"])
        
        with tab_create:
            st.subheader("Create a New Category")
            new_category_name = st.text_input("Category Name:", placeholder="e.g., Desserts...", key="new_cat")
            
            if st.button("📁 Save Category", key="btn_save_cat"):
                if new_category_name:
                    try:
                        cat_url = API_URL.replace("/recipes", "/categories") if "/recipes" in API_URL else f"{API_URL}/categories"
                        response = requests.post(cat_url, json={"name": new_category_name})
                        if response.status_code in [200, 201]:
                            st.success(f"Category '{new_category_name}' created! 🎉")
                            st.rerun()
                        else:
                            st.error("Failed to create category.")
                    except requests.exceptions.ConnectionError:
                        st.error("🚨 Backend is offline.")

        with tab_edit_delete:
            st.subheader("Edit or Delete Existing Category")
            
            # Replaced unsafe local variable lookups with the secure category list array
            if categories_from_api and not (len(categories_from_api) == 1 and categories_from_api[0]["name"] == "General"):
                cat_options = {c['name']: c['id'] for c in categories_from_api}
                selected_cat_name = st.selectbox("Select Category:", options=list(cat_options.keys()), key="select_cat_manage")
                selected_cat_id = cat_options[selected_cat_name]
                
                edit_name = st.text_input("New Name:", value=selected_cat_name, key="edit_cat_name")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📝 Update Name", key="btn_update_cat"):
                        put_url = f"{API_URL.replace('/recipes', '/categories')}/{selected_cat_id}"
                        res = requests.put(put_url, json={"name": edit_name})
                        if res.status_code == 200:
                            st.success("Category updated!")
                            st.rerun()
                
                with col2:
                    if st.button("🗑️ Delete Category", key="btn_delete_cat", type="primary"):
                        del_url = f"{API_URL.replace('/recipes', '/categories')}/{selected_cat_id}"
                        res = requests.delete(del_url)
                        if res.status_code == 200:
                            st.success("Category deleted!")
                            st.rerun()
            else:
                st.info("No customized categories available to manage yet.")       
    
    # --- FORM TO ADD A NEW RECIPE ---
    with st.expander("➕ Add New Recipe (Gem Opskrift)", expanded=False):
        st.subheader("Create a New Recipe")
        
        new_title = st.text_input("Recipe Title:", placeholder="e.g., Flæskesteg")
        new_portions = st.number_input("Base Portions (Servings):", min_value=1, value=2, step=1)
        
        # File Uploader component connecting directly with API upload pipeline
        uploaded_image_url = None
        uploaded_file = st.file_uploader("Upload Recipe Photo (Valgfri):", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            # Streams image binary data via multipart form encoding to FastAPI safely
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                upload_url = API_URL + "/upload-image" if API_URL.endswith("/recipes") else f"{API_URL}/upload-image"
                upload_resp = requests.post(upload_url, files=files)
                if upload_resp.status_code == 200:
                    uploaded_image_url = upload_resp.json().get("image_url")
                    st.success("Photo uploaded and processed successfully! 📸")
                else:
                    st.error("Failed to store image on backend server.")
            except Exception as e:
                st.error(f"Error establishing communication with upload stream: {e}")
        
        category_options = {cat["name"]: cat["id"] for cat in categories_from_api}
        selected_category = st.selectbox("Select Category:", list(category_options.keys()))
        category_id = category_options[selected_category]
        
        new_instructions = st.text_area("Preparation Instructions:", placeholder="Step by step guide...")
        
        st.markdown("#### Ingredients")
        ingredients_data = []
        
        for i in range(st.session_state.ingredient_rows):
            col1, col2, col3 = st.columns([2, 2, 4])
            with col1:
                qty = st.number_input(f"Qty #{i+1}", min_value=0.0, step=0.1, key=f"qty_{i}")
            with col2:
                unit = st.text_input(f"Unit #{i+1}", placeholder="g, dl, tbsp", key=f"unit_{i}")
            with col3:
                name = st.text_input(f"Ingredient Name #{i+1}", placeholder="e.g., Sugar", key=f"name_{i}")
            
            if name:
                ingredients_data.append({"quantity": qty, "unit": unit, "ingredient_name": name})
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("➕ Add Ingredient Row"):
                st.session_state.ingredient_rows += 1
                st.rerun()
        with col_btn2:
            if st.button("❌ Remove Row") and st.session_state.ingredient_rows > 1:
                st.session_state.ingredient_rows -= 1
                st.rerun()
                
        st.markdown("---")
        
        if st.button("💾 Save Recipe (Gem Opskrift)"):
            if not new_title or not new_instructions:
                st.warning("Please fill out both the title and instructions before saving.")
            else:
                payload = {
                    "title": new_title,
                    "portions": int(new_portions),
                    "instructions": new_instructions,
                    "ingredients": ingredients_data,
                    "category_id": category_id,
                    "image_url": uploaded_image_url
                }
                
                try:
                    response = requests.post(API_URL, json=payload)
                    if response.status_code in [200, 201]:
                        st.success("Opskrift gemt! Recipe successfully saved to the database. 🎉")
                        st.session_state.ingredient_rows = 1  # Reset dynamic input rows
                        st.rerun()
                    else:
                        st.error(f"Failed to save recipe. API returned status: {response.status_code}")
                except requests.exceptions.ConnectionError:
                    st.error("🚨 Connection error: Make sure the FastAPI backend is running.")

    st.markdown("---")
    
    # --- RECIPE DISPLAY SECTION WITH SEARCH ---
    st.subheader("Your Recipes")
    
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            recipes = response.json()
            
            if not recipes:
                st.info("You don't have any recipes saved yet. Use the form above to add your first one!")
            else:
                search_query = st.text_input("🔍 Search recipes by title...", "").strip().lower()
                
                filtered_recipes = [
                    r for r in recipes 
                    if search_query in r["title"].lower() or search_query in r.get("instructions", "").lower()
                ]
                
                if not filtered_recipes:
                    st.warning("No recipes match your search criteria.")
                else:
                    for recipe in filtered_recipes:
                     with st.expander(f"🍰 {recipe['title']}"):
                        
                        # --- Smart Image Preview Pipeline ---
                        if recipe.get("image_url"):
                            if st.toggle("🔍 View Full Size Photo", key=f"zoom_img_{recipe['id']}"):
                                st.image(recipe["image_url"], use_column_width=True)
                            else:
                                st.image(recipe["image_url"], width=180)
                        else:
                            st.caption("📸 No photo attached to this recipe.")
                            
                        st.write("**Instructions:**")
                        st.write(recipe["instructions"])
                        
                        st.write("**Ingredients List:**")
                        if recipe.get("ingredients"):
                            for ing in recipe["ingredients"]:
                                st.write(f"- {ing['quantity']} {ing['unit']} of {ing['ingredient_name']}")
                        else:
                            st.caption("No ingredients recorded for this recipe.")
                        
                        # =========================================================
                        # NEW: SHARE RECIPE FEATURE - WHATSAPP & COPY LINK
                        # =========================================================
                        st.markdown("---")
                        st.markdown("#### 📢 Share Recipe (Del Opskrift)")
                        
                        # Format the full text payload specifically for WhatsApp sharing
                        tit_share = recipe['title']
                        inst_share = recipe['instructions']
                        
                        share_text = f"🇩🇰 *{tit_share}* - Shared from Anna's Køkken\n\n"
                        share_text += "*Ingredients:*\n"
                        if recipe.get("ingredients"):
                            for ing in recipe["ingredients"]:
                                share_text += f"- {ing['quantity']} {ing['unit']} de {ing['ingredient_name']}\n"
                        else:
                            share_text += "No registered ingredients.\n"
                        
                        share_text += f"\n*Preparation Instructions:*\n{inst_share}\n\n"
                        share_text += "Få det hyggeligt i køkkenet! 🍰 Velbekomme!"
                        
                        # Encode text for the native WhatsApp web/app redirection link
                        encoded_text = urllib.parse.quote(share_text)
                        whatsapp_url = f"https://api.whatsapp.com/send?text={encoded_text}"
                        
                        # Dynamic link constructor (update 'localhost' to your production domain later)
                        APP_BASE_URL = "http://localhost:8501"
                        recipe_link = f"{APP_BASE_URL}/?recipe_id={recipe['id']}"
                        
                        # Render full-width button for active WhatsApp redirection
                        st.link_button("Send to WhatsApp 💬", whatsapp_url, use_container_width=True)
                        
                        # Display the generated recipe URL inside a native copy-paste component
                        st.caption("📋 Click the icon in the right corner of the box below to copy the recipe link:")
                        st.code(recipe_link, language="text")
                        # =========================================================
                        
                        # =========================================================
                        # NEW: RECIPE FEEDBACK SYSTEM (RATINGS & COMMENTS)
                        # =========================================================
                        st.markdown("---")
                        st.markdown("#### 💬 Reviews & Comments (Anmeldelser & Kommentarer)")
                        
                        # Fetch and display existing reviews
                        feedbacks = get_recipe_feedbacks(recipe['id'])
                        
                        if not feedbacks:
                            st.info("This recipe has no comments yet. Be the first to review it! 🌟")
                        else:
                            for fb in feedbacks:
                                stars = "⭐" * fb['rating']
                                st.markdown(f"**{stars}**")
                                st.write(fb['comment'])
                                st.markdown("<hr style='margin: 8px 0; border: 0; border-top: 1px dashed #ddd;'/>", unsafe_allow_html=True)
                        
                        # Form to submit new feedback
                        st.markdown("##### Write a review (Skriv en anmeldelse)")
                        with st.form(key=f"feedback_form_{recipe['id']}", clear_on_submit=True):
                            rating_value = st.selectbox(
                                "BRating (Bedømmelse):", 
                                options=[5, 4, 3, 2, 1], 
                                format_func=lambda x: "⭐" * x,
                                key=f"sb_rating_{recipe['id']}"
                            )
                            
                            comment_text = st.text_area(
                                "Your comment (Din kommentar):", 
                                placeholder="What did you think of the recipe?...",
                                key=f"ta_comment_{recipe['id']}"
                            )
                            
                            submit_button = st.form_submit_button(label="Submit review 🚀")
                            
                            if submit_button:
                                if not comment_text.strip():
                                    st.warning("Please write a comment before sending. 📝")
                                else:
                                    success = submit_recipe_feedback(recipe['id'], rating_value, comment_text)
                                    if success:
                                        st.success("Thank you for your feedback! 🎉")
                                        st.rerun()
                                    else:
                                        st.error("Could not save your review. Please try again.")
                        
                            st.markdown("---")
                            # =========================================================
                        
                        # --- FIXED: Replaced nested st.expander with st.toggle to satisfy UI nesting restrictions ---
                        if st.toggle("✏️ Edit Recipe Details", key=f"toggle_edit_{recipe['id']}"):
                            st.markdown("##### Update Recipe Specifications")
                            edit_title = st.text_input("Recipe Title:", value=recipe["title"], key=f"ed_title_{recipe['id']}")
                            edit_portions = st.number_input("Portions:", min_value=1, value=int(recipe["portions"]), step=1, key=f"ed_port_{recipe['id']}")
                            
                            edit_uploaded_file = st.file_uploader("Change Photo:", type=["jpg", "jpeg", "png"], key=f"ed_file_{recipe['id']}")
                            current_image_url = recipe.get("image_url")
                            
                            if edit_uploaded_file is not None:
                                try:
                                    files = {"file": (edit_uploaded_file.name, edit_uploaded_file.getvalue(), edit_uploaded_file.type)}
                                    upload_url = API_URL + "/upload-image" if API_URL.endswith("/recipes") else f"{API_URL}/upload-image"
                                    upload_resp = requests.post(upload_url, files=files)
                                    if upload_resp.status_code == 200:
                                        current_image_url = upload_resp.json().get("image_url")
                                        st.success("New photo staged successfully! 📸")
                                except Exception as e:
                                    st.error(f"Image upload stream error: {e}")
                            
                            cat_names = list(category_options.keys())
                            default_index = 0
                            for name, cid in category_options.items():
                                if cid == recipe.get("category_id"):
                                    default_index = cat_names.index(name)
                                    break
                            
                            edit_selected_cat = st.selectbox("Category:", cat_names, index=default_index, key=f"ed_cat_{recipe['id']}")
                            edit_category_id = category_options[edit_selected_cat]
                            
                            edit_instructions = st.text_area("Instructions:", value=recipe["instructions"], key=f"ed_inst_{recipe['id']}")
                            
                            st.markdown("##### Ingredients Matrix")
                            updated_ingredients = []
                            for idx, ing in enumerate(recipe.get("ingredients", [])):
                                c1, c2, c3 = st.columns([2, 2, 4])
                                with c1:
                                    e_qty = st.number_input("Qty", min_value=0.0, value=float(ing["quantity"]), step=0.1, key=f"eqy_{recipe['id']}_{idx}")
                                with c2:
                                    e_unit = st.text_input("Unit", value=ing["unit"], key=f"eun_{recipe['id']}_{idx}")
                                with c3:
                                    e_name = st.text_input("Name", value=ing["ingredient_name"], key=f"enm_{recipe['id']}_{idx}")
                                
                                if e_name:
                                    updated_ingredients.append({"quantity": e_qty, "unit": e_unit, "ingredient_name": e_name})
                            
                            if st.button("💾 Save Recipe Changes", key=f"btn_ed_save_{recipe['id']}", type="secondary"):
                                edit_payload = {
                                    "title": edit_title,
                                    "portions": int(edit_portions),
                                    "instructions": edit_instructions,
                                    "ingredients": updated_ingredients,
                                    "category_id": edit_category_id,
                                    "image_url": current_image_url
                                }
                                try:
                                    put_recipe_url = f"{API_URL}/{recipe['id']}"
                                    put_resp = requests.put(put_recipe_url, json=edit_payload)
                                    if put_resp.status_code == 200:
                                        st.success("Recipe changes saved successfully! 🎉")
                                        st.rerun()
                                    else:
                                        st.error("Backend validation failed to store updates.")
                                except Exception as e:
                                    st.error(f"Connection error to update stream: {e}")
                        
                        st.markdown("---")
                        
                        if st.button(f"🗑️ Delete Recipe", key=f"del_rec_{recipe['id']}", type="primary"):
                            try:
                                del_recipe_url = f"{API_URL}/{recipe['id']}"
                                del_resp = requests.delete(del_recipe_url)
                                if del_resp.status_code in [200, 204]:
                                    st.success(f"Recipe '{recipe['title']}' permanently removed! 💥")
                                    st.rerun()
                                else:
                                    st.error("API encountered an obstacle deleting this record.")
                            except Exception as e:
                                st.error(f"Error contacting backend during execution: {e}")
        else:
            st.error(f"Error loading recipes from API (Status: {response.status_code})")
            
    except requests.exceptions.ConnectionError:
        st.error("🚨 Backend server disconnected! Please run: uvicorn backend.main:app --reload")

# --- SCREEN 2: THE SCALE MASTER (CALCULATOR) ---
elif page == "⚖️ The Scale Master (Danish Calculator)":
    st.header("⚖️ The Scale Master")
    st.write("Adjust your recipe portions instantly and convert units with a Danish touch.")

    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            recipes = response.json()
            
            if not recipes:
                st.info("No recipes found. Add a recipe in the Digital Recipe Book first! 📖")
            else:
                recipe_titles = [r['title'] for r in recipes]
                selected_title = st.selectbox("Vælg en opskrift (Choose a recipe):", recipe_titles)
                recipe = next(r for r in recipes if r['title'] == selected_title)
                
                st.markdown("---")
                
                base_servings = recipe.get('portions', 2)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="Original Portioner (Base Servings)", value=base_servings)
                with col2:
                    target_servings = st.number_input(
                        "Nye Portioner (Target Servings):", 
                        min_value=1, 
                        max_value=100, 
                        value=int(base_servings),
                        step=1
                    )
                
                scale_factor = target_servings / base_servings
                st.markdown("---")
                
                convert_units = st.toggle("Switch to international units (cups/tbsp)")
                st.subheader("🛒 Adjusted Ingredients List")
                
                ingredients = recipe.get("ingredients", [])
                if ingredients:
                    for ing in ingredients:
                        qty = float(ing['quantity'])
                        unit = ing['unit']
                        name = ing['ingredient_name']
                        
                        scaled_qty = qty * scale_factor
                        
                        if convert_units:
                            if unit.lower() == 'dl' and scaled_qty >= 2.4:
                                scaled_qty = scaled_qty / 2.4
                                unit = "cups"
                            elif unit.lower() == 'g' and scaled_qty >= 450:
                                scaled_qty = scaled_qty / 453.6
                                unit = "lbs"
                        
                        st.write(f"- **{scaled_qty:.2f} {unit}** of {name}")
                else:
                    st.caption("No ingredients recorded for this recipe.")
                    
                st.markdown("<h4 style='color: #C8102E; text-align: center; margin-top: 30px;'>Velbekomme!</h4>", unsafe_allow_html=True)
        else:
            st.error(f"Error loading recipes from the API (Status: {response.status_code})")
            
    except requests.exceptions.ConnectionError:
        st.error("🚨 Backend disconnected! Make sure Uvicorn is running.")
##supermaket list table
elif page == "🛒 Mad & Market (Smart Shopping List)":
    st.header("🛒 Mad & Market")
    st.write("Plan your upcoming meals and compile a persistent, consolidated shopping list.")

    # Deriving the dedicated shopping list endpoint path from your base API structure
    SHOPPING_API_URL = API_URL.replace("/recipes", "/shopping-list") if "/recipes" in API_URL else "http://127.0.0.1:8000/shopping-list"

    try:
        # 1. Fetch available recipes to populate selection layout inputs
        response = requests.get(API_URL)
        if response.status_code == 200:
            recipes = response.json()
            
            if not recipes:
                st.info("No recipes found in the database. Please add recipes first! 📖")
            else:
                recipe_options = {r["title"]: r["id"] for r in recipes}
                selected_titles = st.multiselect(
                    "Vælg opskrifter til ugens menu (Select recipes for your plan):",
                    options=list(recipe_options.keys())
                )
                
                if st.button("🛍️ Generate Shopping List (Generer Indkøbsliste)", type="primary"):
                    if not selected_titles:
                        st.warning("Please select at least one recipe to aggregate.")
                    else:
                        target_ids = [recipe_options[title] for title in selected_titles]
                        try:
                            gen_resp = requests.post(f"{SHOPPING_API_URL}/generate", json={"recipe_ids": target_ids})
                            if gen_resp.status_code == 200:
                                st.success("Indkøbsliste genereret! Shopping list successfully stored in database. 🎉")
                                st.rerun()
                            else:
                                st.error("Backend validation framework failed processing aggregation request.")
                        except Exception as e:
                            st.error(f"Error establishing communication with compilation stream: {e}")
                
        st.markdown("---")
        
        # 2. Retrieve and display persistent records directly from the database table
        list_resp = requests.get(SHOPPING_API_URL)
        if list_resp.status_code == 200:
            shopping_list = list_resp.json()
            
            if shopping_list:
                st.subheader("Indkøbsliste (Your Smart Shopping List)")
                st.caption("Check off items on your phone as you place them into your shopping cart:")
                
                for item in shopping_list:
                    # Visual hygge feedback mapping: strikes through text dynamically if item is checked
                    if item["is_checked"]:
                        display_text = f"~~**{item['quantity']:.2f} {item['unit']}** of {item['ingredient_name']}~~ 🇩🇰 ✓"
                    else:
                        display_text = f"**{item['quantity']:.2f} {item['unit']}** of {item['ingredient_name']}"
                        
                    check_key = f"db_shop_{item['id']}"
                    
                    # Renders state natively mapped directly out of the row attributes
                    is_checked = st.checkbox(display_text, value=item["is_checked"], key=check_key)
                    
                    # If UI state shifts away from database state, dispatch immediate synchronized update
                    if is_checked != item["is_checked"]:
                        try:
                            requests.put(f"{SHOPPING_API_URL}/{item['id']}?is_checked={is_checked}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to synchronize checkbox execution state: {e}")
                
                st.markdown("---")
                if st.button("🗑️ Clear Shopping List", type="secondary"):
                    try:
                        del_resp = requests.delete(SHOPPING_API_URL)
                        if del_resp.status_code == 200:
                            st.success("Shopping list permanently cleared from database!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error executing clear command on database: {e}")
            else:
                st.info("Your shopping list is currently empty. Select recipes above to populate it.")
        else:
            st.error("Failed to retrieve current active shopping list state from the API server.")
            
    except requests.exceptions.ConnectionError:
        st.error("🚨 Backend disconnected! Make sure Uvicorn web server is active.")