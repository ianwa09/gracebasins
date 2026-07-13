import os
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd

# Loop through all 5 modes (1 to 5)
for mode in range(1, 6):
    print(f"\n--- Processing Mode {mode} ---")
    
    # Dynamic Configuration based on the current mode
    SHAPEFILE_PATH = f"africa_output/deseasonalized/datafiles/basin_mode_{mode}.shp"
    OUTPUT_VERIFICATION_PLOT = f"visuals/deseasonalized/africa/africa_mode_{mode}.png"

    print("Checking for exported shapefile...")
    if not os.path.exists(SHAPEFILE_PATH):
        print(f"Skipping: Could not find '{SHAPEFILE_PATH}'.")
        continue

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
    print("Rendering exported geometries...")
    ax.add_geometries(
        gdf.geometry, 
        crs=ccrs.PlateCarree(), 
        facecolor='salmon',     # Fills the exported basins
        edgecolor='crimson',    # Sharp border around the exported regions
        linewidth=1.5, 
        alpha=0.6
    )

    # Add gridlines and text
    ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, alpha=0.2)
    ax.set_title(
        f"Verification Map: Exact Geometries Exported to GIS (Mode {mode})\n"
        f"File: {SHAPEFILE_PATH} ({len(gdf)} discrete features)", 
        fontsize=13, pad=15
    )

    # 4. Save and display
    # Ensure output directory exists before saving
    os.makedirs(os.path.dirname(OUTPUT_VERIFICATION_PLOT), exist_ok=True)
    
    plt.savefig(OUTPUT_VERIFICATION_PLOT, dpi=200, bbox_inches='tight')
    print(f"Verification plot successfully saved to: {OUTPUT_VERIFICATION_PLOT}")
    
    # Display the plot
    plt.show()
    
    # Close the current figure to free up memory before the next loop iteration
    plt.close(fig)

print("\nAll available modes processed!")