import streamlit as st
import os
import json
from google import genai
from google.genai import types

st.set_page_config(page_title="AI Clothing Management System", page_icon="👕", layout="centered")

st.title("👕 AI-Powered Clothing Management System")
st.write("Upload a clothing product image to automatically extract inventory metadata using Google Gemini 2.5 Flash.")

api_key = st.text_input("Enter Gemini API Key (or set environment variable):", type="password") or os.getenv("GEMINI_API_KEY")

uploaded_file = st.file_uploader("Choose a clothing photo...", type=["jpg", "jpeg", "png"])

if uploaded_file and st.button("✨ Auto-Tag Item with AI"):
    if not api_key:
        st.error("Please provide a Gemini API Key to proceed.")
    else:
        try:
            client = genai.Client(api_key=api_key)
            prompt = """
            Analyze this clothing image and output ONLY a raw JSON object with these keys:
            'name', 'category' (Men/Women/Kids), 'season' (Summer/Winter), 'size' (S/M/L/XL), 'color'.
            Do not output markdown formatting.
            """
            
            image_bytes = uploaded_file.read()
            response = client.models.generateContent(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=uploaded_file.type),
                    prompt
                ]
            )
            
            clean_json = response.text.strip().replace("```json", "").replace("```", "")
            data = json.loads(clean_json)
            
            st.success("Metadata Extracted Successfully!")
            st.json(data)
            
        except Exception as e:
            st.error(f"Error processing image: {e}")
