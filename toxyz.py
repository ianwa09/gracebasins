import os
import geopandas as gpd
import xarray as xr
from rasterio import features

# =====================================================================
# CONFIGURATION & INPUT PARAMETERS
# =====================================================================
TARGET_MODE_TO_CONVERT = 1              # <--- CHANGE THIS to the mode ID you want to convert
OUTPUT_DIR = "africa_output/deseasonalized/datafiles"            # Folder where your shapefiles are stored
INPUT_NETCDF = "grace_data.nc"          # Path to original GRACE dataset (for grid template)
VARIABLE_NAME = "lwe_thickness"         # Variable name in your GRACE file

# Construct file paths dynamically based on your target mode input
SHP_FILENAME = f"basin_mode_{TARGET_MODE_TO_CONVERT}.shp"
SHP_PATH = os.path.join(OUTPUT_DIR, SHP_FILENAME)
XYZ_OUTPUT_PATH = os.path.join(OUTPUT_DIR, f"basin_mode_{TARGET_MODE_TO_CONVERT}.xyz")

# =====================================================================
# CONVERSION PROCESS
# =====================================================================
# 1. Validation check
print(f"Checking for Mode {TARGET_MODE_TO_CONVERT} shapefile files...")
# Check for the primary structural files (.shp and .dbf) before continuing
if not os.path.exists(SHP_PATH):
    raise FileNotFoundError(
        f"Could not find '{SHP_FILENAME}' in '{OUTPUT_DIR}'. "
        f"Please ensure you've run your REOF script for this mode first."
    )
if not os.path.exists(SHP_PATH.replace(".shp", ".dbf")):
    raise FileNotFoundError(
        f"Missing the accompanying .dbf attribute file for Mode {TARGET_MODE_TO_CONVERT}. "
        f"The conversion cannot run without it."
    )

# 2. Load the template GRACE grid to match the original spatial resolution
print("Loading grid template coordinate structure...")
ds = xr.open_dataset(INPUT_NETCDF)
grid_template = ds[VARIABLE_NAME].isel(time=0)  # Extract 1 spatial snapshot

# 3. Read the vector geometries
print(f"Reading shapefile data for Mode {TARGET_MODE_TO_CONVERT}...")
gdf = gpd.read_file(SHP_PATH)

# 4. Burn the vector polygon geometry back into a 2D binary raster grid
print("Rasterizing shapes onto the target coordinate array...")
shapes = [(geom, 1) for geom in gdf.geometry]

rasterized_mask = features.rasterize(
    shapes,
    out_shape=grid_template.shape,
    transform=grid_template.rio.transform(),
    fill=0,             # Area outside your basin will become 0
    default_value=1     # Area inside your basin will become 1
)

# Map the raw matrix data back into an Xarray DataArray structure
da_mask = xr.DataArray(
    rasterized_mask, 
    coords=grid_template.coords, 
    dims=grid_template.dims
)

# 5. Flatten the 2D spatial grid into a tabular 3-column string structure
print("Converting grid to space-separated XYZ table format...")
df_xyz = da_mask.to_dataframe(name="value").reset_index()

# Sort and clean up columns to strictly output [longitude, latitude, value]
df_xyz = df_xyz[['lon', 'lat', 'value']]

# Save out to text file matching standard .xyz configurations
df_xyz.to_csv(XYZ_OUTPUT_PATH, sep=' ', header=False, index=False)

print(f"\nSuccess! Mode {TARGET_MODE_TO_CONVERT} has been converted and saved to:\n -> {XYZ_OUTPUT_PATH}")