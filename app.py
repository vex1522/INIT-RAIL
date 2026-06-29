"""Flask dashboard for the Chennai suburban rail analysis."""

from __future__ import annotations

import logging
import subprocess
import threading
from pathlib import Path

import pandas as pd
from flask import Flask, abort, jsonify, render_template, request, send_from_directory

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
OUTPUT_DIR = Path("outputs")
_running = False
_lock = threading.Lock()

QUERY_PRESETS = {
    "avg_load_crossings": {
        "question": "What is the average passenger load for manned vs. unmanned crossings?",
        "title": "Average Passenger Load by Crossing Type",
        "fn": lambda d: d.groupby("crossing_type")["passengers"]
        .mean()
        .reset_index()
        .rename(columns={"passengers": "avg_passenger_load"}),
    },
    "high_peak_zones": {
        "question": "Which zones experience the highest frequency of 'High' peak loads?",
        "title": "High Peak Load Frequency by Zone",
        "fn": lambda d: d[d["peak_load"] == "High"]
        .groupby("zone")
        .size()
        .reset_index(name="high_peak_count")
        .sort_values("high_peak_count", ascending=False),
    },
    "top_ratio_routes": {
        "question": "What are the top 5 routes with the highest passenger-to-delay ratio?",
        "title": "Top 5 Routes by Passenger-to-Delay Ratio",
        "fn": lambda d: (
            lambda r: r.assign(passenger_delay_ratio=r["avg_passengers"] / (1 + r["avg_delay"]))
            .nlargest(5, "passenger_delay_ratio")
        )(
            d.groupby("route_id")
            .agg(avg_passengers=("passengers", "mean"), avg_delay=("delay_min", "mean"))
            .reset_index()
        ),
    },
    "low_peak_high_delay": {
        "question": "Which routes have consistently 'Low' peak loads but still experience high delays?",
        "title": "Low Peak Routes with High Delays",
        "fn": lambda d: d[d["peak_load"] == "Low"]
        .groupby("route_id")
        .agg(avg_delay=("delay_min", "mean"), low_peak_count=("route_id", "count"))
        .reset_index()
        .query("low_peak_count >= 2")
        .sort_values("avg_delay", ascending=False)
        .head(10),
    },
    "crossing_volume_distribution": {
        "question": "What is the total passenger volume distribution across different crossing types?",
        "title": "Total Passenger Volume by Crossing Type",
        "fn": lambda d: d.groupby("crossing_type")["passengers"]
        .sum()
        .reset_index()
        .rename(columns={"passengers": "total_passengers"})
        .sort_values("total_passengers", ascending=False),
    },
    "weekend_vs_weekday_delays": {
        "question": "Are weekend delays significantly different from weekday delays?",
        "title": "Weekend vs Weekday Delays",
        "fn": lambda d: d.assign(
            day_group=d["day_of_week"].isin(["Saturday", "Sunday"]).map({True: "Weekend", False: "Weekday"})
        )
        .groupby("day_group")["delay_min"]
        .agg(["mean", "median", "std", "count"])
        .reset_index()
        .rename(columns={"mean": "avg_delay", "median": "median_delay", "std": "delay_std"}),
    },
    "top_dates_volume": {
        "question": "Which 5 specific dates had the highest total passenger volume across all routes?",
        "title": "Top 5 Dates by Total Passenger Volume",
        "fn": lambda d: d.groupby("date")["passengers"]
        .sum()
        .reset_index()
        .rename(columns={"passengers": "total_passengers"})
        .nlargest(5, "total_passengers"),
    },
    "efficiency_by_day": {
        "question": "How does the efficiency score fluctuate across different days of the week?",
        "title": "Efficiency Score by Day of Week",
        "fn": lambda d: (
            d.groupby("day_of_week")
            .agg(avg_passengers=("passengers", "mean"), avg_delay=("delay_min", "mean"))
            .reset_index()
            .assign(efficiency_score=lambda x: x["avg_passengers"] / (1 + x["avg_delay"]))
            .sort_values("efficiency_score", ascending=False)
        ),
    },
    "high_peak_month": {
        "question": "What time of year (or month) sees the highest spike in 'High' peak load occurrences?",
        "title": "High Peak Load Occurrences by Month",
        "fn": lambda d: d[d["peak_load"] == "High"]
        .groupby(["month_num", "month"])
        .size()
        .reset_index(name="high_peak_count")
        .sort_values("month_num")
        .drop(columns="month_num"),
    },
    "tambaram_vs_beach": {
        "question": "How does the average delay in the Tambaram zone compare to the Beach zone?",
        "title": "Average Delay: Tambaram vs Beach",
        "fn": lambda d: d[d["zone"].isin(["Tambaram", "Beach"])]
        .groupby("zone")["delay_min"]
        .mean()
        .reset_index()
        .rename(columns={"delay_min": "avg_delay"}),
    },
    "egmore_delay_percent": {
        "question": "What percentage of trains in the Egmore zone experience delays over 15 minutes?",
        "title": "Egmore Trains with Delays Over 15 Minutes",
        "fn": lambda d: pd.DataFrame(
            [
                {
                    "zone": "Egmore",
                    "percentage_over_15": round(
                        100
                        * d[d["zone"] == "Egmore"]["delay_min"].gt(15).mean(),
                        2,
                    ),
                }
            ]
        ),
    },
    "zone_efficiency": {
        "question": "What is the overall average efficiency score for each railway zone?",
        "title": "Average Efficiency Score by Zone",
        "fn": lambda d: (
            d.groupby("zone")
            .agg(avg_passengers=("passengers", "mean"), avg_delay=("delay_min", "mean"))
            .reset_index()
            .assign(efficiency_score=lambda x: x["avg_passengers"] / (1 + x["avg_delay"]))
            .sort_values("efficiency_score", ascending=False)
        ),
    },
    "route_passenger_variance": {
        "question": "Which routes have the highest variance (unpredictability) in daily passenger counts?",
        "title": "Routes with Highest Passenger Variance",
        "fn": lambda d: d.groupby("route_id")["passengers"]
        .var()
        .reset_index()
        .rename(columns={"passengers": "passenger_variance"})
        .dropna()
        .nlargest(10, "passenger_variance"),
    },
    "avadi_drag_routes": {
        "question": "Are there specific routes that drag down the average efficiency score of the Avadi zone?",
        "title": "Lowest Efficiency Routes in Avadi",
        "fn": lambda d: (
            d[d["zone"] == "Avadi"]
            .groupby("route_id")
            .agg(avg_passengers=("passengers", "mean"), avg_delay=("delay_min", "mean"))
            .reset_index()
            .assign(efficiency_score=lambda x: x["avg_passengers"] / (1 + x["avg_delay"]))
            .nsmallest(10, "efficiency_score")
        ),
    },
    "unmanned_delay_correlation": {
        "question": "Is there a correlation between 'Unmanned' crossing types and higher average delays?",
        "title": "Average Delay by Crossing Type",
        "fn": lambda d: d.groupby("crossing_type")["delay_min"]
        .mean()
        .reset_index()
        .rename(columns={"delay_min": "avg_delay"})
        .sort_values("avg_delay", ascending=False),
    },
    "best_zone_balance": {
        "question": "Which zone has the best balance of high passenger volume and low delay?",
        "title": "Zone Balance Score",
        "fn": lambda d: (
            d.groupby("zone")
            .agg(avg_passengers=("passengers", "mean"), avg_delay=("delay_min", "mean"))
            .reset_index()
            .assign(balance_score=lambda x: x["avg_passengers"] / (1 + x["avg_delay"]))
            .sort_values("balance_score", ascending=False)
        ),
    },
    "semi_manned_high_peak": {
        "question": "Do routes with 'Semi-manned' crossings experience more 'High' peak loads?",
        "title": "High Peak Loads on Semi-manned Crossings",
        "fn": lambda d: d[d["crossing_type"] == "Semi-manned"]
        .groupby("peak_load")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False),
    },
}


def _output_status() -> dict[str, dict[str, object]]:
    """Build file existence metadata for dashboard rendering."""
    files = [
        ("cleaned_ridership.csv", "cleaned_ridership.csv"),
        ("train_mobility_dashboard.png", "train_mobility_dashboard.png"),
        ("railway_mobility_map.html", "railway_mobility_map.html"),
    ]
    status = {}
    for key, filename in files:
        path = OUTPUT_DIR / filename
        status[key] = {"exists": path.exists(), "size": path.stat().st_size if path.exists() else 0}
    return status


@app.route("/")
def index():
    """Render the landing page with output status cards."""
    return render_template("index.html", status_files=_output_status())


@app.route("/run", methods=["POST"])
def run_pipeline():
    """Run the analysis pipeline unless it is already in progress."""
    global _running
    with _lock:
        if _running:
            return jsonify({"status": "busy"}), 409
        _running = True
    try:
        logger.info("Starting solution.py pipeline")
        result = subprocess.run(["python", "solution.py"], capture_output=True, text=True, timeout=120)
        logger.info("Pipeline completed with return code %s", result.returncode)
        return jsonify({"status": "ok", "stdout": result.stdout, "stderr": result.stderr})
    except subprocess.TimeoutExpired as exc:
        logger.error("Pipeline timed out: %s", exc)
        return jsonify({"status": "error", "stdout": exc.stdout or "", "stderr": exc.stderr or "Timeout"}), 500
    except Exception:
        logger.exception("Pipeline execution failed")
        return jsonify({"status": "error", "stdout": "", "stderr": "Unhandled server error"}), 500
    finally:
        with _lock:
            _running = False


@app.route("/dashboard")
def dashboard():
    """Render the analytics dashboard."""
    return render_template("dashboard.html")


@app.route("/query")
def query_page():
    """Render the query explorer page."""
    map_exists = (OUTPUT_DIR / "railway_mobility_map.html").exists()
    return render_template("query.html", map_exists=map_exists)


@app.route("/map")
def map_view():
    """Render the map view page."""
    map_exists = (OUTPUT_DIR / "railway_mobility_map.html").exists()
    return render_template("map_view.html", map_exists=map_exists)


@app.route("/outputs/<filename>")
def outputs(filename):
    """Serve generated output files."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        abort(404)
    return send_from_directory(OUTPUT_DIR, filename)


@app.route("/api/status")
def api_status():
    """Return generated output file metadata."""
    files = []
    for key, filename in [
        ("cleaned_ridership.csv", "cleaned_ridership.csv"),
        ("train_mobility_dashboard.png", "train_mobility_dashboard.png"),
        ("railway_mobility_map.html", "railway_mobility_map.html"),
    ]:
        path = OUTPUT_DIR / filename
        files.append({"key": key, "filename": filename, "exists": path.exists(), "size": path.stat().st_size if path.exists() else 0})
    return jsonify({"files": files})


@app.route("/api/stats")
def api_stats():
    """Return aggregate dashboard statistics from the cleaned dataset."""
    csv_path = OUTPUT_DIR / "cleaned_ridership.csv"
    if not csv_path.exists():
        return jsonify({"error": "Pipeline not run yet"}), 404
    df = pd.read_csv(csv_path)
    rg = (
        df.groupby("route_id")
        .agg(
            avg_passengers=("passengers", "mean"),
            avg_delay=("delay_min", "mean"),
            peak_load=("peak_load", lambda x: x.mode()[0]),
        )
        .reset_index()
    )
    rg["efficiency_score"] = rg["avg_passengers"] / (1 + rg["avg_delay"])
    top10 = rg.nlargest(10, "efficiency_score").to_dict(orient="records")
    return jsonify(
        {
            "total_records": int(len(df)),
            "total_passengers": float(df["passengers"].sum()),
            "avg_passengers": float(df["passengers"].mean()),
            "avg_delay": float(df["delay_min"].mean()),
            "total_routes": int(df["route_id"].nunique()),
            "total_zones": int(df["zone"].nunique()),
            "top10_routes": top10,
            "files": [
                {
                    "key": "csv",
                    "exists": csv_path.exists(),
                    "size": csv_path.stat().st_size if csv_path.exists() else 0,
                },
                {"key": "png", "exists": (OUTPUT_DIR / "train_mobility_dashboard.png").exists()},
                {"key": "html", "exists": (OUTPUT_DIR / "railway_mobility_map.html").exists()},
            ],
        }
    )


@app.route("/api/query", methods=["POST"])
def api_query():
    """Execute preset or custom dataset queries."""
    csv_path = OUTPUT_DIR / "cleaned_ridership.csv"
    if not csv_path.exists():
        return jsonify({"error": "Run pipeline first"}), 404

    df = pd.read_csv(csv_path, parse_dates=["date"])
    df["month"] = df["date"].dt.month_name()
    df["month_num"] = df["date"].dt.month
    body = request.get_json(silent=True) or {}

    preset = body.get("preset")
    custom = body.get("filter")

    try:
        question_lookup = {value["question"]: key for key, value in QUERY_PRESETS.items()}
        if preset in question_lookup:
            preset = question_lookup[preset]
        if preset and preset in QUERY_PRESETS:
            result_df = QUERY_PRESETS[preset]["fn"](df)
            title = QUERY_PRESETS[preset]["title"]
        elif custom:
            result_df = df.query(custom).head(100)
            title = f"Custom filter: {custom}"
        else:
            return jsonify({"error": "No query provided"}), 400

        result_df = result_df.round(2)
        return jsonify(
            {
                "title": title,
                "columns": list(result_df.columns),
                "rows": result_df.to_dict(orient="records"),
            }
        )
    except Exception as e:
        logger.error("Query error: %s", e)
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    app.run(debug=True, port=5000)
