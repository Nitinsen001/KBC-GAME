"""
KBC Quiz - Streamlit edition

Voice OUT : browser speechSynthesis (no pyttsx3, works on any device, zero server load)
Voice IN  : st.audio_input (browser mic) -> Google speech recognition
"""
import hashlib
import io
import json
import random
import re
import time

import streamlit as st
import streamlit.components.v1 as components

try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False

st.set_page_config(page_title="Kaun Banega Crorepati", page_icon="🏆", layout="wide",
                   initial_sidebar_state="collapsed")

# ───────────────────────── Config & data ─────────────────────────
TIME_LIMIT = 30                      # seconds per question
LETTERS = "ABCD"
AMOUNTS = [10000, 20000, 50000, 100000, 200000, 400000, 800000, 1600000, 3200000, 7000000]
SAFE = {3, 6}                        # safe zones: ₹10,000 and ₹80,000
LIFELINES = {"50-50": "✂️ 50-50", "Audience Poll": "📊 Audience Poll",
             "Phone a Friend": "📞 Phone a Friend", "Flip": "🔄 Flip Question"}

# (tier, question, options, index of correct option)
# tier: e = easy (Q1-3), m = medium (Q4-6), h = hard (Q7-10)
BANK = [
    # ── easy ──
    ("e", "What is the capital of India?", ["Mumbai", "New Delhi", "Kolkata", "Chennai"], 1),
    ("e", "Which colour is at the top of the Indian national flag?", ["Green", "White", "Saffron", "Blue"], 2),
    ("e", "What is the national animal of India?", ["Lion", "Tiger", "Elephant", "Leopard"], 1),
    ("e", "Which planet is known as the Red Planet?", ["Earth", "Venus", "Mars", "Jupiter"], 2),
    ("e", "Who is called the Father of the Nation in India?",
     ["Mahatma Gandhi", "Jawaharlal Nehru", "Sardar Patel", "B. R. Ambedkar"], 0),
    ("e", "Which is the national flower of India?", ["Rose", "Lotus", "Marigold", "Jasmine"], 1),
    ("e", "How many players are there in a cricket team?", ["9", "10", "11", "12"], 2),
    ("e", "Which gas do plants absorb for photosynthesis?",
     ["Oxygen", "Nitrogen", "Carbon dioxide", "Hydrogen"], 2),
    ("e", "Which planet is closest to the Sun?", ["Venus", "Mercury", "Mars", "Earth"], 1),
    ("e", "What is the chemical symbol of Gold?", ["Ag", "Fe", "Go", "Au"], 3),
    ("e", "What is the capital of Madhya Pradesh?", ["Indore", "Gwalior", "Bhopal", "Jabalpur"], 2),
    ("e", "Which is the national bird of India?", ["Sparrow", "Peacock", "Parrot", "Crow"], 1),
    ("e", "Which festival is known as the Festival of Lights?", ["Holi", "Diwali", "Eid", "Baisakhi"], 1),
    ("e", "Who was the first Prime Minister of India?",
     ["Jawaharlal Nehru", "Mahatma Gandhi", "Sardar Patel", "Subhash Chandra Bose"], 0),
    ("e", "In which year did India gain independence?", ["1947", "1950", "1935", "1942"], 0),
    # ── medium ──
    ("m", "Which river flows through Ujjain?", ["Narmada", "Chambal", "Shipra", "Betwa"], 2),
    ("m", "Which is the largest planet in our Solar System?", ["Saturn", "Neptune", "Earth", "Jupiter"], 3),
    ("m", "Which is the smallest state of India by area?", ["Goa", "Sikkim", "Tripura", "Manipur"], 0),
    ("m", "Who wrote the Indian national anthem 'Jana Gana Mana'?",
     ["Bankim Chandra Chatterjee", "Rabindranath Tagore", "Sarojini Naidu", "Muhammad Iqbal"], 1),
    ("m", "Which river is known as the 'Sorrow of Bihar'?", ["Gandak", "Kosi", "Son", "Ghaghara"], 1),
    ("m", "Who is known as the Missile Man of India?",
     ["Homi Bhabha", "A. P. J. Abdul Kalam", "Vikram Sarabhai", "Satish Dhawan"], 1),
    ("m", "Which gas is the most abundant in Earth's atmosphere?",
     ["Oxygen", "Nitrogen", "Carbon dioxide", "Argon"], 1),
    ("m", "Which is the largest state of India by area?",
     ["Madhya Pradesh", "Maharashtra", "Rajasthan", "Uttar Pradesh"], 2),
    ("m", "Which city is known as the Pink City?", ["Jodhpur", "Udaipur", "Jaipur", "Jaisalmer"], 2),
    ("m", "Who was the first woman Prime Minister of India?",
     ["Sarojini Naidu", "Indira Gandhi", "Pratibha Patil", "Sonia Gandhi"], 1),
    ("m", "Which Jyotirlinga is located in Ujjain?",
     ["Omkareshwar", "Mahakaleshwar", "Kedarnath", "Somnath"], 1),
    ("m", "Which is the hardest natural substance?", ["Gold", "Iron", "Diamond", "Quartz"], 2),
    ("m", "Which vitamin do we get from sunlight?", ["Vitamin A", "Vitamin C", "Vitamin D", "Vitamin K"], 2),
    ("m", "In which year did India win its first Cricket World Cup?", ["1975", "1983", "1987", "2011"], 1),
    ("m", "Who was the first President of India?",
     ["S. Radhakrishnan", "Rajendra Prasad", "Zakir Husain", "V. V. Giri"], 1),
    # ── hard ──
    ("h", "Which Article of the Indian Constitution abolishes untouchability?",
     ["Article 14", "Article 15", "Article 17", "Article 21"], 2),
    ("h", "What was the name of India's first satellite?",
     ["Bhaskara", "Aryabhata", "INSAT-1A", "Rohini"], 1),
    ("h", "Chandrayaan-3 landed near which region of the Moon?",
     ["North pole", "South pole", "Equator", "Far side centre"], 1),
    ("h", "In which year was the Battle of Plassey fought?", ["1757", "1764", "1857", "1526"], 0),
    ("h", "Who discovered the electron?", ["Rutherford", "J. J. Thomson", "Niels Bohr", "James Chadwick"], 1),
    ("h", "Who won India's first individual Olympic gold medal?",
     ["Neeraj Chopra", "Abhinav Bindra", "Rajyavardhan Rathore", "Leander Paes"], 1),
    ("h", "The Tropic of Cancer passes through which of these states?",
     ["Maharashtra", "Madhya Pradesh", "Karnataka", "Kerala"], 1),
    ("h", "Which is the highest mountain peak located entirely within India?",
     ["Mount Everest", "K2", "Kangchenjunga", "Nanda Devi"], 3),
    ("h", "Who composed the national song 'Vande Mataram'?",
     ["Rabindranath Tagore", "Bankim Chandra Chatterjee", "Muhammad Iqbal", "Subramania Bharati"], 1),
    ("h", "Which Indian state has the longest coastline?",
     ["Tamil Nadu", "Andhra Pradesh", "Gujarat", "Maharashtra"], 2),
    ("h", "Which city was the capital of British India before Delhi?",
     ["Bombay", "Calcutta", "Madras", "Allahabad"], 1),
    ("h", "Which Indian scientist won the Nobel Prize in Physics in 1930?",
     ["S. N. Bose", "C. V. Raman", "Meghnad Saha", "S. Chandrasekhar"], 1),
    ("h", "In which year did Gandhi lead the Dandi March?", ["1919", "1920", "1930", "1942"], 2),
    ("h", "Which great Sanskrit poet is linked with Ujjain and Vikramaditya's court?",
     ["Banabhatta", "Kalidasa", "Bhasa", "Jayadeva"], 1),
]
NEED = {"e": 3, "m": 3, "h": 4}      # questions drawn per tier -> 10 per game

# ───────────────────────── Styling ─────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Mukta:wght@400;600;700&display=swap');
:root{--gold:#f5b942;--gold2:#ffe08a;--ink:#0a0d2c;--indigo:#1a1660;--green:#1faa59;--red:#d63a4a}
.stApp{background:radial-gradient(1200px 700px at 50% -10%,#2b2290 0%,#120f45 45%,#070920 100%);
  color:#f3f1ff;font-family:'Mukta',sans-serif}
#MainMenu,footer,header[data-testid="stHeader"]{visibility:hidden}
.block-container{padding-top:1.2rem;max-width:1250px}
h1,h2,h3,.brand{font-family:'Marcellus',serif!important;letter-spacing:.5px}
.brand{font-size:2.3rem;color:var(--gold2);text-align:center;margin:0}
.sub{text-align:center;color:#b9b4ee;margin-bottom:1rem}
.qbox{border:2px solid var(--gold);border-radius:18px;padding:1.3rem 1.6rem;margin:.6rem 0 1rem;
  background:linear-gradient(180deg,#1b1771,#100d4a);font-size:1.5rem;line-height:1.4;
  box-shadow:0 0 28px rgba(245,185,66,.22)}
.qmeta{color:var(--gold);font-size:.95rem;margin-bottom:.3rem}
.stButton>button{width:100%;border-radius:999px;border:2px solid var(--gold);color:#fff;
  background:linear-gradient(180deg,#221d86,#120f4d);padding:.65rem 1.2rem;font-size:1.1rem;
  text-align:left;transition:transform .12s,box-shadow .12s}
.stButton>button:hover:not(:disabled){transform:translateY(-1px);border-color:var(--gold2);
  box-shadow:0 0 16px rgba(245,185,66,.45);color:#fff}
.stButton>button[kind="primary"],.stButton>button[data-testid="stBaseButton-primary"]{
  background:linear-gradient(180deg,#ffd466,#e29a1c);color:#2a1b00;font-weight:700;border-color:#fff1b8}
.stButton>button:disabled{opacity:.35}
.opt{border-radius:999px;padding:.65rem 1.2rem;font-size:1.1rem;border:2px solid var(--gold);
  background:#120f4d;margin-bottom:.55rem}
.opt.correct{background:var(--green);border-color:#b8ffd3;font-weight:700}
.opt.wrong{background:var(--red);border-color:#ffc2c9;font-weight:700}
.opt.dim{opacity:.45}
.ladder{border:1px solid #3a34a8;border-radius:14px;padding:.5rem;background:#0d0b3a}
.rung{display:flex;justify-content:space-between;padding:.22rem .7rem;border-radius:8px;
  color:#a9a4e6;font-size:.98rem}
.rung.safe{color:#fff}.rung.safe b{color:var(--gold2)}
.rung.done{color:#6fe3a0}
.rung.now{background:linear-gradient(90deg,#ffd466,#e29a1c);color:#2a1b00;font-weight:700}
.timer{height:10px;border-radius:99px;background:#241f7a;overflow:hidden}
.timer>div{height:100%;background:linear-gradient(90deg,#1faa59,#f5b942);transition:width 1s linear}
.timer.low>div{background:var(--red)}
.tnum{text-align:right;color:var(--gold2);font-size:1.1rem;margin-bottom:.2rem}
.poll{display:flex;gap:.6rem;align-items:flex-end;height:120px;margin:.4rem 0 1rem}
.poll div.col{flex:1;text-align:center}
.poll div.bar{background:linear-gradient(180deg,#ffd466,#e29a1c);border-radius:6px 6px 0 0}
.friend{border-left:4px solid var(--gold);padding:.5rem .9rem;background:#171358;border-radius:8px;
  margin-bottom:1rem}
.center{text-align:center}
.amount{font-family:'Marcellus',serif;font-size:3rem;color:var(--gold2)}
.trophy{animation:glow 2.4s ease-in-out infinite;display:block;margin:0 auto}
@keyframes glow{0%,100%{filter:drop-shadow(0 0 12px rgba(245,185,66,.5))}
  50%{filter:drop-shadow(0 0 34px rgba(255,224,138,.95))}}
@media (prefers-reduced-motion:reduce){.trophy{animation:none}.timer>div{transition:none}}

.stButton>button{min-height:3rem;line-height:1.25}
.stButton>button p{margin:0}
[class*="st-key-ll_"] button{font-size:.88rem;padding:.4rem .3rem;min-height:2.4rem;
  justify-content:center;text-align:center}
.stButton>button[kind="primary"]:hover:not(:disabled){color:#2a1b00}
.qbox{font-size:1.35rem;text-align:center}
.ladder{position:sticky;top:1rem}
.rung span{opacity:.7}
[data-testid="stAudioInput"]{margin-top:.6rem}
.block-container{padding-bottom:2rem}
</style>
""", unsafe_allow_html=True)

TROPHY = """
<svg class="trophy" viewBox="0 0 200 240" width="230" role="img" aria-label="Winner trophy">
<defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
<stop offset="0" stop-color="#fff2b0"/><stop offset=".5" stop-color="#f5b942"/>
<stop offset="1" stop-color="#b9770e"/></linearGradient></defs>
<path d="M50 20h100v50c0 38-22 62-50 66-28-4-50-28-50-66z" fill="url(#g)"/>
<path d="M50 34H20c0 34 14 52 36 58M150 34h30c0 34-14 52-36 58" fill="none"
 stroke="#e0a02b" stroke-width="10" stroke-linecap="round"/>
<rect x="92" y="132" width="16" height="42" fill="url(#g)"/>
<path d="M62 174h76l8 24H54z" fill="url(#g)"/>
<rect x="46" y="198" width="108" height="24" rx="4" fill="#7a4a0a"/>
<text x="100" y="215" text-anchor="middle" font-size="12" fill="#ffe08a"
 font-family="serif" letter-spacing="2">CHAMPION</text>
<path d="M100 38l8 18 20 2-15 13 5 19-18-10-18 10 5-19-15-13 20-2z" fill="#fff6cc" opacity=".9"/>
</svg>"""

# ───────────────────────── Helpers ─────────────────────────
def inr(n: int) -> str:
    """Indian digit grouping: 640000 -> ₹6,40,000"""
    s = str(n)
    if len(s) <= 3:
        return "₹" + s
    head, tail, parts = s[:-3], s[-3:], []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return "₹" + ",".join(parts + [tail])


def say(text: str):
    """Queue text to be spoken by the browser at the end of this run."""
    if st.session_state.get("voice_on", True):
        st.session_state.say = text


def flush_speech():
    text = st.session_state.pop("say", None)
    if text:
        components.html(f"""<script>/*{time.time()}*/
        try {{
          const synth = (window.parent && window.parent.speechSynthesis) || window.speechSynthesis;
          synth.cancel();
          const u = new SpeechSynthesisUtterance({json.dumps(text)});
          u.lang = 'en-IN'; u.rate = 0.95;
          const v = synth.getVoices().find(v => v.lang === 'en-IN') ||
                    synth.getVoices().find(v => v.lang.startsWith('en'));
          if (v) u.voice = v;
          synth.speak(u);
        }} catch (e) {{}}
        </script>""", height=0)


@st.cache_resource
def get_recognizer():
    return sr.Recognizer()


def transcribe(data: bytes) -> str:
    with sr.AudioFile(io.BytesIO(data)) as src:
        audio = get_recognizer().record(src)
    return get_recognizer().recognize_google(audio, language="en-IN")


WORD_TO_LETTER = {
    "a": "A", "ay": "A", "eh": "A", "first": "A", "ए": "A", "एक": "A",
    "b": "B", "bee": "B", "be": "B", "second": "B", "बी": "B",
    "c": "C", "see": "C", "sea": "C", "third": "C", "सी": "C",
    "d": "D", "dee": "D", "the": "D", "fourth": "D", "डी": "D",
}


def parse_letter(text: str):
    for tok in re.findall(r"[a-zA-Z\u0900-\u097F]+", text.lower()):
        if tok in WORD_TO_LETTER:
            return WORD_TO_LETTER[tok]
    return None


def shuffled(q, opts, ans):
    order = random.sample(range(4), 4)
    return {"q": q, "opts": [opts[i] for i in order], "ans": order.index(ans)}


# ───────────────────────── Game logic ─────────────────────────
s = st.session_state
if "stage" not in s:
    s.stage = "intro"


def start_question():
    s.selected, s.removed, s.poll, s.friend = None, set(), None, None
    s.locked, s.correct, s.timed_out = False, False, False
    s.q_start = time.time()
    s.attempt += 1
    q = s.qs[s.qi]
    opts = ". ".join(f"Option {LETTERS[i]}, {t}" for i, t in enumerate(q["opts"]))
    say(f"Question {s.qi + 1}, for {AMOUNTS[s.qi]} rupees. {q['q']} {opts}")


def pick_questions():
    """Draw fresh random questions per tier; replays avoid repeats until a tier is used up."""
    if "seen" not in s:
        s.seen = set()
    chosen, pool = [], {}
    for tier, n in NEED.items():
        ids = [i for i, b in enumerate(BANK) if b[0] == tier]
        fresh = [i for i in ids if i not in s.seen]
        if len(fresh) < n + 1:                     # keep >=1 spare for Flip
            s.seen -= set(ids)
            fresh = ids[:]
        random.shuffle(fresh)
        chosen += fresh[:n]
        pool[tier] = fresh[n:]
        s.seen |= set(fresh[:n])
    s.pool = pool
    s.tiers = [t for t, n in NEED.items() for _ in range(n)]
    s.qs = [shuffled(*BANK[i][1:]) for i in chosen]


def new_game():
    pick_questions()
    s.lifelines = {k: True for k in LIFELINES}
    s.update(stage="play", qi=0, final=0, reason=None, celebrated=False,
             last_audio=None, attempt=0, mic_msg=None)
    start_question()


def finish(reason: str):
    qi = s.qi
    if reason == "win":
        amt = AMOUNTS[-1]
    elif reason == "quit":
        amt = AMOUNTS[qi - 1] if qi else 0
    else:
        amt = max([AMOUNTS[i] for i in SAFE if i < qi], default=0)
    s.update(stage="result", reason=reason, final=amt, celebrated=False)
    if reason == "win":
        say("Congratulations! You are the champion of Kaun Banega Crorepati!")
    else:
        say(f"The game is over. You are going home with {amt} rupees.")


def select(i):
    s.selected = i
    say(f"Option {LETTERS[i]}. Lock it?")


def lock():
    q = s.qs[s.qi]
    s.locked, s.correct = True, s.selected == q["ans"]
    if s.correct:
        say("Absolutely correct answer!")
    else:
        say(f"Oh no, that is wrong. The correct answer was option {LETTERS[q['ans']]}, "
            f"{q['opts'][q['ans']]}.")


def next_step():
    if not s.correct:
        finish("timeout" if s.timed_out else "wrong")
    elif s.qi == len(s.qs) - 1:
        s.qi += 1
        finish("win")
    else:
        s.qi += 1
        start_question()


def use_lifeline(name):
    q = s.qs[s.qi]
    s.lifelines[name] = False
    alive = [i for i in range(4) if i not in s.removed]
    if name == "50-50":
        s.removed = set(random.sample([i for i in range(4) if i != q["ans"]], 2))
        if s.selected in s.removed:
            s.selected = None
        say("Two wrong options removed.")
    elif name == "Audience Poll":
        top = max(0.30, random.uniform(0.60, 0.82) - 0.035 * s.qi)
        w = {i: random.random() for i in alive if i != q["ans"]}
        tot = sum(w.values()) or 1
        poll = {i: round((1 - top) * 100 * v / tot) for i, v in w.items()}
        poll[q["ans"]] = 100 - sum(poll.values())
        s.poll = poll
        say("The audience has voted.")
    elif name == "Phone a Friend":
        wrong = random.choice([i for i in alive if i != q["ans"]])
        pick = random.choice([q["ans"], wrong])     # friend is torn between one right, one wrong
        a, b = sorted([q["ans"], wrong])
        s.friend = (f"I'm confused between option {LETTERS[a]} and option {LETTERS[b]}. "
                    f"I'll go with option {LETTERS[pick]}.")
        say(f"Your friend says: {s.friend}")
    elif name == "Flip":
        tier = s.tiers[s.qi]
        if s.pool[tier]:
            i = s.pool[tier].pop()
            s.seen.add(i)
            s.qs[s.qi] = shuffled(*BANK[i][1:])
            start_question()


def quit_game():
    finish("quit")


# ───────────────────────── Screens ─────────────────────────
st.markdown('<p class="brand">Kaun Banega Crorepati</p>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Settings")
    st.toggle("🔊 Read questions aloud", True, key="voice_on")
    st.toggle("🎙️ Answer by voice", HAS_SR, key="mic_on", disabled=not HAS_SR)
    if not HAS_SR:
        st.caption("Install SpeechRecognition to enable voice answers.")
    st.caption("Tip: use Chrome or Edge, and allow microphone access.")


def ladder():
    rows = []
    for i in reversed(range(len(AMOUNTS))):
        cls = "rung" + (" safe" if i in SAFE else "")
        if s.stage == "play" and i == s.qi:
            cls += " now"
        elif i < s.qi:
            cls += " done"
        rows.append(f'<div class="{cls}"><span>{i + 1}</span><b>{inr(AMOUNTS[i])}</b></div>')
    st.markdown(f'<div class="ladder">{"".join(rows)}</div>', unsafe_allow_html=True)


@st.fragment(run_every="1s")
def timer():
    left = TIME_LIMIT - (time.time() - s.q_start)
    if left <= 0 and not s.locked:
        s.locked, s.correct, s.timed_out = True, False, True
        say("Time is up.")
        st.rerun()
    left = max(0, left)
    low = " low" if left < 10 else ""
    st.markdown(f'<div class="tnum">⏱ {int(left)}s</div>'
                f'<div class="timer{low}"><div style="width:{left / TIME_LIMIT * 100:.0f}%"></div></div>',
                unsafe_allow_html=True)


def screen_intro():
    st.markdown('<p class="sub">10 questions · 4 lifelines · safe zones at ₹10,000 and ₹80,000</p>',
                unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        st.button("▶  Start the game", type="primary", on_click=new_game)
    st.markdown("<p class='sub'>Answer with the buttons or by voice – say A, B, C or D, "
                "then lock your final answer.</p>", unsafe_allow_html=True)


def screen_play():
    q = s.qs[s.qi]
    main, side = st.columns([3, 1.15], gap="large")

    with side:
        ladder()

    with main:
        # lifelines
        cols = st.columns(4)
        for col, (key, label) in zip(cols, LIFELINES.items()):
            col.button(label, key=f"ll_{key}", on_click=use_lifeline, args=(key,),
                       disabled=(not s.lifelines[key] or s.locked
                                 or (key == "Flip" and not s.pool[s.tiers[s.qi]])))

        if not s.locked:
            timer()

        st.markdown(f'<div class="qbox"><div class="qmeta">Question {s.qi + 1} · '
                    f'{inr(AMOUNTS[s.qi])}</div>{q["q"]}</div>', unsafe_allow_html=True)

        if s.friend:
            st.markdown(f'<div class="friend">📞 Friend: {s.friend}</div>', unsafe_allow_html=True)
        if s.poll:
            bars = "".join(
                f'<div class="col"><small>{s.poll.get(i, 0)}%</small>'
                f'<div class="bar" style="height:{s.poll.get(i, 0) * 1.1}px"></div>'
                f'<b>{LETTERS[i]}</b></div>' for i in range(4) if i in s.poll)
            st.markdown(f'<div class="poll">{bars}</div>', unsafe_allow_html=True)

        # options
        oc = st.columns(2)
        for i, text in enumerate(q["opts"]):
            label = f"{LETTERS[i]}.  {text}"
            with oc[i % 2]:
                if s.locked:
                    cls = "correct" if i == q["ans"] else ("wrong" if i == s.selected else "dim")
                    st.markdown(f'<div class="opt {cls}">{label}</div>', unsafe_allow_html=True)
                elif i in s.removed:
                    st.button("—", key=f"o{i}_{s.attempt}", disabled=True)
                else:
                    st.button(label, key=f"o{i}_{s.attempt}", on_click=select, args=(i,),
                              type="primary" if s.selected == i else "secondary")

        if s.locked:
            if s.timed_out:
                st.warning("⏰ Time's up!")
            elif s.correct:
                st.success(f"✅ Correct! You have won {inr(AMOUNTS[s.qi])}")
            else:
                st.error("❌ Wrong answer.")
            last = s.qi == len(s.qs) - 1
            st.button("Next question →" if s.correct and not last else
                      "🏆 Claim your prize" if s.correct else "See result →",
                      type="primary", on_click=next_step)
            return

        a, b = st.columns(2)
        a.button("🔒 Lock final answer", type="primary", disabled=s.selected is None, on_click=lock)
        if s.qi > 0:
            b.button(f"🚪 Quit with {inr(AMOUNTS[s.qi - 1])}", on_click=quit_game)

        # voice answer
        if s.get("mic_on") and HAS_SR:
            audio = st.audio_input("🎙️ Say A, B, C or D", key=f"aud_{s.attempt}")
            if audio is not None:
                data = audio.getvalue()
                h = hashlib.md5(data).hexdigest()
                if h != s.last_audio:
                    s.last_audio = h
                    try:
                        with st.spinner("Listening…"):
                            heard = transcribe(data)
                        letter = parse_letter(heard)
                        idx = LETTERS.index(letter) if letter else None
                        if idx is None or idx in s.removed:
                            st.warning(f"Heard “{heard}”. Please say A, B, C or D clearly.")
                        else:
                            select(idx)
                            st.rerun()
                    except Exception:
                        st.warning("Could not understand the voice. Try again or tap an option.")


def screen_result():
    win = s.reason == "win"
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if win:
            st.markdown(TROPHY, unsafe_allow_html=True)
            st.markdown('<h2 class="center">Congratulations, Champion!</h2>', unsafe_allow_html=True)
            st.markdown('<p class="sub">You answered all 10 questions correctly.</p>',
                        unsafe_allow_html=True)
        else:
            msg = {"quit": "You quit with your winnings.",
                   "timeout": "Time ran out.", "wrong": "That was not the right answer."}[s.reason]
            st.markdown(f'<h2 class="center">{msg}</h2>', unsafe_allow_html=True)
        st.markdown(f'<p class="center sub">Final winning amount</p>'
                    f'<p class="center amount">{inr(s.final)}</p>', unsafe_allow_html=True)
        st.button("🔁 Play again", type="primary", on_click=new_game)
    if win and not s.celebrated:
        s.celebrated = True
        st.balloons()


{"intro": screen_intro, "play": screen_play, "result": screen_result}[s.stage]()
flush_speech()