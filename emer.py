import streamlit as st
import time
from io import BytesIO
from gtts import gTTS

# Enhanced First Aid Instructions Database
FIRST_AID_INSTRUCTIONS = {
    "bleeding": {
        "title": "Bleeding Control",
        "steps": [
            "Apply direct pressure with a clean cloth or sterile gauze.",
            "If blood soaks through, add more layers without removing the first.",
            "Keep the injured area elevated above the heart if possible.",
            "Apply pressure for at least 15 minutes without lifting to check.",
            "For severe bleeding, call emergency services (911) immediately.",
            "If bleeding is from a limb and cannot be controlled, use a tourniquet as a last resort."
        ],
        "emergency_level": "Critical",
        "symptoms": [
            "Continuous blood flow",
            "Blood soaking through bandages",
            "Pale or clammy skin",
            "Weakness or dizziness",
            "Severe pain in the injured area"
        ],
        "keywords": ["blood", "bleeding", "wound", "cut", "hemorrhage"]
    },
    "cardiac_emergency": {
        "title": "Cardiac Emergency",
        "steps": [
            "Call emergency services (911) immediately.",
            "Check for responsiveness and breathing.",
            "If no breathing, begin CPR: 30 chest compressions followed by 2 rescue breaths.",
            "Continue CPR until help arrives or the person shows signs of life.",
            "If an AED is available, use it following the device instructions."
        ],
        "emergency_level": "Critical",
        "symptoms": [
            "Chest pain or pressure",
            "Shortness of breath",
            "Pain in arms, back, neck, or jaw",
            "Cold sweat",
            "Nausea"
        ],
        "keywords": ["heart", "chest pain", "cardiac", "heart attack"]
    },
    "burns": {
        "title": "Burns Treatment",
        "steps": [
            "Remove the source of burning.",
            "Cool the burn under cool (not cold) running water for at least 10 minutes.",
            "Remove any jewelry or tight items near the burned area.",
            "Cover with a sterile gauze bandage.",
            "Do not apply ice, butter, or ointments.",
            "Seek medical attention for serious burns."
        ],
        "emergency_level": "Serious",
        "symptoms": [
            "Redness and pain",
            "Blistering",
            "Charred or blackened skin",
            "Swelling",
            "White or peeling skin"
        ],
        "keywords": ["burn", "fire", "scalding", "hot"]
    }
}

class FirstAidSystem:
    def __init__(self):
        self.supported_languages = {
            'English': 'en',
            'Spanish': 'es',
            'French': 'fr',
            'German': 'de',
            'Italian': 'it'
        }

    def search_emergency(self, search_term):
        """Search through emergencies and their keywords."""
        search_term = search_term.lower()
        for emergency_id, data in FIRST_AID_INSTRUCTIONS.items():
            if search_term in data['title'].lower() or \
               any(keyword in search_term for keyword in data['keywords']) or \
               any(search_term in symptom.lower() for symptom in data['symptoms']):
                return data
        return None

    def generate_voice(self, text, lang):
        """Generate voice audio for the given text."""
        try:
            tts = gTTS(text=text, lang=lang)
            audio_fp = BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            return {"status": "success", "audio": audio_fp}
        except Exception as e:
            return {"status": "error", "message": str(e)}


def initialize_session_state():
    if 'system' not in st.session_state:
        st.session_state.system = FirstAidSystem()
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_language' not in st.session_state:
        st.session_state.current_language = 'English'

def main():
    st.set_page_config(
        page_title="Emergency First Aid Assistant",
        page_icon="🚑",
        layout="wide"
    )

    initialize_session_state()
    system = st.session_state.system

    st.title("🚑 Emergency First Aid Assistant")
    st.markdown("### Ask me about any first aid situation, and I'll guide you!")

    # Sidebar
    with st.sidebar:
        st.header("Settings")
        selected_language = st.selectbox(
            "Select Language",
            options=list(system.supported_languages.keys()),
            key="language_selector"
        )
        st.session_state.current_language = selected_language

        enable_voice = st.checkbox("Enable Voice Instructions", value=True)

        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

    # Main content
    query = st.text_input(
        "💬 Ask about a first aid situation (e.g., 'How to treat burns?')",
        placeholder="Type your question here..."
    )

    if query:
        with st.spinner("Processing your query..."):
            result = system.search_emergency(query)
            if result:
                response = f"**{result['title']}**\n\n"
                response += "**Emergency Level:** " + result['emergency_level'] + "\n\n"
                response += "**Common Symptoms:**\n"
                response += "\n".join([f"- {symptom}" for symptom in result['symptoms']]) + "\n\n"
                response += "**Steps to Follow:**\n"
                response += "\n".join([f"{i+1}. {step}" for i, step in enumerate(result['steps'])])

                # Save to chat history
                st.session_state.chat_history.append({
                    "query": query,
                    "response": response,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })

                # Display response
                st.markdown(response)

                # Generate voice
                if enable_voice:
                    steps_text = ". ".join(result['steps'])
                    voice_result = system.generate_voice(
                        steps_text,
                        system.supported_languages[selected_language]
                    )
                    if voice_result["status"] == "success":
                        st.audio(voice_result["audio"].getvalue(), format="audio/mp3")
                    else:
                        st.error(f"Error generating voice: {voice_result['message']}")
            else:
                st.warning("Sorry, I couldn't find any relevant first aid instructions. Please try different keywords.")

    # Chat history
    st.markdown("---")
    st.markdown("### Chat History")
    if st.session_state.chat_history:
        for entry in reversed(st.session_state.chat_history):
            st.markdown(f"**Query:** {entry['query']}")
            st.markdown(f"**Response:** {entry['response']}")
            st.caption(f"Asked at: {entry['timestamp']}")
            st.markdown("---")
    else:
        st.info("No queries yet. Start by asking a question!")

if __name__ == "__main__":
    main()
