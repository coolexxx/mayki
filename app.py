import streamlit as st
from datetime import datetime
import time
import requests
import json
from openai import OpenAI
from PIL import Image
import base64

# Streamlit Seitenkonfiguration
st.set_page_config(page_title="Maya-Horoskop", layout="wide", , page_icon="⭐")

# OpenAI API-Schlüssel Setup
# Zugriff auf den API-Schlüssel aus den Streamlit-Secrets
OPENAI_API_KEY = st.secrets["openai"]["api_key"]

# Initialisiere den OpenAI-Client
client = OpenAI(api_key=OPENAI_API_KEY)

# Function to load and encode images
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


# Load background image
def set_bg_hack(main_bg):
    bin_str = get_base64_of_bin_file(main_bg)
    page_bg_img = '''
    <style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    background-attachment: fixed;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)


# GPT-4o-mini API call function
def gpt4o_mini_api_call(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": "You are MayKI. Output in German! You are a motivational and empathetic fortune teller. Respond to the user's input with a personalized and uplifting prediction based on their zodiac sign and the challenges they face. Ensure the tone is loving, motivational, and deeply spiritual."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        n=1,
        temperature=0.7,
    )
    return response.choices[0].message.content


# Load greeting text with UTF-8 encoding
try:
    with open("start.txt", "r", encoding="utf-8") as file:
        greeting_text = file.read()
except FileNotFoundError:
    greeting_text = "Willkommen bei MayKI! Leider konnte der Begrüßungstext nicht geladen werden."

# Maya zodiac signs and their data
maya_zodiac_signs = [
    "Imix (Krokodil)", "Ik (Wind)", "Akbal (Nacht)", "Kan (Eidechse)",
    "Chicchan (Schlange)", "Cimi (Tot)", "Manik (Hirsch)", "Lamat (Hase)",
    "Muluc (Wasser)", "Oc (Hund)", "Chuen (Affe)", "Eb (Gras)", "Ben (Schilf)"
]

# Maya zodiac sign descriptions
descriptions = {
    "Imix (Krokodil)": "Du gehörst dem Mayasternzeichen Imix an. In dir ruht eine mächtige Energie voller innerer Stärke. Du bist dazu berufen, mit Mut und Entschlossenheit deinen Weg zu gehen, wie das Krokodil, das ruhig, aber kraftvoll durch das Leben gleitet.",
    "Ik (Wind)": "Als Kind des Zeichens Ik bist du wie der Wind: frei, kraftvoll und ständig in Bewegung. Du bewegst die Seelen der Menschen um dich herum und trägst große Verantwortung für deine Worte und Taten. Du bringst Veränderungen in die Welt.",
    "Akbal (Nacht)": "Du gehörst dem Zeichen Akbal an, das die Tiefe der Nacht symbolisiert. In der Dunkelheit findest du Klarheit und Weisheit. Du hast die Gabe, Geheimnisse zu ergründen und die Herausforderungen des Lebens mit Mut zu meistern.",
    "Kan (Eidechse)": "Das Zeichen Kan, dem du angehörst, vereint die Anpassungsfähigkeit und Weisheit der Eidechse. Du kannst dich geschmeidig den Wellen des Lebens anpassen und findest in der Veränderung deine größte Stärke.",
    "Chicchan (Schlange)": "Als Kind des Zeichens Chicchan trägst du die Weisheit und die Kraft der Schlange in dir. Du bist tief mit der spirituellen Welt verbunden und hast die Fähigkeit, alte Wunden zu heilen und neue Wege des Wachstums zu finden.",
    "Cimi (Tot)": "Du bist im Zeichen Cimi geboren, das für Tod und Wiedergeburt steht. Du durchläufst zyklische Phasen des Endes und Neubeginns und findest in diesen Wandlungen deine innere Stärke. Du bist ein Meister der Transformation.",
    "Manik (Hirsch)": "Manik, das Sternzeichen des Hirsches, steht für Anmut und spirituelle Kraft. Du bist ein Anführer auf deinem Weg und hast die Fähigkeit, Herausforderungen mit Anmut und Klarheit zu meistern.",
    "Lamat (Hase)": "Als Kind des Zeichens Lamat trägst du die Kreativität und den Erfindungsreichtum des Hasen in dir. Du bringst Leichtigkeit und Freude in dein Umfeld und findest immer wieder neue Wege, um dein Leben kreativ zu gestalten.",
    "Muluc (Wasser)": "Du gehörst dem Sternzeichen Muluc an, das mit der Energie des Wassers verbunden ist. In deiner ruhigen, aber kraftvollen Natur findest du Balance und Harmonie. Deine Emotionen fließen tief und du bist in der Lage, Heilung und Erneuerung in die Welt zu bringen.",
    "Oc (Hund)": "Als Kind des Zeichens Oc trägst du die Energie des Hundes in dir, ein Symbol für Loyalität und Freundschaft. Du bist ein treuer Begleiter auf dem Lebensweg anderer und hast die Gabe, Menschen in schwierigen Zeiten zur Seite zu stehen.",
    "Chuen (Affe)": "Du bist im Zeichen Chuen geboren, das für Verspieltheit und Kreativität steht. Du hast eine große Gabe, Menschen zum Lachen zu bringen und Probleme auf kreative Weise zu lösen. Dein Leben ist ein Abenteuer, das du mit Begeisterung angehst.",
    "Eb (Gras)": "Das Zeichen Eb steht für Anpassungsfähigkeit und Durchhaltevermögen. Du bist in der Lage, dich jeder Situation anzupassen und in den schwierigsten Zeiten Stärke zu zeigen. Du gehst deinen Weg mit großer Zuversicht und Klarheit.",
    "Ben (Schilf)": "Als Kind des Zeichens Ben trägst du die Energie des Schilfs in dir. Du bist stark, flexibel und in der Lage, in stürmischen Zeiten festen Halt zu finden. Deine Entschlossenheit hilft dir, große Herausforderungen zu meistern."
}


# Calculate Maya zodiac sign
def calculate_maya_zodiac_sign(birthdate_str):
    try:
        birthdate = datetime.strptime(birthdate_str, "%d.%m.%Y")
        tzolkin_day_number = (birthdate - datetime(1900, 1, 1)).days % 260
        sign_index = tzolkin_day_number % 13
        return maya_zodiac_signs[sign_index]
    except ValueError:
        return None


# Custom CSS
st.markdown("""
    <style>
    .custom-title {
        font-family: 'Cinzel', serif;
        font-size: 4rem;
        color: #FFD700;
        text-align: center;
        padding: 20px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        background-color: rgba(0, 0, 0, 0.8);
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .content-box {
        background-color: rgba(0, 0, 0, 0.8);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        color: #FFD700;
    }
    .input-section {
        background: linear-gradient(45deg, rgba(75, 0, 130, 0.7), rgba(0, 0, 0, 0.7));
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .stButton>button {
        background: linear-gradient(45deg, #4B0082, #8A2BE2);
        color: #FFD700;
        font-weight: bold;
        border: none;
        padding: 15px 30px;
        border-radius: 25px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 1.2em;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 2px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton>button:hover {
        background: linear-gradient(45deg, #8A2BE2, #4B0082);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.2);
        transform: translateY(-2px);
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: rgba(255, 255, 255, 0.1);
        border: 2px solid #FFD700;
        color: #000000;
        font-size: 1.1em;
        border-radius: 5px;
    }
    .stTextInput>label, .stTextArea>label {
        color: #FFD700 !important;
        font-weight: bold;
        font-size: 1.3em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        background: linear-gradient(45deg, #4B0082, #000000);
        padding: 5px 10px;
        border-radius: 5px;
        display: inline-block;
        margin-bottom: 5px;
    }
    footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: rgba(0, 0, 0, 0.8);
        color: #FFD700;
        text-align: center;
        padding: 10px 0;
        z-index: 1000;
    }
    .loader {
        border: 16px solid #4B0082;
        border-top: 16px solid #FFD700;
        border-radius: 50%;
        width: 120px;
        height: 120px;
        animation: spin 2s linear infinite;
        margin: auto;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# Set background image
try:
    set_bg_hack('kalender.png')
except FileNotFoundError:
    st.warning("Das Hintergrundbild 'kalender.png' konnte nicht gefunden werden.")

# Title
st.markdown('<h1 class="custom-title">MayKI</h1>', unsafe_allow_html=True)

# Greeting text and pyramid image
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f'<div class="content-box">{greeting_text}</div>', unsafe_allow_html=True)
with col2:
    try:
        st.image("pyramide.webp", use_column_width=True)
    except FileNotFoundError:
        st.warning("Das Bild 'pyramide.webp' konnte nicht gefunden werden.")

# Input fields and prediction
with st.container():
    st.markdown('<div class="input-section">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Dein Name")
        birthdate = st.text_input("Dein Geburtsdatum (TT.MM.JJJJ)")

    with col2:
        wishes_problems = st.text_area("Deine Wünsche und Sorgen")

    if st.button("Maya-Tierkreiszeichen und Zukunft anzeigen"):
        maya_sign = calculate_maya_zodiac_sign(birthdate)
        if maya_sign:
            # Display zodiac sign and description
            description = descriptions.get(maya_sign, "Keine Beschreibung vorhanden")
            st.markdown(
                f'<div class="content-box"><h3 style="color: #FFD700;">Dein Maya-Tierkreiszeichen: {maya_sign}</h3>{description}</div>',
                unsafe_allow_html=True)

            # Creative loader
            with st.spinner("Deine Vorhersage wird erstellt..."):
                loader_placeholder = st.empty()
                loader_placeholder.markdown('<div class="loader"></div>', unsafe_allow_html=True)

                # GPT API call for prediction
                prompt = f"My name is {name}, my birthdate is {birthdate}, and my zodiac sign is {maya_sign}. I am currently facing the following wishes and problems: {wishes_problems}. Please give me an uplifting prediction and advice."
                gpt_response = gpt4o_mini_api_call(prompt)

                # Remove the loader
                loader_placeholder.empty()

            st.markdown(
                f'<div class="content-box"><h3 style="color: #FFD700;">Deine MayKI-Vorhersage:</h3>{gpt_response}</div>',
                unsafe_allow_html=True)

            # Display zodiac sign image
            german_sign_name = maya_sign.split(" ")[-1].lower()  # Get the German name and convert to lowercase
            german_sign_name = german_sign_name.strip("()")  # Remove parentheses
            try:
                st.image(f"{german_sign_name}.webp", use_column_width=True)
            except FileNotFoundError:
                st.warning(f"Symbolbild für {maya_sign} konnte nicht geladen werden.")
        else:
            st.error("Bitte ein gültiges Datum im Format TT.MM.JJJJ eingeben!")

    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<footer>
    Made with ❤️ by Alex - Support if you want and can: <a href="https://paypal.me/tuGutes" target="_blank" style="color: #FFD700;">paypal.me/tuGutes</a>
</footer>
""", unsafe_allow_html=True)
