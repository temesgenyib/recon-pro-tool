import xml.etree.ElementTree as ET
import pandas as pd
import os
import glob
from datetime import datetime

def run_pro_reconciliation():
    source_dir = r"D:\personal\Development\phyton"
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    checklist_path = os.path.join(desktop, "checklist.xlsx")

    # Issue 4: Verify Checklist
    if not os.path.exists(checklist_path):
        print("❌ Error: checklist.xlsx missing.")
        return

    # Issue 1 & 3: Force String and Uppercase on Checklist
    expected_df = pd.read_excel(checklist_path)
    if 'ID' not in expected_df.columns:
        print("❌ Error: checklist.xlsx must have a column named 'ID'")
        return
        
    expected_ids = set(expected_df['ID'].astype(str).str.strip().str.upper())

    # Extraction Logic
    xml_files = glob.glob(os.path.join(source_dir, "*.xml"))
    all_actual_data = []

    for source_file in xml_files:
        try:
            tree = ET.parse(source_file)
            root = tree.getroot()
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
                    "ID": str(ids[i]).strip().upper() # Fix 1 & 3
                })
        except Exception as e:
            print(f"⚠️ Error reading {source_file}: {e}")

    if not all_actual_data:
        print("❌ No data found in XML files.")
        return

    # Issue 2: Drop Duplicates
    actual_df = pd.DataFrame(all_actual_data).drop_duplicates()
    actual_ids = set(actual_df['ID'])

    # Reconciliation Sets
    missing_ids = expected_ids - actual_ids
    extra_ids = actual_ids - expected_ids

    # Final Output
    report_path = os.path.join(desktop, f"FINAL_BANK_RECON_{datetime.now().strftime('%H%M')}.xlsx")
    with pd.ExcelWriter(report_path) as writer:
        actual_df.to_excel(writer, sheet_name='Matched_Data', index=False)
        pd.DataFrame({"MISSING_ID": list(missing_ids)}).to_excel(writer, sheet_name='ERRORS_Missing', index=False)
        pd.DataFrame({"UNEXPECTED_ID": list(extra_ids)}).to_excel(writer, sheet_name='ERRORS_Unexpected', index=False)

    print(f"✅ Recon finished. Total Missing: {len(missing_ids)}")

if __name__ == "__main__":
    run_pro_reconciliation()