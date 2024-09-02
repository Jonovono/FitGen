import streamlit as st
import random
import time
from PIL import Image
import requests
from io import BytesIO
from openai import OpenAI
import replicate
import asyncio

ANTHROPIC_API_KEY = st.secrets.get('ANTHROPIC_API_KEY', '')
OPENAI_API_KEY = st.secrets.get('OPENAI_API_KEY', '')
REPLICATE_API_TOKEN = st.secrets.get('REPLICATE_API_TOKEN', '')

# openai.api_key = OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)
replicate_client = replicate.Client(api_token=REPLICATE_API_TOKEN)


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

def generate_image(prompt):
    input_data = {
        "prompt": prompt,
        "guidance": 3.5,
        "aspect_ratio": "9:16",
        "output_format": "jpg"
    }

    output = replicate_client.run(
        "black-forest-labs/flux-dev",
        input=input_data
    )
    print("OUTPUT IMAGE: ", output)
    return output[0]  # Return the first image URL


async def async_chatgpt_call(messages):
    response = await client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=messages,
        max_tokens=600
    )
    return response

def generate_outfit_message(details):
    description_parts = []
    
    if details["season"]:
        description_parts.append(f"Season: {details['season']}")
    if details["venue_type"]:
        description_parts.append(f"Venue: {details['venue_type']}")
    if details["event_type"]:
        description_parts.append(f"Event Type: {details['event_type']}")
    if details["location"]:
        description_parts.append(f"Location: {details['location']}")
    if details["dress_code"]:
        description_parts.append(f"Dress Code: {details['dress_code']}")
    if details["hair_color"]:
        description_parts.append(f"Hair Color: {details['hair_color']}. Make sure the outfit looks good with this hair color.")
    if details["skin_tone"]:
        description_parts.append(f"Skin Tone: {details['skin_tone']}. Make sure the outfit looks good with this skin tone.")
    if details["extra_details"]:
        description_parts.append(f"Extra Details: {details['extra_details']}")

    description = "\n".join(description_parts)

    prompt = f"""Here are details of the wedding event that I am attending. Please generate a stable diffusion prompt to generate an image of a unique and elegant wedding outfit design for an attendee based on the following details:

{description}
"""
    
    return {
        "role": "user",
        "content": prompt
    }


def rate_outfit(liked):
    st.session_state.loading = True
    st.session_state.current_image = None

    if liked:
        prompt = "I liked the outfit design. Please generate a new outfit design that I may like"
    else:
        prompt = "I did not like the outfit design. Please generate a new outfit design that I may like"

    st.session_state.messages.append({"role": "user", "content": prompt})

    # with st.spinner('Generating outfit based on your feedback...'):
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=st.session_state.messages,
        max_tokens=600
    )

    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})

    # Generate image using Replicate API
    image_url = generate_image(msg)
    st.session_state.current_image = image_url

    st.session_state.loading = False  

    st.rerun()

    return


def get_random_image_url():
    return f"https://picsum.photos/400/600?random={random.randint(1, 1000)}"


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": "You are a fashion expert. Generate a stable diffusion prompt to generate an image of a unique and elegant wedding outfit design for an attendee based on the following details of the wedding event that I am attending. The user will then follow up if they like the outfit that was generated or not, so continously improve your outfit based on the feedback. Describe in as much detail as possible the outfit, including hair, makeup, accessories, and shoes. Please put the person and outfit in an appropriate setting based on the event details. Respond with the prompt only."},]


if 'current_image' not in st.session_state:
    st.session_state.current_image = None

if 'loading' not in st.session_state:
    st.session_state.loading = False


# # if 'messages' not in st.session_state:
# #     st.session_state.messages = []
# if 'current_outfit' not in st.session_state:
#     st.session_state.current_outfit = None
# if 'feedback' not in st.session_state:
#     st.session_state.feedback = []

# Sidebar for input
with st.sidebar:
    st.title("Dress Gen 👗")

    # Add Generate Outfit and Reset buttons at the top
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🔄"):
            # Reset session state values to default
            for key in default_values.keys():
                st.session_state[key] = default_values[key]
                st.session_state.messages = []
                st.session_state.current_image = None
                st.session_state.loading = False
            st.rerun()
    with col2:
      generate_button = st.button("✨ Generate Outfit")

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
        st.session_state.loading = True 
        st.session_state.current_image = None  # Reset the current image
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
        outfit_message = generate_outfit_message(details)
        st.session_state.messages.append(outfit_message)


        # response = asyncio.run(async_chatgpt_call(st.session_state.messages))

        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=st.session_state.messages,
            max_tokens=600
        )

        msg = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": msg})

        # # Generate image using Replicate API
        image_url = generate_image(msg)
        print("IMAGE URL: ", image_url)
        st.session_state.current_image = image_url
        st.session_state.loading = False


        
        # st.rerun()
        # rating_message = generate_rating_message(False)

        # st.session_state.messages.append(outfit_message)
        # st.session_state.messages.append(rating_message)

        # print(st.session_state.current_outfit)
        # st.session_state.current_outfit = new_outfit
        # st.session_state.current_image = get_random_image_url()
        # st.session_state.messages.append({"role": "assistant", "content": new_outfit})
        # st.session_state.messages.append({"role": "assistant", "content": st.session_state.current_outfit})


# Main area for chat and image display
# Main area for chat and image display
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.write(message["content"])


st.write("LOADING: ", st.session_state.loading)

if st.session_state.current_image:
    # st.image(st.session_state.current_image, caption=st.session_state.current_outfit, width=300)
  left_co, cent_co,last_co, other_co = st.columns(4)
  with cent_co:
      # st.image(st.session_state.current_image, caption=st.session_state.current_image, width=300)
      # if st.session_state.current_image:
      #     st.image(st.session_state.current_image, caption=st.session_state.current_image, width=300)
      # else:
      #     with st.spinner('Generating your outfit...'):
      #         time.sleep(5) 
      st.image(st.session_state.current_image, caption="", width=300)
  # if st.session_state.loading:
  #     with st.spinner('Generating your outfit...'):
  #         time.sleep(5) # Spinner is shown while loading is True
  # elif st.session_state.current_image:
  #     st.image(st.session_state.current_image, caption="", width=300)
    # st.image(st.session_state.current_image, 
    #          caption=st.session_state.current_outfit, 
    #      width=300)


if st.session_state.loading:
    with st.spinner('Generating your outfit...'):
        time.sleep(5)

if st.session_state.current_image:  
  with st.container():
      col1, col2, col3 = st.columns(3)
      with col1:
          if st.button("Dislike 👎", key="dislike_button", use_container_width=True):
              # st.session_state.feedback.append(("dislike", st.session_state.current_outfit))
              # st.info("Got it! Let's try something different...")
              rate_outfit(False)
              # time.sleep(1)  # Simulating processing time
              # st.session_state.current_outfit = generate_outfit({})
              # st.session_state.current_image = get_random_image_url()
              # st.experimental_rerun()
      with col2:
          # for msg in st.session_state.messages:
          #     st.chat_message(msg["role"]).write(msg["content"])

          st.link_button("Shop 🛍️", 
                          f"https://dupe.com/{st.session_state.current_image}", 
                          use_container_width=True)
      with col3:
          if st.button("Like 👍", key="like_button", use_container_width=True):
              # st.session_state.feedback.append(("like", st.session_state.current_outfit))
              # st.success("Thanks for your feedback! Generating a new outfit...")
              # time.sleep(1)  # Simulating processing time
              rate_outfit(True)
            # st.session_state.current_outfit = generate_outfit({})
            # st.session_state.current_image = get_random_image_url()
            # st.experimental_rerun()

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