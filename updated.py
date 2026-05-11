import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="ReconPro Terminal", 
    page_icon="🏦", 
    layout="wide"
)

# --- 2. HIGH-VISIBILITY UI STYLING ---
st.markdown("""
    <style>
    /* Force high-visibility text colors */
    html, body, [class*="css"], .stMarkdown, p, li {
        color: #1f2937 !important; 
    }

    /* Main App Background */
    .stApp {
        background-color: #f8fafc;
    }

    /* Top Header Banner */
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2.5rem;
        border-radius: 15px;
        color: white !important; 
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        color: white !important;
        margin-bottom: 0.5rem;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #cbd5e1;
    }

    /* Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        background-color: #1e3a8a;
        color: white !important;
        font-weight: bold;
        border: none;
    }
    
    .stButton>button:hover {
        background-color: #2563eb;
        transform: translateY(-2px);
    }

    /* Footer Styling */
    .footer {
        text-align: center;
        padding: 25px;
        color: #475569 !important;
        font-size: 0.9rem;
        border-top: 1px solid #e2e8f0;
        margin-top: 50px;
        line-height: 1.6;
    }
    .footer a {
        color: #2563eb !important;
        text-decoration: none;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE LOGIC ---
@st.cache_resource
def get_engine():
    try:
        pg = st.secrets["postgres"]
        conn_str = f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['dbname']}"
        return create_engine(conn_str, pool_pre_ping=True)
    except Exception as e:
        st.error(f"❌ Database connection failed.")
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
                conn.execute(query, {"b": branch_code, "e": expected, "f": found, "m": expected - found, "s": status})
                conn.commit()
        except: pass

# --- 4. DASHBOARD UI ---
st.markdown('<div class="main-header"><h1>🏦 ReconPro Terminal</h1><p style="color: #dbeafe !important;">Enterprise Financial Reconciliation Engine</p></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🛠️ Control Panel")
    branch_id = st.text_input("Branch Identifier", value="BR-ADDIS-01")
    
    st.divider()
    with st.expander("Settings & Mapping", expanded=False):
        sys_col = st.text_input("System Key (T24)", "transaction_id")
        ext_col = st.text_input("External Key (Partner)", "txn_ref")

# File Uploaders
c1, c2 = st.columns(2)
with c1:
    st.markdown("#### 📤 Internal: T24 Core")
    system_file = st.file_uploader("Upload System CSV", type=['csv'], key="sys_up")

with c2:
    st.markdown("#### 📤 External: Partner")
    external_file = st.file_uploader("Upload External CSV", type=['csv'], key="ext_up")

# --- 5. EXECUTION ENGINE ---
if system_file and external_file:
    st.markdown("---")
    if st.button("🚀 EXECUTE RECONCILIATION"):
        df_sys = pd.read_csv(system_file)
        df_ext = pd.read_csv(external_file)
        
        df_sys[sys_col] = df_sys[sys_col].astype(str).str.strip()
        df_ext[ext_col] = df_ext[ext_col].astype(str).str.strip()
        
        missing_df = df_sys[~df_sys[sys_col].isin(df_ext[ext_col])]
        
        expected, found = len(df_sys), len(df_ext)
        diff = len(missing_df)
        status = "Balanced" if diff == 0 else "Discrepancy"
        
        m1, m2, m3 = st.columns(3)
        m1.metric("EXPECTED RECORDS", expected)
        m2.metric("FOUND RECORDS", found)
        m3.metric("MISSING", diff, delta=-diff if diff > 0 else 0, delta_color="inverse")
        
        if status == "Balanced":
            st.success("✨ **Reconciliation Successful:** No discrepancies found.")
        else:
            st.error(f"🚨 **Discrepancy Detected:** {diff} records missing.")
            st.dataframe(missing_df, use_container_width=True)
            
            csv = missing_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Discrepancy Report", data=csv, file_name="discrepancy_report.csv")
        
        log_to_db(branch_id, expected, found, status)

# --- 6. HISTORY ---
st.markdown("---")
with st.expander("📜 View Audit Trail History"):
    engine = get_engine()
    if engine:
        try:
            with engine.connect() as conn:
                hist = pd.read_sql("SELECT * FROM reconciliation_audit ORDER BY id DESC LIMIT 5", conn)
                st.dataframe(hist, use_container_width=True)
        except:
            st.info("Log into your database to see the audit trail.")

# --- 7. FOOTER ---
st.markdown(f"""
    <div class="footer">
        <b>ReconPro Terminal v2.3</b> | High-Visibility Mode<br>
        Developed by <b>Temesgen Yibeltal</b><br>
        📧 <a href="mailto:temesgenyib@gmail.com">temesgenyib@gmail.com</a> | 📞 +251941625829<br>
        © 2026 Cooperative Bank of Oromia
    </div>
""", unsafe_allow_html=True)