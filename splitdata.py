import os
import geopandas as gpd
import xarray as xr
from rasterio import features

# =====================================================================
# CONFIGURATION
# =====================================================================
TARGET_MODE = 2                         # The mode you want to split
OUTPUT_DIR = "africa_output/deseasonalized/datafiles"            # Folder where files live
INPUT_NETCDF = "grace_data.nc"          # Needed for the coordinate grid
VARIABLE_NAME = "lwe_thickness"

SHP_PATH = os.path.join(OUTPUT_DIR, f"basin_mode_{TARGET_MODE}.shp")

# =====================================================================
# PROCESSING & SPLITTING
# =====================================================================
print(f"Loading template coordinate grid...")
ds = xr.open_dataset(INPUT_NETCDF)
grid_template = ds[VARIABLE_NAME].isel(time=0)

print(f"Reading shapefile for Mode {TARGET_MODE}...")
gdf = gpd.read_file(SHP_PATH)

# Explode multi-part geometries into separate, individual single polygons
exploded_gdf = gdf.explode(index_parts=False).reset_index(drop=True)
num_individual_basins = len(exploded_gdf)

print(f"Found {num_individual_basins} disconnected individual basin(s) inside this mode.")

# Loop through every single disconnected basin
for index, row in exploded_gdf.iterrows():
    # Create a unique ID for this specific sub-basin (e.g., mode_8_basin_1)
    basin_id = index + 1
    xyz_output_path = os.path.join(OUTPUT_DIR, f"basin_mode_{TARGET_MODE}_sub_{basin_id}.xyz")
    
    print(f" -> Processing sub-basin {basin_id}/{num_individual_basins}...")
    
    # Rasterize ONLY this specific polygon
    shapes = [(row.geometry, 1)]
    print("Shapefile CRS:", gdf.crs)
    print("Shapefile bounds (minx, miny, maxx, maxy):", gdf.total_bounds)

    print("Grid lon range:", grid_template.lon.min().values, "to", grid_template.lon.max().values)
    print("Grid lat range:", grid_template.lat.min().values, "to", grid_template.lat.max().values)

    print("Grid transform:", grid_template.rio.transform())
    print("Grid CRS:", grid_template.rio.crs)
    rasterized_mask = features.rasterize(
        shapes,
        out_shape=grid_template.shape,
        transform=grid_template.rio.transform(),
        fill=0,
        default_value=1
    )
    
    # Rebuild into an Xarray DataArray
    da_mask = xr.DataArray(
        rasterized_mask, 
        coords=grid_template.coords, 
        dims=grid_template.dims
    )
    
    # Convert to tabular DataFrame [lon, lat, value]
    df_xyz = da_mask.to_dataframe(name="value").reset_index()
    df_xyz = df_xyz[['lon', 'lat', 'value']]
    
    # Save this specific sub-basin's XYZ file
    df_xyz.to_csv(xyz_output_path, sep=' ', header=False, index=False)
    print(f"    Saved: {xyz_output_path}")

print("\nAll sub-basins successfully isolated and exported to individual XYZ files!")