import streamlit as st
import pandas as pd
from google import genai

st.set_page_config(page_title="Asystent Sprzedaży Zielony Ogród", page_icon="🌱")

# 1. Twój Klucz API Gemini
API_KEY = st.secrets.get("GEMINI_API_KEY", "AQ.Ab8RN6J32eFXDD_vnTphZT07RUsT0g2x19z7mtsmAaaPmMINow")
client = genai.Client(api_key=API_KEY)

# 2. Bezpośrednie połączenie z Twoim plikiem na Dysku Google
FILE_ID = "1ZVBmkFK98bBZcGHxC20j10zCGMQXcSjPhVEEBkWvML0"
URL = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx"

@st.cache_data(ttl=3600)  # Odświeża dane z Dysku Google co 1 godzinę
def load_data():
    try:
        df = pd.read_excel(URL)
        cols = ['Symbol', 'Nazwa', 'Grupa', 'Netto', 'Marża (C)']
        available_cols = [c for c in cols if c in df.columns]
        df_clean = df[available_cols].dropna(subset=['Nazwa'])
        return df_clean
    except Exception as e:
        st.error(f"Nie udało się pobrać pliku z Dysku Google. Upewnij się, że plik ma włączone udostępnianie. Błąd: {e}")
        return pd.DataFrame()

df_products = load_data()

# 3. Ekran logowania dla pracowników
HASLO = "magnus2026"  # Hasło dla pracowników

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

# 4. Główny interfejs aplikacji
st.title("🌱 Asystent Sprzedaży Centrum Ogrodniczego")
st.caption("Aplikacja połączona na żywo z bazą asortymentową Subiekt nexo")

user_query = st.text_area("Wpisz potrzebę / problem klienta (np. zestaw do sadzenia hortensji w cieniu, budżet 200 zł):", height=100)

if st.button(" Wygeneruj rekomendację dla klienta", type="primary"):
    if not user_query.strip():
        st.warning("Wpisz najpierw zapytanie klienta.")
    else:
        with st.spinner("Analizuję ofertę i dobieram najefektywniejszy zestaw..."):
            prompt = f"""
            Jesteś doradcą handlowym w centrum ogrodniczym.
            Oto baza naszych dostępnych produktów z Subiekta wraz z marżami:
            {df_products.head(400).to_string(index=False)}

            Potrzeba/problem klienta: {user_query}

            Zadanie:
            1. Zaproponuj zestaw 3-5 konkretnych produktów z powyższej bazy.
            2. Uzasadnij wybór każdego z nich krótko i rzeczowo.
            3. Zadbaj o to, aby w zestawie znalazł się przynajmniej jeden produkt wysokomarżowy (cross-selling, np. ziemia premium, nawóz, biostymulator).
            4. Podaj szacunkowy koszt netto całego zestawu.
            """
            
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                st.markdown("### 📋 Sugerowany zestaw:")
                st.write(response.text)
            except Exception as e:
                st.error(f"Błąd komunikacji z Gemini API: {e}")
