import streamlit as st
import pandas as pd
import random
import time
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

def generate_content_with_retry(client, model_name, contents, max_retries=3):
    """Functie die bij een 503 serverfout automatisch tot 3 keer opnieuw probeert met een korte pauze."""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model=model_name, contents=contents)
            return response.text
        except Exception as e:
            if "503" in str(e) and attempt < max_retries - 1:
                time.sleep(2)  # Wacht 2 seconden voor de volgende poging
                continue
            raise e

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
                            Analyseer het volgende CV rigoureus voor logistieke werving. 
                            
                            STRIKTE PRIVACY REGELS (AVG):
                            - Je mag de ECHTE NAAM van de persoon ENKEL EN ALLEEN invullen op de regel 'NAAM:'.
                            - In de velden 'FUNCTIE', 'TALEN', 'REGIO', 'BESCHIKBAARHEID', 'ERVARING', 'CERTIFICATEN' en vooral in het 'PROFIEL' mag de echte naam van de persoon of diens huidige werkgever(s) NOOIT, MAAR DAN OOK NOOIT voorkomen. 
                            - Vervang de naam in de lopende tekst van het PROFIEL altijd door termen zoals 'deze kandidaat', 'deze logistieke professional' of 'hij/zij'.
                            
                            Geef exact terug in dit formaat:
                            NAAM: [Echte voor- en achternaam]
                            FUNCTIE: [Functietitel]
                            TALEN: [Talen]
                            REGIO: [Anonieme regio/woonplaats]
                            BESCHIKBAARHEID: [Beschikbaarheid]
                            ERVARING: [Ervaring]
                            CERTIFICATEN: [Certificaten/Rijbewijzen, volledig geanonimiseerd]
                            PROFIEL: [Commerciële, wervende samenvatting - STRIKT GEANONIMISEERD EN ZONDER NAAM]
                            
                            CV TEXT:
                            {cv_tekst}
                            """
                            
                            # Gecorrigeerde modelnaam voor de nieuwe SDK
                            output = generate_content_with_retry(client, 'gemini-1.5-flash-002', prompt)
                            
                            kandidaat_data = {"code": f"LF-{random.randint(100, 999)}", "naam": "", "functie": "", "talen": "", "regio": "", "beschikbaarheid": "", "ervaring": "", "certificaten": "", "profiel": ""}
                            for line in output.split('\n'):
                                if line.startswith("NAAM:"): kandidaat_data["naam"] = line.replace("NAAM:", "").strip()
                                if line.startswith("FUNCTIE:"): kandidaat_data["functie"] = line.replace("FUNCTIE:", "").strip()
                                if line.startswith("TALEN:"): kandidaat_data["talen"] = line.replace("TALEN:", "").strip()
                                if line.startswith("REGIO:"): kandidaat_data["regio"] = line.replace("REGIO:", "").strip()
                                if line.startswith("BESCHIKBAARHEID:"): kandidaat_data["beschikbaarheid"] = line.replace("BESCHIKBAARHEID:", "").strip()
                                if line.startswith("ERVARING:"): kandidaat_data["ervaring"] = line.replace("ERVARING:", "").strip()
                                if line.startswith("CERTIFICATEN:"): kandidaat_data["certificaten"] = line.replace("CERTIFICATEN:", "").strip()
                                if line.startswith("PROFIEL:"): kandidaat_data["profiel"] = line.replace("PROFIEL:", "").strip()
                            
                            st.session_state.huidige_kandidaten.append(kandidaat_data)
                            time.sleep(1.0)
                            
                        except Exception as e:
                            st.error(f"Fout bij {file.name}: {e}")
                st.success("Analyse voltooid!")

    if st.session_state.huidige_kandidaten:
        st.header("📝 2. Controleren & Aanpassen")
        for idx, kand in enumerate(st.session_state.huidige_kandidaten):
            with st.expander(f"Kandidaat {kand['code']} - {kand['functie']}", expanded=True):
                st.session_state.huidige_kandidaten[idx]['naam'] = st.text_input(f"Echte Naam #{idx+1}", value=kand['naam'], key=f"n_{idx}")
                st.session_state.huidige_kandidaten[idx]['functie'] = st.text_input(f"Functie #{idx+1}", value=kand['functie'], key=f"f_{idx}")
                st.session_state.huidige_kandidaten[idx]['talen'] = st.text_input(f"Gesproken Talen #{idx+1}", value=kand['talen'], key=f"t_{idx}")
                st.session_state.huidige_kandidaten[idx]['regio'] = st.text_input(f"Regio #{idx+1}", value=kand['regio'], key=f"r_{idx}")
                st.session_state.huidige_kandidaten[idx]['beschikbaarheid'] = st.text_input(f"Beschikbaarheid #{idx+1}", value=kand['beschikbaarheid'], key=f"b_{idx}")
                st.session_state.huidige_kandidaten[idx]['ervaring'] = st.text_input(f"Relevante Ervaring #{idx+1}", value=kand['ervaring'], key=f"e_{idx}")
                st.session_state.huidige_kandidaten[idx]['certificaten'] = st.text_area(f"Certificaten #{idx+1}", value=kand['certificaten'], key=f"c_{idx}")
                st.session_state.huidige_kandidaten[idx]['profiel'] = st.text_area(f"Pakkend Profiel #{idx+1}", value=kand['profiel'], key=f"p_{idx}")

        if st.button("📊 Genereer Gecombineerde Outlook Mailing"):
            html_kaarten = ""
            kandidaten_samenvatting_voor_prompt = ""
            
            for kand in st.session_state.huidige_kandidaten:
                cert_list = "".join([f"<li style='margin-bottom:4px;'>{c.strip()}</li>" for c in kand['certificaten'].split(",") if c.strip()])
                kaart_html = f"""<div style="background-color: #1a1a1a; color: #ffffff; padding: 25px; border-radius: 10px; border-left: 8px solid #A3C639; font-family: 'Segoe UI', Arial, sans-serif; width: 500px; margin-bottom: 25px;"><table style="width: 100%; border-collapse: collapse;"><tr><td><span style="color: #ffffff; font-weight: bold; font-size: 20px; font-family: Arial, sans-serif;">LOGISTIC FORCE</span></td><td style="text-align: right; color: #A3C639; font-weight: bold; font-size: 14px; vertical-align: middle;">CODE: {kand['code']}</td></tr></table><hr style="border: 0; border-top: 1px solid #333; margin: 15px 0;"><h3 style="color: #ffffff; margin: 0 0 5px 0; font-size: 20px;">{kand['functie']}</h3><p style="margin: 0 0 15px 0; color: #A3C639; font-style: italic; font-size: 13px;">{kand['profiel']}</p><table style="width: 100%; font-size: 13px; color: #e0e0e0; margin-bottom: 15px;"><tr><td style="padding: 3px 0; width: 130px;"><b>📍 Woonregio:</b></td><td>{kand['regio']}</td></tr><tr><td style="padding: 3px 0;"><b>🗣️ Talenkennis:</b></td><td><b>{kand['talen']}</b></td></tr><tr><td style="padding: 3px 0;"><b>⏰ Beschikbaarheid:</b></td><td>{kand['beschikbaarheid']}</td></tr><tr><td style="padding: 3px 0; vertical-align: top;"><b>💼 Ervaring:</b></td><td>{kand['ervaring']}</td></tr></table><h4 style="color: #A3C639; margin: 10px 0 5px 0; font-size: 14px;">Certificaten & Kwaliteiten:</h4><ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #b0b0b0;">{cert_list}</ul></div>"""
                html_kaarten += kaart_html
                kandidaten_samenvatting_voor_prompt += f"- Code: {kand['code']}, Functie: {kand['functie']}, Regio: {kand['regio']}, Talen: {kand['talen']}, Profiel: {kand['profiel']}\n"

            with st.spinner("AI genereert een krachtige, commerciële begeleidende mail..."):
                try:
                    client = genai.Client(api_key=st.session_state.api_key)
                    mail_prompt = f"""
                    Schrijf een krachtige, enthousiaste en commerciële B2B-begeleidende e-mail namens Logistic Force, gericht aan een potentieel bedrijf (suspect). 
                    Het doel is om hen te overtuigen om met Logistic Force in zee te gaan aan de hand van deze specifieke toptalenten die we vandaag beschikbaar hebben.
                    
                    De e-mail moet professioneel, overtuigend ogend van toon en vlot geschreven zijn. Geen standaard saai mailtje, maar een tekst die de suspect activeert om te reageren.
                    Begin met een sterke opening over de uitdagingen op de logistieke arbeidsmarkt en hoe Logistic Force dé oplossing biedt met direct inzetbaar personeel.
                    
                    Lijst de volgende kandidaten kort en krachtig op met bullet points (gebruik hun codes, GEEN echte namen):
                    {kandidaten_samenvatting_voor_prompt}
                    
                    Sluit af met een sterke call-to-action (bijvoorbeeld: 'Wilt u morgen al kennismaken met een van deze toppers? Laat het me direct weten, dan plan ik het in.').
                    Gebruik '[Naam Suspect]' als aanhef en sluit af met 'Met vriendelijke groet, Logistic Force'.
                    """
                    # Gecorrigeerde modelnaam ook voor de e-mailtekst
                    commerciele_mail = generate_content_with_retry(client, 'gemini-1.5-flash-002', mail_prompt)
                except Exception as e:
                    commerciele_mail = f"Beste [Naam Suspect],\n\n(Fout bij genereren verkooptekst: {e})\n\nMet vriendelijke groet,\nLogistic Force"

            st.subheader("📋 3. Outlook Output")
            st.text_area("Stap A: Kopieer commerciële mailtekst:", value=commerciele_mail.strip(), height=300)
            st.components.v1.html(html_kaarten, height=500)

with col2:
    st.header("📊 CRM Handmatige Input")
    if st.session_state.huidige_kandidaten:
        st.write("📋 Kopieer deze regels hematig en plak ze onderaan je Google Sheet:")
        export_data = []
        for kand in st.session_state.huidige_kandidaten:
            export_data.append({
                'Kandidaat Code': kand['code'],
                'Echte Naam': kand['naam'],
                'Functie': kand['functie'],
                'Talen': kand['talen'],
                'Status': 'In Mailing'
            })
        df_export = pd.DataFrame(export_data)
        st.dataframe(df_export, hide_index=True)
        st.caption("💡 Selecteer de cellen in de tabel hierboven, druk op Cmd+C (of Ctrl+C) en plak ze direct in je Google Sheet.")
    else:
        st.info("Zodra je CV's uploadt en op analyseren klikt, verschijnen hier de kant-en-klare Excel-rijen voor je Google Sheet.")
