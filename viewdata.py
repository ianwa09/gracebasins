import os
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd

# Configuration - must match the output name from your processing script
SHAPEFILE_PATH = "africa_output/deseasonalized/datafiles/basin_mode_2.shp"
OUTPUT_VERIFICATION_PLOT = "visuals/deseasonalized/africa/africa_mode_2.png"

print("Checking for exported shapefile...")
if not os.path.exists(SHAPEFILE_PATH):
    raise FileNotFoundError(
        f"Could not find '{SHAPEFILE_PATH}'. Please run your main export script first!"
    )

# 1. Load the exported shapefile
print(f"Loading vector boundaries from {SHAPEFILE_PATH}...")
gdf = gpd.read_file(SHAPEFILE_PATH)

print(f"Found {len(gdf)} isolated polygon(s) in the export file.")

# 2. Setup the Map Plot
fig = plt.figure(figsize=(12, 7))
ax = plt.axes(projection=ccrs.PlateCarree())

# Add global basemap features for clear context
ax.add_feature(cfeature.COASTLINE, linewidth=0.6, edgecolor='#444444')
ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5, edgecolor='#aaaaaa')
ax.add_feature(cfeature.LAND, facecolor='#f5f5f5')
ax.add_feature(cfeature.OCEAN, facecolor='#eef5f8')

# 3. Plot the exact exported shapes
# We use ax.add_geometries to correctly project the GeoDataFrame geometries onto Cartopy
print("Rendering exported geometries...")
ax.add_geometries(
    gdf.geometry, 
    crs=ccrs.PlateCarree(), 
    facecolor='salmon',     # Fills the exported basins so you can spot tiny pixel clusters easily
    edgecolor='crimson',    # Sharp border around the exported regions
    linewidth=1.5, 
    alpha=0.6
)

# Add gridlines and text
ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, alpha=0.2)
ax.set_title(
    f"Verification Map: Exact Geometries Exported to GIS\n"
    f"File: {SHAPEFILE_PATH} ({len(gdf)} discrete features)", 
    fontsize=13, pad=15
)

# 4. Save and display
plt.savefig(OUTPUT_VERIFICATION_PLOT, dpi=200, bbox_inches='tight')
print(f"Verification plot successfully saved to: {OUTPUT_VERIFICATION_PLOT}")
plt.show()