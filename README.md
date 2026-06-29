# INIT/RAIL 
> **Hackathon Set A Solution: Local Train Traffic Analysis**

**INIT/RAIL** is a Python-based interactive analytical dashboard built to analyze 3 years of suburban train ridership data across 50 routes in the Chennai metropolitan area. It provides rail planners with actionable insights into peak loads, anomaly detection, route efficiency, and station congestion to optimize scheduling.

##  Live Application
The application is deployed and currently live on Render:
**[Insert Your Render URL Here]**

*(Note: As this is hosted on a free tier, the initial load may take 30-50 seconds if the server has gone to sleep from inactivity. Subsequent navigation is instant).*

##  Key Features
* **Automated ETL Pipeline:** Robust data cleaning that handles missing values, string garbage coercion, sentinel value replacement, and outlier capping using `pandas`.
* **Algorithmic Efficiency Ranking:** Implements a custom Merge Sort algorithm to rank routes based on a composite efficiency score (Passenger Volume vs. Delay Time).
* **Interactive Visualizations:** A modern, tabbed dashboard built with `Plotly`, featuring time-series trends, grouped bar charts for zone loads, delay distribution histograms, and scatter plots.
* **Geographical Health Map:** An interactive `Folium` map allowing users to toggle base layers and visually inspect zone health via color-coded, radius-scaled markers.
* **Query Explorer:** A built-in dropdown interface allowing non-technical users to execute specific natural-language queries against the cleaned dataset.
* **Modern UI/UX:** A responsive, dark-themed interface featuring a dynamic full-screen background video on the landing page and sharp, professional KPI tiles.

##  Tech Stack
* **Backend:** Python 3.11, Flask, Gunicorn
* **Data Processing & DSA:** Pandas, NumPy, Custom Merge Sort implementation
* **Visualizations:** Plotly Express, Plotly Graph Objects, Folium
* **Frontend:** HTML5, CSS3 (Custom Dark Theme), Vanilla JavaScript
* **Deployment:** Render (Platform as a Service)

##  Project Structure

```text
Team_SetA/
│
├── app.py                      # Main Flask application and route definitions
├── requirements.txt            # Python dependencies (includes gunicorn for deployment)
├── README.md                   # Project documentation
│
├── data/
│   ├── raw_ridership.csv       # Original dataset (with injected noise)
│   └── cleaned_ridership.csv   # Post-ETL output data
│
├── tasks/
│   ├── task1_cleaning.py       # ETL, Noise handling, Outlier detection
│   ├── task2_ranking.py        # Merge Sort and Efficiency logic
│   ├── task3_visualization.py  # Plotly chart generation
│   └── task4_map.py            # Folium interactive map generation
│
├── static/
│   ├── css/
│   │   └── style.css           # Global UI styling and dark theme
│   └── video/
│       └── train_bg.mp4        # Homepage background video
│
└── templates/
    ├── index.html              # Landing page with video and navigation cards
    ├── dashboard.html          # KPI tiles, Plotly tabs, and Query Explorer
    └── map.html                # Full-screen Folium map rendering



 Local Setup and Installation
1. Clone the repository:

Bash
git clone [https://github.com/YourUsername/init-rail.git](https://github.com/YourUsername/init-rail.git)
cd init-rail
2. Create and activate a virtual environment:

Bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
3. Install dependencies:

Bash
pip install -r requirements.txt
4. Run the ETL Pipeline (Optional if cleaned data is provided):

Bash
python tasks/task1_cleaning.py
5. Start the Flask Server:

Bash
flask run
Navigate to http://127.0.0.1:5000 in your browser to view the application locally.
