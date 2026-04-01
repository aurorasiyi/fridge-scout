import streamlit as st
import json
import os
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Fridge Scout",
    page_icon="🥗",
    layout="centered"
)

# Constants
PANTRY_ITEMS = [
    "Olive oil", "Butter", "Salt", "Pepper", 
    "Dried Oregano/Herbs de Provence", "Garlic", 
    "Flour", "Dried Pasta", "Vinegar", "Milk"
]

def generate_recipe_image(dish_name: str, primary_fridge: str = "", secondary_fridge: str = "", pantry_carb: str = "") -> Optional[str]:
    """Generate a beautiful food image for the recipe using image generation with ingredient alignment"""
    try:
        # Define ultra-specific food photography prompt with ingredient constraints
        image_prompt = f"Professional food photography of a {dish_name}, high-angle shot, white background, strictly ONLY the ingredients in the recipe. No poke bowl toppings, no garnish. Photography style: Minimalist. White plate only. NO SIDE DISHES. The image MUST explicitly show the main ingredients: {primary_fridge}, {secondary_fridge}, and {pantry_carb}. **Do not add extraneous fruits like bananas, berries, or maple syrup. STRICT RULE: Only show ingredients listed. Do NOT add salmon, avocado, or grains unless specified. Minimalist plating.** Focus on textures: charred leeks, melting tomatoes, cooked egg. 8k resolution, highly detailed, appetizing, soft bokeh."
        
        # Try to use the image generation tool
        # For now, we'll provide ingredient-aligned mock URLs
        ingredient_based_urls = {
            "tomato": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&h=600&fit=crop",
            "leek": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&h=600&fit=crop",
            "egg": "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800&h=600&fit=crop",
            "pasta": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800&h=600&fit=crop",
            "ham": "https://images.unsplash.com/photo-1563379091339-032409b4f2b4?w=800&h=600&fit=crop"
        }
        
        # Select image based on primary ingredient for better alignment
        primary_lower = primary_fridge.lower()
        for ingredient, url in ingredient_based_urls.items():
            if ingredient in primary_lower:
                return url
        
        # Fallback to a general food photo
        return "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&h=600&fit=crop"
        
    except Exception as e:
        # Fallback to a reliable food photo
        return "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&h=600&fit=crop"

def get_recipe_from_llama(ingredients: List[str], serving_size: int = 2, available_pantry: List[str] = None) -> Optional[str]:
    """Get recipe recommendation from Hugging Face Llama-3.1-8B model"""
    
    # Create the prompt
    if available_pantry is None:
        available_pantry = []
    pantry_list = ", ".join(available_pantry)
    ingredients_list = ", ".join(ingredients)
    
    prompt = f"""You are a Michelin-star Chef. I have: {ingredients_list}.

Pantry staples: {pantry_list}.

Create a {serving_size}-person recipe under 30 minutes.

SCALING LAW:
- For every +1 serving, increase Pasta/Rice/Flour by 100g and Milk by 100ml
- 2 servings = ~200-250g pasta. 4 servings = ~400-500g pasta
- Every Amount MUST have units (g, ml, tbsp, pieces). No naked numbers.

INGREDIENT LOGIC:
- Priority 1: Use ALL fridge items (ingredients entered by user)
- Priority 2: Use checked Pantry Staples to bulk up the meal

NAMING RULE:
- The dish name should be descriptive but flexible
- If a different pantry staple (e.g., Rice instead of Pasta) makes more sense for larger serving size, feel free to pivot

MANDATORY TABLE FORMAT:
| Ingredient | Amount | Prep |
| :--- | :--- | :--- |

CONSTRAINT: Do NOT combine 'Prep' into the 'Amount' column.

Bad: | Leek | 100g sliced | |
Good: | Leek | 100g | Sliced into rounds |

Format:

[Dish Name]
Prep: X mins | Cook: Y mins | Servings: {serving_size}

Ingredients
| Ingredient | Amount | Prep |
| :--- | :--- | :--- |

Instructions
1. Step 1
2. Step 2
3. Step 3

SCALING RULE: If Stretch is ON, the 'Amount' for selected pantry items must be doubled compared to the 2-serving version.

Only respond with recipe."""

    try:
        # Initialize InferenceClient
        api_key = os.getenv('HUGGINGFACE_API_KEY')
        if not api_key:
            st.error("❌ API key not loaded! Check your .env file.")
            return None
            
        client = InferenceClient(
            model='meta-llama/Llama-3.1-8B-Instruct',
            token=api_key,
            timeout=30
        )
        
        # Add loading message
        st.info("🔄 Loading recipe from AI...")
        
        # Generate recipe using chat completions
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        
        # Extract content from response
        generated_text = response.choices[0].message.content
        
        # Return the markdown recipe directly
        return generated_text.strip()
        
    except Exception as e:
        # Print full error to Streamlit for debugging
        st.error(f"🚨 Full Error Details: {str(e)}")
        st.error(f"Error Type: {type(e).__name__}")
        st.write("🔍 Debug Info - Check the following:")
        st.write(f"- Model: meta-llama/Llama-3.1-8B-Instruct")
        st.write(f"- API Key loaded: {'Yes' if api_key else 'No'}")
        st.write(f"- Ingredients: {ingredients}")
        st.write(f"- Serving size: {serving_size}")
        return None

def settings_changed_callback():
    """Mark settings as changed"""
    st.session_state.settings_changed = True

def add_item_callback():
    """Callback to add pantry item and clear input"""
    val = st.session_state.pantry_input.strip().lower()
    if val and val not in st.session_state.custom_pantry_items:
        st.session_state.custom_pantry_items.append(val)
    # This is the magic part: clearing the state directly in callback
    st.session_state.pantry_input = ""
    st.session_state.update({'settings_changed': True})

def main():
    # Initialize session state
    if 'recipe' not in st.session_state:
        st.session_state.recipe = None
    if 'settings_changed' not in st.session_state:
        st.session_state.settings_changed = False
    if 'recipe_generated' not in st.session_state:
        st.session_state.recipe_generated = False
    if 'serving_size' not in st.session_state:
        st.session_state.serving_size = 2
    if 'available_pantry' not in st.session_state:
        st.session_state.available_pantry = []
    if 'ingredients' not in st.session_state:
        st.session_state.ingredients = ""
    if 'ingredients_input' not in st.session_state:
        st.session_state.ingredients_input = ""
    if 'custom_pantry_items' not in st.session_state:
        st.session_state.custom_pantry_items = []
    
    # Check API key
    api_key = os.getenv('HUGGINGFACE_API_KEY')
    if not api_key:
        st.error("❌ HUGGINGFACE_API_KEY not found!")
        return
    
    # Sidebar with single block logic
    with st.sidebar:
        st.title("🍱 My Parisian Pantry")
        st.info('💡 Missing an ingredient? Uncheck it below!')
        
        # The Essentials
        st.markdown('**Basic Essentials:**')
        pantry_selection = {
            'Pasta': st.checkbox('Pasta', key='basic_pasta', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Rice': st.checkbox('Rice', key='basic_rice', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Flour': st.checkbox('Flour', key='basic_flour', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Milk': st.checkbox('Milk', key='basic_milk', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Butter': st.checkbox('Butter', key='basic_butter', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Eggs': st.checkbox('Eggs', key='basic_eggs', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Garlic': st.checkbox('Garlic', key='basic_garlic', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Onion': st.checkbox('Onion', key='basic_onion', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Dried Herbs': st.checkbox('Dried Herbs', key='basic_herbs', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Olive Oil': st.checkbox('Olive Oil', value=True, key='basic_oil', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Salt': st.checkbox('Salt', value=True, key='basic_salt', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Pepper': st.checkbox('Pepper', value=True, key='basic_pepper', on_change=lambda: st.session_state.update({'settings_changed': True}))
        }
        
        # The Custom Section
        st.markdown('**🍱 Your Custom Staples:**')
        for item in st.session_state.custom_pantry_items:
            st.checkbox(item, value=True, key=f'custom_item_{item}', on_change=lambda: st.session_state.update({'settings_changed': True}))
        
        # The Add Tool (Mobile Friendly)
        st.sidebar.text_input('Add a staple:', key='pantry_input', on_change=add_item_callback)
        # Optional button for users who prefer clicking
        if st.sidebar.button('➕ Add to Pantry'):
            add_item_callback()
            st.rerun()
        
        # The Clear Tool
        if st.sidebar.button('🗑️ Clear Custom Pantry'):
            st.session_state.custom_pantry_items = []
            st.rerun()  # Immediate refresh
        
        # Combine all pantry items
        checked_staples = [item for item, checked in pantry_selection.items() if checked]
        checked_custom = [item for item in st.session_state.custom_pantry_items if st.session_state.get(f'custom_item_{item}')]
        available_pantry = checked_staples + checked_custom
        st.session_state.available_pantry = available_pantry
    
    # Main UI
    st.title("🥗 Fridge Scout: The Zero-Waste Urban Chef")
    
    # Mobile sidebar guidance
    if st.session_state.get('sidebar_opened', False) == False or st.session_state.get('screen_width', 1000) < 768:
        st.info('👈 Tip: Open the sidebar menu to check your Pantry Essentials!')
    
    # Update Required Cue
    if st.session_state.recipe and st.session_state.settings_changed:
        st.warning('⚠️ Your kitchen settings have changed! Click "Update Recipe" to refresh.')
    
    # Serving Size Toggle (moved to main page)
    serving_size = st.select_slider('Number of Servings', options=['2 (Standard)', '4 (Stretch)', '6 (Party)'], value='2 (Standard)', on_change=lambda: st.session_state.update({'settings_changed': True}))
    serving_size_num = int(serving_size.split(' ')[0])  # Extract number
    
    st.markdown("### What's in your fridge?")
    st.caption("Enter at least 2 items to start.")
    
    # Unified Form to eliminate red box
    with st.form('recipe_form', clear_on_submit=False):
        st.text_input(
            "Step 1: Enter your 2 main ingredients (e.g. Leek, Ham)",
            placeholder="e.g., tomatoes, cheese, eggs, spinach",
            key='ingredients_input'
        )
        
        # Dynamic labeling
        submit_label = '🔄 Update Recipe' if st.session_state.recipe else '👨‍🍳 Get Chef\'s Recommendation'
        submitted = st.form_submit_button(submit_label, type='primary')
        
        # Validation and processing
        if submitted:
            ingredients_list = [i.strip() for i in st.session_state.ingredients_input.split(',') if i.strip()]
            
            if len(ingredients_list) < 2:
                st.warning('Please enter at least 2 ingredients!')
            else:
                with st.spinner("The Chef is cooking and taking photos..."):
                    recipe = get_recipe_from_llama(ingredients_list, serving_size_num, available_pantry)
                    if recipe:
                        # Extract dish name from first line of recipe
                        dish_name = recipe.split('\n')[0].strip()
                        
                        # Extract ingredients for image alignment
                        primary_fridge = ingredients_list[0] if len(ingredients_list) > 0 else ""
                        secondary_fridge = ingredients_list[1] if len(ingredients_list) > 1 else ""
                        pantry_carb = "Eggs" if "Eggs" in available_pantry else ("Pasta" if "Pasta" in available_pantry else "Rice")
                        
                        # Save recipe to session state
                        st.session_state.recipe = recipe
                        st.session_state.settings_changed = False  # Reset after successful update
        
        # Recipe display only
        if st.session_state.recipe:
            st.markdown("### 🍽️ Chef's Recommendation")
            st.markdown(st.session_state.recipe)

if __name__ == "__main__":
    main()
