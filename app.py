"""Streamlit port of the RisingSeas notebook."""
from pathlib import Path

import folium
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pymannkendall as mk
import requests
import streamlit as st
from plotly.subplots import make_subplots
from streamlit_folium import st_folium

VLM_FILENAME = "GPS_VLM_at_TideGauges_LongTable.txt"
VLM_URL = f"https://geodesy.unr.edu/vlm/{VLM_FILENAME}"
BASE_YEAR = 2023
SCENARIOS = ("SSP1-2.6", "SSP3-7.0", "SSP5-8.5")
PERIODS = ((2023, 2050), (2050, 2075), (2075, 2100))
PROJECTIONS = pd.DataFrame(
    [
        (2030, .09, .09, .10), (2040, .14, .14, .16),
        (2050, .19, .21, .23), (2060, .23, .28, .31),
        (2070, .29, .37, .40), (2080, .34, .46, .51),
        (2090, .39, .56, .63), (2100, .44, .68, .77),
    ],
    columns=("Year", *SCENARIOS),
)


def parse_gauges(content):
    rows = []
    name = None
    for line in content.splitlines():
        if line.startswith(">>"):
            fields = line.split(maxsplit=2)
            name = fields[2] if len(fields) == 3 else None
        elif name and line.startswith("##"):
            fields = line[2:].split()
            try:
                lon, lat, rate = map(float, fields[:3])
            except ValueError:
                continue
            if -90 <= lat <= 90 and -180 <= lon <= 360 and np.isfinite(rate):
                rows.append((name, lat, (lon + 180) % 360 - 180, rate))
    if not rows:
        raise ValueError("No valid tide-gauge records were found in the table.")
    return pd.DataFrame(rows, columns=["Name", "Latitude", "Longitude", "VLM_mm_yr"])


@st.cache_data(ttl=86400, show_spinner=False)
def load_gauges():
    response = requests.get(VLM_URL, timeout=(5, 12))
    response.raise_for_status()
    return parse_gauges(response.text)


def nearest_gauge(gauges, latitude, longitude):
    latitudes = np.radians(gauges["Latitude"])
    lat = np.radians(latitude)
    delta_lon = np.radians(gauges["Longitude"] - longitude)
    a = np.sin((latitudes - lat) / 2) ** 2
    a += np.cos(lat) * np.cos(latitudes) * np.sin(delta_lon / 2) ** 2
    distances = 6371 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    index = distances.idxmin()
    return gauges.loc[index], float(distances.loc[index])


def project(rate_mm_yr):
    decades = PROJECTIONS["Year"].to_numpy()
    years = np.r_[BASE_YEAR, decades]
    annual_years = np.arange(BASE_YEAR, 2101)
    elapsed = years - BASE_YEAR
    land_motion = elapsed * (rate_mm_yr / 1000)
    sampled = pd.DataFrame({"Year": years})
    annual = pd.DataFrame({"Year": annual_years})
    for scenario in SCENARIOS:
        global_values = PROJECTIONS[scenario].to_numpy()
        baseline = np.polyval(np.polyfit(decades - BASE_YEAR, global_values, 2), 0)
        relative = np.r_[0, global_values - baseline] - land_motion
        sampled[scenario] = relative
        annual[scenario] = np.polyval(np.polyfit(elapsed, relative, 2), annual_years - BASE_YEAR)
    sampled["Vertical land motion"] = land_motion
    return sampled, annual


def projection_chart(sampled):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for scenario in SCENARIOS:
        fig.add_scatter(x=sampled["Year"], y=sampled[scenario], name=scenario)
    fig.add_scatter(
        x=sampled["Year"], y=sampled["Vertical land motion"],
        name="Vertical land motion", line=dict(dash="dot"), secondary_y=True,
    )
    fig.update_xaxes(title_text="Year", tickformat="d")
    fig.update_yaxes(title_text="Relative sea level (m)", secondary_y=False)
    fig.update_yaxes(title_text="Vertical land motion (m)", secondary_y=True)
    fig.update_layout(legend=dict(orientation="h", y=1.15), hovermode="x unified")
    return fig


def trend_chart(annual, scenario):
    labels = [f"{start} to {end}" for start, end in PERIODS]
    fig = make_subplots(rows=1, cols=3, shared_yaxes=True, subplot_titles=labels)
    rows = []
    for column, (start, end) in enumerate(PERIODS, start=1):
        period = annual.loc[annual["Year"].between(start, end)]
        years = period["Year"]
        result = mk.original_test(period[scenario].to_numpy())
        fit = result.intercept + result.slope * (years - start)
        fig.add_scatter(
            x=years, y=period[scenario], name="Projection", legendgroup="projection",
            showlegend=column == 1, line=dict(color="#146682"), row=1, col=column,
        )
        fig.add_scatter(
            x=years, y=fit, name="Sen's slope", legendgroup="slope",
            showlegend=column == 1, line=dict(color="#ba592e", dash="dash"),
            row=1, col=column,
        )
        rows.append((labels[column - 1], result.trend, result.slope * 1000, result.p))
    fig.update_xaxes(tickformat="d", nticks=4)
    fig.update_yaxes(title_text="Relative sea level (m)", row=1, col=1)
    fig.update_layout(legend=dict(orientation="h", y=-0.18))
    summary = pd.DataFrame(rows, columns=["Period", "Trend", "Sen’s slope (mm/year)", "p-value"])
    return fig, summary


def coordinates_from_map():
    location = st.session_state.get("location_map", {}).get("last_clicked")
    if not location:
        return
    longitude = (location["lng"] + 180) % 360 - 180
    st.session_state.latitude = round(max(-90, min(90, location["lat"])), 5)
    st.session_state.longitude = round(longitude, 5)


def main():
    st.set_page_config(page_title="RisingSeas", layout="wide")
    st.title("RisingSeas")
    st.write("Explore global sea level scenarios with a vertical land motion adjustment from the nearest tide gauge.")
    st.session_state.setdefault("latitude", -12.03932)
    st.session_state.setdefault("longitude", -76.90430)

    controls, map_panel = st.columns([1, 2])
    with controls:
        st.subheader("Location")
        st.caption("Click the map or enter coordinates.")
        latitude = st.number_input("Latitude (°)", -90.0, 90.0, key="latitude", format="%.5f")
        longitude = st.number_input("Longitude (°)", -180.0, 180.0, key="longitude", format="%.5f")
        with st.expander("Use a local tide-gauge file"):
            uploaded = st.file_uploader(VLM_FILENAME, type=["txt"], max_upload_size=10)

    gauge = None
    error = None
    try:
        if uploaded is not None:
            gauges = parse_gauges(uploaded.getvalue().decode("utf-8-sig"))
        else:
            with st.spinner("Loading tide-gauge data…"):
                gauges = load_gauges()
        gauge, distance = nearest_gauge(gauges, latitude, longitude)
    except (requests.RequestException, ValueError) as exc:
        if isinstance(exc, requests.RequestException):
            error = "The tide-gauge download failed. Retry or upload the source text file."
        else:
            error = "The tide-gauge text could not be read. Use the original NGL long-table format."

    with map_panel:
        location_map = folium.Map(location=[-12.03932, -76.90430], zoom_start=3, max_bounds=True)
        markers = folium.FeatureGroup(name="Locations")
        folium.Marker([latitude, longitude], tooltip="Selected location").add_to(markers)
        if gauge is not None:
            folium.CircleMarker(
                [gauge["Latitude"], gauge["Longitude"]], radius=7,
                color="#b35324", fill=True, tooltip="Nearest tide gauge",
            ).add_to(markers)
        st_folium(
            location_map, key="location_map", height=360, use_container_width=True,
            returned_objects=["last_clicked"], feature_group_to_add=markers,
            on_change=coordinates_from_map,
        )

    with controls:
        if error:
            st.error(error)
            st.button("Retry data download")
            st.markdown(f"[Download the NGL tide-gauge file]({VLM_URL})")
        else:
            st.metric("Nearest tide gauge", gauge["Name"])
            st.caption(f"{distance:,.1f} km from the selected location")
            st.metric("Vertical land motion", f"{gauge['VLM_mm_yr']:+.2f} mm/year")
    if gauge is None:
        st.stop()

    sampled, annual = project(gauge["VLM_mm_yr"])
    st.subheader("Sea level projections")
    st.plotly_chart(projection_chart(sampled), width="stretch")
    st.caption("The app adjusts the notebook’s global scenario values using the nearest gauge’s constant land-motion rate. Positive land motion indicates uplift and lowers relative sea level.")
    st.subheader("Trends by period")
    scenario = st.selectbox("Scenario", SCENARIOS)
    figure, summary = trend_chart(annual, scenario)
    st.plotly_chart(figure, width="stretch")
    st.dataframe(summary, hide_index=True)
    st.caption("Mann-Kendall tests summarize the fitted projection curves. The annual values come from the notebook’s quadratic fit, which can differ from zero in 2023.")
    export = annual.assign(
        Selected_latitude=latitude, Selected_longitude=longitude,
        Gauge=gauge["Name"], Gauge_distance_km=distance, Gauge_VLM_mm_yr=gauge["VLM_mm_yr"],
    )
    st.download_button("Download annual projections (CSV)", export.to_csv(index=False),
                       "SLRproject.csv", "text/csv", on_click="ignore")
    with st.expander("Sources and credits"):
        st.markdown(
            "RisingSeas notebook by Shihab Uddin, Adnan Rajib, and Qianjin Zheng, "
            "[H2I Lab](https://www.adnanrajib.com), The University of Texas at Arlington.\n\n"
            "[IPCC AR6 sea level projections (Garner et al.)](https://zenodo.org/record/5914710) · "
            "[Nevada Geodetic Laboratory tide-gauge data](https://geodesy.unr.edu/vlm.php) · "
            "[Hammond et al. (2021)](https://doi.org/10.1029/2021JB022355)"
        )


if __name__ == "__main__":
    main()
