import streamlit as st
import os
from typing import List, Optional
from huggingface_hub import InferenceClient

# --- 1. INITIALIZATION & CONFIG ---
st.set_page_config(
    page_title="Fridge Scout",
    page_icon="🥗",
    layout="centered"
)

# This handles both your local computer and the Streamlit Cloud "Secrets"
HF_TOKEN = st.secrets.get("HUGGINGFACE_API_KEY") or os.getenv("HUGGINGFACE_API_KEY")

# --- 2. THE AI CHEF LOGIC ---
def get_recipe_from_llama(ingredients: List[str], serving_size: int = 2, available_pantry: List[str] = None) -> Optional[str]:
    if not HF_TOKEN:
        st.error("❌ API Key not found. Please add HUGGINGFACE_API_KEY to Streamlit Secrets.")
        return None

    pantry_list = ", ".join(available_pantry) if available_pantry else "Basic salt and pepper"
    ingredients_list = ", ".join(ingredients)
    
    # Prompt with the new EMOJI instruction we discussed
    prompt = f"""You are a Michelin-star Chef. Create a recipe using: {ingredients_list}.
    Pantry staples available: {pantry_list}.
    Servings: {serving_size}.
    
    RULES:
    1. Every ingredient in the list MUST start with a relevant emoji (e.g. 🥚 2 Eggs).
    2. The title MUST start with a food emoji (e.g. 🥘 Leek Bake).
    3. Use a Markdown table for ingredients.
    4. Keep instructions brief and professional.
    
    Format:
    [Emoji] [Dish Name]
    Prep: X mins | Cook: Y mins | Servings: {serving_size}

    ### Ingredients
    | Ingredient | Amount | Prep |
    | :--- | :--- | :--- |
    
    ### Instructions
    1. Step 1...
    """

    try:
        client = InferenceClient(model='meta-llama/Llama-3.1-8B-Instruct', token=HF_TOKEN, timeout=30)
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"🚨 Chef is busy! Error: {str(e)}")
        return None

# --- 3. CALLBACKS ---
def add_item_callback():
    val = st.session_state.pantry_input.strip().lower()
    if val and val not in st.session_state.custom_pantry_items:
        st.session_state.custom_pantry_items.append(val)
    st.session_state.pantry_input = "" # Clear input
    st.session_state.settings_changed = True

# --- 4. MAIN APP ---
def main():
    # Initialize all states at once
    for key, default in [
        ('recipe', None), ('settings_changed', False), 
        ('custom_pantry_items', []), ('ingredients_input', "")
    ]:
        if key not in st.session_state: st.session_state[key] = default

    # SIDEBAR
    with st.sidebar:
        st.title("🍱 My Parisian Pantry")
        
        pantry_selection = {
            'Pasta': st.checkbox('Pasta', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Rice': st.checkbox('Rice', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Eggs': st.checkbox('Eggs', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Garlic': st.checkbox('Garlic', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Onion': st.checkbox('Onion', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Olive Oil': st.checkbox('Olive Oil', value=True, on_change=lambda: st.session_state.update({'settings_changed': True})),
        }
        
        st.markdown('**Custom Staples:**')
        for item in st.session_state.custom_pantry_items:
            st.checkbox(item, value=True, key=f"check_{item}", on_change=lambda: st.session_state.update({'settings_changed': True}))
            
        st.text_input('Add a staple:', key='pantry_input', on_change=add_item_callback)
        if st.button('➕ Add'): add_item_callback()

    # MAIN PAGE
    st.title("🥗 Fridge Scout")
    
    # Warning Nudge
    if st.session_state.recipe and st.session_state.settings_changed:
        st.warning('⚠️ Settings changed! Click Update to refresh.')

    serving_size = st.select_slider('Servings', options=['2', '4', '6'], on_change=lambda: st.session_state.update({'settings_changed': True}))
    
    with st.form('recipe_form'):
        ingredients_input = st.text_input("What's in the fridge?", placeholder="e.g. Leek, Ham", key='main_input')
        submit_label = '🔄 Update Recipe' if st.session_state.recipe else '👨‍🍳 Get Recommendation'
        submitted = st.form_submit_button(submit_label, type='primary') # Bold CTA
        
        if submitted:
            ing_list = [i.strip() for i in ingredients_input.split(',') if i.strip()]
            if len(ing_list) < 2:
                st.warning("Please enter at least 2 items!")
            else:
                pantry_list = [k for k, v in pantry_selection.items() if v] + st.session_state.custom_pantry_items
                recipe = get_recipe_from_llama(ing_list, int(serving_size), pantry_list)
                if recipe:
                    st.session_state.recipe = recipe
                    st.session_state.settings_changed = False
                    st.rerun()

    if st.session_state.recipe:
        st.markdown("---")
        st.markdown(st.session_state.recipe)

if __name__ == "__main__":
    main()
