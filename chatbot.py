import streamlit as st
import os
import time
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# ✅ Set up Streamlit page
st.set_page_config(page_title="Skill Nest Chatbot", page_icon="🤖", layout="centered")

# ✅ Load API key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("API key not found. Please set the GEMINI_API_KEY environment variable.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# ✅ API Endpoint & Payload
USER_DATA_API = "https://skill-nest-backend.onrender.com/get_all_users_data"
API_PAYLOAD = {"batch_id": "batch_001"}

def fetch_users():
    """Fetch users dynamically from API using POST request."""
    try:
        response = requests.post(USER_DATA_API, json=API_PAYLOAD)
        response.raise_for_status()  # Raise an error if request fails
        data = response.json()
        return data.get("data", []) if "data" in data else []
    except requests.exceptions.RequestException as e:
        st.error(f"⚠️ Error fetching users: {e}")
        return []

def extract_skills_from_query(query, available_skills):
    """Extract skills from user input based on available skills."""
    return [skill for skill in available_skills if skill.lower() in query.lower()]

def recommend_users_for_skills(required_skills, users):
    """Find users with at least one of the required skills."""
    recommended_users = []
    
    for user in users:
        tech_skills = user.get("Tech-skills", {})
        if not tech_skills:
            continue

        for skill in required_skills:
            if skill.lower() in [s.lower() for s in tech_skills.keys()]:  # Case-insensitive match
                recommended_users.append({
                    "name": user.get("name", "Unknown"),
                    "USN": user.get("USN", "No USN"),
                    "points": user.get("points", 0),
                    "matched_skill": skill
                })
                break  # Stop checking more skills if a match is found
    
    # Sort by points (higher points first) and return top 5
    return sorted(recommended_users, key=lambda x: x["points"], reverse=True)[:5]

def generate_response(prompt, users, mode):
    """Generate chatbot response based on the selected mode."""
    skill_nest_keywords = ["skill nest", "what is skill nest", "about skill nest"]
    sutradhara_keywords = ["who are you", "what is sutradhara", "who is sutradhara"]

    if any(keyword in prompt.lower() for keyword in skill_nest_keywords):
        return "**Skill Nest** is a platform for collaboration and skill-sharing among students. 🚀"

    if any(keyword in prompt.lower() for keyword in sutradhara_keywords):
        return "**I am Sutradhara**, your chatbot assistant for Skill Nest! 🤖"

    if mode == "Find Members":
        available_skills = {skill.lower() for user in users for skill in user.get("Tech-skills", {}).keys()}
        
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
            response = "❌ No matching skills found in the database."
    else:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([{"text": prompt}])
        response = response.text if response else "Sorry, I couldn't process that request."

    return response

# ✅ Streamlit UI
st.title("🧭 सूत्रधार (Sūtradhāra)")
st.write("👋 Welcome! Choose a mode below:")

mode = st.radio("Select Mode:", ["General Conversation", "Find Members"], index=1)
user_input = st.text_input("💬 Enter your message:", key="user_message")
users = fetch_users()  # Fetch users on load

if st.button("Submit") or st.session_state.get("send_clicked", False):
    loader_text = "⏳ Generating response..." if mode == "General Conversation" else "🔍 Finding best members for you..."
    with st.spinner(loader_text):
        time.sleep(2)
        response_text = generate_response(user_input, users, mode)
        st.markdown("### 🧭 सूत्रधार Response:")
        st.markdown(response_text, unsafe_allow_html=True)
    st.session_state["send_clicked"] = False
