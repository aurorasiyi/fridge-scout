import streamlit as st
import os
from typing import List, Optional
from huggingface_hub import InferenceClient

# --- 1. INITIALIZATION & CONFIG ---
st.set_page_config(page_title="Fridge Scout", page_icon="🥗", layout="centered")

# Secure API Key Retrieval
HF_TOKEN = st.secrets.get("HUGGINGFACE_API_KEY") or os.getenv("HUGGINGFACE_API_KEY")

# --- 2. THE AI CHEF LOGIC ---
def get_recipe_from_llama(ingredients: List[str], serving_size: int, available_pantry: List[str]) -> Optional[str]:
    if not HF_TOKEN:
        st.error("❌ API Key missing in Secrets!")
        return None

    pantry_str = ", ".join(available_pantry)
    ing_str = ", ".join(ingredients)
    
    prompt = f"Chef, create a {serving_size}-serving recipe using {ing_str}. Pantry items available: {pantry_str}. Use Emojis for every ingredient!"

    try:
        # Explicit client to avoid auto-router errors
        client = InferenceClient(token=HF_TOKEN, timeout=30)
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"🚨 Chef is busy! Error: {str(e)}")
        return None

# --- 3. CALLBACKS (Restoring UX Logic) ---
def add_item_callback():
    val = st.session_state.pantry_input.strip()
    if val and val not in st.session_state.custom_pantry_items:
        st.session_state.custom_pantry_items.append(val)
    st.session_state.pantry_input = "" 
    st.session_state.settings_changed = True

def clear_pantry_callback():
    st.session_state.custom_pantry_items = []
    st.session_state.settings_changed = True

# --- 4. MAIN APP ---
def main():
    # Initialize state for UX persistence
    if 'recipe' not in st.session_state: st.session_state.recipe = None
    if 'custom_pantry_items' not in st.session_state: st.session_state.custom_pantry_items = []
    if 'settings_changed' not in st.session_state: st.session_state.settings_changed = False

    # --- SIDEBAR (Pantry Management) ---
    with st.sidebar:
        st.title("🍱 My Parisian Pantry")
        st.info('👈 Tip: Check items you have at home!')
        
        pantry_selection = {
            'Salt': st.checkbox('Salt', value=True, on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Pepper': st.checkbox('Pepper', value=True, on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Olive Oil': st.checkbox('Olive Oil', value=True, on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Pasta': st.checkbox('Pasta', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Rice': st.checkbox('Rice', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Eggs': st.checkbox('Eggs', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Garlic': st.checkbox('Garlic', on_change=lambda: st.session_state.update({'settings_changed': True})),
            'Onion': st.checkbox('Onion', on_change=lambda: st.session_state.update({'settings_changed': True})),
        }
        
        st.markdown('---')
        st.markdown('**Custom Staples:**')
        for item in st.session_state.custom_pantry_items:
            st.checkbox(item, value=True, key=f"c_{item}", on_change=lambda: st.session_state.update({'settings_changed': True}))
            
        # UI Restoration: Add & Clear Buttons
        st.text_input('Add a staple:', key='pantry_input', on_change=add_item_callback)
        col1, col2 = st.columns(2)
        with col1:
            if st.button('➕ Add'): add_item_callback(); st.rerun()
        with col2:
            if st.button('🗑️ Clear'): clear_pantry_callback(); st.rerun()

    # --- MAIN PAGE UI ---
    st.title("🥗 Fridge Scout")
    
    # UI Restoration: Visual reminder message
    st.info('💡 Tip: Open the sidebar menu to check your Pantry Essentials!')
    
    # UI Restoration: Warning message when settings change
    if st.session_state.recipe and st.session_state.settings_changed:
        st.warning('⚠️ Your kitchen settings have changed! Click "Update Recipe" to refresh.')

    # UI Restoration: Serving bar with labels
    serving_labels = {2: "2 (Standard)", 4: "4 (Stretch)", 6: "6 (Party)"}
    serving_size = st.select_slider(
        'Number of Servings', 
        options=[2, 4, 6], 
        format_func=lambda x: serving_labels[x],
        on_change=lambda: st.session_state.update({'settings_changed': True})
    )
    
    with st.form('recipe_form'):
        st.markdown("### What's in your fridge?")
        ingredients_input = st.text_input("Enter main items (e.g. Leek, Ham)", placeholder="tomatoes, cheese, eggs...")
        
        # UI Restoration: CTA that changes text dynamically
        submit_label = '🔄 Update Recipe' if st.session_state.recipe else '👨‍🍳 Get Recommendation'
        submitted = st.form_submit_button(submit_label, type='primary')
        
        if submitted:
            ing_list = [i.strip() for i in ingredients_input.split(',') if i.strip()]
            if len(ing_list) < 2:
                st.warning("Please enter at least 2 items to help the Chef!")
            else:
                pantry_list = [k for k, v in pantry_selection.items() if v] + st.session_state.custom_pantry_items
                with st.spinner("The Chef is composing your recipe..."):
                    recipe = get_recipe_from_llama(ing_list, serving_size, pantry_list)
                    if recipe:
                        st.session_state.recipe = recipe
                        st.session_state.settings_changed = False # Reset the warning
                        st.rerun()

    if st.session_state.recipe:
        st.markdown("---")
        st.markdown("### 🍽️ Chef's Recommendation")
        st.markdown(st.session_state.recipe)

if __name__ == "__main__":
    main()
