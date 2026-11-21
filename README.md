# RisingSeas on Streamlit

Use Python 3.12. Open a terminal in this folder and run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Streamlit Community Cloud, put `app.py` and `requirements.txt` in the root
of your GitHub repository, select `app.py` as the entry point, and choose
Python 3.12 under Advanced settings.
[Deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)

Pan and zoom to a location, or search using the magnifying glass. Click
**Draw a circlemarker** on the left toolbar, then click the map. The blue dot
marks your selection and the orange ring marks the nearest gauge. Selecting
a new point updates the gauge and projections. You can also enter coordinates
and click **Center map on coordinates** to zoom to them. The app shows the nearest tide gauge, its
distance from the selected point, three sea level scenarios, and trend results
for the selected scenario. The chart menu shows all series, an individual scenario, or vertical land
motion. Select an SSP for trend analysis and to download the notebook-style
`SLRproject.csv` with one column per period. The separate annual CSV includes
all three scenarios and gauge metadata from 2023 through 2100.

The app downloads and caches the
[NGL tide-gauge table](https://geodesy.unr.edu/vlm/GPS_VLM_at_TideGauges_LongTable.txt)
for up to 24 hours. If the server cannot fetch that table, download it and use
the local upload in the app. Esri World Topographic Map tiles load in the browser.

The original RisingSeas notebook by Shihab Uddin, Adnan Rajib, and Qianjin Zheng
provides the global scenario values and modeling method. The app reads the
tide-gauge coordinates in source order (longitude, latitude), which corrects
a reversal in the notebook. The local adjustment assumes constant land motion
from the nearest tide gauge. Check the distance when interpreting the results.
