#!/usr/bin/env python3
"""
GRACE Basin Identification via Rotated EOFs (Masked Batch Generation)
Date: 2026
"""

import os
import numpy as np
import xarray as xr
import pandas as pd
import xeofs as xe
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# =====================================================================
# 1. CONFIGURATION & FILE PATHS
# =====================================================================
INPUT_NETCDF = "grace_data.nc"          # Path to your GRACE dataset
VARIABLE_NAME = "lwe_thickness"         # Variable name (Liquid Water Equivalent)
MASK_XYZ_FILE = "Africa.xyz"         # Path to your .XYZ mask file
N_MODES_TO_ROTATE = 5                   # Total number of modes to calculate
OUTPUT_DIR = "africa_output"            # Folder where all maps will be saved

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =====================================================================
# 2. DATA LOADING & MASK PREPROCESSING
# =====================================================================
print("Loading GRACE data...")
if not os.path.exists(INPUT_NETCDF):
    raise FileNotFoundError(f"Please place your GRACE file at: {INPUT_NETCDF}")

ds = xr.open_dataset(INPUT_NETCDF)
ds['time'] = pd.to_datetime(ds.time.values, unit='D', origin='2002-01-01')

grid_anomaly = ds[VARIABLE_NAME]
grid_anomaly = grid_anomaly.load()
print("Deseasonalizing data (removing seasonal cycle)...")
monthly_climatology = grid_anomaly.groupby("time.month").mean("time")
grid_anomaly = grid_anomaly.groupby("time.month") - monthly_climatology

print(f"Loading and building mask from {MASK_XYZ_FILE}...")
if not os.path.exists(MASK_XYZ_FILE):
    raise FileNotFoundError(f"Please place your mask file at: {MASK_XYZ_FILE}")

# Load tabular XYZ data
df_mask = pd.read_csv(MASK_XYZ_FILE, sep=r'\s+', names=['lon', 'lat', 'value'], header=None)
df_mask = df_mask.set_index(['lat', 'lon'])
mask_da = df_mask['value'].to_xarray()

# Interp/reindex the mask grid so it matches your GRACE grid exactly
mask_da = mask_da.reindex_like(grid_anomaly, method='nearest')

# Apply boundary mask to GRACE data (values outside mask become NaN)
print("Applying boundary mask to GRACE data...")
grid_anomaly = grid_anomaly.where(mask_da > 0)

# FIX: Find true geographic boundaries of just the valid unmasked cells
valid_coords = grid_anomaly.dropna(dim='lon', how='all').dropna(dim='lat', how='all')
lon_min, lon_max = float(valid_coords.lon.min()), float(valid_coords.lon.max())
lat_min, lat_max = float(valid_coords.lat.min()), float(valid_coords.lat.max())

# Calculate cosine latitude weights to account for earth's curvature
weights = np.sqrt(np.cos(np.deg2rad(grid_anomaly.lat)))

# =====================================================================
# 3. ROTATED EOF (REOF) ANALYSIS
# =====================================================================
print("Running Base EOF analysis on the masked region...")
eof_model = xe.single.EOF(n_modes=N_MODES_TO_ROTATE)
eof_model.fit(grid_anomaly, dim="time", weights=weights)

print(f"Applying Varimax Rotation ({N_MODES_TO_ROTATE} modes)...")
rotator = xe.single.EOFRotator(n_modes=N_MODES_TO_ROTATE)
rotator.fit(eof_model)

# Extract all spatial patterns (loadings)
spatial_patterns = rotator.components()




# =====================================================================
# 4. BATCH ITERATION LOOP (PLOT & SAVE ALL MODES)
# =====================================================================
print(f"Iterating through all {N_MODES_TO_ROTATE} modes...")

mode_ids = spatial_patterns.coords['mode'].values

for mode_id in mode_ids:
    print(f" -> Generating map for Mode {mode_id}...")
    
    # Isolate the specific mode loading
    spatial_mode = spatial_patterns.sel(mode=mode_id)
    
    # Isolate basin grid cells (using a relative threshold per mode)
    threshold = float(spatial_mode.std() * 1.5)
    basin_mask = xr.where(np.abs(spatial_mode) > threshold, 1, np.nan)
    
    # -----------------------------------------------------------------
    # DIAGNOSTIC MODULE
    # -----------------------------------------------------------------
    valid_cells_count = int(np.nansum(basin_mask == 1))
    total_masked_cells = int(np.sum(~np.isnan(spatial_mode.values)))
    
    if valid_cells_count == 0:
        print(f"      [Warning - Mode {mode_id}]: The threshold ({threshold:.5f}) is TOO HIGH.")
        print(f"           No grid cells passed. Max loading value in this region is only {float(np.abs(spatial_mode).max()):.5f}.")
    else:
        pct = (valid_cells_count / total_masked_cells) * 100
        print(f"      [Success - Mode {mode_id}]: {valid_cells_count} cells passed ({pct:.1f}% of masked area).")
    # -----------------------------------------------------------------

    # Setup Map Plot using Cartopy
    fig = plt.figure(figsize=(12, 7))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Map features
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black')
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5, edgecolor='gray')
    ax.add_feature(cfeature.LAND, facecolor='#f9f9f9')
    
    # Zoom the map dynamically to your calculated boundaries with a 3-degree buffer
    ax.set_extent([lon_min - 3, lon_max + 3, lat_min - 3, lat_max + 3], crs=ccrs.PlateCarree())
    
    # Plot continuous correlation field
    vmax = float(np.abs(spatial_mode).max())
    spatial_mode.plot(
        ax=ax, transform=ccrs.PlateCarree(),
        cmap='RdBu', vmin=-vmax, vmax=vmax,
        cbar_kwargs={'label': 'REOF Loading (Spatial Correlation Strength)', 'shrink': 0.7},
        alpha=0.75
    )
    
    # Overlay outline boundary
    try:
        basin_mask.plot.contour(
            ax=ax, transform=ccrs.PlateCarree(),
            colors='black', linewidths=2.5, levels=[0.5]
        )
    except Exception:
        pass
        
    ax.set_title(f"Regional Data-Driven Basin Detection: Mode {mode_id}", fontsize=14, pad=15)
    ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, alpha=0.3)
    
    # Save file unique to this mode and close plot to free RAM
    plot_filepath = os.path.join(OUTPUT_DIR, f"basin_mode_{mode_id}.png")
    plt.savefig(plot_filepath, dpi=200, bbox_inches='tight')
    plt.close(fig) 

print(f"\nExecution Complete! All maps are saved inside the '{OUTPUT_DIR}' folder.")