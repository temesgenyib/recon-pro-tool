import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import time

# --- 1. INITIALIZE STATE ---
if 'db' not in st.session_state:
    st.session_state.db = {"admin": "1234"}
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'view' not in st.session_state:
    st.session_state.view = "login"

# --- 2. RECONCILIATION LOGIC ---
@st.cache_data
def perform_reconciliation(master_file, xml_files):
    if master_file.name.endswith('.csv'):
        df_master = pd.read_csv(master_file)
    else:
        df_master = pd.read_excel(master_file)
    
    id_column = df_master.columns[0]
    master_ids = set(df_master[id_column].astype(str).unique())

    xml_content_pool = set()
    for xml in xml_files:
        tree = ET.parse(xml)
        root = tree.getroot()
        for elem in root.iter():
            if elem.text:
                xml_content_pool.add(elem.text.strip())

    missing_ids = [m_id for m_id in master_ids if m_id not in xml_content_pool]
    return missing_ids

# --- 3. UI STYLING & FOOTER CSS ---
st.set_page_config(page_title="ReconPro Terminal", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #0B0E11 !important; font-family: 'Sora', sans-serif; color: white; }
    .auth-card { background: #151921; padding: 40px; border-radius: 28px; border: 1px solid #232D3F; text-align: center; width: 450px; margin: auto; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .main-btn button { background-color: #F0B90B !important; color: black !important; font-weight: bold !important; width: 100%; border-radius: 12px; height: 48px; border: none; }
    .side-btn button { background-color: transparent !important; color: #848E9C !important; border: 1px solid #2B3139 !important; width: 100%; border-radius: 12px; height: 48px; }
    
    /* Footer Styling */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #151921;
        color: #848E9C;
        text-align: center;
        padding: 10px 0;
        font-size: 14px;
        border-top: 1px solid #232D3F;
        z-index: 999;
    }
    .footer b { color: #F0B90B; }
    
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION FLOW ---
if not st.session_state.logged_in:
    st.markdown('<div style="padding-top: 50px;">', unsafe_allow_html=True)
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)

    if st.session_state.view == "register":
        st.markdown("<h1>Create Account</h1>", unsafe_allow_html=True)
        new_u = st.text_input("New Access ID", key="reg_u")
        new_p = st.text_input("New Secret Key", type="password", key="reg_p")
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="main-btn">', unsafe_allow_html=True)
            if st.button("Save User"):
                if new_u and new_p:
                    st.session_state.db[new_u] = new_p
                    st.session_state.view = "login"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="side-btn">', unsafe_allow_html=True)
            if st.button("Back"):
                st.session_state.view = "login"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown("<h1>ReconPro</h1><p>Financial Reconciliation Terminal</p>", unsafe_allow_html=True)
        l_u = st.text_input("Access ID", key="log_u")
        l_p = st.text_input("Secret Key", type="password", key="log_p")
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="main-btn">', unsafe_allow_html=True)
            if st.button("Login"):
                if l_u in st.session_state.db and st.session_state.db[l_u] == l_p:
                    st.session_state.logged_in = True
                    st.session_state.username = l_u
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="side-btn">', unsafe_allow_html=True)
            if st.button("Create User"):
                st.session_state.view = "register"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)

# --- 5. RECONCILIATION DASHBOARD ---
else:
    with st.sidebar:
        st.title("Terminal")
        st.info(f"User: **{st.session_state.username}**")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.view = "login"
            st.rerun()

    st.title("⚖️ Reconciliation Tool")
    
    c1, c2 = st.columns(2)
    with c1:
        master = st.file_uploader("Master Record", type=['xlsx', 'csv'])
    with c2:
        xmls = st.file_uploader("XML Streams", type=['xml'], accept_multiple_files=True)

    if master and xmls:
        st.markdown('<div class="main-btn">', unsafe_allow_html=True)
        if st.button("🚀 Run Reconciliation Analysis"):
            with st.spinner("Processing Data..."):
                missing = perform_reconciliation(master, xmls)
                if not missing:
                    st.balloons()
                    st.success("Reconciliation Complete: All IDs found.")
                else:
                    st.error(f"Alert: {len(missing)} IDs missing in XML.")
                    st.table(pd.DataFrame(missing, columns=["Missing ID"]))
        st.markdown('</div>', unsafe_allow_html=True)

# --- 6. GLOBAL FOOTER ---
st.markdown("""
    <div class="footer">
        Contact: <b>TEMESGEN YIBELTAL</b> | 📞 +251 941 625 829 | 📧 temesgenyib@gmail.com
    </div>
""", unsafe_allow_html=True)