import xml.etree.ElementTree as ET
import pandas as pd
import os
import glob
from datetime import datetime

def process_flexible_filenames():
    # 1. Setup paths
    source_dir = r"D:\personal\Development\phyton"
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    
    # 2. Find ANY file ending in .xml
    # The '*' is a wildcard meaning 'anything'
    xml_files = glob.glob(os.path.join(source_dir, "*.xml"))

    if not xml_files:
        print(f"🔍 Checking {source_dir}...")
        print("❌ No XML files found to process.")
        return

    print(f"Found {len(xml_files)} file(s). Starting processing...")

    for source_file in xml_files:
        current_filename = os.path.basename(source_file)
        print(f"\n🚀 Processing: {current_filename}")

        try:
            # 3. Parse the XML
            tree = ET.parse(source_file)
            root = tree.getroot()

            names, ids = [], []
            for element in root.iter():
                # Clean tag names to ignore complex SoapUI namespaces
                tag_clean = element.tag.split('}')[-1].lower()
                
                if "name" in tag_clean and element.text:
                    names.append(element.text.strip())
                elif "id" in tag_clean and element.text:
                    ids.append(element.text.strip())

            # 4. Save to Excel if data exists
            length = min(len(names), len(ids))
            if length > 0:
                df = pd.DataFrame({
                    "NAME": names[:length],
                    "ID": ids[:length]
                })
                
                # Make the Excel filename match the original XML name + timestamp
                timestamp = datetime.now().strftime("%H%M%S")
                clean_name = current_filename.replace(".xml", "")
                output_excel = os.path.join(desktop, f"{clean_name}_{timestamp}.xlsx")
                
                df.to_excel(output_excel, index=False)
                print(f"✅ Excel generated: {os.path.basename(output_excel)}")

                # 5. Cleanup: Delete the file we just finished
                os.remove(source_file)
                print(f"🗑️ Removed source file: {current_filename}")
            else:
                print(f"⚠️ No Name/ID data found in {current_filename}. Skipping delete to be safe.")

        except Exception as e:
            print(f"❌ Error processing {current_filename}: {e}")

if __name__ == "__main__":
    process_flexible_filenames()