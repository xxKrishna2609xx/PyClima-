"""UI helpers and dataset preparation functions for PyClimaExplorer."""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st
import xarray as xr

from .data_loader import load_dataset, summarize_dataset


SAMPLE_DATA_PATH = Path("datasets/sample.nc")


def inject_custom_css() -> None:
	st.markdown(
		"""
		<style>
			.stApp {
				background: radial-gradient(circle at top left, #0d1b2a 0%, #0a101f 45%, #070b14 100%);
				color: #e7ecf3;
			}
			section.main > div {
				padding-top: 0.8rem;
			}
			div.block-container {
				padding-top: 0.9rem;
				padding-right: 1.4rem;
				padding-left: 1.4rem;
				padding-bottom: 1.2rem;
				max-width: 100%;
			}
			section[data-testid="stSidebar"] {
				background: linear-gradient(180deg, rgba(9, 20, 36, 0.94) 0%, rgba(6, 13, 24, 0.92) 100%);
				border-right: 1px solid rgba(120, 145, 170, 0.2);
			}
			[data-testid="stMetric"] {
				background: rgba(14, 26, 43, 0.7);
				border: 1px solid rgba(88, 115, 145, 0.32);
				border-radius: 12px;
				padding: 0.55rem 0.75rem;
			}
			[data-testid="stMetricLabel"] {
				color: #9fb3c8;
			}
			[data-testid="stMetricValue"] {
				color: #f3f7fb;
			}
		</style>
		""",
		unsafe_allow_html=True,
	)


def preferred_local_dataset() -> tuple[str | None, Path | None]:
	if SAMPLE_DATA_PATH.exists():
		return SAMPLE_DATA_PATH.name, SAMPLE_DATA_PATH
	# Sort so the first file is always the same regardless of filesystem ordering
	alt_files = sorted(Path("datasets").glob("*.nc"))
	if alt_files:
		path = alt_files[0]
		return path.name, path
	return (None, None)


def prepare_dataset(source_choice: str, uploaded_file) -> tuple[str, xr.Dataset]:
	if source_choice == "Sample dataset":
		label, path = preferred_local_dataset()
		if path is None:
			st.error("No sample dataset found in the datasets folder. Please upload a NetCDF file.")
			st.stop()
		ds = load_dataset(path)
		return str(label), ds

	if uploaded_file is None:
		st.info("Upload a NetCDF (.nc) file or a .tar containing NetCDF data to begin.")
		st.stop()

	content = uploaded_file.read()
	ds = load_dataset(content)
	return uploaded_file.name, ds


def load_optional_dataset(title: str, fallback_ds: xr.Dataset, uploader_key: str) -> tuple[xr.Dataset, str]:
	st.sidebar.markdown(f"**{title}**")
	source_choice = st.sidebar.radio("Source", ["Use primary dataset", "Upload"], key=f"{uploader_key}_source")
	if source_choice == "Use primary dataset":
		return fallback_ds, "Primary"

	uploaded = st.sidebar.file_uploader("Upload NetCDF or .tar", type=["nc", "tar", "tgz", "gz"], key=uploader_key)
	if uploaded is None:
		st.warning(f"Please upload a file for {title.lower()}.")
		st.stop()

	return load_dataset(uploaded.read()), uploaded.name


def render_dataset_summary(ds_label: str, ds: xr.Dataset) -> None:
	summary = summarize_dataset(ds)
	with st.expander(f"Dataset summary - {ds_label}"):
		st.write("Dimensions", summary["dimensions"])
		st.write("Coordinates", summary["coords"])
		st.write("Variables", summary["variables"])
		if summary["attributes"]:
			st.write("Attributes")
			st.json(summary["attributes"])


def variable_category(variable: str) -> str:
	name = variable.lower()
	if "tas" in name or "temp" in name:
		return "Temperature"
	if name.startswith("pr") or "precip" in name or "rain" in name:
		return "Precipitation"
	if "sst" in name or "sea_surface" in name:
		return "Sea Surface"
	if "wind" in name:
		return "Wind"
	if "humidity" in name or "rh" in name:
		return "Humidity"
	return "Climate"


def variable_label_map(variables: list[str]) -> dict[str, str]:
	label_map: dict[str, str] = {}
	existing_labels: set[str] = set()
	for var in variables:
		base = f"{variable_category(var)} - {var}"
		label = base
		i = 2
		while label in existing_labels:
			label = f"{base} ({i})"
			i += 1
		label_map[label] = var
		existing_labels.add(label)
	return label_map


def intersect_bounds(primary_bounds: tuple[float, float], secondary_bounds: tuple[float, float]) -> tuple[float, float]:
	p_min, p_max = sorted(primary_bounds)
	s_min, s_max = sorted(secondary_bounds)
	low = max(p_min, s_min)
	high = min(p_max, s_max)
	if low >= high:
		return (p_min, p_max)
	return (low, high)


def format_value(value: float, unit: str) -> str:
	if pd.isna(value):
		return "N/A"
	return f"{value:,.3f}{unit}"
