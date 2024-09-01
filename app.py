import streamlit as st
import random
import time
from PIL import Image
import requests
from io import BytesIO

# Default values
default_values = {
    "location": "",
    "dress_code": "",
    "season": "",
    "hair_color": "",
    "skin_tone": "",
    "venue_type": "",
    "event_type": "💍 Ceremony",
    "extra_details": ""
}

for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value



def generate_outfit(details):
    outfits = [
        "A flowing maxi dress in deep blue with floral accents",
        "An elegant cocktail dress in emerald green with lace details",
        "A chic jumpsuit in burgundy with a statement necklace",
        "A sophisticated A-line dress in soft pink with a matching jacket"
    ]
    return random.choice(outfits)

def get_random_image_url():
    return f"https://picsum.photos/400/600?random={random.randint(1, 1000)}"

if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_outfit' not in st.session_state:
    st.session_state.current_outfit = None
if 'feedback' not in st.session_state:
    st.session_state.feedback = []

# Sidebar for input
with st.sidebar:
    st.title("Dress Gen 👗")

    # Add Generate Outfit and Reset buttons at the top
    col1, col2 = st.columns([2, 1])
    with col1:
      generate_button = st.button("✨ Generate Outfit")
    with col2:
        if st.button("🔄"):
            # Reset session state values to default
            for key in default_values.keys():
                st.session_state[key] = default_values[key]
            st.rerun()

    location = st.text_input("📍 Wedding location", value=st.session_state["location"], key="location")
    dress_code = st.text_input("👗 Dress code", value=st.session_state["dress_code"], key="dress_code")
    season = st.selectbox("🌦️ Season", ["", "🌸 Spring", "☀️ Summer", "🍂 Autumn", "❄️ Winter"], index=["", "🌸 Spring", "☀️ Summer", "🍂 Autumn", "❄️ Winter"].index(st.session_state["season"]), key="season")
    hair_color = st.selectbox(
        "💇 Hair color",
        [
            "",
            "Blonde",
            "Light Brown",
            "Dark Brown",
            "Black",
            "Red",
            "Gray",
            "White",
            "Highlighted",
            "Other",
        ],
        index=["", "Blonde", "Light Brown", "Dark Brown", "Black", "Red", "Gray", "White", "Highlighted", "Other"].index(st.session_state["hair_color"]),
        key="hair_color"
    )
    skin_tone = st.selectbox(
        "👩 Skin tone",
        [
            "",
            "Fair",
            "Light",
            "Medium",
            "Olive",
            "Tan",
            "Brown",
            "Dark",
            "Deep",
            "Other",
        ],
        index=["", "Fair", "Light", "Medium", "Olive", "Tan", "Brown", "Dark", "Deep", "Other"].index(st.session_state["skin_tone"]),
        key="skin_tone"
    )
    venue_type = st.selectbox(
        "🏛️ Venue type",
        [
            "",
            "🏖️ Beach",
            "🎩 Ballroom",
            "🌳 Garden",
            "⛪ Church",
            "🏡 Rustic",
            "🏙️ Urban",
            "🐴 Barn",
            "🏰 Castle",
            "🍷 Winery",
            "🌲 Forest",
            "🏢 Courthouse",
            "Other",
        ],
        index=["", "🏖️ Beach", "🎩 Ballroom", "🌳 Garden", "⛪ Church", "🏡 Rustic", "🏙️ Urban", "🐴 Barn", "🏰 Castle", "🍷 Winery", "🌲 Forest", "🏢 Courthouse", "Other"].index(st.session_state["venue_type"]),
        key="venue_type"
    )
    event_type = st.selectbox(
        "🎉 Event type",
        [
            "💍 Ceremony",
            "🎊 Welcome Party",
            "🍽️ Rehearsal Dinner",
            "🥂 Reception",
            "🕺 After Party",
        ],
        index=["💍 Ceremony", "🎊 Welcome Party", "🍽️ Rehearsal Dinner", "🥂 Reception", "🕺 After Party"].index(st.session_state["event_type"]),
        key="event_type"
    )
    extra_details = st.text_area("📝 Any extra details?", value=st.session_state["extra_details"], key="extra_details")

    if generate_button:
        details = {
            "location": location,
            "dress_code": dress_code,
            "season": season,
            "hair_color": hair_color,
            "skin_tone": skin_tone,
            "venue_type": venue_type,
            "event_type": event_type,
            "extra_details": extra_details
        }
        new_outfit = generate_outfit(details)
        st.session_state.current_outfit = new_outfit
        st.session_state.current_image = get_random_image_url()
        st.session_state.messages.append({"role": "assistant", "content": new_outfit})


# Main area for chat and image display
# Main area for chat and image display
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.write(message["content"])

if st.session_state.current_outfit:
    # st.image(st.session_state.current_image, caption=st.session_state.current_outfit, width=300)
    left_co, cent_co,last_co, other_co = st.columns(4)
    with cent_co:
        st.image(st.session_state.current_image, 
                 caption=st.session_state.current_outfit, 
             width=300)

    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Dislike 👎", key="dislike_button", use_container_width=True):
                st.session_state.feedback.append(("dislike", st.session_state.current_outfit))
                st.info("Got it! Let's try something different...")
                time.sleep(1)  # Simulating processing time
                st.session_state.current_outfit = generate_outfit({})
                st.session_state.current_image = get_random_image_url()
                st.experimental_rerun()
        with col2:
            st.link_button("Shop 🛍️", 
                           f"https://dupe.com/{st.session_state.current_image}", 
                           use_container_width=True)
        with col3:
            if st.button("Like 👍", key="like_button", use_container_width=True):
                st.session_state.feedback.append(("like", st.session_state.current_outfit))
                st.success("Thanks for your feedback! Generating a new outfit...")
                time.sleep(1)  # Simulating processing time
                st.session_state.current_outfit = generate_outfit({})
                st.session_state.current_image = get_random_image_url()
                st.experimental_rerun()
# Display feedback history
# if st.session_state.feedback:
#     st.header("Your Feedback History")
#     for feedback, outfit in st.session_state.feedback:
#         st.write(f"{'👍' if feedback == 'like' else '👎'} {outfit}")

# User input for questions or comments
# user_input = st.chat_input("Ask a question or provide more details about your preferences")
# if user_input:
#     st.session_state.messages.append({"role": "user", "content": user_input})
#     # Here you would typically process the user input and generate a response
#     # For now, we'll just acknowledge the input
#     st.session_state.messages.append({"role": "assistant", "content": f"Thank you for your input: '{user_input}'. I'll take that into account for future outfit suggestions."})
#     st.experimental_rerun()