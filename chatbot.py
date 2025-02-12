import streamlit as st
import os
import time
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import re

# ✅ Set up Streamlit page
st.set_page_config(page_title="Skill Nest Chatbot", page_icon="🤖", layout="wide")

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
        response.raise_for_status()
        data = response.json()
        return data.get("data", []) if "data" in data else []
    except requests.exceptions.RequestException as e:
        st.error(f"⚠️ Error fetching users: {e}")
        return []

def normalize_skills(skills):
    """Convert various skill formats (list, dict) into a standardized list."""
    if isinstance(skills, dict):
        return list(skills.keys())
    elif isinstance(skills, list):
        return skills
    else:
        return []

def recommend_users_for_skills(skill, users, max_members=5):
    """Find users with the requested skill, limited to max_members."""
    recommended_users = []

    for user in users:
        tech_skills = normalize_skills(user.get("Tech-skills", []))
        soft_skills = normalize_skills(user.get("Soft-skills", []))
        combined_skills = set(tech_skills + soft_skills)

        if skill.lower() in [s.lower() for s in combined_skills]:
            recommended_users.append({
                "name": user.get("name", "Unknown"),
                "USN": user.get("USN", "No USN"),
                "points": user.get("points", 0)
            })

    return sorted(recommended_users, key=lambda x: x["points"], reverse=True)[:max_members]

def extract_member_count(prompt):
    """Extract the number of members requested from the user's prompt."""
    match = re.search(r"(\d+)\s+members", prompt.lower())
    return int(match.group(1)) if match else 5

def generate_response(prompt, users, mode):
    """Generate chatbot response based on the selected mode."""
    if mode == "Find Members":
        # Extract skills and requested member count
        available_skills = set()
        for user in users:
            tech_skills = normalize_skills(user.get("Tech-skills", []))
            soft_skills = normalize_skills(user.get("Soft-skills", []))
            available_skills.update(skill.lower() for skill in tech_skills + soft_skills)

        required_skills = [skill for skill in available_skills if skill in prompt.lower()]
        member_count = extract_member_count(prompt)

        if required_skills:
            response = "🎯 **Members Categorized by Skills:**\n\n"
            for skill in required_skills:
                response += f"🔹 **For {skill.capitalize()}:**\n\n"  # Bold skill name and add a line break
                suggestions = recommend_users_for_skills(skill, users, member_count)
                if suggestions:
                    for user in suggestions:
                        response += f"🔥 **{user['name']}** \n📌 *USN:* `{user['USN']}` \n🏆 *Points:* `{user['points']}`\n\n"
                else:
                    response += "❌ No members found for this skill.\n\n"
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

# 🔥 Sidebar for About & Help
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712032.png", width=100)
    st.title("🔹 About Sutradhara")
    st.write("""
        **Sutradhara** is an AI-powered assistant for **Skill Nest**,  
        helping students find skilled collaborators and answer questions. 🤖  
    """)
    
    st.title("🆘 Help")
    st.write("""
        **How to Use:**
        - Select **General Conversation** for chatbot Q&A.
        - Select **Find Members** to search for skilled people.
        - Type your query in the text box and click **Submit**.
    """)

# User Input & Mode Selection
mode = st.radio("Select Mode:", ["General Conversation", "Find Members"], index=1)
user_input = st.text_input("💬 Enter your message:", key="user_message")
users = fetch_users()  # Fetch users on load

# ✅ Display Response
if st.button("Submit") or st.session_state.get("send_clicked", False):
    loader_text = "⏳ Generating response..." if mode == "General Conversation" else "🔍 Finding best members for you..."
    with st.spinner(loader_text):
        time.sleep(2)
        response_text = generate_response(user_input, users, mode)
        st.markdown("### 🧭 सूत्रधार Response:")
        st.markdown(response_text, unsafe_allow_html=True)
    st.session_state["send_clicked"] = False
