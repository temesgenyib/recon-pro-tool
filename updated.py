import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --- 1. DATABASE CONFIGURATION ---
def get_engine():
    try:
        pg = st.secrets["postgres"]
        conn_str = f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['dbname']}?sslmode=require"
        return create_engine(conn_str, pool_pre_ping=True)
    except Exception as e:
        st.error(f"❌ Database Config Error: {e}")
        return None

def log_to_db(branch_code, expected, found, status):
    engine = get_engine()
    if engine:
        try:
            with engine.connect() as conn:
                query = text("""
                    INSERT INTO reconciliation_audit 
                    (branch_code, expected_count, found_count, missing_count, status)
                    VALUES (:b, :e, :f, :m, :s)
                """)
                conn.execute(query, {
                    "b": str(branch_code)[:50], "e": int(expected), 
                    "f": int(found), "m": int(expected - found), "s": str(status)[:20]
                })
                conn.commit()
        except Exception as e:
            st.sidebar.error(f"⚠️ Logging Error: {e}")

# --- 2. AUTHENTICATION & USER MGMT ---
def login():
    st.title("🔐 ReconPro Secure Access")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            engine = get_engine()
            if engine:
                with engine.connect() as conn:
                    result = conn.execute(
                        text("SELECT role FROM users WHERE username = :u AND password = :p"),
                        {"u": u, "p": p}
                    ).fetchone()
                    if result:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = u
                        st.session_state["role"] = result[0]
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

# --- 3. MAIN APPLICATION ---
if "authenticated" not in st.session_state:
    login()
else:
    st.set_page_config(page_title="ReconPro Terminal", page_icon="🏦", layout="wide")
    
    # --- SIDEBAR & ADMIN TOOLS ---
    st.sidebar.title(f"Welcome, {st.session_state['username']}")
    branch_id = st.sidebar.text_input("Branch Code", value="BR001")
    
    st.sidebar.subheader("Column Mapping")
    sys_col = st.sidebar.text_input("System ID Column", "transaction_id")
    ext_col = st.sidebar.text_input("External ID Column", "txn_ref")

    if st.session_state["role"] == "admin":
        with st.sidebar.expander("👤 User Management"):
            new_u = st.text_input("New Username")
            new_p = st.text_input("New Password", type="password")
            new_r = st.selectbox("Role", ["admin", "viewer"])
            if st.button("Create User"):
                engine = get_engine()
                with engine.connect() as conn:
                    conn.execute(
                        text("INSERT INTO users (username, password, role) VALUES (:u, :p, :r)"),
                        {"u": new_u, "p": new_p, "r": new_r}
                    )
                    conn.commit()
                    st.success(f"User {new_u} created!")

    if st.sidebar.button("Logout"):
        del st.session_state["authenticated"]
        st.rerun()

    # --- MAIN UI ---
    st.title("🏦 ReconPro: Automated Reconciliation Terminal")
    
    col1, col2 = st.columns(2)
    with col1:
        system_file = st.file_uploader("Upload T24 CSV", type=['csv'])
    with col2:
        external_file = st.file_uploader("Upload External CSV", type=['csv'])

    if system_file and external_file:
        df_sys = pd.read_csv(system_file)
        df_ext = pd.read_csv(external_file)
        
        # ERROR HANDLING FOR KEYERROR
        if sys_col not in df_sys.columns:
            st.error(f"❌ Column '{sys_col}' not found in System File!")
        elif ext_col not in df_ext.columns:
            st.error(f"❌ Column '{ext_col}' not found in External File!")
        else:
            if st.button("🚀 Run Reconciliation"):
                # Missing records logic
                missing_df = df_sys[~df_sys[sys_col].astype(str).isin(df_ext[ext_col].astype(str))]
                
                # Metrics
                st.divider()
                m1, m2, m3 = st.columns(3)
                m1.metric("Expected", len(df_sys))
                m2.metric("Found", len(df_ext))
                m3.metric("Unmatched", len(missing_df), delta=len(missing_df), delta_color="inverse")
                
                if len(missing_df) == 0:
                    st.success("✅ Balanced")
                    log_to_db(branch_id, len(df_sys), len(df_ext), "Balanced")
                else:
                    st.error("❌ Discrepancy Found")
                    st.dataframe(missing_df, use_container_width=True)
                    log_to_db(branch_id, len(df_sys), len(df_ext), "Discrepancy")

    # --- FOOTER ---
    st.markdown("<br><hr><center>Developed by <b>Temesgen Yibeltal</b> | Temenos Core Banking Manager</center>", unsafe_allow_html=True)