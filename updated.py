import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --- 1. DATABASE CONFIGURATION ---
def get_engine():
    """Establishes a robust connection to the Neon PostgreSQL database."""
    try:
        pg = st.secrets["postgres"]
        conn_str = f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['dbname']}?sslmode=require"
        return create_engine(
            conn_str, 
            pool_pre_ping=True,
            connect_args={"options": "-c statement_timeout=5000"}
        )
    except Exception as e:
        st.error(f"❌ Database Configuration Error: {e}")
        return None

def log_to_db(branch_code, expected, found, status):
    """Saves the summary to the audit table with strict type casting."""
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
                    "b": str(branch_code)[:50], 
                    "e": int(expected), 
                    "f": int(found),
                    "m": int(expected - found), 
                    "s": str(status)[:20]
                })
                conn.commit()
        except Exception as e:
            st.sidebar.error(f"⚠️ SQL Logging Error: {e}")

# --- 2. AUTHENTICATION ---
def login():
    st.title("🔐 ReconPro Secure Access")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            engine = get_engine()
            if engine:
                with engine.connect() as conn:
                    # Check users table in Neon
                    result = conn.execute(
                        text("SELECT role FROM users WHERE username = :u AND password = :p"),
                        {"u": u, "p": p}
                    ).fetchone()
                    if result:
                        st.session_state["authenticated"] = True
                        st.session_state["role"] = result[0]
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

# --- 3. MAIN APPLICATION ---
if "authenticated" not in st.session_state:
    login()
else:
    st.set_page_config(page_title="ReconPro Terminal", page_icon="🏦", layout="wide")
    
    # Custom CSS
    st.markdown("""
        <style>
        .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        </style>
        """, unsafe_allow_html=True)

    st.title("🏦 ReconPro: Automated Reconciliation Terminal")
    
    # Sidebar
    st.sidebar.header("⚙️ Settings")
    branch_id = st.sidebar.text_input("Branch Code", value="BR001")
    sys_col = st.sidebar.text_input("System ID Column", "transaction_id")
    ext_col = st.sidebar.text_input("External ID Column", "txn_ref")
    if st.sidebar.button("Logout"):
        del st.session_state["authenticated"]
        st.rerun()

    # Layout
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📁 System Records (T24)")
        system_file = st.file_uploader("Upload T24 CSV", type=['csv'])
    with col2:
        st.subheader("📁 External Records")
        external_file = st.file_uploader("Upload External CSV", type=['csv'])

    if system_file and external_file:
        if st.button("🚀 Run Reconciliation Analysis"):
            df_sys = pd.read_csv(system_file)
            df_ext = pd.read_csv(external_file)
            
            # Identify missing records
            missing_df = df_sys[~df_sys[sys_col].astype(str).isin(df_ext[ext_col].astype(str))]
            
            expected = len(df_sys)
            found = len(df_ext)
            diff = len(missing_df)
            status = "Balanced" if diff == 0 else "Discrepancy"
            
            # Metrics
            st.divider()
            m1, m2, m3 = st.columns(3)
            m1.metric("Expected", expected)
            m2.metric("Found", found)
            m3.metric("Unmatched", diff, delta=diff, delta_color="inverse")
            
            if status == "Balanced":
                st.success(f"✅ Branch {branch_id} is Balanced.")
            else:
                st.error(f"❌ Discrepancy Found in {branch_id}!")
                st.subheader("🕵️ Detailed Missing Records")
                st.dataframe(missing_df, use_container_width=True)
                
                csv_dl = missing_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Report", csv_dl, f"Missing_{branch_id}.csv")
            
            # Log to Neon
            log_to_db(branch_id, expected, found, status)

    # History Section
    st.divider()
    with st.expander("📜 View Recent Audit Logs"):
        engine = get_engine()
        if engine:
            try:
                with engine.connect() as conn:
                    history = pd.read_sql("SELECT * FROM reconciliation_audit ORDER BY run_date DESC LIMIT 10", conn)
                    st.dataframe(history, use_container_width=True)
            except:
                st.info("No audit logs found yet.")

    # --- 4. CONTACT FOOTER ---
    st.markdown("<br><br><hr>", unsafe_allow_html=True)
    footer_html = f"""
    <div style="text-align: center; color: #555; font-family: sans-serif;">
        <p><b>ReconPro Terminal v1.2</b></p>
        <p>Developed by: <b>👨‍💻 Temesgen Yibeltal</b> | Temenos Core Banking Manager</p>
        <p style="font-size: 0.9em;">
            📧 <a href="mailto:temesgen.yibeltal@coopbankoromia.com.et" style="color: #0066cc;">Support</a> | 
            🔗 <a href="https://www.linkedin.com/in/temesgen-yibeltal-231a7122b" target="_blank" style="color: #0066cc;">LinkedIn</a>
        </p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)