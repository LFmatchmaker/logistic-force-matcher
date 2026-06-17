import streamlit as st
import pandas as pd
import random
from pypdf import PdfReader
from google import genai

st.set_page_config(page_title="Logistic Force - Cloud Matcher", page_icon="🚚", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { background-color: #A3C639; color: black; font-weight: bold; border-radius: 5px; width: 100%; border: none; padding: 10px; }
    .stButton>button:hover { background-color: #90B626; color: white; }
    </style>
""", unsafe_allow_html=True)

if 'api_key' not in st.session_state: st.session_state.api_key = ""
if 'huidige_kandidaten' not in st.session_state: st.session_state.huidige_kandidaten = []

def extract_text_from_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

st.title("🚚 Logistic Force - Cloud Matcher & CRM")
st.caption("🌐 Centraal platform voor het hele team.")

with st.sidebar:
    st.header("⚙️ Instellingen")
    st.session_state.api_key = st.text_input("Gemini API Key", value=st.session_state.api_key, type="password")

col1, col2 = st.columns([1.3, 1])

with col1:
    st.header("1. Upload & Bulk Analyse")
    uploaded_files = st.file_uploader("Sleep hier max 5 originele CV's (PDF)", type=["pdf"], accept_multiple_files=True)
    
    if uploaded_files:
        if len(uploaded_files) > 5:
            st.error("Je kunt maximaal 5 CV's tegelijkertijd selecteren.")
        elif st.button("⚡ Start Automatische Analyse"):
            if not st.session_state.api_key:
                st.error("Vul eerst je Gemini API Key in de linker zijbalk in!")
            else:
                st.session_state.huidige_kandidaten = []
                for index, file in enumerate(uploaded_files):
                    with st.spinner(f"Analyseren van CV {index+1}: {file.name}..."):
                        try:
                            cv_tekst = extract_text_from_pdf(file)
                            client = genai.Client(api_key=st.session_state.api_key)
                            
                            prompt = f"""
                            Analyseer het volgende CV rigoureus. Extraheer de informatie en zorg dat ALLE persoonsgegevens strikt worden GEANONIMISEERD. 
                            Haal de ECHTE NAAM van de persoon wel op voor intern gebruik. Focus sterk op logistieke elementen en TALEN.
                            
                            Geef het antwoord EXACT terug in dit formaat (gebruik GEEN markdown of sterretjes bij de labels):
                            NAAM: [Echte naam]
                            FUNCTIE: [Functietitel]
                            TALEN: [Welke talen spreekt de kandidaat?]
                            REGIO: [Anonieme regio]
                            BESCHIKBAARHEID: [Beschikbaarheid]
                            ERVARING: [Korte samenvatting van werkervaring]
                            CERTIFICATEN: [Relevante certificaten/rijbewijzen]
                            PROFIEL: [Korte, pakkende, commerciële samenvatting van 2 zinnen]
                            
                            Hier is de CV tekst:
                            {cv_tekst}
                            """
                            
                            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                            output = response.text
                            
                            kandidaat_data = {"code": f"LF-{random.randint(100, 999)}", "naam": "Onbekend", "functie": "Logistiek Medewerker", "talen": "Niet gespecificeerd", "regio": "Onbekend", "beschikbaarheid": "In overleg", "ervaring": "Niet gespecificeerd", "certificaten": "Geen", "profiel": ""}
                            
                            # Slimme regelfilter die bestand is tegen extra sterretjes of spaties van de AI
                            for line in output.split('\n'):
                                clean_line = line.replace('*', '').strip()
                                
                                if clean_line.upper().startswith("NAAM:"): kandidaat_data["naam"] = clean_line[5:].strip()
                                elif clean_line.upper().startswith("FUNCTIE:"): kandidaat_data["functie"] = clean_line[8:].strip()
                                elif clean_line.upper().startswith("TALEN:"): kandidaat_data["talen"] = clean_line[6:].strip()
                                elif clean_line.upper().startswith("REGIO:"): kandidaat_data["regio"] = clean_line[6:].strip()
                                elif clean_line.upper().startswith("BESCHIKBAARHEID:"): kandidaat_data["beschikbaarheid"] = clean_line[16:].strip()
                                elif clean_line.upper().startswith("ERVARING:"): kandidaat_data["ervaring"] = clean_line[9:].strip()
                                elif clean_line.upper().startswith("CERTIFICATEN:"): kandidaat_data["certificaten"] = clean_line[13:].strip()
                                elif clean_line.upper().startswith("PROFIEL:"): kandidaat_data["profiel"] = clean_line[8:].strip()
                            
                            st.session_state.huidige_kandidaten.append(kandidaat_data)
                        except Exception as e:
                            st.error(f"Fout bij {file.name}: {e}")
                st.success("Analyse voltooid!")

    if st.session_state.huidige_kandidaten
