import streamlit as st
import os
from typing import List, Optional
from huggingface_hub import InferenceClient

# --- 1. INITIALIZATION & CONFIG ---
st.set_page_config(page_title="Fridge Scout", page_icon="🥗", layout="centered")

# Get the token safely
HF_TOKEN = st.secrets.get("HUGGINGFACE_API_KEY") or os.getenv("HUGGINGFACE_API_KEY")

# --- 2. THE AI CHEF LOGIC ---
def get_recipe_from_llama(ingredients: List[str], serving_size: int, available_pantry: List[str]) -> Optional[str]:
    if not HF_TOKEN:
        st.error("❌ API Key missing in Secrets!")
        return None

    pantry_str = ", ".join(available_pantry)
    ing_str = ", ".join(ingredients)
    
    prompt = f"Chef, create a {serving_size}-serving recipe using {ing_str}. Pantry: {pantry_str}. Use Emojis for every ingredient!"

    try:
        # We specify the provider to avoid the "auto-router" error
        client = InferenceClient(token=HF_TOKEN, timeout=30)
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"🚨 Chef is busy! Error: {str(e)}")
        return None

# --- 3. CALLBACKS ---
def add_item_callback():
    val = st.session_state.pantry_input.strip()
    if val and val not in st.session_state.custom_pantry_items:
        st.session_state.custom_pantry_items.append(val)
    st.session_state.pantry_input = "" 

# --- 4. MAIN APP ---
def main():
    if 'recipe' not in st.session_state: st.session_state.recipe = None
    if 'custom_pantry_items' not in st.session_state: st.session_state.custom_pantry_items = []

    with st.sidebar:
        st.title("🍱 My Parisian Pantry")
        
        # Added Salt & Pepper back here
        pantry_selection = {
            'Salt': st.checkbox('Salt', value=True),
            'Pepper': st.checkbox('Pepper', value=True),
            'Olive Oil': st.checkbox('Olive Oil', value=True),
            'Pasta': st.checkbox('Pasta'),
            'Rice': st.checkbox('Rice'),
            'Eggs': st.checkbox('Eggs'),
            'Garlic': st.checkbox('Garlic'),
            'Onion': st.checkbox('Onion'),
        }
        
        st.markdown('---')
        for item in st.session_state.custom_pantry_items:
            st.checkbox(item, value=True, key=f"c_{item}")
            
        st.text_input('Add a staple:', key='pantry_input', on_change=add_item_callback)

    st.title("🥗 Fridge Scout")
    serving_size = st.select_slider('Servings', options=[2, 4, 6])
    
    with st.form('recipe_form'):
        ingredients_input = st.text_input("What's in the fridge?", placeholder="e.g. Leek, Ham")
        submitted = st.form_submit_button('👨‍🍳 Get Recommendation', type='primary')
        
        if submitted:
            ing_list = [i.strip() for i in ingredients_input.split(',') if i.strip()]
            if len(ing_list) < 2:
                st.warning("Please enter at least 2 items!")
            else:
                pantry_list = [k for k, v in pantry_selection.items() if v] + st.session_state.custom_pantry_items
                recipe = get_recipe_from_llama(ing_list, serving_size, pantry_list)
                if recipe:
                    st.session_state.recipe = recipe

    if st.session_state.recipe:
        st.markdown("---")
        st.markdown(st.session_state.recipe)

if __name__ == "__main__":
    main()
