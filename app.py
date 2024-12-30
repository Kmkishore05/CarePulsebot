import streamlit as st
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2, service_pb2_grpc, resources_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2
from googletrans import Translator
from gtts import gTTS
import base64
from io import BytesIO
from datetime import datetime
import re

class ClarifaiSystem:
    def __init__(self, api_key, user_id, app_id, workflow_id):
        self.api_key = api_key
        self.user_id = user_id
        self.app_id = app_id
        self.workflow_id = workflow_id
        self.channel = ClarifaiChannel.get_grpc_channel()
        self.stub = service_pb2_grpc.V2Stub(self.channel)
        self.metadata = (('authorization', f'Key {self.api_key}'),)
        self.translator = Translator()
        
        # Define medical-related keywords and phrases
        self.medical_keywords = [
    'symptom', 'pain', 'doctor', 'medicine', 'treatment', 'health',
    'disease', 'condition', 'medical', 'hospital', 'clinic', 'diagnosis',
    'therapy', 'prescription', 'medication', 'illness', 'injury', 'healing',
    'recovery', 'patient', 'healthcare', 'examination', 'test', 'checkup',
    'vaccine', 'vaccination', 'surgery', 'emergency', 'ambulance', 'first aid',
    'blood', 'heart', 'lung', 'brain', 'stomach', 'skin', 'bone', 'muscle',
    'joint', 'nerve', 'infection', 'virus', 'bacteria', 'fever', 'cough',
    'allergy', 'diet', 'nutrition', 'exercise', 'wellness', 'diabetes',
    'hypertension', 'asthma', 'cancer', 'tumor', 'arthritis', 'depression',
    'anxiety', 'cholesterol', 'stroke', 'epilepsy', 'migraine', 'headache',
    'obesity', 'anemia', 'ulcer', 'gastroenteritis', 'hepatitis', 'jaundice',
    'thyroid', 'osteoporosis', 'dementia', 'paralysis', 'pneumonia', 'bronchitis',
    'cardiovascular', 'respiratory', 'dermatology', 'psychiatry', 'neurology',
    'urology', 'gynecology', 'oncology', 'pathology', 'orthopedics', 'radiology',
    'ophthalmology', 'dentistry', 'immunology', 'endocrinology', 'pediatrics',
    'geriatrics', 'cardiology', 'pulmonology', 'nephrology', 'hepatology',
    'infertility', 'eczema', 'psoriasis', 'sepsis', 'shock', 'autism',
    'bipolar', 'schizophrenia', 'insomnia', 'fatigue', 'constipation',
    'diarrhea', 'vomiting', 'rash', 'hives', 'swelling', 'fracture', 'sprain',
    'bleeding', 'burn', 'cut', 'wound', 'scar', 'inflammation', 'laceration',
    'concussion', 'dehydration', 'malnutrition', 'sinusitis', 'tuberculosis',
    'cholera', 'dysentery', 'HIV', 'AIDS', 'malaria', 'dengue', 'Zika', 'Ebola',
    'COVID-19', 'SARS', 'MERS', 'Lyme', 'Rabies', 'typhoid', 'meningitis',
    'polio', 'cirrhosis', 'fibrosis', 'colitis', 'Crohn', 'IBS', 'GERD', 'appendicitis',
    'kidney stones', 'gallstones', 'pancreatitis', 'prostate', 'testosterone',
    'estrogen', 'menopause', 'pregnancy', 'prenatal', 'postnatal', 'childbirth',
    'labor', 'miscarriage', 'abortion', 'contraception', 'STD', 'STI',
    'hormones', 'immunity', 'genes', 'genetic', 'DNA', 'RNA', 'stem cells'
]


    def is_medical_related(self, text):
        """Check if the input text is related to medical/health topics"""
        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Check if any medical keyword is present in the text
        return any(keyword in text_lower for keyword in self.medical_keywords)

    def get_qa_response(self, question, source_lang, target_lang):
        try:
            # Translate to English first for content checking
            if source_lang != 'en':
                question_en = self.translator.translate(question, src=source_lang, dest='en').text
            else:
                question_en = question

            # Check if the question is medical-related
            if not self.is_medical_related(question_en):
                return {
                    "status": "error",
                    "response": "Please ask only medical or health-related questions. For other topics, please use a different service."
                }

            workflow_response = self.stub.PostWorkflowResults(
                service_pb2.PostWorkflowResultsRequest(
                    user_app_id=resources_pb2.UserAppIDSet(
                        user_id=self.user_id,
                        app_id=self.app_id
                    ),
                    workflow_id=self.workflow_id,
                    inputs=[
                        resources_pb2.Input(
                            data=resources_pb2.Data(
                                text=resources_pb2.Text(raw=question_en)
                            )
                        )
                    ]
                ),
                metadata=self.metadata
            )

            if workflow_response.status.code != status_code_pb2.SUCCESS:
                return {"status": "error", "response": f"Workflow failed: {workflow_response.status.description}"}

            response_text = workflow_response.results[0].outputs[-1].data.text.raw
            
            if target_lang != 'en':
                translated = self.translator.translate(response_text, dest=target_lang)
                response_text = translated.text

            return {"status": "success", "response": response_text}
        except Exception as e:
            return {"status": "error", "response": f"Error: {str(e)}"}

    def analyze_symptoms(self, symptoms, source_lang, target_lang):
        try:
            if source_lang != 'en':
                symptoms_en = self.translator.translate(symptoms, src=source_lang, dest='en').text
            else:
                symptoms_en = symptoms

            # Check if the input is medical-related
            if not self.is_medical_related(symptoms_en):
                return {
                    "status": "error",
                    "response": "Please describe only medical symptoms or health-related concerns. For other topics, please use a different service."
                }

            # Construct a medical prompt
            medical_prompt = f"""You are a medical assistant. Please analyze these symptoms carefully and provide:
1. Potential causes (from most likely to least likely)
2. Recommended next steps
3. Important information to tell the doctor
4. Urgency level (Emergency/Urgent/Non-urgent)
5. Warning signs to watch for

Please note: This is not a diagnosis, just an initial analysis to help prepare for a medical consultation.

Patient's symptoms: {symptoms_en}"""

            workflow_response = self.stub.PostWorkflowResults(
                service_pb2.PostWorkflowResultsRequest(
                    user_app_id=resources_pb2.UserAppIDSet(
                        user_id=self.user_id,
                        app_id=self.app_id
                    ),
                    workflow_id=self.workflow_id,
                    inputs=[
                        resources_pb2.Input(
                            data=resources_pb2.Data(
                                text=resources_pb2.Text(raw=medical_prompt)
                            )
                        )
                    ]
                ),
                metadata=self.metadata
            )

            if workflow_response.status.code != status_code_pb2.SUCCESS:
                return {"status": "error", "response": f"Analysis failed: {workflow_response.status.description}"}

            response_text = workflow_response.results[0].outputs[-1].data.text.raw
            
            if target_lang != 'en':
                translated = self.translator.translate(response_text, dest=target_lang)
                response_text = translated.text

            return {"status": "success", "response": response_text}
        except Exception as e:
            return {"status": "error", "response": f"Error: {str(e)}"}
    
    def get_diet_recommendations(self, health_conditions, source_lang, target_lang):
        try:
            if source_lang != 'en':
                conditions_en = self.translator.translate(health_conditions, src=source_lang, dest='en').text
            else:
                conditions_en = health_conditions

            diet_prompt = f"""As a medical nutrition expert, please provide specific dietary recommendations for a patient with the following health conditions:

Health Conditions: {conditions_en}

Please provide only:
1. List of foods that are RECOMMENDED for these conditions
2. List of foods that should be AVOIDED for these conditions
3. Brief explanation of why these recommendations are important

Note: This is general dietary guidance that should be reviewed with a healthcare provider."""

            workflow_response = self.stub.PostWorkflowResults(
                service_pb2.PostWorkflowResultsRequest(
                    user_app_id=resources_pb2.UserAppIDSet(
                        user_id=self.user_id,
                        app_id=self.app_id
                    ),
                    workflow_id=self.workflow_id,
                    inputs=[
                        resources_pb2.Input(
                            data=resources_pb2.Data(
                                text=resources_pb2.Text(raw=diet_prompt)
                            )
                        )
                    ]
                ),
                metadata=self.metadata
            )

            if workflow_response.status.code != status_code_pb2.SUCCESS:
                return {"status": "error", "response": f"Diet recommendations failed: {workflow_response.status.description}"}

            response_text = workflow_response.results[0].outputs[-1].data.text.raw
            
            if target_lang != 'en':
                translated = self.translator.translate(response_text, dest=target_lang)
                response_text = translated.text

            return {"status": "success", "response": response_text}
        except Exception as e:
            return {"status": "error", "response": f"Error: {str(e)}"}


    def generate_voice(self, text, lang):
        try:
            tts = gTTS(text=text, lang=lang)
            audio_fp = BytesIO()
            tts.write_to_fp(audio_fp)
            return {"status": "success", "audio": base64.b64encode(audio_fp.getvalue()).decode()}
        except Exception as e:
            return {"status": "error", "response": f"Error generating voice: {str(e)}"}

def initialize_session_state():
    if 'system' not in st.session_state:
        st.session_state.system = ClarifaiSystem(
            api_key="da6c272af9f345cb8945fcc48d3a9da5",
            user_id="jvqrpit5yo8j",
            app_id="my-first-application-vr48qs",
            workflow_id="workflow-d9626d"
        )
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def main():
    st.title("Your Medical Assistant")
    
    st.markdown("""
    > **Disclaimer**: This tool provides general information only and is not a substitute for professional medical advice. 
    > Always consult a qualified healthcare provider for medical concerns.
    """)
    
    st.markdown("""
    > **Note**: This assistant is designed to handle only medical and health-related questions. 
    > Please keep your questions focused on health, medical conditions, symptoms, and wellness topics.
    """)
    
    initialize_session_state()
    
    indian_languages = {
        'English': 'en',
        'Hindi': 'hi',
        'Bengali': 'bn',
        'Tamil': 'ta',
        'Telugu': 'te',
        'Marathi': 'mr',
        'Gujarati': 'gu',
        'Kannada': 'kn',
        'Malayalam': 'ml',
        'Punjabi': 'pa',
        'Urdu': 'ur'
    }
    
    with st.sidebar:
        selected_language = st.selectbox("Select Language", list(indian_languages.keys()))
        mode = st.radio("Select Mode", ["General Q&A", "Symptom Analysis"])
        generate_voice = st.checkbox("Enable Voice", value=True)
        if st.button("Clear History"): 
            st.session_state.chat_history = []
            st.rerun()

    selected_lang_code = indian_languages[selected_language]

    if mode == "General Q&A":
        st.subheader("Medical Q&A")
        question = st.text_input("Your medical question:", key="question_input",
                               help="Please ask only medical or health-related questions.")
        if question:
            process_qa(question, selected_language, selected_lang_code, generate_voice)
    else:
        st.subheader("Symptom Analyzer")
        st.markdown("""
        Please describe your symptoms in detail. Include:
        - What symptoms are you experiencing?
        - When did they start?
        - How severe are they?
        - Any relevant medical history?
        """)
        symptoms = st.text_area("Describe your symptoms:", key="symptoms_input", 
                              help="Be as specific as possible about your symptoms and their timeline.")
        if symptoms:
            process_symptoms(symptoms, selected_language, selected_lang_code, generate_voice)

    display_chat_history()
def main():
    st.title("Your Medical Assistant")
    
    st.markdown("""
    > **Disclaimer**: This tool provides general information only and is not a substitute for professional medical advice. 
    > Always consult a qualified healthcare provider for medical concerns.
    """)
    
    initialize_session_state()
    
    indian_languages = {
        'English': 'en',
        'Hindi': 'hi',
        'Bengali': 'bn',
        'Tamil': 'ta',
        'Telugu': 'te',
        'Marathi': 'mr',
        'Gujarati': 'gu',
        'Kannada': 'kn',
        'Malayalam': 'ml',
        'Punjabi': 'pa',
        'Urdu': 'ur'
    }
    
    with st.sidebar:
        selected_language = st.selectbox("Select Language", list(indian_languages.keys()))
        mode = st.radio("Select Mode", ["Health Guidelines chatbot", "Symptom Analysis", "Dietary Planning"])
        generate_voice = st.checkbox("Enable Voice", value=True)
        if st.button("Clear History"): 
            st.session_state.chat_history = []
            st.rerun()

    selected_lang_code = indian_languages[selected_language]

    if mode == "General Q&A":
        st.subheader("Medical Q&A")
        question = st.text_input("Your medical question:", key="question_input",
                               help="Please ask only medical or health-related questions.")
        if question:
            process_qa(question, selected_language, selected_lang_code, generate_voice)
    
    elif mode == "Symptom Analysis":
        st.subheader("Symptom Analyzer")
        st.markdown("""
        Please describe your symptoms in detail. Include:
        - What symptoms are you experiencing?
        - When did they start?
        - How severe are they?
        - Any relevant medical history?
        """)
        symptoms = st.text_area("Describe your symptoms:", key="symptoms_input", 
                              help="Be as specific as possible about your symptoms and their timeline.")
        if symptoms:
            process_symptoms(symptoms, selected_language, selected_lang_code, generate_voice)
    
    else:  # Dietary Planning
        st.subheader("Dietary Planning")
        st.markdown("""
        Please provide your health conditions to receive dietary recommendations. 
        Examples: diabetes, hypertension, high cholesterol, etc.
        """)
        health_conditions = st.text_area("Health Conditions:", key="diet_input",
                                       help="List your health conditions for dietary recommendations")
        if st.button("Get Dietary Recommendations") and health_conditions:
            process_diet(health_conditions, selected_language, selected_lang_code, generate_voice)

    display_chat_history()

def process_diet(health_conditions, selected_language, selected_lang_code, generate_voice):
    with st.spinner("Generating dietary recommendations..."):
        result = st.session_state.system.get_diet_recommendations(
            health_conditions,
            source_lang=selected_lang_code,
            target_lang=selected_lang_code
        )
        handle_response(result, health_conditions, selected_language, selected_lang_code, generate_voice, "Diet")

def display_chat_history():
    if st.session_state.chat_history:
        for chat in reversed(st.session_state.chat_history):
            with st.container():
                st.markdown("---")
                if chat["type"] == "Q&A":
                    st.markdown(f"**Question:** {chat['input']}")
                    st.markdown(f"**Answer:** {chat['response']}")
                elif chat["type"] == "Symptoms":
                    st.markdown("### Symptom Analysis")
                    st.markdown(f"**Reported Symptoms:** {chat['input']}")
                    st.markdown(f"**Analysis:** {chat['response']}")
                else:  # Diet recommendations
                    st.markdown("### Dietary Recommendations")
                    st.markdown(f"**Health Conditions:** {chat['input']}")
                    st.markdown(f"**Recommendations:** {chat['response']}")
                st.caption(f"Language: {chat['language']}")
                if chat.get('audio'):
                    st.audio(base64.b64decode(chat['audio']), format='audio/mp3')
                st.caption(f"Timestamp: {chat['timestamp']}")
    else:
        st.info("Ask a medical question, describe your symptoms, or get dietary recommendations to start!")

def process_qa(question, selected_language, selected_lang_code, generate_voice):
    with st.spinner("Processing..."):
        result = st.session_state.system.get_qa_response(
            question,
            source_lang=selected_lang_code,
            target_lang=selected_lang_code
        )
        handle_response(result, question, selected_language, selected_lang_code, generate_voice, "Q&A")

def process_symptoms(symptoms, selected_language, selected_lang_code, generate_voice):
    with st.spinner("Analyzing symptoms..."):
        result = st.session_state.system.analyze_symptoms(
            symptoms,
            source_lang=selected_lang_code,
            target_lang=selected_lang_code
        )
        handle_response(result, symptoms, selected_language, selected_lang_code, generate_voice, "Symptoms")

def handle_response(result, input_text, selected_language, selected_lang_code, generate_voice, entry_type):
    if result["status"] == "success":
        chat_entry = {
            "type": entry_type,
            "input": input_text,
            "response": result["response"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "language": selected_language
        }
        
        if generate_voice:
            voice_result = st.session_state.system.generate_voice(
                result["response"],
                lang=selected_lang_code
            )
            if voice_result["status"] == "success":
                chat_entry["audio"] = voice_result["audio"]
        
        st.session_state.chat_history.append(chat_entry)
    else:
        st.error(result["response"])

def display_chat_history():
    if st.session_state.chat_history:
        for chat in reversed(st.session_state.chat_history):
            with st.container():
                st.markdown("---")
                if chat["type"] == "Q&A":
                    st.markdown(f"**Question:** {chat['input']}")
                    st.markdown(f"**Answer:** {chat['response']}")
                else:
                    st.markdown("### Symptom Analysis")
                    st.markdown(f"**Reported Symptoms:** {chat['input']}")
                    st.markdown(f"**Analysis:** {chat['response']}")
                st.caption(f"Language: {chat['language']}")
                if chat.get('audio'):
                    st.audio(base64.b64decode(chat['audio']), format='audio/mp3')
                st.caption(f"Timestamp: {chat['timestamp']}")
    else:
        st.info("Ask a medical question or describe your symptoms to start!")

if __name__ == "__main__":
    main()