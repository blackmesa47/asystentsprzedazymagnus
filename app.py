import streamlit as st
import pandas as pd
from google import genai
from PIL import Image

st.set_page_config(page_title="Asystent Sprzedaży Zielony Ogród", page_icon="🌱")

# 1. Połączenie z Gemini API
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# 2. Twój opublikowany link CSV z Dysku Google
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7zfxIqdbLY810lWlY9BHyYfjd6QPnarB4Cb3igboxyCgPSk6U_qMdVO1bUt3EYJnou9MIqjO2kq7D/pub?gid=1401580556&single=true&output=csv"

@st.cache_data(ttl=3600)
def load_data():
    try:
        df = pd.read_csv(URL)
        cols = ['Symbol', 'Nazwa', 'Grupa', 'Netto', 'Marża (C)']
        available_cols = [c for c in cols if c in df.columns]
        df_clean = df[available_cols].dropna(subset=['Nazwa'])
        return df_clean
    except Exception as e:
        st.error(f"Błąd pobierania danych z Dysku Google: {e}")
        return pd.DataFrame()

df_products = load_data()

# 3. Ekran logowania
HASLO = "magnus2026"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Logowanie – Asystent Sprzedaży")
    pwd = st.text_input("Wpisz hasło dostępu:", type="password")
    if st.button("Zaloguj się"):
        if pwd == HASLO:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Nieprawidłowe hasło!")
    st.stop()

# 4. Interfejs główny z obsługą zdjęć i aparatu
st.title("🌱 Asystent Sprzedaży Zielony Ogród")
st.caption("Rozpoznawanie ze zdjęcia oraz doradztwo z bazy Subiekt nexo")

option = st.radio("Wybierz sposób zapytania:", ("Opis słowny", "📸 Zdjęcie / Aparat w telefonie"))

user_query = ""
uploaded_image = None

if option == "Opis słowny":
    user_query = st.text_area("Wpisz potrzebę lub problem klienta:", height=100)
else:
    cam_image = st.camera_input("Zrób zdjęcie rośliny, liścia, etykiety lub kodu:")
    file_image = st.file_uploader("Lub wybierz zdjęcie z galerii telefonu:", type=["jpg", "jpeg", "png"])
    
    uploaded_image = cam_image if cam_image is not None else file_image
    user_query = st.text_input("Dodatkowy komentarz do zdjęcia (opcjonalnie):")

if st.button("Wygeneruj rekomendację", type="primary"):
    if option == "Opis słowny" and not user_query.strip():
        st.warning("Wpisz opis słowny.")
    elif option != "Opis słowny" and uploaded_image is None:
        st.warning("Zrób zdjęcie lub dodaj plik z galerii.")
    else:
        with st.spinner("Analizuję i szukam dopasowania w bazie nexo..."):
            prompt = f"""
            Jesteś wybitnym ekspertem ogrodnictwa i doradcą handlowym w centrum ogrodniczym.
            Oto baza naszych dostępnych produktów z Subiekta nexo z marżami:
            {df_products.head(500).to_string(index=False)}

            Zadanie:
            1. Jeśli dołączono zdjęcie, dokładnie przeanalizuj co na nim jest (gatunek rośliny, objaw choroby, szkodnik, kod/etykieta).
            2. Znajdź w naszej bazie Subiekt nexo najbardziej odpowiednie i popularne produkty.
            3. Zaproponuj pełny zestaw 3-5 produktów (np. roślina + właściwa ziemia premium + preparat/nawóz).
            4. Postaw na cross-selling produktów wysokomarżowych.
            5. Podaj orientacyjny koszt netto zestawu.
            Komentarz do zapytania: {user_query}
            """
            
            try:
                contents = [prompt]
                if uploaded_image is not None:
                    img = Image.open(uploaded_image)
                    contents.append(img)
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents
                )
                st.markdown("### 📋 Diagnoza i rekomendowany zestaw:")
                st.write(response.text)
            except Exception as err:
                st.error(f"Błąd podczas analizy: {err}")
