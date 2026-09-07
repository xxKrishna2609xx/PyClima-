<div align="center">

# 🌍 PyClimaExplorer

### _Interactive Climate Analytics Dashboard_

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.58-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-6.7-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![xarray](https://img.shields.io/badge/xarray-2025.6-00BFFF?style=for-the-badge)](https://xarray.pydata.org)
[![HackItOut](https://img.shields.io/badge/HackItOut-2026-FF6B35?style=for-the-badge)](https://github.com)

<br/>

> **Drop in a NetCDF file. Explore climate. No code needed.**
>
> PyClimaExplorer transforms raw NetCDF climate datasets into interactive
> spatial maps, time-series trends, model-vs-observation comparisons,
> and warming hotspot analyses — all through a beautiful dark-themed dashboard.

<br/>

</div>

---

## ✨ Features at a Glance

| Feature | Description |
|---|---|
| 🗺️ **Global Climate Map** | Visualise any spatial variable as an interactive lat/lon heatmap for any year in the dataset |
| 📈 **Time Series Trend** | Analyse temporal trends at any grid point with linear regression overlays |
| ⚖️ **Model vs Observation** | Compare two datasets side-by-side with difference shading and trend lines |
| 🔥 **Climate Hotspots** | Identify the top warming regions between any two time periods |
| 🧠 **Smart Coord Detection** | Auto-resolves `lat`, `latitude`, `nav_lat`, `TLAT`, `Y`, `X` — works with any NetCDF |
| 📁 **Flexible Input** | Upload `.nc` files directly, or use the bundled CESM/BEST sample datasets |
| ⚡ **Cached Loading** | Streamlit `@cache_resource` ensures datasets are loaded only once per session |

---

## 🏗️ Project Structure

```
PyClimaExplorer/
│
├── app.py                        # 🚀 Streamlit entry-point & mode router
│
├── modules/
│   ├── config.py                 # ⚙️  Central constants (colors, aliases, limits)
│   ├── data_loader.py            # 📦 NetCDF I/O, caching, coord helpers
│   ├── ui_helpers.py             # 🎨 CSS, sidebar widgets, variable labelling
│   ├── global_map.py             # 🗺️  Spatial field heatmap visualization
│   ├── time_series.py            # 📈 Time-series extraction, trend, dashboard
│   ├── comparison.py             # ⚖️  Model vs observation comparison dashboard
│   └── hotspots.py               # 🔥 Warming hotspot detection & leaderboard
│
├── datasets/                     # 🗄️  Place your NetCDF files here
│   └── *.nc                      # (CESM1/CESM2 ensembles + BEST observations)
│
└── requirements.txt              # 📋 Python dependencies
```

---

## ⚙️ Setup & Installation

### 1 · Prerequisites

- **Python 3.10 or higher**
- A terminal / PowerShell window

### 2 · Clone & create a virtual environment

```bash
# Clone the repository
git clone https://github.com/your-username/PyClimaExplorer.git
cd PyClimaExplorer
```

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3 · Install dependencies

```bash
pip install -r requirements.txt
```

### 4 · Launch the app

```bash
streamlit run app.py
```

Then open the local URL Streamlit prints — typically **http://localhost:8501** 🚀

---

## 🖥️ Analysis Modes

<details>
<summary><b>🗺️ Global Climate Map</b></summary>

1. Select a variable with `lat` and `lon` dimensions.
2. Drag the **Year** slider to a target year.
3. The dashboard renders a full global heatmap using `RdBu_r` colorscale.
4. Hover over any grid point for exact coordinate and value.

</details>

<details>
<summary><b>📈 Time Series Trend</b></summary>

1. Pick any variable with a time dimension.
2. Set the **Latitude** and **Longitude** sliders to your point of interest.
3. Toggle **Show trend line** for a linear regression overlay.
4. Use the **Reference year** slider to see year-on-year delta metrics.
5. Expand **Time series values preview** for a scrollable data table.

</details>

<details>
<summary><b>⚖️ Model vs Observation Comparison</b></summary>

1. Optionally upload a second NetCDF for the observed dataset (or reuse the primary).
2. Select **Model variable** and **Observed variable** independently.
3. The difference between the two series is shaded in yellow.
4. Toggle trend lines for both series simultaneously.
5. Stats panel shows model mean, observed mean, difference mean, min, max, and a reference-year delta metric.

</details>

<details>
<summary><b>🔥 Climate Hotspots</b></summary>

1. Select a variable with both `lat/lon` and a time dimension.
2. Set the **Baseline period** (e.g. early decades of the dataset).
3. Set the **Recent period** (e.g. last decades of the dataset).
4. The dashboard computes Δ = Recent Mean − Baseline Mean on every grid point.
5. A ranked **Top Warming Regions** leaderboard table is shown below the map.

</details>

---

## 📦 Datasets

The `datasets/` folder bundles a large collection of NetCDF climate files:

| Collection | Files | Period |
|---|---|---|
| **CESM1-LENS** | Ensemble members 001–035, 101–105, EM | 1950–2024 |
| **CESM2-LENS** | Ensemble members 1001–1021 | 1850–2100 |
| **CESM1 Forced Ocean** | 3 simulations | 1950–2015 |
| **BEST** | Berkeley Earth Surface Temperature | 1950–2023 |

> **Tip:** The app auto-loads `datasets/sample.nc` if it exists, otherwise it picks the first `.nc` file alphabetically. You can always upload any `.nc` file directly through the sidebar.

---

## 🔧 Configuration

All tuneable constants live in **[`modules/config.py`](modules/config.py)** — no need to hunt through the codebase:

```python
# Colorscales
GLOBAL_MAP_COLORSCALE = "RdBu_r"    # change to "Viridis", "Plasma", etc.
HOTSPOT_COLORSCALE    = "Turbo"

# Chart colors
SERIES_LINE_COLOR   = "#4FC3F7"
OBSERVED_LINE_COLOR = "#FF8A65"
TREND_LINE_COLOR    = "#FFC1A6"

# Display limits
HOTSPOT_TABLE_TOP_N = 10    # rows in warming leaderboard
PREVIEW_TABLE_ROWS  = 25    # rows in data preview expanders

# Spatial coordinate aliases (extend to support custom NetCDF conventions)
LAT_ALIASES = ("lat", "latitude", "nav_lat", "TLAT", "y", "Y", ...)
LON_ALIASES = ("lon", "longitude", "nav_lon", "TLONG", "x", "X", ...)
```

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| `h5netcdf` / `h5py` import error | Run `pip install -r requirements.txt` to ensure backends are installed |
| _No time coordinate found_ | Your variable must have a time-like dim (`time`, `date`, `datetime`). Use **Time Series** or **Hotspots** only on such variables |
| _No lat/lon dims_ | **Global Map** and **Hotspots** require spatial variables. Check `config.LAT_ALIASES` and add your coord name if needed |
| Cache stale after file edit | Touch the dataset file or restart Streamlit to invalidate `@cache_resource` |
| Wrong default variable | Edit `PREFERRED_VARIABLES` in `config.py` to match your dataset's naming convention |

---

## 🧰 Tech Stack

| Library | Role |
|---|---|
| [Streamlit](https://streamlit.io) | Dashboard framework & reactive UI |
| [xarray](https://xarray.pydata.org) | NetCDF reading, CF decoding, array operations |
| [Plotly](https://plotly.com/python) | Interactive charts, heatmaps, scatter traces |
| [pandas](https://pandas.pydata.org) | Time-series indexing, alignment, DataFrames |
| [NumPy](https://numpy.org) | Numerical operations, trend fitting |
| [netcdf4](https://unidata.github.io/netcdf4-python) | NetCDF backend |
| [h5netcdf](https://github.com/h5netcdf/h5netcdf) | HDF5-backed NetCDF fallback |
| [cftime](https://unidata.github.io/cftime) | CF-compliant calendar time decoding |

---

## 🙏 Acknowledgements

- Built for the **HackItOut 2026** hackathon.
- Climate datasets courtesy of the **CESM Large Ensemble Community Project** and **Berkeley Earth (BEST)**.
- Inspired by the need to make climate diagnostics fast, visual, and accessible — without writing code.

---

<div align="center">

Made with ❤️ and ☕ &nbsp;|&nbsp; PyClimaExplorer © 2026

</div>
