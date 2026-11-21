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

Click the map or enter coordinates. The app shows the nearest tide gauge, its
distance from the selected point, three sea level scenarios, and trend results
for the selected scenario. The CSV has one row per year from 2023 through 2100
and includes all three scenarios and gauge metadata.

The app downloads and caches the
[NGL tide-gauge table](https://geodesy.unr.edu/vlm/GPS_VLM_at_TideGauges_LongTable.txt)
for up to 24 hours. If the server cannot fetch that table, download it and use
the local upload in the app. Map tiles load from OpenStreetMap in the browser.

The original RisingSeas notebook by Shihab Uddin, Adnan Rajib, and Qianjin Zheng
provides the global scenario values and modeling method. The app reads the
tide-gauge coordinates in source order (longitude, latitude), which corrects
a reversal in the notebook. The local adjustment assumes constant land motion
from the nearest tide gauge. Check the distance when interpreting the results.
