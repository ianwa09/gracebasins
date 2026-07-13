import os
import pandas as pd
import numpy as np
import xarray as xr
import xeofs as xe
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd
from rasterio import features
from shapely.geometry import shape

# =====================================================================
# 1. CONFIGURATION & FILE PATHS
# =====================================================================
INPUT_NETCDF = "grace_data.nc"          # Path to your GRACE dataset
VARIABLE_NAME = "lwe_thickness"         # Variable name (Liquid Water Equivalent)
N_MODES_TO_ROTATE = 10                  # Number of EOF modes to calculate/rotate
TARGET_MODE = 1                         # Which mode/basin to extract and plot
OUTPUT_SHAPEFILE = "grace_reof_basins.shp"
OUTPUT_PLOT = f"basin_mode_{TARGET_MODE}.png"

# =====================================================================
# 2. DATA LOADING & PREPROCESSING
# =====================================================================
print("Loading and preprocessing GRACE data...")
if not os.path.exists(INPUT_NETCDF):
    raise FileNotFoundError(f"Please place your GRACE file at: {INPUT_NETCDF}")

ds = xr.open_dataset(INPUT_NETCDF)
ds['time'] = pd.to_datetime(ds.time.values, unit='D', origin='2002-01-01')

grid_anomaly = ds[VARIABLE_NAME]
grid_anomaly = grid_anomaly.load()
print("Deseasonalizing data (removing seasonal cycle)...")
monthly_climatology = grid_anomaly.groupby("time.month").mean("time")
grid_anomaly = grid_anomaly.groupby("time.month") - monthly_climatology
# Calculate cosine latitude weights to account for earth's curvature
weights = np.sqrt(np.cos(np.deg2rad(grid_anomaly.lat)))

# =====================================================================
# 3. ROTATED EOF (REOF) ANALYSIS
# =====================================================================
print(f"Running Base EOF analysis...")
# 1. Initialize and fit the base EOF model
# (xeofs actually has a built-in 'use_coslat=True' feature, but since we manually 
# computed 'weights', we pass them into the fit function here)
eof_model = xe.single.EOF(n_modes=N_MODES_TO_ROTATE)
eof_model.fit(grid_anomaly, dim="time", weights=weights)

print(f"Applying Varimax Rotation ({N_MODES_TO_ROTATE} modes)...")
# 2. Initialize the rotator and fit it to your base EOF model
rotator = xe.single.EOFRotator(n_modes=N_MODES_TO_ROTATE)
rotator.fit(eof_model)

# 3. Extract the rotated spatial patterns (loadings)
spatial_patterns = rotator.components()
spatial_mode = spatial_patterns.sel(mode=TARGET_MODE)

# =====================================================================
# 4. BASIN DETECTION & ISOLATION (THRESHOLDING)
# =====================================================================
print(f"Isolating basin grid cells for Mode {TARGET_MODE}...")
# Isolate grid cells with strong regional correlation (1.5 standard deviations)
threshold = float(spatial_mode.std() * 1.5)
basin_mask = xr.where(np.abs(spatial_mode) > threshold, 1, np.nan)

# =====================================================================
# 5. EXPORT BASIN TO GIS SHAPEFILE
# =====================================================================
print("Converting raster basin grid to a GIS Vector Shapefile...")
try:
    # Ensure spatial coordinate metadata is written properly for rasterio
    import rioxarray
    grid_anomaly.rio.write_crs("EPSG:4326", inplace=True)
    
    # Prep mask for polygonization
    mask_filled = basin_mask.fillna(0).astype(np.int32)
    shapes = features.shapes(mask_filled.values, transform=grid_anomaly.rio.transform())
    
    # Filter out the background (0) and keep the basin polygon (1)
    basin_polygons = [shape(geom) for geom, val in shapes if val == 1]
    
    if basin_polygons:
        gdf = gpd.GeoDataFrame(geometry=basin_polygons, crs="EPSG:4326")
        gdf.to_file(OUTPUT_SHAPEFILE)
        print(f"Successfully exported vector basin to: {OUTPUT_SHAPEFILE}")
    else:
        print("Warning: No distinct basin polygon met the threshold criteria.")
except ImportError:
    print("Skipping Shapefile export. Install 'rioxarray' and 'geopandas' to enable it.")

# =====================================================================
# 6. MAP PLOTTING & VISUALIZATION
# =====================================================================
print("Generating map visualization...")
fig = plt.figure(figsize=(12, 7))
ax = plt.axes(projection=ccrs.PlateCarree())

# Add global map features for spatial context
ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black')
ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5, edgecolor='gray')
ax.add_feature(cfeature.LAND, facecolor='#f9f9f9')

# Plot the underlying REOF loading values (continuous correlation field)
vmax = float(np.abs(spatial_mode).max())
im = spatial_mode.plot(
    ax=ax, transform=ccrs.PlateCarree(),
    cmap='RdBu', vmin=-vmax, vmax=vmax,
    cbar_kwargs={'label': 'REOF Loading (Spatial Correlation Strength)', 'shrink': 0.7},
    alpha=0.75
)

# Overlay the hard black outline representing your new basin boundary
basin_mask.plot.contour(
    ax=ax, transform=ccrs.PlateCarree(),
    colors='black', linewidths=2.5, levels=[0.5]
)

# Text overlays
ax.set_title(f"Data-Driven Basin Detection via GRACE REOF\nIsolated Mode {TARGET_MODE}", fontsize=14, pad=15)
ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, alpha=0.3)

# Save and Show
plt.savefig(OUTPUT_PLOT, dpi=300, bbox_inches='tight')
print(f"Saved plot successfully to: {OUTPUT_PLOT}")
plt.show()

import os

# Create an output folder so your workspace stays clean
output_dir = "grace_basins_output/deseasonalized"
os.makedirs(output_dir, exist_ok=True)

# Loop through every mode calculated by the rotator
# (If n_modes=10, this will loop from 1 to 10)
for mode_id in spatial_patterns.coords['mode'].values:
    print(f"Processing Mode {mode_id}...")
    
    # 1. Isolate the specific mode
    spatial_mode = spatial_patterns.sel(mode=mode_id)
    
    # 2. Isolate basin grid cells (using a relative threshold per mode)
    threshold = float(spatial_mode.std() * 1.5)
    basin_mask = xr.where(np.abs(spatial_mode) > threshold, 1, np.nan)
    
    # 3. Setup Plot
    fig = plt.figure(figsize=(12, 7))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black')
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5, edgecolor='gray')
    ax.add_feature(cfeature.LAND, facecolor='#f9f9f9')
    
    # Plot continuous correlation field
    vmax = float(np.abs(spatial_mode).max())
    spatial_mode.plot(
        ax=ax, transform=ccrs.PlateCarree(),
        cmap='RdBu', vmin=-vmax, vmax=vmax,
        cbar_kwargs={'label': 'REOF Loading', 'shrink': 0.7},
        alpha=0.75
    )
    
    # Overlay outline boundary
    try:
        basin_mask.plot.contour(
            ax=ax, transform=ccrs.PlateCarree(),
            colors='black', linewidths=2.5, levels=[0.5]
        )
    except Exception:
        # Pass if a mode is completely flat/noise and contouring fails
        pass
        
    ax.set_title(f"Data-Driven Basin Detection: Mode {mode_id}", fontsize=14, pad=15)
    
    # 4. Save file unique to this mode
    plot_filepath = os.path.join(output_dir, f"basin_mode_{mode_id}.png")
    plt.savefig(plot_filepath, dpi=200, bbox_inches='tight')
    plt.close() # Crucial to close the figure to save system memory!

print(f"All modes processed! Check the '{output_dir}' directory for your maps.")