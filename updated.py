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

# --- 2. AUTHENTICATION ---
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

if "authenticated" not in st.session_state:
    login()
else:
    st.set_page_config(page_title="ReconPro Terminal", page_icon="🏦", layout="wide")
    
    # --- SIDEBAR ---
    st.sidebar.title(f"Welcome, {st.session_state['username']}")
    branch_id = st.sidebar.text_input("Branch Code", value="BR001")
    
    st.sidebar.subheader("Column Mapping")
    sys_col = st.sidebar.text_input("System ID Column", "transaction_id")
    ext_col = st.sidebar.text_input("External ID Column", "txn_ref")

    if st.session_state["role"] == "admin":
        with st.sidebar.expander("👤 User Management"):
            new_u = st.text_input("New Username")
            new_p = st.text_input("New Password", type="password")
            if st.button("Create User"):
                engine = get_engine()
                with engine.connect() as conn:
                    conn.execute(text("INSERT INTO users (username, password, role) VALUES (:u, :p, 'viewer')"), {"u": new_u, "p": new_p})
                    conn.commit()
                    st.success("User created!")

    if st.sidebar.button("Logout"):
        del st.session_state["authenticated"]
        st.rerun()

    # --- SHARED FILE UPLOADER (Global Scope) ---
    st.title("🏦 ReconPro: Automated Reconciliation Terminal")
    st.markdown("### 📁 Data Input")
    u1, u2 = st.columns(2)
    with u1:
        sys_file = st.file_uploader("Upload T24 (System) CSV", type=['csv'])
    with u2:
        ext_file = st.file_uploader("Upload External Source CSV", type=['csv'])

    # --- MAIN UI TABS ---
    tab1, tab2, tab3 = st.tabs(["🚀 Reconciliation", "📂 Duplicate Check", "📜 Audit History"])

    # Load Dataframes into state if files exist
    df_sys = pd.read_csv(sys_file) if sys_file else None
    df_ext = pd.read_csv(ext_file) if ext_file else None

    # --- TAB 1: RECONCILIATION ---
    with tab1:
        if df_sys is not None and df_ext is not None:
            if sys_col not in df_sys.columns or ext_col not in df_ext.columns:
                st.error("❌ Column mapping mismatch. Please check sidebar settings.")
            else:
                if st.button("🚀 Run Reconciliation Analysis"):
                    missing_df = df_sys[~df_sys[sys_col].astype(str).isin(df_ext[ext_col].astype(str))]
                    status = "Balanced" if len(missing_df) == 0 else "Discrepancy"
                    
                    st.divider()
                    st.metric("Unmatched Records", len(missing_df), delta=len(missing_df), delta_color="inverse")
                    
                    if status == "Balanced":
                        st.success("✅ Reconciliation Successful")
                    else:
                        st.error("❌ Discrepancy Found")
                        st.dataframe(missing_df, use_container_width=True)
                    
                    log_to_db(branch_id, len(df_sys), len(df_ext), status)
        else:
            st.info("Please upload both T24 and External files above to start.")

    # --- TAB 2: DUPLICATE CHECK ---
    with tab2:
        st.subheader("🕵️ Duplicate Detection")
        if df_sys is not None or df_ext is not None:
            file_choice = st.radio("Which file would you like to scan?", ["T24 (System)", "External Source"], horizontal=True)
            target_df = df_sys if file_choice == "T24 (System)" else df_ext
            
            if target_df is not None:
                id_col = st.selectbox("Select ID column to check for duplicates", target_df.columns)
                if st.button("🔍 Scan for Duplicates"):
                    duplicates = target_df[target_df.duplicated(subset=[id_col], keep=False)]
                    if not duplicates.empty:
                        st.warning(f"Found {len(duplicates)} duplicate entries in {file_choice}.")
                        st.dataframe(duplicates.sort_values(by=id_col), use_container_width=True)
                    else:
                        st.success(f"✅ No duplicates found in {file_choice} for column '{id_col}'.")
        else:
            st.info("Upload files in the header to run a duplicate check.")

    # --- TAB 3: AUDIT HISTORY ---
    with tab3:
        st.subheader("📜 Branch Reconciliation Logs")
        if st.button("🔄 Refresh History"):
            engine = get_engine()
            if engine:
                with engine.connect() as conn:
                    history = pd.read_sql("SELECT run_date, branch_code, expected_count, found_count, status FROM reconciliation_audit ORDER BY run_date DESC", conn)
                    st.dataframe(history, use_container_width=True)
                    if not history.empty:
                        st.line_chart(history.set_index('run_date')['expected_count'])

    st.markdown("<br><hr><center>Developed by <b>Temesgen Yibeltal</b> | Temenos Core Banking Manager</center>", unsafe_allow_html=True)