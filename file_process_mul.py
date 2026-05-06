import xml.etree.ElementTree as ET
import pandas as pd
import os
import glob
from datetime import datetime

def run_master_merger():
    source_dir = r"D:\personal\Development\phyton"
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    
    # Find all XML files
    xml_files = glob.glob(os.path.join(source_dir, "*.xml"))

    if not xml_files:
        print("❌ No files found to merge.")
        return

    print(f"📂 Found {len(xml_files)} files. Starting Master Merger...")

    # This list will hold the data from ALL files
    all_records = []

    for source_file in xml_files:
        print(f"Reading: {os.path.basename(source_file)}...")
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

            # Pair them up and add to our master list
            length = min(len(names), len(ids))
            for i in range(length):
                all_records.append({
                    "NAME": names[i],
                    "ID": ids[i],
                    "SOURCE_FILE": os.path.basename(source_file) # Added for tracking
                })

        except Exception as e:
            print(f"⚠️ Error reading {source_file}: {e}")

    # After the loop, save EVERYTHING to one file
    if all_records:
        df_master = pd.DataFrame(all_records)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(desktop, f"MASTER_RECON_REPORT_{timestamp}.xlsx")
        
        df_master.to_excel(output_path, index=False)
        print(f"\n✅ SUCCESS! {len(all_records)} total records merged.")
        print(f"📄 Master Report: {os.path.basename(output_path)}")

        # Cleanup: Delete all processed XMLs
        for f in xml_files:
            os.remove(f)
        print("🗑️ All source XML files cleared.")
    else:
        print("⚠️ No valid data found in any files.")

if __name__ == "__main__":
    run_master_merger()