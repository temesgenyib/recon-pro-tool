import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(page_title="ReconPro Terminal", page_icon="🏦", layout="wide")

def apply_ui_theme():
    st.markdown("""
        <style>
        /* Force High-Contrast Visibility */
        [data-testid="stMetricValue"] { color: #1e3a8a !important; font-weight: 800 !important; }
        [data-testid="stMetricLabel"] { color: #334155 !important; font-weight: 600 !important; }
        
        /* Tab Text Visibility Fix */
        button[data-baseweb="tab"] p {
            color: #1e3a8a !important;
            font-size: 1.1rem !important;
            font-weight: 700 !important;
        }
        button[aria-selected="true"] p { color: #ef4444 !important; }

        /* Main Header Styling */
        .main-header {
            background: linear-gradient(90deg, #0f172a 0%, #1e3a8a 100%);
            padding: 2rem; border-radius: 15px; color: white !important; 
            text-align: center; margin-bottom: 2rem;
        }
        .main-header h1 { color: white !important; margin: 0; }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] { background-color: #111827 !important; }
        section[data-testid="stSidebar"] * { color: white !important; }
        
        div[data-testid="stMetric"] {
            background-color: white !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 12px; padding: 15px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ENGINE (SSL-FORCED FOR STABILITY) ---
@st.cache_resource
def get_engine():
    try:
        if "postgres" not in st.secrets:
            st.error("Secrets not found! Check your Streamlit Cloud Dashboard.")
            return None
            
        pg = st.secrets["postgres"]
        # Added ?sslmode=require to solve the OperationalError during login
        conn_str = f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['dbname']}?sslmode=require"
        
        return create_engine(
            conn_str, 
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10}
        )
    except Exception as e:
        st.error(f"Engine Configuration Error: {e}")
        return None

# --- 3. AUTHENTICATION GATEKEEPER ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    apply_ui_theme()
    st.markdown('<style>.stApp { background: #0f172a !important; }</style>', unsafe_allow_html=True)
    
    _, col_mid, _ = st.columns([1, 1.2, 1])
    with col_mid:
        st.markdown('<div style="text-align:center; color:white; margin-top:100px;"><h1>🚀 ReconPro Login</h1><p>Financial Audit Terminal</p></div>', unsafe_allow_html=True)
        with st.container():
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Enter Secure Terminal", use_container_width=True):
                engine = get_engine()
                if engine:
                    try:
                        with engine.connect() as conn:
                            res = conn.execute(text("SELECT role FROM users WHERE username = :u AND password = :p"), {"u": u, "p": p}).fetchone()
                            if res:
                                st.session_state.update({"authenticated": True, "username": u, "role": res[0]})
                                st.rerun()
                            else:
                                st.error("Invalid Username or Password.")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")
                else:
                    st.error("Could not initialize database engine.")
    st.stop()

# --- 4. MAIN APPLICATION INTERFACE ---
apply_ui_theme()
st.markdown('<div class="main-header"><h1>🚀 ReconPro Enterprise v5.1</h1><p>Internal Audit & Reconciliation Control | CBO</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"## Welcome, {st.session_state['username']}")
    if st.button("🚪 Secure Logout"):
        st.session_state["authenticated"] = False
        st.rerun()
    st.divider()
    
    nav_options = ["Reconciliation"]
    if st.session_state["role"] == "admin":
        nav_options.append("User Management")
    nav_options.append("History")
    menu = st.radio("Navigation", nav_options)
    
    st.divider()
    id_col = st.text_input("Transaction ID Column", "transaction_id")
    date_col = st.text_input("Date Column", "date")
    amt_col = st.text_input("Amount Column", "amount")
    branch_id = st.text_input("Branch Code", "BR-ADDIS-01")

# --- 5. RECONCILIATION LOGIC ---
if menu == "Reconciliation":
    c1, c2 = st.columns(2)
    with c1: sys_file = st.file_uploader("📂 T24 Core CSV", type=['csv'])
    with c2: ext_file = st.file_uploader("📂 Partner Records CSV", type=['csv'])

    if sys_file and ext_file:
        if st.button("🚀 START TRIPLE-LOCK AUDIT", use_container_width=True):
            df_sys, df_ext = pd.read_csv(sys_file), pd.read_csv(ext_file)
            
            # Formatting
            for df in [df_sys, df_ext]:
                df.columns = df.columns.str.strip()
                df[id_col] = df[id_col].astype(str).str.strip()
                if date_col in df.columns:
                    df[date_col] = df[date_col].astype(str).str.strip()

            # Logic 1: Symmetrical Duplicate Scanning
            s_dupes = df_sys[df_sys.duplicated(subset=[id_col], keep=False)].copy()
            e_dupes = df_ext[df_ext.duplicated(subset=[id_col], keep=False)].copy()

            # Logic 2: Multi-Key Matching (ID + Date)
            merged = pd.merge(df_sys, df_ext, on=[id_col, date_col], how='left', suffixes=('_sys', '_ext'))
            missing = merged[merged[f'{amt_col}_ext'].isna()].copy()
            variance = merged[(merged[f'{amt_col}_ext'].notna()) & (merged[f'{amt_col}_sys'] != merged[f'{amt_col}_ext'])].copy()

            # Dashboard
            st.divider()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Records", len(df_sys))
            m2.metric("Missing Items", len(missing))
            m3.metric("Value Variances", len(variance))
            m4.metric("Duplicates Found", len(s_dupes) + len(e_dupes))

            # Final Report Tabs
            t1, t2, t3 = st.tabs(["🕵️ Discrepancy Analysis", "📉 Variances", "⚠️ Duplicates"])
            
            with t1:
                st.write("### Records not found in Partner Data")
                st.dataframe(missing[[id_col, date_col, f'{amt_col}_sys']], use_container_width=True)
            
            with t2:
                st.write("### Amount Discrepancies")
                st.dataframe(variance[[id_col, date_col, f'{amt_col}_sys', f'{amt_col}_ext']], use_container_width=True)
                
            with t3:
                ca, cb = st.columns(2)
                with ca: 
                    st.write("T24 Duplicates")
                    st.dataframe(s_dupes, use_container_width=True)
                with cb: 
                    st.write("Partner Duplicates")
                    st.dataframe(e_dupes, use_container_width=True)

            # Audit Logging
            engine = get_engine()
            if engine:
                with engine.connect() as conn:
                    conn.execute(text("INSERT INTO reconciliation_audit (branch_code, expected_count, found_count, missing_count, status) VALUES (:b, :e, :f, :m, :s)"),
                                 {"b": branch_id[:50], "e": len(df_sys), "f": len(df_ext), "m": len(missing), "s": "Success"})
                    conn.commit()
                st.toast("✅ Database Trail Updated")

elif menu == "User Management":
    st.subheader("👤 Admin: Account Management")
    with st.form("add_user"):
        nu, np, nr = st.text_input("Username"), st.text_input("Password", type="password"), st.selectbox("Role", ["admin", "viewer"])
        if st.form_submit_button("Create User"):
            with get_engine().connect() as conn:
                conn.execute(text("INSERT INTO users (username, password, role) VALUES (:u, :p, :r)"), {"u":nu, "p":np, "r":nr})
                conn.commit()
            st.success("User successfully added.")

elif menu == "History":
    st.subheader("📜 System Audit Trail")
    engine = get_engine()
    if engine:
        df_h = pd.read_sql("SELECT * FROM reconciliation_audit ORDER BY id DESC LIMIT 20", engine)
        st.dataframe(df_h, use_container_width=True)

st.markdown('<div style="text-align:center; padding:30px; color:#94a3b8;">© 2026 Cooperative Bank of Oromia | v5.1</div>', unsafe_allow_html=True)