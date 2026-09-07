"""Time series trend analysis module for PyClimaExplorer."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import xarray as xr

from .data_loader import (
	dataset_lat_bounds,
	dataset_lon_bounds,
	get_time_index,
	time_coord_candidates,
	variables_with_time_dim,
)
from .ui_helpers import format_value, variable_label_map


def _is_time_like(name: str) -> bool:
	lower = name.lower()
	return lower in {"time", "date", "datetime", "timestamp"} or "time" in lower or "date" in lower


def _pick_time_coord(ds: xr.Dataset, data: xr.DataArray) -> str:
	candidates = [name for name in time_coord_candidates(ds, data=data) if name in data.dims or name in data.coords]
	for candidate in candidates:
		idx = get_time_index(ds, coord_name=candidate, data=data)
		if idx is not None and len(idx) > 0:
			return candidate

	for dim in data.dims:
		if _is_time_like(dim):
			return dim

	raise ValueError("Could not find a valid time coordinate for this variable")


def extract_series(
	ds: xr.Dataset,
	variable: str,
	lat: float,
	lon: float,
	time_coord: str | None = None,
) -> pd.Series:
	"""Extract time-series at nearest lat/lon for a given variable."""
	if variable not in ds:
		raise ValueError(f"Variable '{variable}' was not found in the selected dataset")

	data = ds[variable]
	if "lat" in data.dims:
		data = data.sel(lat=lat, method="nearest")
	if "lon" in data.dims:
		data = data.sel(lon=lon, method="nearest")

	selected_time_coord = time_coord or _pick_time_coord(ds, data)
	if selected_time_coord not in data.dims and selected_time_coord not in data.coords:
		raise ValueError(f"Time coordinate '{selected_time_coord}' is not present for variable '{variable}'")

	for dim in list(data.dims):
		if dim == selected_time_coord:
			continue
		if dim in {"lat", "lon"}:
			continue
		data = data.mean(dim=dim, skipna=True)

	data = data.sortby(selected_time_coord)
	idx = get_time_index(ds, coord_name=selected_time_coord, data=data)
	if idx is None:
		raise ValueError("Dataset time coordinate could not be interpreted as dates")

	values = np.asarray(data.values, dtype="float64").reshape(-1)
	if len(values) > len(idx):
		values = values[: len(idx)]
	elif len(values) < len(idx):
		idx = idx[: len(values)]

	series = pd.Series(values, index=pd.DatetimeIndex(idx), name=variable)
	series = series.replace([np.inf, -np.inf], np.nan).dropna().sort_index()
	if series.empty:
		raise ValueError("No valid values found for the selected variable and location")
	return series


def compute_trend(series: pd.Series) -> pd.Series:
	"""Compute 1D linear regression trendline for a time series."""
	y = np.asarray(series.values, dtype="float64")
	x = np.arange(len(y), dtype="float64")
	valid = np.isfinite(y)
	if valid.sum() < 2:
		return pd.Series(np.full_like(y, np.nan), index=series.index)

	slope, intercept = np.polyfit(x[valid], y[valid], deg=1)
	trend = slope * x + intercept
	return pd.Series(trend, index=series.index)


def build_time_series_figure(
	series: pd.Series,
	variable: str,
	lat: float,
	lon: float,
	show_trend: bool,
) -> go.Figure:
	"""Construct Plotly figure for time series and trend line."""
	fig = go.Figure()

	fig.add_trace(
		go.Scatter(
			x=series.index,
			y=series.values,
			name=variable,
			mode="lines+markers",
			line={"color": "#4FC3F7", "width": 2.9, "shape": "spline", "smoothing": 0.8},
			marker={"size": 5},
			hovertemplate="Time: %{x|%Y-%m-%d}<br>Value: %{y:.3f}<extra></extra>",
		)
	)

	if show_trend:
		trend = compute_trend(series)
		fig.add_trace(
			go.Scatter(
				x=series.index,
				y=trend.values,
				name="Trend",
				mode="lines",
				line={"color": "#FFC1A6", "dash": "dash", "width": 2.2},
				hovertemplate="Time: %{x|%Y-%m-%d}<br>Trend: %{y:.3f}<extra></extra>",
			)
		)

	trace_count = len(fig.data)

	def _visibility(show_series: bool, show_trend_trace: bool) -> list[bool]:
		visible = [False] * trace_count
		visible[0] = show_series
		if show_trend and trace_count > 1:
			visible[1] = show_trend_trace
		return visible

	buttons = [{"label": "Series", "method": "update", "args": [{"visible": _visibility(True, False)}]}]
	if show_trend:
		buttons = [
			{"label": "Both", "method": "update", "args": [{"visible": _visibility(True, True)}]},
			{"label": "Series", "method": "update", "args": [{"visible": _visibility(True, False)}]},
			{"label": "Trend", "method": "update", "args": [{"visible": _visibility(False, True)}]},
		]

	fig.update_layout(
		template="plotly_dark",
		height=660,
		hovermode="x unified",
		title={
			"text": f"{variable} trend @ lat {lat:.2f}, lon {lon:.2f}",
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
			"title": variable,
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
				"buttons": buttons,
			}
		],
	)

	return fig


def render_time_series_dashboard(ds: xr.Dataset) -> None:
	"""Render the Streamlit dashboard UI for time series trend mode."""
	variables = variables_with_time_dim(ds)
	if not variables:
		st.error("No variables with a time dimension are available for this analysis.")
		return

	label_map = variable_label_map(variables)
	labels = list(label_map)
	preferred = "tas_global_avg_ann"
	if preferred in variables:
		default_var = preferred
	else:
		default_var = next((v for v in variables if "tas" in v.lower() or "temp" in v.lower()), variables[0])
	default_label = next(label for label, var in label_map.items() if var == default_var)

	selected_label = st.sidebar.selectbox("Variable", labels, index=labels.index(default_label), key="trend_variable")
	variable = label_map[selected_label]

	lat_min, lat_max = dataset_lat_bounds(ds)
	lon_min, lon_max = dataset_lon_bounds(ds)
	lat = st.sidebar.slider("Latitude", float(lat_min), float(lat_max), value=float((lat_min + lat_max) / 2), key="trend_lat")
	lon = st.sidebar.slider("Longitude", float(lon_min), float(lon_max), value=float((lon_min + lon_max) / 2), key="trend_lon")

	data_var = ds[variable]
	candidates = time_coord_candidates(ds, data=data_var)
	if not candidates:
		st.error("Selected variable has no time-like dimension. Choose another variable or add a time axis.")
		return
	time_coord = st.sidebar.selectbox("Time coordinate", candidates, index=0, key="trend_time_coord")
	show_trend = st.sidebar.toggle("Show trend line", value=True, key="trend_show_line")

	with st.spinner("Building advanced time series dashboard..."):
		series = extract_series(ds, variable, lat, lon, time_coord=time_coord)

	years = sorted(series.index.year.unique().tolist())
	reference_year = st.sidebar.select_slider("Reference year", options=years, value=years[-1], key="trend_reference_year")

	fig = build_time_series_figure(series, variable, lat, lon, show_trend)
	st.plotly_chart(
		fig,
		use_container_width=True,
		config={
			"displaylogo": False,
			"scrollZoom": True,
			"modeBarButtonsToRemove": ["lasso2d", "select2d"],
		},
	)

	unit_raw = str(ds[variable].attrs.get("units", "")).strip()
	unit = f" {unit_raw}" if unit_raw else ""
	current_values = series.loc[series.index.year == reference_year]
	current_mean = float(current_values.mean()) if not current_values.empty else float("nan")
	prev_year = next((year for year in reversed(years) if year < reference_year), None)
	prev_values = series.loc[series.index.year == prev_year] if prev_year is not None else pd.Series(dtype="float64")
	prev_mean = float(prev_values.mean()) if not prev_values.empty else float("nan")
	delta = current_mean - prev_mean if pd.notna(current_mean) and pd.notna(prev_mean) else None

	stats_row_1 = st.columns(4)
	stats_row_1[0].metric("Mean", format_value(float(series.mean()), unit))
	stats_row_1[1].metric("Min", format_value(float(series.min()), unit))
	stats_row_1[2].metric("Max", format_value(float(series.max()), unit))
	stats_row_1[3].metric(
		f"Value @ {reference_year}",
		format_value(current_mean, unit),
		delta=None if delta is None else format_value(delta, unit),
	)

	stats_row_2 = st.columns(2)
	stats_row_2[0].metric("Total samples", f"{len(series):,}")
	stats_row_2[1].metric("Std dev", format_value(float(series.std()), unit))

	with st.expander("Time series values preview"):
		preview = pd.DataFrame({"Value": series})
		preview.index.name = "Time"
		st.dataframe(preview.tail(25), use_container_width=True)
