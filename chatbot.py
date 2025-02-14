import streamlit as st
import os
import time
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import re

# ✅ Set up Streamlit page with custom icon
st.set_page_config(page_title="Skill Nest Chatbot", page_icon="D:/Sutradhara/image/WhatsApp Image 2025-02-14 at 11.23.35_47e0abbb.jpg", layout="wide")

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
    if prompt.strip().lower() in ["who are you?", "who are you","who made you?","who made you"]:
        # Custom response for "Who are you?" question
        return "I am a large language model made by Google and trained by Sumit Kumar."

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
                response += f"🔹 **For {skill.capitalize()}:**\n\n"
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


# ✅ Initialize history
if "history" not in st.session_state:
    st.session_state["history"] = []

def add_to_history(prompt, response, mode):
    """Add prompt-response pair to the history with mode and limit to 10 entries."""
    st.session_state["history"].append({"mode": mode, "prompt": prompt, "response": response})
    if len(st.session_state["history"]) > 10:
        st.session_state["history"].pop(0)

# ✅ Streamlit UI
st.title("🧭 सूत्रधार (Sūtradhāra)")
st.write("👋 Welcome! Choose a mode below:")

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

    # Add to history
    st.session_state["history"].append({
        "prompt": user_input,
        "response": response_text,
        "mode": mode
    })
    st.session_state["send_clicked"] = False


# 🔍 Right Sidebar for History
st.sidebar.header("📜 Chat History")
if st.session_state["history"]:
    for i, entry in enumerate(reversed(st.session_state["history"])):
        # Ensure unique keys for sidebar buttons
        if st.sidebar.button(f"Q{i+1}: {entry['prompt']}", key=f"sidebar_history_{i}"):
            # Expand the conversation view in the sidebar
            st.sidebar.write(f"**User (Mode: {entry['mode']})**: {entry['prompt']}")
            st.sidebar.write(f"**Sutradhāra**: {entry['response']}")
else:
    st.sidebar.write("No history available yet.")

# 👉 About Section
with st.sidebar.expander("📖 About Skill Nest", expanded=False):
    st.write("""
    **Skill Nest** is a dynamic platform designed to connect learners and professionals
    with relevant resources and collaborators. It helps users enhance their skills,
    find team members for projects, and build strong communities for learning.

    **Features**:
    - Connect with members who share your interests.
    - Recommend project collaborators based on required skills.
    - A versatile chatbot for general queries and skill-based searches.
    """)

# 🙋 Help Section
with st.sidebar.expander("❓ Help", expanded=False):
    st.write("""
    ### How to Use Sūtradhāra:
    1. **Select a Mode**: Choose between 'General Conversation' or 'Find Members'.
    2. **Enter Your Message**: Type in your query or skill request.
    3. **Submit**: Click the "Submit" button to generate a response or find members.
    4. **View History**: Check previous queries and responses under "Chat History".
    
    **Tips**:
    - Be specific in your requests for better recommendations.
    - Use keywords related to skills to get accurate suggestions.
    - If you encounter errors, refresh the page or check your internet connection.
    """)

# You can add more sections or enhance these as per your requirements!
