from __future__ import annotations

import streamlit as st

from modules.comparison import render_comparison_dashboard
from modules.data_loader import (
	dataset_year_bounds,
	variables_with_lat_lon,
	variables_with_time_dim,
)
from modules.global_map import show_global_map
from modules.hotspots import show_hotspots
from modules.time_series import render_time_series_dashboard
from modules.ui_helpers import (
	inject_custom_css,
	prepare_dataset,
	render_dataset_summary,
)


def main() -> None:
	st.set_page_config(page_title="PyClimaExplorer", layout="wide")
	inject_custom_css()

	st.title("PyClimaExplorer - Climate Analytics Dashboard")
	st.caption("Interactive NetCDF analytics with model/observation comparison, trends, and hotspots.")

	st.sidebar.header("Controls")
	dataset_choice = st.sidebar.radio("Primary dataset", ["Sample dataset", "Upload dataset"], index=0)
	uploaded_main = st.sidebar.file_uploader("Upload NetCDF or .tar", type=["nc", "tar", "tgz", "gz"])

	try:
		ds_label, ds = prepare_dataset(dataset_choice, uploaded_main)
	except Exception as exc:
		st.error(f"Failed to load dataset: {exc}")
		st.stop()

	analysis_mode = st.sidebar.selectbox(
		"Analysis mode",
		[
			"Model vs Observation Comparison",
			"Global Climate Map",
			"Time Series Trend",
			"Climate Hotspots",
		],
	)

	render_dataset_summary(ds_label, ds)

	if analysis_mode == "Model vs Observation Comparison":
		try:
			render_comparison_dashboard(ds)
		except Exception as exc:
			st.error(f"Unable to build comparison dashboard: {exc}")
		return

	if analysis_mode == "Global Climate Map":
		variables = variables_with_lat_lon(ds)
		if not variables:
			st.error("No variables with lat/lon dimensions are available for mapping.")
			return
		variable = st.sidebar.selectbox("Variable", variables)
		min_year, max_year = dataset_year_bounds(ds)
		if min_year == max_year:
			year = min_year
			st.sidebar.info(f"Single year detected: {year}")
		else:
			year_default = min(max_year, max(min_year, 2000))
			year = st.sidebar.slider("Year", min_year, max_year, value=year_default)
		try:
			fig = show_global_map(ds, variable, year)
			st.plotly_chart(fig, use_container_width=True)
		except Exception as exc:
			st.error(f"Unable to render map: {exc}")
		return

	if analysis_mode == "Time Series Trend":
		try:
			render_time_series_dashboard(ds)
		except Exception as exc:
			st.error(f"Unable to build time series dashboard: {exc}")
		return

	if analysis_mode == "Climate Hotspots":
		spatial_vars = variables_with_lat_lon(ds)
		temporal_vars = set(variables_with_time_dim(ds))
		variables = [v for v in spatial_vars if v in temporal_vars]
		if not variables:
			st.error("No variables with both spatial and temporal dimensions are available for hotspots.")
			return
		variable = st.sidebar.selectbox("Variable", variables)
		min_year, max_year = dataset_year_bounds(ds)
		if min_year == max_year:
			st.sidebar.info("Single-year dataset; hotspot periods collapse to the available year.")
			baseline_years = (min_year, max_year)
			recent_years = (min_year, max_year)
		else:
			baseline_start = max(min_year, min(max_year, 1950))
			baseline_end = max(baseline_start + 1, min(max_year, 1970))
			recent_start = max(min_year, min(max_year, 2000))
			recent_end = max(recent_start + 1, max_year)
			baseline_years = st.sidebar.slider(
				"Baseline period",
				min_year,
				max_year,
				value=(baseline_start, baseline_end) if baseline_start < baseline_end else (min_year, max_year),
			)
			recent_years = st.sidebar.slider(
				"Recent period",
				min_year,
				max_year,
				value=(recent_start, recent_end) if recent_start < recent_end else (min_year, max_year),
			)
		try:
			fig, table_df = show_hotspots(ds, variable, baseline_years, recent_years)
			st.plotly_chart(fig, use_container_width=True)
			if table_df is not None:
				st.subheader("Top warming regions")
				st.dataframe(table_df, use_container_width=True)
		except Exception as exc:
			st.error(f"Unable to detect hotspots: {exc}")
		return


if __name__ == "__main__":
	main()
