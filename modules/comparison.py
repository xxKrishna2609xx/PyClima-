"""Model vs Observation comparison module for PyClimaExplorer."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import xarray as xr

from .data_loader import (
	dataset_lat_bounds,
	dataset_lon_bounds,
	time_coord_candidates,
	variables_with_time_dim,
)
from .time_series import compute_trend, extract_series
from .ui_helpers import (
	format_value,
	intersect_bounds,
	load_optional_dataset,
	variable_label_map,
)


def align_series(model_series: pd.Series, obs_series: pd.Series) -> pd.DataFrame:
	"""Inner join model and observed time series on matching dates and calculate difference."""
	df = pd.concat(
		[
			model_series.rename("Model"),
			obs_series.rename("Observed"),
		],
		axis=1,
		join="inner",
	).dropna()
	if df.empty:
		raise ValueError("No overlapping timestamps between model and observed series")
	df["Difference"] = df["Model"] - df["Observed"]
	return df.sort_index()


def reference_year_difference(df: pd.DataFrame, year: int) -> float:
	"""Calculate mean model vs observation difference for a specific reference year."""
	values = df.loc[df.index.year == year, "Difference"]
	if values.empty:
		return float("nan")
	return float(values.mean())


def build_comparison_figure(
	df: pd.DataFrame,
	model_variable: str,
	obs_variable: str,
	lat: float,
	lon: float,
	show_trend: bool,
) -> go.Figure:
	"""Construct Plotly comparison figure with difference shading and optional trendlines."""
	fig = go.Figure()

	fig.add_trace(
		go.Scatter(
			x=df.index,
			y=df["Model"],
			name="Model",
			mode="lines+markers",
			line={"color": "#4FC3F7", "width": 2.7, "shape": "spline", "smoothing": 0.8},
			marker={"size": 5},
			hovertemplate="Time: %{x|%Y-%m-%d}<br>Model: %{y:.3f}<extra></extra>",
		)
	)

	fig.add_trace(
		go.Scatter(
			x=df.index,
			y=df["Observed"],
			name="Observed",
			mode="lines+markers",
			line={"color": "#FF8A65", "width": 2.7, "shape": "spline", "smoothing": 0.8},
			marker={"size": 5},
			hovertemplate="Time: %{x|%Y-%m-%d}<br>Observed: %{y:.3f}<extra></extra>",
		)
	)

	lower = np.minimum(df["Model"].values, df["Observed"].values)
	upper = np.maximum(df["Model"].values, df["Observed"].values)

	fig.add_trace(
		go.Scatter(
			x=df.index,
			y=lower,
			name="Difference lower",
			mode="lines",
			line={"width": 0},
			showlegend=False,
			hoverinfo="skip",
		)
	)

	fig.add_trace(
		go.Scatter(
			x=df.index,
			y=upper,
			name="Difference (Model - Observed)",
			mode="lines",
			line={"width": 0},
			fill="tonexty",
			fillcolor="rgba(255, 193, 7, 0.17)",
			customdata=df["Difference"],
			hovertemplate="Time: %{x|%Y-%m-%d}<br>Model - Observed: %{customdata:.3f}<extra></extra>",
		)
	)

	if show_trend:
		model_trend = compute_trend(df["Model"])
		obs_trend = compute_trend(df["Observed"])
		fig.add_trace(
			go.Scatter(
				x=df.index,
				y=model_trend,
				name="Model trend",
				mode="lines",
				line={"color": "#7FDBFF", "dash": "dash", "width": 2},
				hovertemplate="Time: %{x|%Y-%m-%d}<br>Model trend: %{y:.3f}<extra></extra>",
			)
		)
		fig.add_trace(
			go.Scatter(
				x=df.index,
				y=obs_trend,
				name="Observed trend",
				mode="lines",
				line={"color": "#FFC1A6", "dash": "dash", "width": 2},
				hovertemplate="Time: %{x|%Y-%m-%d}<br>Observed trend: %{y:.3f}<extra></extra>",
			)
		)

	trace_count = len(fig.data)

	def _visibility(show_model: bool, show_observed: bool) -> list[bool]:
		visible = [False] * trace_count
		visible[0] = show_model
		visible[1] = show_observed
		visible[2] = show_model and show_observed
		visible[3] = show_model and show_observed
		if show_trend:
			visible[4] = show_model
			visible[5] = show_observed
		return visible

	fig.update_layout(
		template="plotly_dark",
		height=660,
		hovermode="x unified",
		title={
			"text": f"Model ({model_variable}) vs Observed ({obs_variable}) @ lat {lat:.2f}, lon {lon:.2f}",
			"x": 0.01,
			"xanchor": "left",
		},
		xaxis={
			"title": "Time",
			"showgrid": True,
			"gridcolor": "rgba(170, 185, 205, 0.15)",
			"rangeslider": {"visible": True},
			"showspikes": True,
			"spikemode": "across",
			"spikecolor": "#9ec5ff",
		},
		yaxis={
			"title": model_variable if model_variable == obs_variable else "Value",
			"showgrid": True,
			"gridcolor": "rgba(170, 185, 205, 0.15)",
			"zeroline": False,
		},
		legend={
			"orientation": "h",
			"yanchor": "bottom",
			"y": 1.02,
			"xanchor": "left",
			"x": 0.01,
		},
		margin={"l": 30, "r": 20, "t": 75, "b": 20},
		updatemenus=[
			{
				"type": "buttons",
				"direction": "right",
				"x": 0.01,
				"y": 1.2,
				"showactive": True,
				"buttons": [
					{"label": "Both", "method": "update", "args": [{"visible": _visibility(True, True)}]},
					{"label": "Model", "method": "update", "args": [{"visible": _visibility(True, False)}]},
					{"label": "Observed", "method": "update", "args": [{"visible": _visibility(False, True)}]},
				],
			}
		],
	)

	return fig


def render_comparison_dashboard(primary_ds: xr.Dataset) -> None:
	"""Render the Streamlit dashboard UI for model vs observation comparison mode."""
	model_ds, model_label = load_optional_dataset("Model dataset", primary_ds, "model_upload")
	obs_ds, obs_label = load_optional_dataset("Observed dataset", primary_ds, "obs_upload")

	model_vars = variables_with_time_dim(model_ds)
	obs_vars = variables_with_time_dim(obs_ds)
	if not model_vars or not obs_vars:
		st.error("Model and observed datasets must both include at least one time-based variable.")
		st.stop()

	model_label_map = variable_label_map(model_vars)
	obs_label_map = variable_label_map(obs_vars)
	model_labels = list(model_label_map)
	obs_labels = list(obs_label_map)
	preferred = "tas_global_avg_ann"
	if preferred in model_vars:
		default_model_var = preferred
	else:
		default_model_var = next((v for v in model_vars if "tas" in v.lower() or "temp" in v.lower()), model_vars[0])
	if default_model_var in obs_vars:
		default_obs_var = default_model_var
	elif preferred in obs_vars:
		default_obs_var = preferred
	else:
		default_obs_var = next((v for v in obs_vars if "tas" in v.lower() or "temp" in v.lower()), obs_vars[0])

	default_model_label = next(label for label, var in model_label_map.items() if var == default_model_var)
	default_obs_label = next(label for label, var in obs_label_map.items() if var == default_obs_var)

	selected_model_label = st.sidebar.selectbox(
		"Model variable",
		model_labels,
		index=model_labels.index(default_model_label),
		key="model_variable_select",
	)
	selected_obs_label = st.sidebar.selectbox(
		"Observed variable",
		obs_labels,
		index=obs_labels.index(default_obs_label),
		key="obs_variable_select",
	)
	model_variable = model_label_map[selected_model_label]
	obs_variable = obs_label_map[selected_obs_label]

	lat_bounds = intersect_bounds(dataset_lat_bounds(model_ds), dataset_lat_bounds(obs_ds))
	lon_bounds = intersect_bounds(dataset_lon_bounds(model_ds), dataset_lon_bounds(obs_ds))
	lat = st.sidebar.slider(
		"Latitude",
		float(lat_bounds[0]),
		float(lat_bounds[1]),
		value=float((lat_bounds[0] + lat_bounds[1]) / 2),
		key="cmp_lat",
	)
	lon = st.sidebar.slider(
		"Longitude",
		float(lon_bounds[0]),
		float(lon_bounds[1]),
		value=float((lon_bounds[0] + lon_bounds[1]) / 2),
		key="cmp_lon",
	)

	model_data_var = model_ds[model_variable]
	model_time_candidates = time_coord_candidates(model_ds, data=model_data_var)
	obs_data_var = obs_ds[obs_variable]
	obs_time_candidates = time_coord_candidates(obs_ds, data=obs_data_var)
	model_time_coord: str | None = None
	obs_time_coord: str | None = None
	if len(model_time_candidates) > 1:
		model_time_coord = st.sidebar.selectbox(
			"Model time coordinate", model_time_candidates, index=0, key="cmp_model_time_coord"
		)
	if len(obs_time_candidates) > 1:
		obs_time_coord = st.sidebar.selectbox(
			"Observed time coordinate", obs_time_candidates, index=0, key="cmp_obs_time_coord"
		)

	show_trend = st.sidebar.toggle("Show trend lines", value=True, key="cmp_show_trend")

	with st.spinner("Building advanced comparison dashboard..."):
		model_series = extract_series(model_ds, model_variable, lat, lon, time_coord=model_time_coord)
		obs_series = extract_series(obs_ds, obs_variable, lat, lon, time_coord=obs_time_coord)
		df = align_series(model_series, obs_series)

	years = sorted(df.index.year.unique().tolist())
	reference_year = st.sidebar.select_slider("Reference year", options=years, value=years[-1])

	fig = build_comparison_figure(df, model_variable, obs_variable, lat, lon, show_trend)
	st.plotly_chart(
		fig,
		use_container_width=True,
		config={
			"displaylogo": False,
			"scrollZoom": True,
			"modeBarButtonsToRemove": ["lasso2d", "select2d"],
		},
	)
	st.caption(
		f"Model source: {model_label} ({model_variable}) | Observed source: {obs_label} ({obs_variable})"
	)

	model_unit_raw = str(model_ds[model_variable].attrs.get("units", "")).strip()
	obs_unit_raw = str(obs_ds[obs_variable].attrs.get("units", "")).strip()
	unit_raw = model_unit_raw if model_unit_raw == obs_unit_raw else ""
	unit = f" {unit_raw}" if unit_raw else ""

	model_mean = float(df["Model"].mean())
	observed_mean = float(df["Observed"].mean())
	diff_mean = float(df["Difference"].mean())
	diff_min = float(df["Difference"].min())
	diff_max = float(df["Difference"].max())
	diff_ref = reference_year_difference(df, reference_year)

	prev_year = next((year for year in reversed(years) if year < reference_year), None)
	prev_diff = reference_year_difference(df, prev_year) if prev_year is not None else float("nan")
	delta_ref = diff_ref - prev_diff if pd.notna(diff_ref) and pd.notna(prev_diff) else None

	stats_row_1 = st.columns(4)
	stats_row_1[0].metric("Model mean", format_value(model_mean, unit))
	stats_row_1[1].metric("Observed mean", format_value(observed_mean, unit))
	stats_row_1[2].metric("Difference mean", format_value(diff_mean, unit))
	stats_row_1[3].metric(
		f"Difference @ {reference_year}",
		format_value(diff_ref, unit),
		delta=None if delta_ref is None else format_value(delta_ref, unit),
	)

	stats_row_2 = st.columns(3)
	stats_row_2[0].metric("Difference min", format_value(diff_min, unit))
	stats_row_2[1].metric("Difference max", format_value(diff_max, unit))
	stats_row_2[2].metric("Total samples", f"{len(df):,}")

	with st.expander("Difference values preview"):
		preview = df[["Difference"]].copy()
		preview.index.name = "Time"
		st.dataframe(preview.tail(25), use_container_width=True)
