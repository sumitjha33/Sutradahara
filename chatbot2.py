import streamlit as st
import requests  # For API requests
import google.generativeai as genai  # Gemini API
import os
import time
from fuzzywuzzy import process

# Load API key securely from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Set this variable in your system
if not GEMINI_API_KEY:
    st.error("API key not found. Please set the GEMINI_API_KEY environment variable.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# API Endpoint for fetching user data
USER_DATA_API = "https://skill-nest-backend.onrender.com/get_all_users_data"

def fetch_users():
    """Fetch users dynamically from API."""
    response = requests.get(USER_DATA_API)
    if response.status_code != 200:
        return []
    return response.json().get("data", [])

def extract_skills_from_query(query, available_skills):
    """Extract skills from user input based on available skills in database."""
    detected_skills = [skill for skill in available_skills if skill.lower() in query.lower()]
    return detected_skills

def recommend_users_for_skills(required_skills, users):
    """Find users who know at least one of the required skills, ensuring C++ and C# are not confused."""
    recommended_users = []
    for user in users:
        tech_skills = user.get("Tech-skills", {})  # Get user skills
        if tech_skills:
            for skill in required_skills:
                if skill.lower() == "c++" and "c#" in tech_skills:
                    continue  # Skip if looking for C++ but user has C#
                if skill.lower() == "c#" and "c++" in tech_skills:
                    continue  # Skip if looking for C# but user has C++
                if skill in tech_skills:  # Exact match check
                    recommended_users.append({
                        "name": user.get("name", "Unknown"),
                        "USN": user.get("USN", "No USN"),
                        "points": user.get("points", 0),
                        "matched_skill": skill
                    })
                    break  # Include user if they match at least one skill
    recommended_users = sorted(recommended_users, key=lambda x: x["points"], reverse=True)[:5]  # Return top 5 users
    return recommended_users

def generate_response(prompt, users, mode):
    """Generate chatbot response based on selected mode."""
    skill_nest_keywords = ["skill nest", "what is skill nest", "about skill nest"]
    sutradhara_keywords = ["who are you", "what is sutradhara", "who is sutradhara"]
    
    if any(keyword in prompt.lower() for keyword in skill_nest_keywords):
        return ("**Skill Nest** is a dynamic platform designed to foster collaboration and skill-sharing among students. 🚀")
    
    if any(keyword in prompt.lower() for keyword in sutradhara_keywords):
        return ("**I am Sutradhara**, your intelligent chatbot assistant for Skill Nest! 🤖")
    
    if mode == "Find Members":
        available_skills = set()
        for user in users:
            available_skills.update(user.get("Tech-skills", {}).keys())
        
        required_skills = extract_skills_from_query(prompt, available_skills)
        if required_skills:
            suggestions = recommend_users_for_skills(required_skills, users)
            if suggestions:
                response = "🎯 **Top Experts Ready to Help!**\n\n"
                for user in suggestions:
                    response += f"🔥 **{user['name']}** \n📌 *USN:* `{user['USN']}` \n🏆 *Points:* `{user['points']}`\n💡 *Matched Skill:* `{user['matched_skill']}`\n\n"
            else:
                response = "❌ No members found with the requested skills. Try another skill or refine your request."
        else:
            response = "❓ No matching skills found in the database. Please specify valid skills from our system!"
    else:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([{"text": prompt}])
        response = response.text if response else "Sorry, I couldn't process that request."
    
    return response

st.set_page_config(page_title="Skill Nest Chatbot", page_icon="🤖", layout="centered")
st.title("🧭 सूत्रधार (Sūtradhāra)")
st.write("👋 Welcome! Choose a mode below:")

mode = st.radio("Select Mode:", ["General Conversation", "Find Members"], index=1)
user_input = st.text_input("💬 Enter your message:", key="user_message")
users = fetch_users()

if st.button("Submit") or st.session_state.get("send_clicked", False):
    loader_text = "⏳ Generating response..." if mode == "General Conversation" else "🔍 Finding best members for you..."
    with st.spinner(loader_text):
        time.sleep(2)  # Simulated loading effect
        response_text = generate_response(user_input, users, mode)
        st.markdown("### 🧭 सूत्रधार Response:")
        st.markdown(response_text, unsafe_allow_html=True)
    st.session_state["send_clicked"] = False
