import streamlit as st
import pandas as pd
from google import genai
from PIL import Image

st.set_page_config(page_title="Asystent Sprzedaży Zielony Ogród", page_icon="🌱")

# 1. Połączenie z Gemini API
if "GEMINI_API_KEY" not in st.secrets:
    st.error("🔑 Brak klucza GEMINI_API_KEY w ustawieniach Streamlit Cloud!")
    st.stop()

API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# 2. Baza produktów (szybkie wczytywanie CSV z Dysku Google)
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7zfxIqdbLY810lWlY9BHyYfjd6QPnarB4Cb3igboxyCgPSk6U_qMdVO1bUt3EYJnou9MIqjO2kq7D/pub?gid=1401580556&single=true&output=csv"

@st.cache_data(ttl=3600)
def load_data():
    try:
        df = pd.read_csv(URL)
        cols = ['Symbol', 'Nazwa', 'Grupa', 'Netto', 'Brutto', 'Marża (C)']
        available_cols = [c for c in cols if c in df.columns]
        df_clean = df[available_cols].dropna(subset=['Nazwa'])
        return df_clean
    except Exception as e:
        st.error(f"Błąd pobierania danych z Dysku: {e}")
        return pd.DataFrame()

df_products = load_data()

# 3. Logowanie
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

# 4. Interfejs główny
st.title("🌱 Asystent Sprzedaży Zielony Ogród")

option = st.radio("Wybierz sposób zapytania:", ("Opis słowny / Szukaj ceny", "📸 Zdjęcie / Aparat w telefonie"))

user_query = ""
uploaded_image = None

if option == "Opis słowny / Szukaj ceny":
    user_query = st.text_area("Wpisz zapytanie (np. 'ile kosztuje bratek', 'cena ziemi wokas', 'co do cienia'):", height=80)
else:
    cam_image = st.camera_input("Zrób zdjęcie rośliny / etykiety / towaru:")
    file_image = st.file_uploader("Lub wybierz z galerii:", type=["jpg", "jpeg", "png"])
    uploaded_image = cam_image if cam_image is not None else file_image
    user_query = st.text_input("Komentarz do zdjęcia (opcjonalnie, np. 'ile to kosztuje?'):")

if st.button("Wyślij zapytanie", type="primary"):
    if option == "Opis słowny / Szukaj ceny" and not user_query.strip():
        st.warning("Wpisz treść zapytania.")
    elif option != "Opis słowny / Szukaj ceny" and uploaded_image is None:
        st.warning("Zrób zdjęcie lub dodaj plik z galerii.")
    else:
        with st.spinner("⚡ Przeszukuję bazę Subiekt nexo..."):
            # Inteligentne przeszukiwanie całej bazy nexo (4800+ pozycji) po słowach kluczowych
            words = [w.strip() for w in user_query.split() if len(w.strip()) > 2]
            if words:
                pattern = '|'.join(words)
                matched_df = df_products[df_products['Nazwa'].str.contains(pattern, case=False, na=False)]
                if not matched_df.empty:
                    context_df = matched_df.head(40)
                else:
                    context_df = df_products.head(80)
            else:
                context_df = df_products.head(80)
            
            prompt = f"""
            Jesteś elastycznym i pomocnym asystentem sprzedawcy w centrum ogrodniczym.
            Masz dostęp do następujących pozycji z bazy Subiekt nexo:
            {context_df.to_string(index=False)}

            Zapytanie użytkownika: {user_query}

            ZASADY ODPOWIEDZI:
            1. DOKŁADNIE SŁUCHAJ INTENCJI UŻYTKOWNIKA:
               - Jeśli użytkownik pyta o CENĘ, SZUKA TOWARU lub SYMBOLU: Podaj bezpośrednią odpowiedź (Nazwa, Symbol, Cena Netto, Cena Brutto, Marża%). Jeśli występuje kilka pasujących wariantów, wypisz je zwięźle w tabeli lub liście.
               - Jeśli użytkownik przesyła ZDJĘCIE: Zidentyfikuj obiekt/roślinę, odszukaj dopasowanie w podanych pozycjach nexo i podaj szczegóły cenowe.
               - Jeśli użytkownik prosi o PORADĘ / DOBÓR ZESTAWU: Dopiero wtedy podaj rekomendację i zestaw produktów.
            2. Odpowiadaj krótko, konkretnie i bez narzucania niepotrzebnych zestawów, chyba że użytkownik sam o nie poprosi.
            """
            
            try:
                contents = [prompt]
                if uploaded_image is not None:
                    img = Image.open(uploaded_image)
                    img.thumbnail((1024, 1024))
                    contents.append(img)
                
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=contents
                )
                st.markdown("### 📋 Odpowiedź Asystenta:")
                st.write(response.text)
            except Exception as err:
                st.error(f"Błąd: {err}")
