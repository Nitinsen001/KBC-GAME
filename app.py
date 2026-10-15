import streamlit as st
from streamlit_lottie import st_lottie
import requests
import pandas as pd
import numpy as np

st.set_page_config(page_title="KBC Game UI", layout="wide", initial_sidebar_state="expanded")

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Load a fun Lottie animation
lottie_url = "https://assets9.lottiefiles.com/packages/lf20_jcikwtux.json"
lottie_json = load_lottieurl(lottie_url)

# Custom CSS for gradient background and glassmorphism cards
custom_css = """
<style>
@keyframes gradient {
    0% {background-position:0% 50%;}
    50% {background-position:100% 50%;}
    100% {background-position:0% 50%;}
}
.card {
    background: linear-gradient(135deg, #ff9800, #ff5722);
    border-radius:15px;
    padding:1.5rem;
    margin:1rem 0;
    backdrop-filter:blur(12px);
    box-shadow:0 4px 30px rgba(0,0,0,0.5);
    color:#fff;
    transition: transform 0.2s, box-shadow 0.2s;
}
.card:hover {
    transform:scale(1.04);
    box-shadow:0 6px 35px rgba(0,0,0.0.6);
}
.title {
    font-family:'Orbitron',sans-serif;
    font-size:3.8rem;
    text-align:center;
    color:#ffd700;
    text-shadow:0 0 12px #ffd700;
    margin-bottom:1rem;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# KBC style header with logo and title
kbc_logo_url = "https://upload.wikimedia.org/wikipedia/en/6/68/Kabhi_Kabhi_logo.png"  # placeholder KBC logo
st.image(kbc_logo_url, width=120)
st.markdown("<div class='title'>KBC Game Dashboard</div>", unsafe_allow_html=True)
if lottie_json:
    st_lottie(lottie_json, height=180, key="kbc_lottie")

@st.cache_data
def get_sample_data():
    np.random.seed(42)
    df = pd.DataFrame({
        "Question": [f"Q{i}" for i in range(1, 11)],
        "Score": np.random.randint(0, 100, size=10)
    })
    return df

df = get_sample_data()

tab1, tab2, tab_home = st.tabs(["🏆 Leaderboard", "🎮 Play Game", "🏠 Home"])
# Question bank for the KBC style game
QUESTIONS = [
    {"question":"What is the capital of India?","options":["Mumbai","New Delhi","Kolkata","Chennai"],"answer":"New Delhi"},
    {"question":"Who wrote the play 'Romeo and Juliet'?","options":["Shakespeare","Marlowe","Chaucer","Hemingway"],"answer":"Shakespeare"},
    {"question":"What is the chemical symbol for Gold?","options":["Au","Ag","Gd","Go"],"answer":"Au"},
    {"question":"What is the largest planet in our solar system?","options":["Earth","Mars","Jupiter","Saturn"],"answer":"Jupiter"},
    {"question":"Which language is primarily spoken in Brazil?","options":["Spanish","Portuguese","French","English"],"answer":"Portuguese"},
    {"question":"Who painted the Mona Lisa?","options":["Van Gogh","Picasso","Leonardo da Vinci","Michelangelo"],"answer":"Leonardo da Vinci"},
    {"question":"What is the smallest prime number?","options":["0","1","2","3"],"answer":"2"},
    {"question":"Which element has atomic number 1?","options":["Helium","Oxygen","Hydrogen","Carbon"],"answer":"Hydrogen"},
    {"question":"What year did the Titanic sink?","options":["1910","1912","1914","1916"],"answer":"1912"},
    {"question":"Who is known as the Father of Computers?","options":["Alan Turing","Charles Babbage","Bill Gates","Steve Jobs"],"answer":"Charles Babbage"},
    {"question":"Which country hosted the 2016 Summer Olympics?","options":["China","Brazil","UK","Russia"],"answer":"Brazil"},
    {"question":"What is the hardest natural substance?","options":["Gold","Diamond","Iron","Platinum"],"answer":"Diamond"},
    {"question":"Which planet is known as the Red Planet?","options":["Mars","Venus","Mercury","Jupiter"],"answer":"Mars"},
    {"question":"Who wrote 'Pride and Prejudice'?","options":["Emily Brontë","Jane Austen","Charlotte Brontë","Mary Shelley"],"answer":"Jane Austen"},
    {"question":"What is the currency of Japan?","options":["Yuan","Yen","Won","Dollar"],"answer":"Yen"},
    {"question":"Which organ pumps blood in the human body?","options":["Liver","Brain","Heart","Kidney"],"answer":"Heart"},
    {"question":"What is the chemical formula for water?","options":["H2O","CO2","O2","NaCl"],"answer":"H2O"},
    {"question":"Who discovered penicillin?","options":["Alexander Fleming","Marie Curie","Louis Pasteur","Isaac Newton"],"answer":"Alexander Fleming"},
    {"question":"Which city is known as the Big Apple?","options":["Los Angeles","Chicago","New York","San Francisco"],"answer":"New York"},
    {"question":"What is the speed of light in vacuum (approx km/s)?","options":["150,000","300,000","450,000","600,000"],"answer":"300,000"}
]

with tab1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📊 Player Scores")
    st.bar_chart(df.set_index("Question"))
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    # Initialize session state
    if 'name' not in st.session_state:
        st.session_state.name = ""
    if 'q_idx' not in st.session_state:
        st.session_state.q_idx = 0
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'won_prize' not in st.session_state:
        st.session_state.won_prize = "₹0"
    if 'game_over' not in st.session_state:
        st.session_state.game_over = False

    # Prize ladder (one prize per question)
    PRIZES = [f"₹{i} crore" for i in range(1, len(QUESTIONS) + 1)]
    
    # Name input
    if not st.session_state.name:
        st.session_state.name = st.text_input("Enter your name", "")
        
    
    # Show current prize for the next question (if game in progress)
    if not st.session_state.game_over and st.session_state.q_idx < len(PRIZES):
        st.info(f"Current prize for this question: {PRIZES[st.session_state.q_idx]}")
    
    # Quit button (available at any time)
    if st.button("Quit and take prize"):
        st.success(f"You quit! You win {st.session_state.won_prize}")
        st.balloons()
        st.session_state.game_over = True
    
    # Quiz interface
    if st.session_state.name and not st.session_state.game_over:
        q = QUESTIONS[st.session_state.q_idx]
        st.subheader(f"Question {st.session_state.q_idx + 1}: {q['question']}")
        answer = st.radio("Choose an option", q['options'], key=f"option_{st.session_state.q_idx}")
        col1, col2 = st.columns(2)
        if col1.button("Submit Answer"):
            if answer == q['answer']:
                st.success("Correct! 🎉")
                st.session_state.score += 1
                # Update won prize after correct answer
                st.session_state.won_prize = PRIZES[st.session_state.q_idx]
            else:
                st.error(f"Incorrect. Correct answer: {q['answer']}")
                # Keep previous prize
            if st.session_state.q_idx < len(QUESTIONS) - 1:
                st.session_state.q_idx += 1
                st.rerun()
            else:
                st.session_state.game_over = True
    
    # End of game summary
    if st.session_state.game_over:
        if st.session_state.score == len(QUESTIONS):
            st.success(f"🎉 शानदार! {st.session_state.name}, आप सभी प्रश्न सही उत्तर दे चुके हैं! 🎉")
        st.success(f"Your final prize: {st.session_state.won_prize}")
        st.balloons()
    
    st.markdown("</div>", unsafe_allow_html=True)

with tab_home:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("About the Developer")
    st.write("**Niti Devloper** created this KBC‑style quiz app with a premium animated UI. Enjoy the smooth gradients, glass‑morphism cards, and interactive gameplay!")
    # Add a subtle animation using Lottie (reuse the same Lottie)
    if lottie_json:
        st_lottie(lottie_json, height=150, key="home_lottie")
    st.markdown("---")
    st.caption("© 2026 Niti Devloper – All rights reserved")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='border-color:#00ffcc;'>", unsafe_allow_html=True)
st.caption("Made with Streamlit ✨ | Animated UI | Premium Look")
