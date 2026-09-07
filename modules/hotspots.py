"""Warming hotspots detection."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import xarray as xr

from . import config
from .data_loader import find_lat_dim, find_lon_dim, get_time_index, time_coord_candidates


def _slice_years(ds: xr.Dataset, start_year: int, end_year: int, data: xr.DataArray | None = None) -> xr.Dataset:
	candidates = time_coord_candidates(ds, data=data)
	coord_name = candidates[0] if candidates else None
	idx = get_time_index(ds, coord_name=coord_name, data=data)
	if idx is None or coord_name is None:
		raise ValueError("Dataset lacks a valid time coordinate")
	start = pd.Timestamp(year=start_year, month=1, day=1)
	end = pd.Timestamp(year=end_year, month=12, day=31)
	# Guard: idx must be a DatetimeIndex for Timestamp comparisons to work
	if not isinstance(idx, pd.DatetimeIndex):
		raise ValueError(
			f"Time coordinate '{coord_name}' could not be interpreted as dates "
			f"(got {type(idx).__name__}). Ensure the dataset has a valid time axis."
		)
	mask = (idx >= start) & (idx <= end)
	return ds.isel({coord_name: mask})


def _mean_over_period(ds: xr.Dataset, variable: str, start_year: int, end_year: int) -> xr.DataArray:
	data = ds[variable]
	sliced = _slice_years(ds, start_year, end_year, data=data)
	data = sliced[variable]
	# mean along whichever dim is time-like
	for dim in data.dims:
		if dim.lower() == "time" or "time" in dim.lower() or "date" in dim.lower():
			data = data.mean(dim=dim, skipna=True)
			break
	return data


def show_hotspots(ds: xr.Dataset, variable: str, baseline: tuple[int, int], recent: tuple[int, int]):
	"""Return (fig, table_df) for warming hotspots between two periods."""

	data = ds[variable]

	# Resolve lat/lon dimension names dynamically from config aliases
	lat_dim = find_lat_dim(data)
	lon_dim = find_lon_dim(data)

	if not (lat_dim and lat_dim in data.dims and lon_dim and lon_dim in data.dims):
		raise ValueError("Climate Hotspots requires a variable with lat/lon dimensions; choose a spatial field.")

	baseline_mean = _mean_over_period(ds, variable, baseline[0], baseline[1])
	recent_mean = _mean_over_period(ds, variable, recent[0], recent[1])
	diff = recent_mean - baseline_mean

	# Re-resolve lat/lon on diff since it may have fewer dims after slicing
	lat_dim_diff = find_lat_dim(diff)
	lon_dim_diff = find_lon_dim(diff)

	if lat_dim_diff and lat_dim_diff in diff.dims:
		diff = diff.sortby(lat_dim_diff)
	if lon_dim_diff and lon_dim_diff in diff.dims:
		diff = diff.sortby(lon_dim_diff)

	diff = diff.squeeze()

	if lat_dim_diff and lon_dim_diff and lat_dim_diff in diff.dims and lon_dim_diff in diff.dims:
		diff = diff.transpose(lat_dim_diff, lon_dim_diff)

	array = diff.values
	mask = np.isfinite(array)
	array = np.where(mask, array, np.nan)

	fig = px.imshow(
		array,
		x=diff[lon_dim_diff].values if lon_dim_diff and lon_dim_diff in diff.coords else None,
		y=diff[lat_dim_diff].values if lat_dim_diff and lat_dim_diff in diff.coords else None,
		color_continuous_scale=config.HOTSPOT_COLORSCALE,
		origin="lower",
	)
	fig.update_layout(
		title=f"{variable}: warming intensity ({recent[0]}-{recent[1]} minus {baseline[0]}-{baseline[1]})",
		xaxis_title="Longitude",
		yaxis_title="Latitude",
		coloraxis_colorbar=dict(title="Δ" + variable),
		margin=dict(l=10, r=10, t=50, b=10),
	)

	table_df = None
	if lat_dim_diff and lon_dim_diff and lat_dim_diff in diff.coords and lon_dim_diff in diff.coords:
		stacked = diff.stack(points=(lat_dim_diff, lon_dim_diff)).reset_index("points")
		df = pd.DataFrame({
			"lat": stacked[lat_dim_diff].values,
			"lon": stacked[lon_dim_diff].values,
			"delta": stacked.values,
		})
		df = df.replace([np.inf, -np.inf], np.nan).dropna()
		df = df.sort_values("delta", ascending=False).head(config.HOTSPOT_TABLE_TOP_N)
		table_df = df

	return fig, table_df
