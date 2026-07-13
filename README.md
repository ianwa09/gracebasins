# GRACE Basin Detection

This repository contains Python scripts and generated outputs for identifying
hydrologic basin-like regions from GRACE/GRACE-FO liquid water equivalent
thickness data.

The core workflow uses rotated empirical orthogonal functions (REOFs) on GRACE
water-storage anomaly grids. Spatial REOF loadings are thresholded to isolate
strong coherent regions, then exported as maps, shapefiles, `.xyz` masks, and
CSV mask files.

## Data

Primary input:

- `grace_data.nc` - CSR GRACE/GRACE-FO mascon NetCDF data.
- `Africa.xyz` - gridded Africa mask used by the Africa workflows.
- `Asia.xyz` - gridded Asia mask used by the Asia workflows.

The NetCDF workflow expects the variable:

```text
lwe_thickness
```

Several generated outputs are already present in the repository, including
PNG maps, shapefiles, `.xyz` masks, and converted CSV mask files.

## Main Scripts

### `reofs.py`

Runs a global/deseasonalized REOF workflow:

- loads `grace_data.nc`
- converts GRACE time values to datetimes
- removes the monthly seasonal cycle
- computes 10 EOF modes and applies varimax rotation
- thresholds a target mode into a basin mask
- exports `grace_reof_basins.shp`
- saves basin mode plots under `grace_basins_output/deseasonalized`

### `reofs2.py`

Runs an Africa-focused, deseasonalized REOF workflow:

- applies `Africa.xyz` as a regional mask
- removes monthly climatology
- computes 5 rotated EOF modes
- saves mode plots under `africa_output`

### `reofs3.py`

Runs an Asia-focused REOF workflow without deseasonalizing:

- applies `Asia.xyz` as a regional mask
- computes 5 rotated EOF modes
- saves mode plots under `asia_output/seasons`

### `reofs4.py`

The most complete Africa workflow:

- applies `Africa.xyz`
- removes the seasonal cycle
- computes 5 rotated EOF modes
- thresholds each mode into basin-like grid cells
- exports shapefiles when GIS dependencies are installed
- saves maps under `africa_output`

### `toxyz.py`

Converts a selected basin shapefile back onto the GRACE grid as a binary
space-separated `.xyz` mask.

### `splitdata.py`

Splits disconnected polygons from a selected basin mode shapefile into
individual sub-basin `.xyz` files.

### `xyztocsv.py`

Converts `.xyz` masks into CSV mask files using the naming pattern:

```text
HyBas_<id>_<basin_name>_Lev3_quartdeg.mask.csv
```

### `viewdata.py` and `viewdata2.py`

Render verification plots from exported shapefiles. `viewdata.py` checks one
mode; `viewdata2.py` loops through modes 1-5.

### `ian_basins.ipynb`

An exploratory notebook that uses a correlation/community-detection approach
over GRACE anomalies. It appears to predate or complement the REOF scripts.

## Outputs

Common generated output locations:

- `grace_basins_output/`
- `africa_output/`
- `asia_output/`
- `visuals/`

Output types include:

- `.png` map visualizations
- ESRI shapefile components: `.shp`, `.shx`, `.dbf`, `.prj`, `.cpg`
- `.xyz` binary masks
- `.mask.csv` converted mask files

## Dependencies

The scripts use:

- `numpy`
- `pandas`
- `xarray`
- `xeofs`
- `matplotlib`
- `cartopy`
- `geopandas`
- `rioxarray`
- `rasterio`
- `shapely`

Example install command:

```bash
pip install numpy pandas xarray xeofs matplotlib cartopy geopandas rioxarray rasterio shapely netCDF4
```

GIS packages such as `cartopy`, `geopandas`, and `rasterio` may require system
libraries depending on the Python environment.

## Typical Workflow

1. Place the GRACE NetCDF file at `grace_data.nc`.
2. Place the regional mask file at `Africa.xyz` or `Asia.xyz`.
3. Edit the configuration constants at the top of the target script.
4. Run the REOF script:

```bash
python reofs4.py
```

5. Optionally convert or split exported basin shapefiles:

```bash
python toxyz.py
python splitdata.py
python xyztocsv.py
```

6. Optionally generate verification plots:

```bash
python viewdata2.py
```

## Notes

- The scripts are configured through constants at the top of each file rather
  than command-line arguments.
- Most scripts assume they are run from the repository root.
- Thresholding currently uses `1.5 * standard deviation` of each spatial mode.
- Latitude weighting uses the square root of cosine latitude.
- Some folders contain generated artifacts rather than source code.

