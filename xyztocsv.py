import pandas as pd
import glob
import os

OUTPUT_DIR = "africa_output/deseasonalized/datafiles/split_xyz"
# 1. Define your new destination folder here
NEW_OUTPUT_DIR = "africa_output/deseasonalized/datafiles/split_xyz/final_v2" 

# Create the new folder automatically if it doesn't exist yet
os.makedirs(NEW_OUTPUT_DIR, exist_ok=True)

# Find every .xyz file in the folder
xyz_files = glob.glob(os.path.join(OUTPUT_DIR, "*.xyz"))
dummy_id = 999999 
for xyz_path in xyz_files:
    # Read the space-separated xyz file (no header)
    df = pd.read_csv(xyz_path, sep=r'\s+', header=None, names=['lon', 'lat', 'weight'])

    # 2. Get just the file name (e.g., "basin_mode_1.xyz" -> "basin_mode_1")
    filename_without_ext = os.path.splitext(os.path.basename(xyz_path))[0]
    
    # 3. Combine the new folder path with the new filename
    # Instead of f"{filename_without_ext}.mask.csv"
    # Generate a strict pattern: HyBas_<id>_<name>_Lev3_quartdeg.mask.csv
     # Or increment this in your loop
    csv_path = os.path.join(NEW_OUTPUT_DIR, f"HyBas_{dummy_id}_{filename_without_ext}_Lev3_quartdeg.mask.csv")
    dummy_id += 1
    df.to_csv(csv_path, index=False)
    print(f"Converted: {xyz_path} -> {csv_path}")

print("\nDone converting all .xyz files to the new folder!")