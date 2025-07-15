import pyttsx3
import pyfiglet
import time
import threading
import speech_recognition as sr
import time
import os
import sys
if os.name == "nt":
    sys.stdout.reconfigure(encoding='utf-8')  # For Windows terminal


# Voice setup
def speak(text):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)  # 1 = Zira
    engine.setProperty('rate', 145)
    engine.say(text)
    engine.runAndWait()

# Get voice input
def get_voice_input(timeout=5):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Speak your answer (A/B/C/D)...")
        speak("Kripya apna uttar bolein. Jaise A, B, C, ya D.")
        r.adjust_for_ambient_noise(source)
        try:
            audio = r.listen(source, timeout=timeout)
            answer = r.recognize_google(audio).strip().upper()
            print(f"🗣 You said: {answer}")
            return answer
        except sr.WaitTimeoutError:
            print("⏰ Time out ho gaya.")
            speak("Samay samapt ho gaya.")
        except sr.UnknownValueError:
            print("🤷 Could not understand voice.")
            speak("Aapki aawaaz samajh nahi aayi.")
        except sr.RequestError:
            print("⚠️ Speech Recognition service down.")
            speak("Voice recognition kaam nahi kar raha.")
    return None

# Game data
questions = [
    ("🟨 Q1: What is the capital of India?", "B"),
    ("🟨 Q2: Which planet is known as the Red Planet?", "C"),
    ("🟨 Q3: How many days are there in a leap year?", "B"),
    ("🟨 Q4: Which animal is known as the 'Ship of the Desert'?", "B"),
    ("🟨 Q5: What is the national flower of India?", "C"),
    ("🟨 Q6: Who was the first President of India?", "A"),
    ("🟨 Q7: Which gas do plants absorb?", "C"),
    ("🟨 Q8: Which dance is from Kerala?", "B"),
    ("🟨 Q9: What does HTTP stand for?", "B"),
    ("🟨 Q10: Who composed National Anthem?", "D"),
    ("🟨 Q11: Boiling point of water?", "C"),
    ("🟨 Q12: Longest river in the world?", "C"),
    ("🟨 Q13: Currency of Japan?", "A"),
    ("🟨 Q14: Which organ purifies blood?", "D"),
    ("🟨 Q15: Who invented telephone?", "A")
]

options = [
    ["A. Mumbai", "B. New Delhi", "C. Kolkata", "D. Chennai"],
    ["A. Earth", "B. Venus", "C. Mars", "D. Jupiter"],
    ["A. 365", "B. 366", "C. 364", "D. 367"],
    ["A. Elephant", "B. Camel", "C. Horse", "D. Donkey"],
    ["A. Rose", "B. Marigold", "C. Lotus", "D. Jasmine"],
    ["A. Dr. Rajendra Prasad", "B. Nehru", "C. Ambedkar", "D. Patel"],
    ["A. Oxygen", "B. Nitrogen", "C. Carbon Dioxide", "D. Hydrogen"],
    ["A. Kathak", "B. Kathakali", "C. Bharatanatyam", "D. Kuchipudi"],
    ["A. High Tech", "B. HyperText Transfer Protocol", "C. Terminal Text", "D. High Process"],
    ["A. Bankim", "B. Vivekananda", "C. Lata", "D. Rabindranath Tagore"],
    ["A. 90°C", "B. 80°C", "C. 100°C", "D. 110°C"],
    ["A. Amazon", "B. Ganga", "C. Nile", "D. Yangtze"],
    ["A. Yen", "B. Yuan", "C. Won", "D. Peso"],
    ["A. Heart", "B. Liver", "C. Lungs", "D. Kidney"],
    ["A. Alexander Graham Bell", "B. Newton", "C. Einstein", "D. Edison"]
]

levels = [5000, 10000, 20000, 40000, 60000, 160000, 320000, 640000, 1250000, 2500000, 5000000, 10000000, 30000000, 50000000, 70000000]

# Game loop
def start_game():
    result = pyfiglet.figlet_format("KBC Game", font="slant")
    print(result)
    speak("Swagat hai aapka Kaun Banega Crorepati mein.")
    amount = 0
    for i in range(len(questions)):
        print(f"\n🎯 Question {i+1} for ₹{levels[i]}")
        speak(f"Prashn sankhya {i+1} ke liye, {levels[i]} rupaye.")
        print(questions[i][0])
        for option in options[i]:
            print(option)
        speak("Aapke options hain: " + ", ".join(options[i]))

        print("⏳ You have 10 seconds to speak your answer (A/B/C/D)...")
        answer = get_voice_input(timeout=10)
        if answer is None:
            print("😢 No input received. Game over.")
            speak("Koi uttar nahi mila. Aapka samay samapt hua.")
            break

        answer = answer.strip().upper()
        if answer == questions[i][1]:
            print("✅ Correct Answer!")
            speak("Bilkul sahi jawaab!")
            amount = levels[i]
        else:
            print(f"❌ Wrong Answer! Correct answer was: {questions[i][1]}")
            speak("Durbhagya se, yeh galat jawaab tha.")
            break

        if i in [3, 7, 14]:
            print(f"\n🎉 You’ve reached milestone ₹{amount}")
            speak(f"Aap ne {amount} rupaye jeet liye hain.")
            choice = input("Do you want to continue? (yes/no): ").lower()
            if choice != "yes":
                speak("Dhanyavaad. Aapka safar yahin tak tha.")
                break

    print(f"\n💰 Final Winning Amount: ₹{amount}")
    speak(f"Aapka antim inaam hai {amount} rupaye.")

# Run game
start_game()
