"""Central configuration constants for PyClimaExplorer.

All magic numbers, path literals, color values, and display limits live here.
Import from this module instead of scattering literals across the codebase.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Dataset paths
# ---------------------------------------------------------------------------

SAMPLE_DATA_PATH: Path = Path("datasets/sample.nc")

# ---------------------------------------------------------------------------
# Spatial coordinate alias lists (ordered by priority)
# Datasets from different climate modelling centres use different names.
# ---------------------------------------------------------------------------

LAT_ALIASES: tuple[str, ...] = (
    "lat",
    "latitude",
    "nav_lat",
    "TLAT",
    "lat_rho",
    "y",
    "Y",
    "south_north",
    "rlat",
    "nlat",
)

LON_ALIASES: tuple[str, ...] = (
    "lon",
    "longitude",
    "nav_lon",
    "TLONG",
    "lon_rho",
    "x",
    "X",
    "west_east",
    "rlon",
    "nlon",
)

# ---------------------------------------------------------------------------
# Variable category heuristics (ordered substring lists per category)
# Add new categories or substrings here without touching other modules.
# ---------------------------------------------------------------------------

VARIABLE_CATEGORIES: dict[str, list[str]] = {
    "Temperature": ["tas", "temp", "tmax", "tmin", "t2m", "air_temp"],
    "Precipitation": ["pr", "precip", "rain", "prate", "prcp"],
    "Sea Surface": ["sst", "sea_surface", "tos"],
    "Wind": ["wind", "ua", "va", "uas", "vas", "sfcwind"],
    "Humidity": ["humidity", "hus", "rh", "hurs"],
    "Pressure": ["psl", "ps", "msl", "pressure"],
    "Sea Ice": ["sic", "siconc", "sea_ice"],
    "Radiation": ["rsds", "rlds", "rsus", "rlus", "rad"],
}

# Ranked list: first match found in dataset variables becomes the default selection.
PREFERRED_VARIABLES: list[str] = [
    "tas_global_avg_ann",
    "tas_global_avg",
    "tas",
    "temp",
    "tmax",
    "tmin",
    "sst",
    "pr",
]

# ---------------------------------------------------------------------------
# Colorscales
# ---------------------------------------------------------------------------

GLOBAL_MAP_COLORSCALE: str = "RdBu_r"
HOTSPOT_COLORSCALE: str = "Turbo"

# ---------------------------------------------------------------------------
# Chart colors (Plotly hex strings)
# ---------------------------------------------------------------------------

SERIES_LINE_COLOR: str = "#4FC3F7"      # Model / primary time series
OBSERVED_LINE_COLOR: str = "#FF8A65"    # Observed / secondary time series
TREND_LINE_COLOR: str = "#FFC1A6"       # Trend overlay
MODEL_TREND_COLOR: str = "#7FDBFF"      # Model trend in comparison view
DIFF_FILL_COLOR: str = "rgba(255, 193, 7, 0.17)"  # Difference shading fill

# ---------------------------------------------------------------------------
# Table / display limits
# ---------------------------------------------------------------------------

HOTSPOT_TABLE_TOP_N: int = 10    # Rows shown in the warming-regions leaderboard
PREVIEW_TABLE_ROWS: int = 25     # Rows shown in data preview expanders
