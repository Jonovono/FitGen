import streamlit as st
import random
import time
from PIL import Image
import requests
from io import BytesIO
from openai import OpenAI
import replicate
import fal_client
from litellm import completion


ANTHROPIC_API_KEY = st.secrets.get('ANTHROPIC_API_KEY', '')
OPENAI_API_KEY = st.secrets.get('OPENAI_API_KEY', '')
REPLICATE_API_TOKEN = st.secrets.get('REPLICATE_API_TOKEN', '')
FAL_KEY = st.secrets.get('FAL_KEY', '')

import os
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY

# openai.api_key = OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)
replicate_client = replicate.Client(api_token=REPLICATE_API_TOKEN)

st.set_page_config(
    page_title="fitgen.shop - generate outfits for weddings",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get help': "https://discord.gg/TPmx2Kmrzz",
        'About': 'https://discord.gg/TPmx2Kmrzz',
    }
)


# Reducing whitespace on the top of the page
st.markdown("""
<style>

.block-container
{
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-top: 1rem;
}

</style>
""", unsafe_allow_html=True)


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

def make_api_call():
    # model = random.choice(["gpt-4o-2024-08-06", "claude-3-5-sonnet-20240620"])
    model = "claude-3-5-sonnet-20240620"

    response = completion(
        model=model,
        messages=st.session_state.messages,
        # max_tokens=600
    )
    
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})

    image_url = generate_image(msg)
    print("IMAGE URL: ", image_url)
    st.session_state.current_image = image_url
    st.session_state.loading = False

    st.rerun()

def generate_outfit_callback():
    st.session_state.loading = True
    st.session_state.current_image = None
    details = {
        "location": st.session_state.location,
        "dress_code": st.session_state.dress_code,
        "season": st.session_state.season,
        "hair_color": st.session_state.hair_color,
        "skin_tone": st.session_state.skin_tone,
        "venue_type": st.session_state.venue_type,
        "event_type": st.session_state.event_type,
        "extra_details": st.session_state.extra_details
    }
    outfit_message = generate_outfit_message(details)
    st.session_state.messages.append(outfit_message)

    make_api_call()

def rate_outfit_callback(liked):
    st.session_state.loading = True
    st.session_state.current_image = None

    prompt = "I liked the outfit design. Please generate a new outfit design that I may like" if liked else "I did not like the outfit design. Please generate a new outfit design that I may like"
    st.session_state.messages.append({"role": "user", "content": prompt})

    make_api_call()

def generate_image(prompt, max_retries=3):
    print("Generating image with prompt: ", prompt)
    for attempt in range(max_retries):
        try:
            # 70% chance to use Replicate
            use_replicate = random.random() < 0.7
            
            if use_replicate:
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
                print("Using Replicate API")
                return output[0]  # Return the first image URL
            else:
                handler = fal_client.submit(
                    "fal-ai/flux-realism",
                    arguments={
                        "prompt": prompt,
                        "image_size": "portrait_16_9",  # This is the closest to 9:16 aspect ratio
                        "num_inference_steps": 28,
                        "guidance_scale": 3.5,
                        "num_images": 1,
                        "output_format": "jpeg"
                    },
                )
                result = handler.get()
                print("Using Fal API")
                return result['images'][0]['url']
        except Exception as e:
            print(f"Error generating image (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                raise Exception("Failed to generate image after multiple attempts")
            else:
                print("Retrying with a modified prompt...")
                prompt = f"Family-friendly version: {prompt}"
    
    raise Exception("Failed to generate image after multiple attempts")


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



def get_random_image_url():
    return f"https://picsum.photos/400/600?random={random.randint(1, 1000)}"


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": "You are a fashion expert. Generate a stable diffusion prompt to generate an image of a unique and elegant wedding outfit design for a beautiful women in her mid 20s attending a wedding event based on the following details of the wedding event that they are attending. The user will then follow up if they like the outfit that was generated or not, so continously improve your outfit based on the feedback. Describe in as much detail as possible the outfit, including hair, makeup, accessories, and shoes. Ensure it is a fully body shot by describing the shoes in detail as well. Please put the person and outfit in an appropriate setting based on the event details. Respond with the prompt to generate the image only."},]
    st.session_state["messages"].append({"role": "user", "content": "Here is an example of a prompt: A beautiful woman in her mid-20s with vibrant red hair and medium skin tone stands in front of a charming Toronto church on a sunny summer day. She wears a knee-length, flowy sundress in soft pastel peach with delicate floral embroidery. The dress features thin straps and a sweetheart neckline, cinched at the waist with a light cream ribbon. She pairs the dress with elegant nude strappy sandals with a low heel. Her hair is styled in loose, beachy waves adorned with a small white flower clip. Her makeup is natural and radiant, with peachy blush and a soft pink lip. She accessorizes with dainty gold jewelry, including small hoop earrings and a thin bracelet. She carries a small cream-colored clutch and wears oversized sunglasses perched on top of her head. The background shows other casually dressed wedding guests arriving at the church, with leafy green trees and blue sky visible. Soft, warm lighting enhances the summery atmosphere."})


if 'current_image' not in st.session_state:
    st.session_state.current_image = None

if 'loading' not in st.session_state:
    st.session_state.loading = False


# Sidebar for input
with st.sidebar:
    st.title("fitgen.shop 👗")
    st.caption("Give as much info about the wedding you are attending and our AI will generate outfits for you which you can then shop for!")

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
      # generate_button = st.button("✨ Generate Outfit")
      st.button("✨ Generate Outfit", on_click=generate_outfit_callback)

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

    st.link_button("Join the Discord", "https://discord.gg/TPmx2Kmrzz")

if st.session_state.current_image:
  left_co, cent_co,last_co, other_co = st.columns(4)
  with cent_co:
      st.image(st.session_state.current_image, caption="", width=300)


if st.session_state.loading:
    with st.spinner('Generating your outfit...'):
        time.sleep(5)

if st.session_state.current_image: 
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Dislike 👎", key="dislike_button", on_click=rate_outfit_callback, args=(False,), use_container_width=True)
        with col2:
            st.link_button("Shop 🛍️", f"https://dupe.com/{st.session_state.current_image}", use_container_width=True)
        with col3:
            st.button("Like 👍", key="like_button", on_click=rate_outfit_callback, args=(True,), use_container_width=True) 


    st.link_button("Ask the community for help", "https://discord.gg/TPmx2Kmrzz", use_container_width=True)


    if prompt := st.chat_input():
      st.session_state.messages.append({"role": "user", "content": prompt})
      make_api_call()
      # response = client.chat.completions.create(
      #   model="gpt-4o-2024-08-06",
      #   messages=st.session_state.messages,
      #   max_tokens=600
      # )
      # msg = response.choices[0].message.content
      # st.session_state.messages.append({"role": "assistant", "content": msg})
      # image_url = generate_image(msg)
      # st.session_state.current_image = image_url
      # st.session_state.loading = False
      # st.rerun()
 