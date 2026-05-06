import xml.etree.ElementTree as ET
import pandas as pd
import streamlit as st
from datetime import datetime
import io

# Set page configuration for a professional look
st.set_page_config(page_title="ReconPro Terminal", page_icon="🏦", layout="wide")

def run_streamlit_reconciliation():
    st.title("🏦 ReconPro: Bank Reconciliation Terminal")
    st.markdown("""
    **Instructions:**
    1. Upload your **Checklist (Excel)** containing the 'ID' column.
    2. Upload your **Data Stream (XML)** file.
    3. Click **Process** to generate the reconciliation report.
    """)

    # --- Sidebar / Header Information ---
    st.sidebar.header("System Status")
    st.sidebar.info("Cloud Server: Active")
    st.sidebar.write(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

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
                    expected_df = pd.read_excel(excel_file)
                    if 'ID' not in expected_df.columns:
                        st.error("❌ Critical Error: The Excel file must have a column exactly named 'ID'.")
                        return
                    
                    # Force String, Strip whitespace, and convert to Uppercase for matching
                    expected_ids = set(expected_df['ID'].astype(str).str.strip().str.upper())

                # --- Part 2: Process XML Data ---
                with st.spinner("Parsing XML Data Stream..."):
                    # Parse the uploaded XML file directly
                    tree = ET.parse(xml_file)
                    root = tree.getroot()
                    all_actual_data = []
                    
                    names, ids = [], []
                    # Improved logic to find 'name' and 'id' tags regardless of namespace
                    for element in root.iter():
                        tag_clean = element.tag.split('}')[-1].lower()
                        if "name" in tag_clean and element.text:
                            names.append(element.text.strip())
                        elif "id" in tag_clean and element.text:
                            ids.append(element.text.strip())
                    
                    # Match pairs based on the smaller list size to avoid index errors
                    for i in range(min(len(names), len(ids))):
                        all_actual_data.append({
                            "NAME": names[i].upper(), 
                            "ID": str(ids[i]).strip().upper()
                        })

                if not all_actual_data:
                    st.warning("⚠️ Data Mismatch: No valid 'Name' or 'ID' tags found in the XML structure.")
                    return

                # Create DataFrame & Drop Duplicates
                actual_df = pd.DataFrame(all_actual_data).drop_duplicates()
                actual_ids = set(actual_df['ID'])

                # --- Part 3: Reconciliation Logic ---
                missing_ids = expected_ids - actual_ids
                extra_ids = actual_ids - expected_ids

                # --- Part 4: Display Results & Download ---
                st.divider()
                st.success("✅ Reconciliation Process Complete")
                
                # Summary Stats
                res_col1, res_col2, res_col3 = st.columns(3)
                res_col1.metric("Total Expected", len(expected_ids))
                res_col2.metric("Total Found", len(actual_ids))
                res_col3.metric("Missing IDs", len(missing_ids), delta_color="inverse")

                # --- Part 5: Generate Excel Report ---
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    actual_df.to_excel(writer, sheet_name='Matched_Data', index=False)
                    pd.DataFrame({"MISSING_ID": list(missing_ids)}).to_excel(writer, sheet_name='ERRORS_Missing', index=False)
                    pd.DataFrame({"UNEXPECTED_ID": list(extra_ids)}).to_excel(writer, sheet_name='ERRORS_Unexpected', index=False)
                
                processed_data = output.getvalue()

                st.download_button(
                    label="📥 Download Full Reconciliation Report (.xlsx)",
                    data=processed_data,
                    file_name=f"Recon_Report_{datetime.now().strftime('%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

                # Data Previews
                tab1, tab2 = st.tabs(["Found Data Preview", "Missing IDs List"])
                with tab1:
                    st.dataframe(actual_df, use_container_width=True)
                with tab2:
                    if missing_ids:
                        st.write(list(missing_ids))
                    else:
                        st.write("No missing IDs found!")

            except Exception as e:
                st.error(f"⚠️ System Error: {e}")
    else:
        st.info("Please upload both required files to activate the reconciliation engine.")

# This is the CRITICAL block that tells Streamlit to run the function
if __name__ == "__main__":
    run_streamlit_reconciliation()