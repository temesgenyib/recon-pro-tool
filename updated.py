import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="ReconPro Terminal", page_icon="🏦", layout="wide")

# --- 2. THEME & VISUAL REPAIR ---
def apply_ui_theme():
    st.markdown("""
        <style>
        /* Force Metric Visibility */
        [data-testid="stMetricValue"] { color: #1e3a8a !important; font-weight: 800 !important; }
        [data-testid="stMetricLabel"] { color: #475569 !important; font-weight: 600 !important; }
        
        /* FIX FOR INVISIBLE TAB TEXT (The marked text in your screenshot) */
        button[data-baseweb="tab"] p {
            color: #1e3a8a !important;
            font-size: 1.1rem !important;
            font-weight: 700 !important;
        }
        button[aria-selected="true"] {
            border-bottom-color: #ef4444 !important;
        }
        button[aria-selected="true"] p {
            color: #ef4444 !important;
        }

        /* Sidebar Styling (Matches your Admin Portal screenshot) */
        section[data-testid="stSidebar"] { background-color: #111827 !important; }
        section[data-testid="stSidebar"] * { color: white !important; }
        
        /* Main Header */
        .main-header {
            background: linear-gradient(90deg, #0f172a 0%, #1e3a8a 100%);
            padding: 2rem; border-radius: 15px; color: white !important; 
            text-align: center; margin-bottom: 2rem;
        }
        .main-header h1 { color: white !important; margin: 0; }
        
        /* Metric Box Styling */
        div[data-testid="stMetric"] {
            background-color: white !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 12px; padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE ENGINE ---
@st.cache_resource
def get_engine():
    try:
        pg = st.secrets["postgres"]
        conn_str = f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['dbname']}"
        return create_engine(conn_str, pool_pre_ping=True)
    except: return None

# --- 4. AUTHENTICATION GATEKEEPER ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    apply_ui_theme()
    # Dark Login Background
    st.markdown('<style>.stApp { background: #0f172a !important; }</style>', unsafe_allow_html=True)
    
    _, col_mid, _ = st.columns([1, 1.2, 1])
    with col_mid:
        st.markdown('<div style="text-align:center; color:white; margin-top:100px;"><h1>🚀 ReconPro Login</h1><p>Financial Reconciliation Terminal</p></div>', unsafe_allow_html=True)
        with st.container():
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Enter Terminal", use_container_width=True):
                engine = get_engine()
                if engine:
                    with engine.connect() as conn:
                        res = conn.execute(text("SELECT role FROM users WHERE username = :u AND password = :p"), {"u": u, "p": p}).fetchone()
                        if res:
                            st.session_state.update({"authenticated": True, "username": u, "role": res[0]})
                            st.rerun()
                        else: st.error("Invalid credentials.")
                else: st.error("DB connection failed.")
    st.stop()

# --- 5. DASHBOARD LAYOUT ---
apply_ui_theme()
st.markdown('<div class="main-header"><h1>🚀 Financial Reconciliation Terminal</h1><p>Internal Audit Control | Cooperative Bank of Oromia</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"## Welcome, {st.session_state['username']}")
    if st.button("Logout"):
        st.session_state["authenticated"] = False
        st.rerun()
    st.divider()
    
    st.markdown("### 🛡️ Admin Portal")
    nav_options = ["Reconciliation"]
    if st.session_state["role"] == "admin":
        nav_options.append("User Management")
    nav_options.append("History")
    
    menu = st.radio("Navigation", nav_options)
    
    st.divider()
    st.markdown("### ⚙️ Settings")
    id_col = st.text_input("ID Column", "transaction_id")
    date_col = st.text_input("Date Column", "date")
    amt_col = st.text_input("Amount Column", "amount")
    branch_id = st.text_input("Branch Code", "BR-ADDIS-01")

# --- 6. PAGE LOGIC ---

if menu == "Reconciliation":
    c1, c2 = st.columns(2)
    with c1: sys_file = st.file_uploader("📂 Upload T24 Core Data", type=['csv'])
    with c2: ext_file = st.file_uploader("📂 Upload Partner Records", type=['csv'])

    if sys_file and ext_file:
        if st.button("🚀 EXECUTE TRIPLE-LOCK RECONCILIATION", use_container_width=True):
            df_sys = pd.read_csv(sys_file)
            df_ext = pd.read_csv(ext_file)
            
            # Cleaning
            for df in [df_sys, df_ext]:
                df.columns = df.columns.str.strip()
                df[id_col] = df[id_col].astype(str).str.strip()
                if date_col in df.columns:
                    df[date_col] = df[date_col].astype(str).str.strip()

            # 1. DUPLICATE CHECK (BOTH SIDES)
            s_dupes = df_sys[df_sys.duplicated(subset=[id_col], keep=False)].copy()
            e_dupes = df_ext[df_ext.duplicated(subset=[id_col], keep=False)].copy()
            total_dupes = len(s_dupes) + len(e_dupes)

            # 2. MULTI-KEY RECON (ID + DATE)
            merged = pd.merge(df_sys, df_ext, on=[id_col, date_col], how='left', suffixes=('_sys', '_ext'))
            missing = merged[merged[f'{amt_col}_ext'].isna()].copy()
            variance = merged[(merged[f'{amt_col}_ext'].notna()) & (merged[f'{amt_col}_sys'] != merged[f'{amt_col}_ext'])].copy()

            # 3. DISPLAY SUMMARY
            st.divider()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Records", len(df_sys))
            m2.metric("Unmatched (ID+Date)", len(missing))
            m3.metric("Value Variances", len(variance))
            m4.metric("Duplicates (Both Files)", total_dupes, delta="Action Required", delta_color="inverse")

            # 4. TABBED REPORTS (Fixed Visibility)
            t1, t2, t3 = st.tabs(["🕵️ Discrepancy Analysis", "📉 Value Variances", "⚠️ Duplicate Findings"])
            
            with t1:
                st.write("### Records Missing in Partner File")
                st.dataframe(missing[[id_col, date_col, f'{amt_col}_sys']], use_container_width=True)
            
            with t2:
                st.write("### Amount Mismatches (Same ID/Date)")
                st.dataframe(variance[[id_col, date_col, f'{amt_col}_sys', f'{amt_col}_ext']], use_container_width=True)
                
            with t3:
                ca, cb = st.columns(2)
                with ca: 
                    st.write("**T24 Duplicates**")
                    st.dataframe(s_dupes, use_container_width=True)
                with cb: 
                    st.write("**Partner Duplicates**")
                    st.dataframe(e_dupes, use_container_width=True)

            # 5. LOGGING
            engine = get_engine()
            if engine:
                with engine.connect() as conn:
                    conn.execute(text("INSERT INTO reconciliation_audit (branch_code, expected_count, found_count, missing_count, status) VALUES (:b, :e, :f, :m, :s)"),
                                 {"b": branch_id[:50], "e": len(df_sys), "f": len(df_ext), "m": len(missing), "s": "Audit Completed"})
                    conn.commit()
                st.toast("✅ Audit trail updated.")

elif menu == "User Management":
    st.subheader("👤 Staff Account Control")
    with st.form("new_user"):
        nu, np, nr = st.text_input("Username"), st.text_input("Password", type="password"), st.selectbox("Role", ["admin", "viewer"])
        if st.form_submit_button("Create Account"):
            with get_engine().connect() as conn:
                conn.execute(text("INSERT INTO users (username, password, role) VALUES (:u, :p, :r)"), {"u":nu, "p":np, "r":nr})
                conn.commit()
            st.success("User added.")

elif menu == "History":
    st.subheader("📜 Recent Reconciliation Logs")
    df_h = pd.read_sql("SELECT * FROM reconciliation_audit ORDER BY id DESC LIMIT 20", get_engine())
    st.dataframe(df_h, use_container_width=True)

st.markdown('<div style="text-align:center; padding:30px; color:#94a3b8;">© 2026 Cooperative Bank of Oromia | v5.0</div>', unsafe_allow_html=True)