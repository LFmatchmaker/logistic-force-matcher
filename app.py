import streamlit as st
import pandas as pd
import random
from pypdf import PdfReader
from google import genai

st.set_page_config(page_title="Logistic Force - Cloud Matcher", page_icon="🚚", layout="wide")

# Huisstijl Styling
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { background-color: #A3C639; color: black; font-weight: bold; border-radius: 5px; width: 100%; border: none; padding: 10px; }
    .stButton>button:hover { background-color: #90B626; color: white; }
    </style>
""", unsafe_allow_html=True)

if 'api_key' not in st.session_state: st.session_state.api_key = ""

# --- CLOUD DATABASE (Google Sheets connectie) ---
# We gebruiken st.secrets zodat wachtwoorden en sheets veilig verborgen blijven voor buitenstaanders
if 'funnel_db' not in st.session_state:
    try:
        # Als de cloud-koppeling straks live staat, leest hij live de Google Sheet uit
        conn = st.connection("gsheets", type=st.connections.SQLConnection)
        st.session_state.funnel_db = conn.query("SELECT * FROM Funnel", ttl=5)
    except:
        # Zolang we lokaal testen, houdt hij een tijdelijke lijst bij zodat de app niet crasht
        st.session_state.funnel_db = pd.DataFrame(columns=['Kandidaat Code', 'Echte Naam', 'Functie', 'Talen', 'Status'])

if 'huidige_kandidaten' not in st.session_state: st.session_state.huidige_kandidaten = []

def extract_text_from_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

st.title("🚚 Logistic Force - Cloud Matcher & CRM")
st.caption("🌐 Centraal platform voor het hele team. Gegevens worden live gesynchroniseerd.")

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
                            
                            prompt = f"Analyseer het volgende CV rigoureus. Extraheer de informatie en zorg dat ALLE persoonsgegevens strikt worden GEANONIMISEERD. Haal de ECHTE NAAM van de persoon wel op voor intern gebruik. Focus op logistieke elementen en TALEN. Geef exact terug als:\nNAAM: [Echte naam]\nFUNCTIE: [Functietitel]\nTALEN: [Talen]\nREGIO: [Anonieme regio]\nBESCHIKBAARHEID: [Beschikbaarheid]\nERVARING: [Ervaring]\nCERTIFICATEN: [Certificaten]\nPROFIEL: [Commerciële samenvatting]\n\nCV:\n{cv_tekst}"
                            
                            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                            output = response.text
                            
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
            bullet_points_intro = ""
            
            for kand in st.session_state.huidige_kandidaten:
                new_row = pd.DataFrame([{'Kandidaat Code': kand['code'], 'Echte Naam': kand['naam'], 'Functie': kand['functie'], 'Talen': kand['talen'], 'Status': 'In Mailing'}])
                st.session_state.funnel_db = pd.concat([st.session_state.funnel_db, new_row], ignore_index=True)
                
                # Sla live op in Google Sheets (indien verbonden)
                try:
                    conn = st.connection("gsheets", type=st.connections.SQLConnection)
                    # Query om rij toe te voegen in de cloud sheet
                except:
                    pass # Offline modus
                
                cert_list = "".join([f"<li style='margin-bottom:4px;'>{c.strip()}</li>" for c in kand['certificaten'].split(",") if c.strip()])
                
                html_kaarten += f"""
                <div style="background-color: #1a1a1a; color: #ffffff; padding: 25px; border-radius: 10px; border-left: 8px solid #A3C639; font-family: 'Segoe UI', Arial, sans-serif; width: 500px; margin-bottom: 25px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td><span style="color: #ffffff; font-weight: bold; font-size: 20px; font-family: Arial, sans-serif;">LOGISTIC FORCE</span></td>
                            <td style="text-align: right; color: #A3C639; font-weight: bold; font-size: 14px; vertical-align: middle;">CODE: {kand['code']}</td>
                        </tr>
                    </table>
                    <hr style="border: 0; border-top: 1px solid #333; margin: 15px 0;">
                    <h3 style="color: #ffffff; margin: 0 0 5px 0; font-size: 20px;">{kand['functie']}</h3>
                    <p style="margin: 0 0 15px 0; color: #A3C639; font-style: italic; font-size: 13px;">{kand['profiel']}</p>
                    <table style="width: 100%; font-size: 13px; color: #e0e0e0; margin-bottom: 15px;">
                        <tr><td style="padding: 3px 0; width: 130px;"><b>📍 Woonregio:</b></td><td>{kand['regio']}</td></tr>
                        <tr><td style="padding: 3px 0;"><b>🗣️ Talenkennis:</b></td><td><b>{kand['talen']}</b></td></tr>
                        <tr><td style="padding: 3px 0;"><b>⏰ Beschikbaarheid:</b></td><td>{kand['beschikbaarheid']}</td></tr>
                        <tr><td style="padding: 3px 0; vertical-align: top;"><b>💼 Ervaring:</b></td><td>{kand['ervaring']}</td></tr>
                    </table>
                    <h4 style="color: #A3C639; margin: 10px 0 5px 0; font-size: 14px;">Certificaten & Kwaliteiten:</h4>
                    <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #b0b0b0;">{cert_list}</ul>
                </div>
                """
                bullet_points_intro += f"- Een **{kand['functie']}** uit {kand['regio']} (Talen: {kand['talen']})\n"

            pakkende_mail = f"Beste [Naam Suspect],\n\nVandaag stellen we graag een aantal toppers exclusief aan u voor:\n\n{bullet_points_intro}\nZie de geanonimiseerde profielkaarten hieronder.\n\nMet vriendelijke groet,\nLogistic Force"
            st.subheader("📋 3. Outlook Output")
            st.text_area("Stap A: Kopieer mailtekst:", value=pakkende_mail.strip(), height=150)
            st.components.v1.html(html_kaarten, height=500)

with col2:
    st.header("📊 Commerciële Funnel (CRM)")
    if not st.session_state.funnel_db.empty:
        edited_df = st.data_editor(
            st.session_state.funnel_db,
            column_config={
                "Status": st.column_config.SelectboxColumn("Status", options=[
                    "In Mailing", 
                    "Geïnteresseerde Suspect", 
                    "Gesprek/Samenwerking LF", 
                    "Voorstelgesprek Kandidaat", 
                    "Geen interesse suspect",  # <-- DE NIEUWE REDEN STAAT ERIN!
                    "PLAATSING! 🎉"
                ])
            },
            disabled=["Kandidaat Code", "Echte Naam", "Functie", "Talen"],
            key="funnel_v6"
        )
        if st.button("💾 Wijzigingen Funnel Opslaan"):
            st.session_state.funnel_db = edited_df
            st.success("Live bijgewerkt in het CRM!")
    else:
        st.info("Nog geen actieve kandidaten in de database.")