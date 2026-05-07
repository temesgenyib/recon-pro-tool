import xml.etree.ElementTree as ET
import pandas as pd
import streamlit as st
from datetime import datetime
import io

# Set page configuration for a professional look
st.set_page_config(page_title="ReconPro Terminal", page_icon="🏦", layout="wide")

def run_streamlit_reconciliation():
    # --- Sidebar - Contact & Status ---
    with st.sidebar:
        st.image("https://em-content.zobj.net/source/microsoft-teams/363/bank_1f3e6.png", width=80) 
        st.title("ReconPro Terminal")
        
        st.header("System Status")
        st.info("Cloud Server: Active")
        st.write(f"Server Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        st.divider()
        
        st.markdown("### 👨‍💻Temesgen Yibeltal")
        
        # Contact Information
        st.markdown(f"""
        <div style="font-size: 0.9em; line-height: 1.5; margin-bottom: 10px;">
            <p>📞 <b>Phone:</b> +251941625829</p>
            <p>✉️ <b>Email:</b> temesgenyib@gmail.com</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Use the Link Button for the most reliable LinkedIn redirection
        st.link_button("🌐 View LinkedIn Profile", "https://www.linkedin.com/in/temesgen-yibeltal-231a7122b")
        
        st.divider()
        st.caption("v1.2.0 | Financial Automation Tool")

    # --- Main Content Area ---
    st.title("🏦 ReconPro: Bank Reconciliation Terminal")
    st.markdown("""
    **Instructions:**
    1. Upload your **Checklist (Excel)** containing the 'ID' column.
    2. Upload your **Data Stream (XML)** file.
    3. Click **Run Reconciliation** to generate the report.
    """)

    # --- File Uploaders ---
    col1, col2 = st.columns(2)
    with col1:
        excel_file = st.file_uploader("1. Upload Excel Master Record", type=["xlsx", "xls"])
    with col2:
        xml_file = st.file_uploader("2. Upload XML Data Stream", type=["xml"])

    if excel_file and xml_file:
        if st.button("🚀 Run Reconciliation", use_container_width=True):
            try:
                # --- Part 1: Process Excel Checklist ---
                with st.spinner("Analyzing Excel Checklist..."):
                    if not (excel_file.name.endswith('.xlsx') or excel_file.name.endswith('.xls')):
                         st.error("❌ Critical Error: Please upload a valid Excel file.")
                         return

                    expected_df = pd.read_excel(excel_file)
                    expected_df.columns = expected_df.columns.str.upper()

                    if 'ID' not in expected_df.columns:
                        st.error("❌ Critical Error: The Excel file must have a column named 'ID'.")
                        return
                    
                    expected_ids = set(expected_df['ID'].astype(str).str.strip().str.upper())

                # --- Part 2: Process XML Data ---
                with st.spinner("Parsing XML Data Stream..."):
                    try:
                        tree = ET.parse(xml_file)
                        root = tree.getroot()
                    except ET.ParseError:
                         st.error("❌ Critical Error: Invalid XML file.")
                         return

                    all_actual_data = []
                    names, ids = [], []
                    
                    for element in root.iter():
                        tag_clean = element.tag.split('}')[-1].lower()
                        if "name" in tag_clean and element.text:
                            names.append(element.text.strip())
                        elif "id" in tag_clean and element.text:
                            ids.append(element.text.strip())
                    
                    for i in range(min(len(names), len(ids))):
                        all_actual_data.append({
                            "NAME": names[i].upper(), 
                            "ID": str(ids[i]).strip().upper()
                        })

                if not all_actual_data:
                    st.warning("⚠️ No valid data found in XML.")
                    return

                actual_df = pd.DataFrame(all_actual_data).drop_duplicates()
                actual_ids = set(actual_df['ID'])

                # --- Part 3: Logic ---
                missing_ids = expected_ids - actual_ids
                extra_ids = actual_ids - expected_ids

                # --- Part 4: Display Results ---
                st.divider()
                st.success("✅ Reconciliation Complete")
                
                res_col1, res_col2, res_col3 = st.columns(3)
                res_col1.metric("Expected", len(expected_ids))
                res_col2.metric("Found", len(actual_ids))
                res_col3.metric("Missing", len(missing_ids), delta_color="inverse")

                # --- Part 5: Export ---
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    actual_df.to_excel(writer, sheet_name='Matched_Data', index=False)
                    pd.DataFrame({"MISSING_ID": list(missing_ids)}).to_excel(writer, sheet_name='Missing', index=False)
                    pd.DataFrame({"UNEXPECTED_ID": list(extra_ids)}).to_excel(writer, sheet_name='Unexpected', index=False)
                
                st.download_button(
                    label="📥 Download Reconciliation Report (.xlsx)",
                    data=output.getvalue(),
                    file_name=f"Recon_Report_{datetime.now().strftime('%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

                tab1, tab2 = st.tabs(["Preview Found Data", "List Missing IDs"])
                with tab1:
                    st.dataframe(actual_df, use_container_width=True)
                with tab2:
                    st.write(list(missing_ids) if missing_ids else "No missing IDs!")

            except Exception as e:
                st.error(f"⚠️ System Error: {e}")
    else:
        st.info("Please upload your Excel and XML files to begin.")

if __name__ == "__main__":
    run_streamlit_reconciliation()