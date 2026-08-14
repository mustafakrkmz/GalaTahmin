import streamlit as st
import sqlite3
import requests
import re
import os
import json
from datetime import datetime, timezone, timedelta
import pandas as pd

# Try importing gspread for Google Sheets support
try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False

# ==========================================
# PAGE CONFIG & CUSTOM CSS (GS THEME)
# ==========================================
st.set_page_config(
    page_title="GS Skor Tahmin Portalı",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Montserrat', sans-serif !important;
        letter-spacing: -0.2px;
    }

    /* Main Theme Colors */
    :root {
        --gs-red: #A90429;
        --gs-dark-red: #6B0017;
        --gs-gold: #FDB913;
        --gs-bg: #0c0e12;
    }
    
    .stApp {
        background-color: #0c0e12;
        color: #f3f4f6;
    }
    
    /* Hide Streamlit Header, Footer, and MainMenu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Hide the entire sidebar component and control button */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    /* Premium Glassmorphic Card Box */
    .content-card {
        background: rgba(22, 25, 34, 0.55);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(253, 185, 19, 0.15);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .content-card:hover {
        border-color: rgba(253, 185, 19, 0.4);
        box-shadow: 0 10px 40px 0 rgba(253, 185, 19, 0.08);
        transform: translateY(-2px);
    }
    
    /* Fixture Cards */
    .fixture-card {
        background: rgba(22, 25, 34, 0.6);
        border-left: 5px solid #FDB913;
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 12px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
        transition: all 0.2s ease;
        border-top: 1px solid rgba(253, 185, 19, 0.05);
        border-right: 1px solid rgba(253, 185, 19, 0.05);
        border-bottom: 1px solid rgba(253, 185, 19, 0.05);
    }
    
    .fixture-card:hover {
        transform: translateX(4px);
        background: rgba(28, 32, 44, 0.85);
        border-color: rgba(253, 185, 19, 0.25);
    }

    .past-fixture-card {
        background: rgba(22, 25, 34, 0.6);
        border-left: 5px solid #A90429;
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 12px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
        transition: all 0.2s ease;
        border-top: 1px solid rgba(169, 4, 41, 0.05);
        border-right: 1px solid rgba(169, 4, 41, 0.05);
        border-bottom: 1px solid rgba(169, 4, 41, 0.05);
    }
    
    .past-fixture-card:hover {
        transform: translateX(4px);
        background: rgba(28, 32, 44, 0.85);
        border-color: rgba(169, 4, 41, 0.25);
    }
    
    /* Score Pill */
    .score-badge {
        background: #151822;
        border: 1px solid rgba(253, 185, 19, 0.3);
        color: #FDB913;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.92rem;
        display: inline-block;
        margin: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    
    /* Sleek top login bar styling */
    .login-bar {
        background: rgba(22, 25, 34, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(253, 185, 19, 0.2);
        border-radius: 16px;
        padding: 12px 24px;
        margin-bottom: 28px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
    }

    /* Style Streamlit Tabs for modern UI */
    button[data-baseweb="tab"] {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #9ca3af !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.3s ease !important;
        padding: 12px 20px !important;
        background-color: transparent !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #FDB913 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FDB913 !important;
        border-bottom: 2px solid #FDB913 !important;
        background: rgba(253, 185, 19, 0.04) !important;
        border-top-left-radius: 8px !important;
        border-top-right-radius: 8px !important;
    }
    
    /* Input field styling */
    .stTextInput input, .stNumberInput input {
        background-color: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
        padding: 8px 12px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #FDB913 !important;
        box-shadow: 0 0 10px rgba(253, 185, 19, 0.2) !important;
    }

    /* Button styling adjustments */
    button[kind="primary"] {
        background: linear-gradient(135deg, #A90429 0%, #7B0017 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(169, 4, 41, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(169, 4, 41, 0.5) !important;
    }
    
    button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #d1d5db !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }
    button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. KULLANICI BİLGİLERİ & OTURUM YÖNETİMİ
# ==========================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "custom_match_override" not in st.session_state:
    st.session_state.custom_match_override = None

# ==========================================
# 2. VERİTABANI YÖNETİMİ (100% GOOGLE SHEETS BULUT)
# ==========================================

@st.cache_resource
def get_gsheet_client():
    if not HAS_GSPREAD:
        return None, None
        
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 1. First check local credentials.json file
    if os.path.exists("credentials.json"):
        try:
            creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
            client = gspread.authorize(creds)
            sheet = client.open("GS_Skor_Tahmin_DB")
            return client, sheet
        except Exception:
            pass

    # 2. Then check Streamlit secrets
    try:
        if "gdrive" in st.secrets:
            creds_dict = dict(st.secrets["gdrive"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
            client = gspread.authorize(creds)
            sheet_name = st.secrets.get("GSHEET_NAME", "GS_Skor_Tahmin_DB")
            sheet = client.open(sheet_name)
            return client, sheet
    except Exception:
        pass
        
    return None, None

@st.cache_resource
def init_db():
    gs_client, gs_sheet = get_gsheet_client()
    if gs_sheet:
        try:
            existing_titles = [w.title for w in gs_sheet.worksheets()]
            
            if "predictions" not in existing_titles:
                ws_p = gs_sheet.add_worksheet(title="predictions", rows=1000, cols=5)
                ws_p.append_row(["username", "match_id", "gs_score", "away_score", "created_at"])
                
            if "match_results" not in existing_titles:
                ws_m = gs_sheet.add_worksheet(title="match_results", rows=500, cols=6)
                ws_m.append_row(["match_id", "match_title", "gs_score", "away_score", "is_finished", "is_manual"])
                
            if "users" not in existing_titles:
                ws_u = gs_sheet.add_worksheet(title="users", rows=100, cols=3)
                ws_u.append_row(["username", "password", "updated_at"])
                ws_u.append_row(["admin", "admin", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        except Exception:
            pass

init_db()

# --- DB & KULLANICI YÖNETİM FONKSİYONLARI ---

@st.cache_data(ttl=60)
def fetch_users():
    """Kullanıcı adı ve şifre haritasını Google Sheets bulut tablosundan canlı çeker."""
    gs_client, gs_sheet = get_gsheet_client()
    if gs_sheet:
        try:
            ws = gs_sheet.worksheet("users")
            data = ws.get_all_records()
            if data:
                return {str(row.get("username")).strip().lower(): str(row.get("password")).strip() for row in data if str(row.get("username")).strip()}
        except Exception:
            pass
    return {}

def update_user_password(username, new_password):
    """Kullanıcının şifresini Google Sheets bulut tablosunda günceller."""
    username = str(username).strip().lower()
    new_password = str(new_password).strip()
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    gs_client, gs_sheet = get_gsheet_client()
    if gs_sheet:
        try:
            ws = gs_sheet.worksheet("users")
            records = ws.get_all_records()
            for idx, row in enumerate(records, start=2):
                if str(row.get("username")).strip().lower() == username:
                    ws.update_cell(idx, 2, new_password)
                    ws.update_cell(idx, 3, updated_at)
                    break
        except Exception:
            pass
    st.cache_data.clear()

@st.cache_data(ttl=30)
def fetch_predictions(match_id=None):
    gs_client, gs_sheet = get_gsheet_client()
    if gs_sheet:
        try:
            ws = gs_sheet.worksheet("predictions")
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            if df.empty:
                return pd.DataFrame(columns=["username", "match_id", "gs_score", "away_score", "created_at"])
            if match_id:
                df = df[df["match_id"] == match_id]
            return df
        except Exception:
            return pd.DataFrame(columns=["username", "match_id", "gs_score", "away_score", "created_at"])
    return pd.DataFrame(columns=["username", "match_id", "gs_score", "away_score", "created_at"])

@st.cache_data(ttl=30)
def fetch_match_results():
    gs_client, gs_sheet = get_gsheet_client()
    if gs_sheet:
        try:
            ws = gs_sheet.worksheet("match_results")
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            if df.empty:
                return pd.DataFrame(columns=["match_id", "match_title", "gs_score", "away_score", "is_finished", "is_manual"])
            return df
        except Exception:
            return pd.DataFrame(columns=["match_id", "match_title", "gs_score", "away_score", "is_finished", "is_manual"])
    return pd.DataFrame(columns=["match_id", "match_title", "gs_score", "away_score", "is_finished", "is_manual"])

def insert_prediction(username, match_id, match_title, gs_score, away_score):
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    gs_client, gs_sheet = get_gsheet_client()
    
    if gs_sheet:
        ws_p = gs_sheet.worksheet("predictions")
        records = ws_p.get_all_records()
        for idx, row in enumerate(records, start=2):
            if str(row.get("username")).strip().lower() == str(username).strip().lower() and str(row.get("match_id")) == str(match_id):
                ws_p.update_cell(idx, 3, int(gs_score))
                ws_p.update_cell(idx, 4, int(away_score))
                return
        ws_p.append_row([username, match_id, int(gs_score), int(away_score), created_at])
        
        ws_m = gs_sheet.worksheet("match_results")
        existing_matches = ws_m.get_all_records()
        match_exists = any(str(m.get("match_id")) == str(match_id) for m in existing_matches)
        if not match_exists:
            ws_m.append_row([match_id, match_title, 0, 0, 0, 0])
    st.cache_data.clear()

def save_match_result(match_id, gs_score, away_score, is_manual=0):
    gs_client, gs_sheet = get_gsheet_client()
    if gs_sheet:
        ws_m = gs_sheet.worksheet("match_results")
        records = ws_m.get_all_records()
        for idx, row in enumerate(records, start=2):
            if str(row.get("match_id")) == str(match_id):
                ws_m.update_cell(idx, 3, int(gs_score))
                ws_m.update_cell(idx, 4, int(away_score))
                ws_m.update_cell(idx, 5, 1)
                if len(row) >= 6:
                    ws_m.update_cell(idx, 6, int(is_manual))
                st.cache_data.clear()
                return
        ws_m.append_row([match_id, "Galatasaray Maçı", int(gs_score), int(away_score), 1, int(is_manual)])
    st.cache_data.clear()

def reset_manual_override(match_id):
    """Admin'in manuel ezme kilidini kaldırarak otomatik ICS takvim skoruna dönmesini sağlar."""
    gs_client, gs_sheet = get_gsheet_client()
    if gs_sheet:
        ws_m = gs_sheet.worksheet("match_results")
        records = ws_m.get_all_records()
        for idx, row in enumerate(records, start=2):
            if str(row.get("match_id")) == str(match_id):
                if len(row) >= 6:
                    ws_m.update_cell(idx, 6, 0)
                st.cache_data.clear()
                return
    st.cache_data.clear()

# ==========================================
# 3. FİKSTÜR ÇEKME & GEÇMİŞ / GELECEK MAÇLAR
# ==========================================

TRT = timezone(timedelta(hours=3))

def decode_ics_bytes(raw_bytes):
    """ICS baytlarını doğru UTF-8/Türkçe karakter olarak çözer."""
    try:
        text = raw_bytes.decode("utf-8")
    except Exception:
        text = raw_bytes.decode("latin1", errors="replace")
    return text

def unfold_ics_lines(text):
    """ICS standardına göre uzun katlanmış satırları birleştirir."""
    unfolded = []
    for line in text.splitlines():
        if line.startswith(" ") or line.startswith("\t"):
            if unfolded:
                unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    return unfolded

COMP_TRANSLATIONS = {
    "super lig": "Süper Lig",
    "champions league": "UEFA Şampiyonlar Ligi",
    "europa league": "UEFA Avrupa Ligi",
    "conference league": "UEFA Konferans Ligi",
    "turkish cup": "Türkiye Kupası",
    "club friendlies": "Dostluk Maçı",
}

def translate_comp(comp_name):
    if not comp_name:
        return "Süper Lig"
    comp_clean = comp_name.strip().lower()
    return COMP_TRANSLATIONS.get(comp_clean, comp_name.strip())

def extract_stadium(location_val):
    if not location_val:
        return "Bilinmiyor"
    # İlk \ işaretine kadar olan kısmı veya tamamını al
    part = location_val.split("\\")[0].strip()
    return part

def get_match_competition_map():
    text = fetch_ics_raw_text()
    m_map = {}
    if text:
        try:
            lines = unfold_ics_lines(text)
            curr = {}
            in_event = False
            in_alarm = False
            for line in lines:
                line = line.strip()
                if line.startswith("BEGIN:VEVENT"):
                    in_event = True
                    in_alarm = False
                    curr = {}
                elif line.startswith("END:VEVENT"):
                    if in_event and "date_raw" in curr:
                        raw_dt = curr["date_raw"]
                        match_id = "MATCH_" + re.sub(r"\D", "", raw_dt)
                        m_map[match_id] = curr.get("competition", "Süper Lig")
                    in_event = False
                    in_alarm = False
                elif in_event:
                    if line.startswith("BEGIN:VALARM"):
                        in_alarm = True
                    elif line.startswith("END:VALARM"):
                        in_alarm = False
                    elif not in_alarm:
                        if line.startswith("DTSTART"):
                            curr["date_raw"] = line.split(":")[-1].strip()
                        elif line.startswith("DESCRIPTION:"):
                            desc = line.replace("DESCRIPTION:", "").strip()
                            parts = desc.split("\\n")
                            if len(parts) > 1:
                                curr["competition"] = translate_comp(parts[1])
                            else:
                                curr["competition"] = "Süper Lig"
        except Exception:
            pass
    return m_map

@st.cache_data(ttl=300)
def fetch_ics_raw_text():
    """ICS takvim dosyasını 5 dakikada bir önbelleğe alarak web isteklerini hızlandırır."""
    ics_urls = [
        "https://pub.fotmob.com/prod/pub/api/v2/calendar/team/8637.ics",
        "https://ics.fixtur.es/v2/galatasaray.ics",
        "https://fixtur.es/v2/galatasaray.ics",
        "https://fixtur.es/en/wednesday/galatasaray.ics"
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    for url in ics_urls:
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return decode_ics_bytes(response.content)
        except Exception:
            continue
    return ""

def clean_match_title(title):
    if not title:
        return "Galatasaray Maçı"
    # Fix any specific mangled names if present
    if "orum" in title and "Çorum" not in title:
        title = title.replace("orum", "Çorum FK")
    if "Baakehir" in title:
        title = title.replace("Baakehir", "Başakşehir")
    return title

def get_next_gs_match():
    if st.session_state.custom_match_override:
        return st.session_state.custom_match_override

    text = fetch_ics_raw_text()
    if text:
        try:
            lines = unfold_ics_lines(text)
            events = []
            curr = {}
            in_event = False
            in_alarm = False
            for line in lines:
                line = line.strip()
                if line.startswith("BEGIN:VEVENT"):
                    in_event = True
                    in_alarm = False
                    curr = {}
                elif line.startswith("END:VEVENT"):
                    if in_event and "date_raw" in curr and "summary" in curr:
                        events.append(curr)
                    in_event = False
                    in_alarm = False
                elif in_event:
                    if line.startswith("BEGIN:VALARM"):
                        in_alarm = True
                    elif line.startswith("END:VALARM"):
                        in_alarm = False
                    elif not in_alarm:
                        if line.startswith("SUMMARY:"):
                            summary = line.replace("SUMMARY:", "").strip()
                            curr["summary"] = summary
                        elif line.startswith("DTSTART"):
                            val = line.split(":")[-1].strip()
                            curr["date_raw"] = val
                        elif line.startswith("DESCRIPTION:"):
                            desc = line.replace("DESCRIPTION:", "").strip()
                            parts = desc.split("\\n")
                            if len(parts) > 1:
                                curr["competition"] = translate_comp(parts[1])
                            else:
                                curr["competition"] = "Süper Lig"
                        elif line.startswith("LOCATION:"):
                            loc = line.replace("LOCATION:", "").strip()
                            curr["stadium"] = extract_stadium(loc)

            now_utc = datetime.now(timezone.utc)
            now_utc_str = now_utc.strftime("%Y%m%dT%H%M%SZ")
            
            future_events = []
            for e in events:
                raw_dt = e.get("date_raw", "")
                if len(raw_dt) == 8:
                    raw_dt += "T183000Z"
                if raw_dt >= now_utc_str:
                    future_events.append((raw_dt, e))
                    
            future_events.sort(key=lambda x: x[0])
            
            if future_events:
                raw_dt, next_event = future_events[0]
                
                try:
                    if "T" in raw_dt:
                        dt_utc = datetime.strptime(raw_dt, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                    else:
                        dt_utc = datetime.strptime(raw_dt[:8], "%Y%m%d").replace(hour=18, minute=30, tzinfo=timezone.utc)
                except Exception:
                    dt_utc = now_utc + timedelta(days=1)

                dt_trt = dt_utc.astimezone(TRT)
                match_id = "MATCH_" + re.sub(r"\D", "", raw_dt)
                date_formatted = dt_trt.strftime("%d.%m.%Y %H:%M TRT")
                
                title = clean_match_title(next_event.get("summary", "Galatasaray Maçı"))
                competition = next_event.get("competition", "Süper Lig")
                stadium = next_event.get("stadium", "Bilinmiyor")
                
                return {
                    "title": title,
                    "date": date_formatted,
                    "match_id": match_id,
                    "posix_time": dt_utc,
                    "trt_time": dt_trt,
                    "competition": competition,
                    "stadium": stadium,
                    "success": True
                }
        except Exception:
            pass
        
    dummy_dt_trt = datetime.now(TRT) + timedelta(days=1)
    dummy_dt_trt = dummy_dt_trt.replace(hour=21, minute=30, second=0, microsecond=0)
    dummy_dt_utc = dummy_dt_trt.astimezone(timezone.utc)
    match_id = "MATCH_" + dummy_dt_trt.strftime("%Y%m%d")
    
    return {
        "title": "Galatasaray - Çorum FK",
        "date": dummy_dt_trt.strftime("%d.%m.%Y %H:%M TRT"),
        "match_id": match_id,
        "posix_time": dummy_dt_utc,
        "trt_time": dummy_dt_trt,
        "competition": "Süper Lig",
        "stadium": "RAMS Park",
        "success": False
    }

def get_gs_schedule_overview():
    """ICS dosyasından gelecek 5 maç ve geçmiş 3 maçı çeker."""
    text = fetch_ics_raw_text()
    if text:
        try:
            lines = unfold_ics_lines(text)
            events = []
            curr = {}
            in_event = False
            in_alarm = False
            for line in lines:
                line = line.strip()
                if line.startswith("BEGIN:VEVENT"):
                    in_event = True
                    in_alarm = False
                    curr = {}
                elif line.startswith("END:VEVENT"):
                    if in_event and "date_raw" in curr and "summary" in curr:
                        events.append(curr)
                    in_event = False
                    in_alarm = False
                elif in_event:
                    if line.startswith("BEGIN:VALARM"):
                        in_alarm = True
                    elif line.startswith("END:VALARM"):
                        in_alarm = False
                    elif not in_alarm:
                        if line.startswith("SUMMARY:"):
                            curr["summary"] = line.replace("SUMMARY:", "").strip()
                        elif line.startswith("DTSTART"):
                            curr["date_raw"] = line.split(":")[-1].strip()
                        elif line.startswith("DESCRIPTION:"):
                            desc = line.replace("DESCRIPTION:", "").strip()
                            parts = desc.split("\\n")
                            if len(parts) > 1:
                                curr["competition"] = translate_comp(parts[1])
                            else:
                                curr["competition"] = "Süper Lig"
                        elif line.startswith("LOCATION:"):
                            loc = line.replace("LOCATION:", "").strip()
                            curr["stadium"] = extract_stadium(loc)

            now_utc = datetime.now(timezone.utc)
            now_utc_str = now_utc.strftime("%Y%m%dT%H%M%SZ")

            past_events = [e for e in events if e.get("date_raw", "") < now_utc_str]
            future_events = [e for e in events if e.get("date_raw", "") >= now_utc_str]

            past_events.sort(key=lambda x: x.get("date_raw", ""), reverse=True)
            future_events.sort(key=lambda x: x.get("date_raw", ""))

            formatted_past = []
            for e in past_events[:3]:
                raw_dt = e.get("date_raw", "")
                if len(raw_dt) == 8: raw_dt += "T190000Z"
                try:
                    dt_utc = datetime.strptime(raw_dt[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
                    dt_trt = dt_utc.astimezone(TRT)
                    date_str = dt_trt.strftime("%d.%m.%Y %H:%M TRT")
                except Exception:
                    date_str = "Geçmiş Maç"
                title = clean_match_title(e.get("summary", ""))
                comp = e.get("competition", "Süper Lig")
                stadium = e.get("stadium", "Bilinmiyor")
                formatted_past.append({"tarih": date_str, "mac": title, "comp": comp, "stadium": stadium})

            formatted_future = []
            for e in future_events[:5]: # Gelecek 5 maçı göster
                raw_dt = e.get("date_raw", "")
                if len(raw_dt) == 8: raw_dt += "T190000Z"
                try:
                    dt_utc = datetime.strptime(raw_dt[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
                    dt_trt = dt_utc.astimezone(TRT)
                    date_str = dt_trt.strftime("%d.%m.%Y %H:%M TRT")
                except Exception:
                    date_str = "Gelecek Maç"
                title = clean_match_title(e.get("summary", ""))
                comp = e.get("competition", "Süper Lig")
                stadium = e.get("stadium", "Bilinmiyor")
                formatted_future.append({"tarih": date_str, "mac": title, "comp": comp, "stadium": stadium})

            return formatted_past, formatted_future
        except Exception:
            pass
    return [], []

def sync_match_results_from_ics():
    """ICS dosyasındaki biten maçların gerçek skorlarını otomatik ayrıştırır ve veritabanına kaydeder."""
    results_df = fetch_match_results()
    manual_matches = set()
    if not results_df.empty and "is_manual" in results_df.columns:
        manual_matches = set(results_df[results_df["is_manual"] == 1]["match_id"].astype(str).tolist())

    text = fetch_ics_raw_text()
    if text:
        try:
            lines = unfold_ics_lines(text)
            events = []
            curr = {}
            in_event = False
            in_alarm = False
            for line in lines:
                line = line.strip()
                if line.startswith("BEGIN:VEVENT"):
                    in_event = True
                    in_alarm = False
                    curr = {}
                elif line.startswith("END:VEVENT"):
                    if in_event and "date_raw" in curr and "summary" in curr:
                        events.append(curr)
                    in_event = False
                    in_alarm = False
                elif in_event:
                    if line.startswith("BEGIN:VALARM"):
                        in_alarm = True
                    elif line.startswith("END:VALARM"):
                        in_alarm = False
                    elif not in_alarm:
                        if line.startswith("SUMMARY:"):
                            curr["summary"] = line.replace("SUMMARY:", "").strip()
                        elif line.startswith("DTSTART"):
                            curr["date_raw"] = line.split(":")[-1].strip()

            updated_count = 0
            for e in events:
                raw_dt = e.get("date_raw", "")
                match_id = "MATCH_" + re.sub(r"\D", "", raw_dt)
                
                # Skip matches manually overridden by Admin
                if str(match_id) in manual_matches:
                    continue

                summary = e.get("summary", "")
                
                # Pattern for 'Galatasaray - Team (2-1)' or 'Team - Galatasaray (1-3)'
                m = re.search(r'^(.*?)\s*\-\s*(.*?)\s*\((?:\[.*?\]\s*)?(\d+)[\-\:\s]+(\d+)\)$', summary)
                if m:
                    t1, t2, s1, s2 = m.group(1).strip(), m.group(2).strip(), int(m.group(3)), int(m.group(4))
                    if "Galatasaray" in t1:
                        gs_s, away_s = s1, s2
                    elif "Galatasaray" in t2:
                        gs_s, away_s = s2, s1
                    else:
                        continue
                        
                    save_match_result(match_id, gs_s, away_s, is_manual=0)
                    updated_count += 1
            return updated_count
        except Exception:
            pass
    return 0

def build_leaderboard_chart(preds_all, results_all, users):
    """Maç maç birikimli puan gelişim çizgi grafiği Altair nesnesini oluşturur (Etkileşimli ipuçları ile)."""
    import altair as alt
    if results_all.empty or "is_finished" not in results_all.columns:
        return None
    finished_results = results_all[results_all["is_finished"] == 1].copy()
    if finished_results.empty:
        return None
        
    merged = pd.merge(preds_all, finished_results, on="match_id", suffixes=("_p", "_r"))
    if not merged.empty:
        merged["hit"] = (merged["gs_score_p"] == merged["gs_score_r"]) & (merged["away_score_p"] == merged["away_score_r"])
    else:
        merged = pd.DataFrame(columns=["username", "match_id", "gs_score_p", "away_score_p", "gs_score_r", "away_score_r", "hit"])

    data_list = []
    
    # Her kullanıcı için "Başlangıç" (0 puan) noktası
    for u in users:
        data_list.append({
            "Maç": "Başlangıç",
            "Kullanıcı": u.upper(),
            "Birikimli Puan": 0,
            "Detay": "Sezon Başlangıcı"
        })
        
    for u in users:
        curr_points = 0
        for idx, row in finished_results.iterrows():
            m_id = row["match_id"]
            m_title = row.get("match_title", "Maç") or m_id
            
            # Kullanıcının bu maç için tahmini var mı?
            user_m = merged[(merged["username"] == u) & (merged["match_id"] == m_id)]
            if not user_m.empty:
                pred_str = f"{user_m.iloc[0]['gs_score_p']}-{user_m.iloc[0]['away_score_p']}"
                result_str = f"{user_m.iloc[0]['gs_score_r']}-{user_m.iloc[0]['away_score_r']}"
                if user_m.iloc[0]["hit"]:
                    curr_points += 1
                    detail = f"Tahmin: {pred_str} | Sonuç: {result_str} (Tam İsabet! 🎯 +1 Puan)"
                else:
                    detail = f"Tahmin: {pred_str} | Sonuç: {result_str} (İsabet Yok)"
            else:
                result_str = f"{row['gs_score']}-{row['away_score']}"
                detail = f"Tahmin Yapılmadı | Sonuç: {result_str}"
                
            data_list.append({
                "Maç": m_title,
                "Kullanıcı": u.upper(),
                "Birikimli Puan": curr_points,
                "Detay": detail
            })
            
    df_chart = pd.DataFrame(data_list)
    
    # Altair Grafik Tanımı
    chart = alt.Chart(df_chart).mark_line(point=True).encode(
        x=alt.X('Maç:N', sort=None, title='Maçlar'),
        y=alt.Y('Birikimli Puan:Q', title='Toplam Puan', axis=alt.Axis(tickMinStep=1)),
        color=alt.Color('Kullanıcı:N', title='Yarışmacı'),
        tooltip=[
            alt.Tooltip('Kullanıcı:N', title='Kullanıcı'),
            alt.Tooltip('Maç:N', title='Maç'),
            alt.Tooltip('Birikimli Puan:Q', title='Toplam Puan'),
            alt.Tooltip('Detay:N', title='Tahmin Detayı')
        ]
    ).properties(
        height=400
    ).interactive()
    
    return chart

def check_time_window(match_utc):
    now_utc = datetime.now(timezone.utc)
    match_trt = match_utc.astimezone(TRT)
    
    open_trt = match_trt.replace(hour=12, minute=0, second=1, microsecond=0)
    open_utc = open_trt.astimezone(timezone.utc)
    close_utc = match_utc - timedelta(minutes=5)
    
    if now_utc < open_utc:
        return {
            "status": "BEFORE_OPEN",
            "open_time": open_trt.strftime("%d.%m.%Y saat 12:00:01 TRT")
        }
    if now_utc > close_utc:
        return {
            "status": "CLOSED",
            "close_time": close_utc.astimezone(TRT).strftime("%d.%m.%Y %H:%M TRT")
        }
        
    return {"status": "OPEN"}

# ==========================================
# 4. ANA SAYFA & UYGULAMA İÇERİĞİ
# ==========================================

# Header Banner with Live Digital Server Clock & Logo
now_trt = datetime.now(TRT)
col_logo, col_banner = st.columns([1, 8])
with col_logo:
    if os.path.exists("logo.svg"):
        st.image("logo.svg", width=95)
with col_banner:
    st.markdown(f"""
    <div style="
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        background: linear-gradient(135deg, rgba(138, 3, 3, 0.95) 0%, rgba(26, 0, 4, 0.98) 100%); 
        border: 1px solid rgba(253, 185, 19, 0.3); 
        padding: 20px 24px; 
        border-radius: 16px; 
        margin-bottom: 28px; 
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4); 
        flex-wrap: wrap; 
        gap: 20px;
    ">
        <div>
            <h1 style="color: #FFFFFF !important; font-weight: 800; font-size: 2.1rem; margin: 0; letter-spacing: -0.5px;">🦁 GALATASARAY <span style="color: #FDB913;">SKOR TAHMİN</span> PORTALI</h1>
            <div style="color: #e5e7eb !important; font-size: 1.02rem; margin-top: 6px; font-style: italic; font-weight: 400; opacity: 0.9;">"Maçtan önce herkes uzman. Bakalım sonra kim konuşacak."</div>
        </div>
        <div style="
            background: rgba(12, 14, 18, 0.7); 
            backdrop-filter: blur(10px); 
            border: 1px solid rgba(253, 185, 19, 0.25); 
            padding: 10px 16px; 
            border-radius: 12px; 
            text-align: center; 
            min-width: 200px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        ">
            <div style="color: #9ca3af; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; margin-bottom: 2px;">🕒 SUNUCU SAATİ</div>
            <div style="color: #FDB913; font-family: 'Montserrat', sans-serif; font-size: 1.1rem; font-weight: 800;">
                {now_trt.strftime('%d.%m.%Y %H:%M:%S')} <span style="font-size:0.7rem; color:#9ca3af; font-weight: 500;">TRT</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# Sleek Horizontal Navbar / Giriş & Profil Barı
# ----------------------------------------------------
if not st.session_state.logged_in:
    with st.container():
        st.markdown('<div class="login-bar">', unsafe_allow_html=True)
        c_label, c_user, c_pass, c_btn = st.columns([3, 4, 4, 3])
        with c_label:
            st.markdown("<div style='line-height: 40px; color: #9ca3af; font-size: 0.9rem; font-weight: 500;'>🔒 Tahmin yapmak için giriş yapın:</div>", unsafe_allow_html=True)
        with c_user:
            login_user = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı Adı (Örn: ahmet)", label_visibility="collapsed").strip().lower()
        with c_pass:
            login_pass = st.text_input("Şifre", type="password", placeholder="Şifre", label_visibility="collapsed")
        with c_btn:
            if st.button("Giriş Yap", type="primary", use_container_width=True):
                current_users = fetch_users()
                if login_user in current_users and current_users[login_user] == login_pass:
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.toast(f"Hoş geldin, {login_user.upper()}! 🎉", icon="🦁")
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre hatalı!")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    with st.container():
        st.markdown('<div class="login-bar">', unsafe_allow_html=True)
        c_info, c_pwd, c_out = st.columns([5, 3, 2])
        with c_info:
            st.markdown(f"<div style='line-height: 40px;'>👤 Aktif Kullanıcı: <strong style='color:#FDB913; font-size:1.05rem;'>{st.session_state.username.upper()}</strong></div>", unsafe_allow_html=True)
        with c_pwd:
            with st.popover("🔑 Şifre Değiştir", use_container_width=True):
                current_users = fetch_users()
                curr_pwd = st.text_input("Mevcut Şifre", type="password", key="pwd_curr")
                new_pwd1 = st.text_input("Yeni Şifre", type="password", key="pwd_new1")
                new_pwd2 = st.text_input("Yeni Şifre (Tekrar)", type="password", key="pwd_new2")
                if st.button("💾 Şifremi Güncelle", type="primary", use_container_width=True):
                    u_curr_pass = current_users.get(st.session_state.username, "")
                    if curr_pwd != u_curr_pass:
                        st.error("Mevcut şifreniz hatalı!")
                    elif not new_pwd1:
                        st.warning("Yeni şifre boş olamaz!")
                    elif new_pwd1 != new_pwd2:
                        st.error("Yeni şifreler birbiriyle eşleşmiyor!")
                    else:
                        update_user_password(st.session_state.username, new_pwd1)
                        st.toast("Şifreniz güncellendi! 🎉", icon="✅")
                        st.rerun()
        with c_out:
            if st.button("🚪 Çıkış Yap", type="secondary", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Load Next Match Details
match_info = get_next_gs_match()
time_check = check_time_window(match_info["posix_time"])

# Navigation Tabs - Always visible
tab_tahmin, tab_fikstur, tab_liderlik, tab_admin = st.tabs([
    "⚽ Ana Sayfa / Tahmin Yap", 
    "📅 Maç Fikstürü (Gelecek & Geçmiş)", 
    "🏆 Liderlik Tablosu", 
    "⚙️ Admin & Ayarlar"
])

# ----------------------------------------------------
# TAB 1: TAHMİN YAP / MAÇ EKRANI
# ----------------------------------------------------
with tab_tahmin:
    st.subheader(f"📌 {match_info['title']}")
    st.caption(f"🗓️ **Müsabaka Tarihi:** {match_info['date']}")
    
    # Yerel Canlı Geri Sayım Sayacı (Client-Side JS)
    target_epoch = int(match_info["posix_time"].timestamp() * 1000)
    countdown_html = f"""
    <div id="gs-countdown" style="
        text-align: center; 
        padding: 16px; 
        background: linear-gradient(135deg, rgba(138, 3, 3, 0.08) 0%, rgba(74, 0, 14, 0.08) 100%); 
        border: 1px solid rgba(253, 185, 19, 0.25); 
        border-radius: 12px; 
        font-family: 'Montserrat', -apple-system, sans-serif;
        color: #ffffff;
        margin-top: 10px;
        margin-bottom: 10px;
    ">
        <div style="font-size: 0.75rem; color: #9ca3af; letter-spacing: 1.5px; font-weight: bold; margin-bottom: 6px; text-transform: uppercase;">⏰ MAÇ BAŞLANGICINA KALAN SÜRE</div>
        <div id="timer-display" style="font-size: 1.6rem; font-weight: 800; color: #FDB913; letter-spacing: 1px; font-family: monospace;">--:--:--</div>
    </div>
    <script>
        (function() {{
            const targetDate = {target_epoch};
            let initialDistance = targetDate - new Date().getTime();
            let reloaded = false;
            function updateTimer() {{
                const now = new Date().getTime();
                const distance = targetDate - now;
                if (distance < 0) {{
                    document.getElementById("timer-display").innerHTML = "⚽ MÜSABAKA BAŞLADI VEYA SONUÇLANDI!";
                    document.getElementById("timer-display").style.color = "#4caf50";
                    
                    // Sadece sayfa ilk açıldığında süre zaten geçmişse yenileme yapma.
                    // Ama süre yeni bittiyse (ilk açılışta pozitif olup şimdi sıfıra ulaştıysa) sayfayı 1 kez yenile:
                    if (initialDistance > 0 && !reloaded) {{
                        reloaded = true;
                        setTimeout(function() {{
                            try {{
                                window.parent.location.reload();
                            }} catch(e) {{
                                window.location.reload();
                            }}
                        }}, 500);
                    }}
                    return;
                }}
                const days = Math.floor(distance / (1000 * 60 * 60 * 24));
                const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((distance % (1000 * 60)) / 1000);
                
                let dayText = days > 0 ? days + " gün " : "";
                let hrText = String(hours).padStart(2, '0');
                let minText = String(minutes).padStart(2, '0');
                let secText = String(seconds).padStart(2, '0');
                
                document.getElementById("timer-display").innerHTML = dayText + hrText + ":" + minText + ":" + secText;
            }}
            updateTimer();
            setInterval(updateTimer, 1000);
        }})();
    </script>
    """
    st.components.v1.html(countdown_html, height=110)

    # Turnuva ve Stadyum Bilgisi Gösterimi
    comp_name = match_info.get("competition", "Süper Lig")
    stadium_name = match_info.get("stadium", "Bilinmiyor")
    
    st.markdown(f"""
    <div style="display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap;">
        <span style="background: rgba(253, 185, 19, 0.12); color: #FDB913; border: 1px solid rgba(253, 185, 19, 0.3); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">🏆 {comp_name}</span>
        <span style="background: rgba(255, 255, 255, 0.08); color: #d1d5db; border: 1px solid rgba(255, 255, 255, 0.15); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">📍 {stadium_name}</span>
    </div>
    """, unsafe_allow_html=True)

    preds_df = fetch_predictions(match_info["match_id"])
    user_pred = preds_df[preds_df["username"] == st.session_state.username] if (st.session_state.logged_in and not preds_df.empty) else pd.DataFrame()
    
    if not st.session_state.logged_in:
        st.info("🔒 Tahmin yapmak veya mevcut tahmininizi kilitlemek için lütfen sayfanın en üstündeki panelden giriş yapınız.")
    else:
        # Status Banner
        if time_check["status"] == "BEFORE_OPEN":
            st.warning(f"⏳ **Tahminler henüz açılmadı.** Tahmin yapma penceresi **{time_check['open_time']}** itibarıyla açılacaktır.")
        elif time_check["status"] == "CLOSED":
            st.error("🔒 **Tahmin süresi dolmuştur.** Maç başlamış veya başlama saatine 5 dakikadan az kalmıştır.")
        else:
            st.success("🟢 **Tahminler Açık!** Skorunuzu seçip kilitleyebilirsiniz.")
            
        st.divider()
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("### 🎯 Tahmin Durumunuz")
        
        if not user_pred.empty:
            gs_s = int(user_pred.iloc[0]["gs_score"])
            away_s = int(user_pred.iloc[0]["away_score"])
            created_at_val = user_pred.iloc[0].get("created_at", "")
            
            # Calculate 1-Hour Editing Window or Match Start Cutoff
            now_utc = datetime.now(timezone.utc)
            can_edit = False
            remaining_mins = 0
            
            try:
                created_dt = datetime.strptime(str(created_at_val), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                edit_expiry = created_dt + timedelta(hours=1)
                match_cutoff = match_info["posix_time"] - timedelta(minutes=5)
                effective_deadline = min(edit_expiry, match_cutoff)
                
                if now_utc < effective_deadline:
                    can_edit = True
                    remaining_mins = max(1, int((effective_deadline - now_utc).total_seconds() // 60))
            except Exception:
                can_edit = False

            if can_edit:
                st.warning(f"✏️ **Tahmin Düzenleme Hakkı Active:** Tahmininizi ilk 1 saat içinde veya maç başlamadan önceki 5 dakikaya kadar değiştirebilirsiniz.\n\n⏳ **Kalan Düzenleme Süresi:** `{remaining_mins} dakika`\n\n📌 **Mevcut Tahmininiz:** Galatasaray **{gs_s} - {away_s}** Rakip")
                st.markdown("#### Tahmininizi Güncelleyin:")
                c_gs, c_away = st.columns(2)
                with c_gs:
                    input_gs = st.number_input("Galatasaray", min_value=0, max_value=20, value=gs_s, step=1, key="edit_gs")
                with c_away:
                    input_away = st.number_input("Rakip Takım", min_value=0, max_value=20, value=away_s, step=1, key="edit_away")
                    
                if st.button("🔄 Tahminimi Güncelle", type="primary", use_container_width=True):
                    # Duplicate check excluding current user
                    other_preds = preds_df[preds_df["username"] != st.session_state.username]
                    if not other_preds.empty:
                        duplicate_check = other_preds[(other_preds["gs_score"] == input_gs) & (other_preds["away_score"] == input_away)]
                        if not duplicate_check.empty:
                            taken_by = duplicate_check.iloc[0]["username"].upper()
                            st.error(f"❌ **Bu skor başkası ({taken_by}) tarafından alındı!** Farklı bir skor seçiniz.")
                            st.stop()
                            
                    insert_prediction(
                        username=st.session_state.username,
                        match_id=match_info["match_id"],
                        match_title=match_info["title"],
                        gs_score=input_gs,
                        away_score=input_away
                    )
                    st.toast("Tahmininiz başarıyla güncellendi! 🎉", icon="✅")
                    st.rerun()
            else:
                st.success(f"🔒 **Tahmininiz Kesinleşti & Kilitlendi:** Galatasaray **{gs_s} - {away_s}** Rakip")
                st.caption("⚠️ Tahmininizin üzerinden 1 saat geçtiği veya maç başlama saatine 5 dakikadan az kaldığı için kilitlenmiştir.")
        elif time_check["status"] == "OPEN":
            st.markdown("#### Skor Giriniz:")
            c_gs, c_away = st.columns(2)
            with c_gs:
                input_gs = st.number_input("Galatasaray", min_value=0, max_value=20, value=0, step=1)
            with c_away:
                input_away = st.number_input("Rakip Takım", min_value=0, max_value=20, value=0, step=1)
                
            if st.button("💾 Tahmini Kaydet (1 Saat Düzenlenebilir)", type="primary", use_container_width=True):
                # Duplicate Check
                if not preds_df.empty:
                    duplicate_check = preds_df[(preds_df["gs_score"] == input_gs) & (preds_df["away_score"] == input_away)]
                    if not duplicate_check.empty:
                        taken_by = duplicate_check.iloc[0]["username"].upper()
                        st.error(f"❌ **Bu skor başkası ({taken_by}) tarafından alındı!** Her kullanıcı farklı bir skor seçmelidir.")
                        st.stop()
                
                # Insert prediction
                insert_prediction(
                    username=st.session_state.username,
                    match_id=match_info["match_id"],
                    match_title=match_info["title"],
                    gs_score=input_gs,
                    away_score=input_away
                )
                st.toast("Tahmininiz kaydedildi! 1 saat boyunca düzenleyebilirsiniz. 🎉", icon="✅")
                st.rerun()
        else:
            st.info("Şu anda yeni tahmin girişi yapılamamaktadır.")

    with col2:
        st.markdown("### 📋 Alınmış Skorlar")
        if not preds_df.empty:
            st.write("Bu maç için kullanıcılar tarafından kilitlenen skorlar:")
            for _, row in preds_df.iterrows():
                u_name = str(row['username']).upper()
                st.markdown(f"- 👤 **{u_name}**: `{row['gs_score']} - {row['away_score']}`")
        else:
            st.info("Henüz hiçbir kullanıcı tahmin yapmadı.")

# ----------------------------------------------------
# TAB 2: GELECEK & GEÇMİŞ MAÇ FİKSTÜRÜ
# ----------------------------------------------------
with tab_fikstur:
    st.subheader("📅 Galatasaray Maç Fikstürü (ICS Takvim Verisi)")
    st.caption("Fikstür takvim dosyasından (ICS) çekilen önümüzdeki 5 maç ve geçmiş son 3 müsabaka sonucu:")
    
    past_matches, future_matches = get_gs_schedule_overview()
    
    col_fut, col_pst = st.columns(2, gap="large")
    
    with col_fut:
        st.markdown("### ⏳ Önümüzdeki 5 Maç")
        if future_matches:
            for idx, fm in enumerate(future_matches, 1):
                comp_badge = f"<span style='font-size:0.75rem; background:rgba(253, 185, 19, 0.12); color:#FDB913; padding:2px 8px; border-radius:10px; margin-right:5px; font-weight:600;'>🏆 {fm.get('comp', 'Süper Lig')}</span>"
                stadium_badge = f"<span style='font-size:0.75rem; background:rgba(255,255,255,0.08); color:#d1d5db; padding:2px 8px; border-radius:10px; font-weight:600;'>📍 {fm.get('stadium', 'Bilinmiyor')}</span>"
                st.markdown(f"""
                <div class="fixture-card">
                    <span style="color:#FDB913; font-weight:bold;">{idx}. Hafta / Maç</span><br/>
                    <strong style="font-size:1.1rem; color:#FFFFFF;">{fm['mac']}</strong><br/>
                    <span style="color:#9ca3af; font-size:0.9rem; display:block; margin-bottom:6px;">🗓️ {fm['tarih']}</span>
                    {comp_badge} {stadium_badge}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Gelecek maç bilgisi yüklenemedi.")

    with col_pst:
        st.markdown("### 📜 Geçmiş Son 3 Maç & Skorları")
        if past_matches:
            for pm in past_matches:
                comp_badge = f"<span style='font-size:0.75rem; background:rgba(253, 185, 19, 0.12); color:#FDB913; padding:2px 8px; border-radius:10px; margin-right:5px; font-weight:600;'>🏆 {pm.get('comp', 'Süper Lig')}</span>"
                stadium_badge = f"<span style='font-size:0.75rem; background:rgba(255,255,255,0.08); color:#d1d5db; padding:2px 8px; border-radius:10px; font-weight:600;'>📍 {pm.get('stadium', 'Bilinmiyor')}</span>"
                st.markdown(f"""
                <div class="past-fixture-card">
                    <strong style="font-size:1.1rem; color:#FFFFFF;">{pm['mac']}</strong><br/>
                    <span style="color:#9ca3af; font-size:0.9rem; display:block; margin-bottom:6px;">🗓️ {pm['tarih']}</span>
                    {comp_badge} {stadium_badge}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Geçmiş maç bilgisi bulunamadı.")

# ----------------------------------------------------
# TAB 3: LİDERLİK TABLOSU
# ----------------------------------------------------
with tab_liderlik:
    st.subheader("🏆 Puan Durumu ve Liderlik Tablosu")
    st.caption("Doğru skor tahmininde bulunan her kullanıcı **1 Puan** kazanır. (Biten maç skorları ICS takviminden otomatik çekilir).")
    
    # Auto sync finished match scores from ICS calendar
    sync_match_results_from_ics()
    
    # Turnuva Seçim Filtresi
    comp_options = ["Tüm Turnuvalar"] + list(COMP_TRANSLATIONS.values())
    selected_comp = st.selectbox("Turnuva Seçin", comp_options, index=0)
    
    preds_all = fetch_predictions()
    results_all = fetch_match_results()
    
    # Eşleşmeleri Çek
    comp_map = get_match_competition_map()
    
    # Verileri Filtrele
    if selected_comp != "Tüm Turnuvalar":
        if not results_all.empty:
            results_all = results_all[results_all["match_id"].map(lambda x: comp_map.get(x, "Süper Lig") == selected_comp)]
        if not preds_all.empty:
            preds_all = preds_all[preds_all["match_id"].map(lambda x: comp_map.get(x, "Süper Lig") == selected_comp)]
            
    active_users = [u for u in fetch_users().keys() if u.lower() != "admin"]
    leaderboard_data = {user: {"Puan": 0, "Doğru Tahmin": 0, "Toplam Tahmin": 0} for user in active_users}
    
    if not preds_all.empty and not results_all.empty:
        merged = pd.merge(preds_all, results_all, on="match_id", suffixes=('_p', '_r'))
        for _, row in merged.iterrows():
            u = str(row['username']).strip().lower()
            if u in leaderboard_data:
                leaderboard_data[u]["Toplam Tahmin"] += 1
                if row.get('is_finished') == 1:
                    if int(row['gs_score_p']) == int(row['gs_score_r']) and int(row['away_score_p']) == int(row['away_score_r']):
                        leaderboard_data[u]["Puan"] += 1
                        leaderboard_data[u]["Doğru Tahmin"] += 1

    if leaderboard_data:
        df_lb = pd.DataFrame.from_dict(leaderboard_data, orient='index').reset_index()
        df_lb.columns = ["Kullanıcı", "Puan", "Doğru Tahmin (Tam İsabet)", "Toplam Tahmin"]
        df_lb["Kullanıcı"] = df_lb["Kullanıcı"].str.upper()
        df_lb = df_lb.sort_values(by=["Puan", "Doğru Tahmin (Tam İsabet)"], ascending=False).reset_index(drop=True)
        df_lb.index = df_lb.index + 1
        
        # Kürsüdeki ilk 3 kişiye madalya ekleme
        def add_badges(row):
            rank = row.name
            username = str(row["Kullanıcı"])
            if rank == 1:
                return f"🥇 {username}"
            elif rank == 2:
                return f"🥈 {username}"
            elif rank == 3:
                return f"🥉 {username}"
            return username
            
        df_lb["Kullanıcı"] = df_lb.apply(add_badges, axis=1)

        # Giriş yapmış aktif kullanıcıyı tabloda vurgulama
        def highlight_current_user(row):
            username_cleaned = row["Kullanıcı"].replace("🥇 ", "").replace("🥈 ", "").replace("🥉 ", "").strip().lower()
            if st.session_state.logged_in and username_cleaned == st.session_state.username.strip().lower():
                return ['background-color: rgba(253, 185, 19, 0.18); font-weight: bold; border: 1.5px solid #FDB913;'] * len(row)
            return [''] * len(row)
            
        styled_df = df_lb.style.apply(highlight_current_user, axis=1)
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("💡 Sistemde henüz kayıtlı kullanıcı (admin dışında) bulunmamaktadır.")
    
    st.divider()
    st.markdown("### 📈 Maç Maç Puan İlerleme Grafiği")
    df_chart = build_leaderboard_chart(preds_all, results_all, active_users)
    if df_chart is not None:
        st.altair_chart(df_chart, use_container_width=True)
    else:
        st.info("💡 Henüz tamamlanan maç bulunmadığı için puan ilerleme grafiği oluşmadı. İlk maç tamamlandığında kullanıcıların maç maç puan gelişimi çizgi grafiğinde görüntülenecektir.")

    st.divider()
    if st.button("🔄 ICS Fikstüründen Skorları Canlı Senkronize Et"):
        updated_n = sync_match_results_from_ics()
        st.toast(f"Biten maç skorları senkronize edildi! ({updated_n} maç işlendi)", icon="✅")
        st.rerun()
        
    st.divider()
    st.markdown("### 📜 Geçmiş Tahminler & Sonuçlar")
    if not preds_all.empty:
        st.dataframe(preds_all, use_container_width=True)
    else:
        st.info("Henüz sistemde kayıtlı geçmiş tahmin bulunmamaktadır.")

# ----------------------------------------------------
# TAB 4: ADMİN PORTALI & AYARLAR
# ----------------------------------------------------
with tab_admin:
    st.subheader("⚙️ Admin Portalı & Maç Ayarları")
    
    if not st.session_state.logged_in or str(st.session_state.username).strip().lower() != "admin":
        st.error("🔒 **Erişim Engellendi:** Admin portalına yalnızca **`admin`** kullanıcı adına sahip yetkili kullanıcılar erişebilir.")
        st.info("💡 Lütfen sayfanın en üstündeki panelden `admin` kullanıcı adı ile giriş yapınız.")
    else:
        st.markdown("#### 1. Maç Bilgisini Manuel Değiştir / Özelleştir")
        c_t1, c_t2 = st.columns(2)
        with c_t1:
            custom_title = st.text_input("Müsabaka Adı", value=match_info['title'])
        with c_t2:
            custom_date = st.text_input("Müsabaka Tarihi & Saati", value=match_info['date'])
            
        if st.button("📝 Maç Bilgilerini Güncelle"):
            st.session_state.custom_match_override = {
                "title": custom_title,
                "date": custom_date,
                "match_id": match_info['match_id'],
                "posix_time": match_info['posix_time'],
                "trt_time": match_info['trt_time'],
                "success": True
            }
            st.success("Maç bilgileri güncellendi!")
            st.rerun()

        st.markdown("---")
        st.markdown("#### 2. Gerçekleşen Maç Sonucu Girişi")
        st.write(f"Aktif Müsabaka: **{match_info['title']}** (`{match_info['match_id']}`)")
        
        c_m1, c_m2 = st.columns(2)
        with c_m1:
            real_gs = st.number_input("Gerçekleşen GS Skoru", min_value=0, max_value=20, value=0, step=1, key="adm_gs")
        with c_m2:
            real_away = st.number_input("Gerçekleşen Rakip Skoru", min_value=0, max_value=20, value=0, step=1, key="adm_away")
            
        c_btn1, c_btn2 = st.columns([1, 1])
        with c_btn1:
            if st.button("✅ Maç Sonucunu Manuel Kaydet & Kilitle", type="primary", use_container_width=True):
                save_match_result(match_info["match_id"], real_gs, real_away, is_manual=1)
                st.success("Maç sonucu manuel olarak kilitlendi! Otomatik ICS güncellemelerinden korundu.")
                st.rerun()
        with c_btn2:
            if st.button("🔄 Manuel Kilidi Kaldır (ICS Skoruna Dön)", type="secondary", use_container_width=True):
                reset_manual_override(match_info["match_id"])
                sync_match_results_from_ics()
                st.toast("Manuel kilit kaldırıldı. Otomatik takvim skorları aktif!", icon="🔄")
                st.rerun()

        st.divider()
        
        st.subheader("🌐 Google Sheets Veritabanı Durumu")
        st.markdown("""
        Tüm tahminler, kullanıcı şifreleri ve maç sonuçları **Google Sheets (`GS_Skor_Tahmin_DB`)** bulut veritabanında saklanmaktadır.
        """)
