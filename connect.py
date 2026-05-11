import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Coopbank ReconPro",
    page_icon="🏦",
    layout="wide"
)

# --- CUSTOM STYLING ---
# Setting the background to light gray (#F5F5F5)
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F5F5F5;
    }
    /* Optional: Makes the dataframe containers look cleaner against the gray */
    .stDataFrame {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_code=True
)

# --- DATABASE ENGINE ---
@st.cache_resource
def get_engine():
    """
    Creates a cached SQLAlchemy engine. 
    Using @st.cache_resource ensures we don't exhaust DB connections on every rerun.
    """
    try:
        pg = st.secrets["postgres"]
        conn_str = f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['dbname']}"
        
        # Connection pooling and timeouts to prevent "forced closure" errors
        engine = create_engine(
            conn_str,
            connect_args={"options": "-c statement_timeout=3000"}, # 3s timeout
            pool_pre_ping=True,  # Checks connection health before use
            pool_size=10,
            max_overflow=20
        )
        return engine
    except Exception as e:
        st.error(f"Engine creation failed: {e}")
        return None

# --- UI HEADER ---
st.title("🏦 Coopbank ReconPro")
st.markdown("---")

# --- MAIN LOGIC ---
engine = get_engine()

if engine:
    try:
        # Using a context manager for proper connection handling
        with engine.connect() as connection:
            # 1. Verify Connection
            connection.execute(text("SELECT 1"))
            st.success("✅ Database Connection Verified")
            
            # 2. Fetch Audit Logs
            st.subheader("Recent Audit Logs")
            query = "SELECT * FROM reconciliation_audit ORDER BY id DESC LIMIT 5"
            
            # Read into DataFrame
            df = pd.read_sql(query, connection)
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No logs found in the reconciliation_audit table.")
                
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        st.info("Check if your password in `secrets.toml` matches your database credentials.")
else:
    st.warning("Database engine is not initialized. Please check your secrets configuration.")

# --- FOOTER ---
st.markdown("---")
st.caption("ReconPro Terminal v1.0 | Internal Use Only")