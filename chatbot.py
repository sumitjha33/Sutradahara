import streamlit as st
import requests  # For API requests
import ollama  # For DeepSeek-R1 model
from fuzzywuzzy import process
import re
import time

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
                match_score = process.extractOne(skill, tech_skills.keys())
                if match_score and match_score[1] > 70:  # 70% similarity threshold
                    recommended_users.append({
                        "name": user.get("name", "Unknown"),
                        "USN": user.get("USN", "No USN"),
                        "points": user.get("points", 0),
                        "matched_skill": match_score[0]
                    })
                    break  # Include user if they match at least one skill
    recommended_users = sorted(recommended_users, key=lambda x: x["points"], reverse=True)[:5]  # Return top 5 users
    return recommended_users
    """Find users who know at least one of the required skills."""
    recommended_users = []
    for user in users:
        tech_skills = user.get("Tech-skills", {})  # Get user skills
        if tech_skills:
            for skill in required_skills:
                match_score = process.extractOne(skill, tech_skills.keys())
                if match_score and match_score[1] > 70:  # 70% similarity threshold
                    recommended_users.append({
                        "name": user.get("name", "Unknown"),
                        "USN": user.get("USN", "No USN"),
                        "points": user.get("points", 0),
                        "matched_skill": match_score[0]
                    })
                    break  # Include user if they match at least one skill
    recommended_users = sorted(recommended_users, key=lambda x: x["points"], reverse=True)[:5]  # Return top 5 users
    return recommended_users

def generate_response(prompt, users, mode):
    """Generate chatbot response based on selected mode."""
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
        response = ollama.chat(model="deepseek-r1:1.5b", messages=[{"role": "user", "content": prompt}])
        response = response.get("message", {}).get("content", "Sorry, I couldn't process that request.")
    return response

# Streamlit UI Enhancements
st.set_page_config(page_title="Skill Nest Chatbot", page_icon="🤖", layout="centered")
st.markdown(""" <style>
    .big-font { font-size:20px !important; color: #4CAF50; }
    .chatbox { background-color: #f9f9f9; padding: 15px; border-radius: 10px; }
    .recommend { color: #2196F3; font-weight: bold; }
    .stTextInput > div > div > input { text-align: left; } /* Removes 'Press Enter to Apply' */
</style> """, unsafe_allow_html=True)

st.title("🧭 सूत्रधार (Sūtradhāra)")
st.write("👋 Welcome! Choose a mode below:")

mode = st.radio("Select Mode:", ["General Conversation", "Find Members"], index=1)
user_input = st.text_input("💬 Enter your message:", key="user_message")
users = fetch_users()  # Fetch users from API on load

if st.button("Submit") or st.session_state.get("send_clicked", False):
    with st.spinner("⏳ Thinking... Finding the best members for you!"):
        time.sleep(2)  # Simulated loading effect
        response_text = generate_response(user_input, users, mode)
        st.markdown("### 🧭 सूत्रधार Response:")
        st.markdown(f"<div class='chatbox'>{response_text}</div>", unsafe_allow_html=True)
    st.session_state["send_clicked"] = False
