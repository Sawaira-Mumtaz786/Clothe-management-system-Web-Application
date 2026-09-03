import streamlit as st
import os
import json
from google import genai
from google.genai import types
from PIL import Image

st.set_page_config(page_title="AI Clothing Management System", page_icon="👕", layout="centered")

st.title("👕 AI-Powered Clothing Management System")
st.write("Analyze sample inventory images from GitHub or upload your own to extract metadata using Google Gemini 2.5 Flash.")

api_key = st.text_input("Enter Gemini API Key (or set environment variable):", type="password") or os.getenv("GEMINI_API_KEY")

# Choose image source: Existing GitHub folder vs Upload
option = st.radio("Choose Image Source:", ("Select from Repository Images", "Upload New Image"))

image_bytes = None
mime_type = "image/jpeg"

if option == "Select from Repository Images":
    image_folder = "item_images"
    if os.path.exists(image_folder):
        files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if files:
            selected_file = st.selectbox("Choose an item from item_images/:", files)
            file_path = os.path.join(image_folder, selected_file)
            
            image = Image.open(file_path)
            st.image(image, caption=f"Selected: {selected_file}", use_container_width=True)
            
            with open(file_path, "rb") as f:
                image_bytes = f.read()
            mime_type = "image/png" if selected_file.lower().endswith('.png') else "image/jpeg"
        else:
            st.warning("No images found in item_images/ directory.")
    else:
        st.error("Directory 'item_images' not found in repository.")

else:
    uploaded_file = st.file_uploader("Choose a clothing photo...", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Clothing Item", use_container_width=True)
        uploaded_file.seek(0)
        image_bytes = uploaded_file.read()
        mime_type = uploaded_file.type

# Trigger AI Auto-Tagging
if image_bytes and st.button("✨ Auto-Tag Item with AI"):
    if not api_key:
        st.error("Please provide a Gemini API Key to proceed.")
    else:
        try:
            client = genai.Client(api_key=api_key)
            prompt = """
            Analyze this clothing image and output ONLY a raw JSON object with these keys:
            'name', 'category' (Men/Women/Kids), 'season' (Summer/Winter), 'size' (S/M/L/XL), 'color'.
            Do not output markdown formatting or extra text.
            """
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt
                ]
            )
            
            clean_json = response.text.strip().replace("```json", "").replace("```", "")
            data = json.loads(clean_json)
            
            st.success("Metadata Extracted Successfully!")
            st.json(data)
            
        except Exception as e:
            st.error(f"Error processing image: {e}")
