"""Render the multi-panel mobility dashboard figure and Plotly charts."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio


OUTPUT_DIR = Path("outputs")
OUTPUT_PATH = OUTPUT_DIR / "train_mobility_dashboard.png"


def _write_empty_chart(filename: str, title: str) -> None:
    """Write a placeholder Plotly chart when no data is available."""
    fig = go.Figure()
    fig.update_layout(
        title=title,
        paper_bgcolor="#fefae0",
        plot_bgcolor="#e9edc9",
        font=dict(color="#3b3a2f"),
        annotations=[
            dict(
                text="No data available",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16, color="#7a7060"),
            )
        ],
    )
    pio.write_html(fig, OUTPUT_DIR / filename, include_plotlyjs="cdn")


def run(df) -> None:
    """Create Plotly HTML charts and save the Matplotlib dashboard PNG."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("Chennai Suburban Rail - Mobility Dashboard", fontsize=16, fontweight="bold")

    daily = df.groupby("date")["passengers"].sum().reset_index()
    if daily.empty:
        print("Warning: daily passengers panel skipped because dataframe is empty.")
        _write_empty_chart("chart_daily_passengers.html", "Daily Total Passengers (2022-2024)")
    else:
        daily["rolling7"] = daily["passengers"].rolling(7).mean()
        axes[0, 0].plot(daily["date"], daily["passengers"], label="Daily Total")
        axes[0, 0].plot(daily["date"], daily["rolling7"], linestyle="--", label="7-Day Rolling Mean")
        axes[0, 0].set_title("Daily Total Passengers (2022-2024)")
        axes[0, 0].set_xlabel("Date")
        axes[0, 0].set_ylabel("Total Passengers")
        axes[0, 0].legend()

        plotly_daily = go.Figure()
        plotly_daily.add_trace(
            go.Scatter(
                x=daily["date"],
                y=daily["passengers"],
                name="Daily Total",
                line=dict(color="#ccd5ae", width=1.5),
                opacity=0.7,
            )
        )
        plotly_daily.add_trace(
            go.Scatter(
                x=daily["date"],
                y=daily["rolling7"],
                name="7-Day Rolling Mean",
                line=dict(color="#d4a373", width=2.5),
            )
        )
        plotly_daily.update_layout(
            title="Daily Total Passengers (2022-2024)",
            xaxis_title="Date",
            yaxis_title="Total Passengers",
            paper_bgcolor="#fefae0",
            plot_bgcolor="#e9edc9",
            font=dict(color="#3b3a2f"),
            hovermode="x unified",
            legend=dict(bgcolor="#faedcd"),
        )
        pio.write_html(plotly_daily, OUTPUT_DIR / "chart_daily_passengers.html", include_plotlyjs="cdn")

    zone_peak = df.groupby(["zone", "peak_load"])["passengers"].mean().unstack()
    if zone_peak.empty:
        print("Warning: zone vs peak load panel skipped because dataframe is empty.")
        _write_empty_chart("chart_zone_bar.html", "Avg Passengers by Zone & Peak Load")
    else:
        zone_peak.plot(kind="bar", ax=axes[0, 1])
        axes[0, 1].set_title("Avg Passengers by Zone & Peak Load")
        axes[0, 1].set_xlabel("Zone")
        axes[0, 1].set_ylabel("Avg Passengers")
        axes[0, 1].tick_params(axis="x", rotation=30)

        grp = df.groupby(["zone", "peak_load"])["passengers"].mean().reset_index()
        colors_map = {"High": "#bc4749", "Medium": "#d4a373", "Low": "#6a994e"}
        plotly_bar = go.Figure()
        for load in ["High", "Medium", "Low"]:
            sub = grp[grp["peak_load"] == load]
            plotly_bar.add_trace(
                go.Bar(x=sub["zone"], y=sub["passengers"], name=load, marker_color=colors_map[load])
            )
        plotly_bar.update_layout(
            barmode="group",
            title="Avg Passengers by Zone & Peak Load",
            xaxis_title="Zone",
            yaxis_title="Avg Passengers",
            paper_bgcolor="#fefae0",
            plot_bgcolor="#e9edc9",
            font=dict(color="#3b3a2f"),
            legend=dict(bgcolor="#faedcd"),
        )
        pio.write_html(plotly_bar, OUTPUT_DIR / "chart_zone_bar.html", include_plotlyjs="cdn")

    delay_values = df["delay_min"].dropna()
    if delay_values.empty:
        print("Warning: delay histogram panel skipped because dataframe is empty.")
        _write_empty_chart("chart_delay_histogram.html", "Distribution of Train Delays")
    else:
        axes[1, 0].hist(delay_values, bins=20, density=True, alpha=0.75, color="#e94560")
        mu = delay_values.mean()
        sigma = delay_values.std(ddof=0)
        x = np.linspace(delay_values.min(), delay_values.max(), 200)
        y_norm = np.zeros_like(x)
        if sigma > 0:
            y_norm = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-((x - mu) ** 2) / (2 * sigma**2))
            axes[1, 0].plot(x, y_norm, color="#64ffda")
        axes[1, 0].set_title("Distribution of Train Delays")
        axes[1, 0].set_xlabel("Delay (minutes)")
        axes[1, 0].set_ylabel("Density")

        mu_plotly = delay_values.mean()
        sigma_plotly = delay_values.std()
        x_norm = np.linspace(delay_values.min(), delay_values.max(), 200)
        y_norm_plotly = np.zeros_like(x_norm)
        if sigma_plotly > 0:
            y_norm_plotly = (1 / (sigma_plotly * np.sqrt(2 * np.pi))) * np.exp(
                -0.5 * ((x_norm - mu_plotly) / sigma_plotly) ** 2
            )
        plotly_hist = go.Figure()
        plotly_hist.add_trace(
            go.Histogram(
                x=delay_values,
                nbinsx=20,
                histnorm="probability density",
                name="Delay Distribution",
                marker_color="#ccd5ae",
                opacity=0.75,
            )
        )
        plotly_hist.add_trace(
            go.Scatter(
                x=x_norm,
                y=y_norm_plotly,
                name="Normal Curve",
                line=dict(color="#d4a373", width=2.5),
            )
        )
        plotly_hist.update_layout(
            title="Distribution of Train Delays",
            xaxis_title="Delay (minutes)",
            yaxis_title="Density",
            paper_bgcolor="#fefae0",
            plot_bgcolor="#e9edc9",
            font=dict(color="#3b3a2f"),
            hovermode="x",
            legend=dict(bgcolor="#faedcd"),
        )
        pio.write_html(plotly_hist, OUTPUT_DIR / "chart_delay_histogram.html", include_plotlyjs="cdn")

    route_stats = (
        df.groupby("route_id").agg(avg_passengers=("passengers", "mean"), avg_delay=("delay_min", "mean")).reset_index()
    )
    if route_stats.empty:
        print("Warning: route scatter panel skipped because dataframe is empty.")
        _write_empty_chart(
            "chart_route_scatter.html",
            "Route Efficiency: Avg Passengers vs Avg Delay (Top 10 Labelled)",
        )
    else:
        zone_by_route = (
            df.groupby("route_id")["zone"].agg(lambda s: s.mode().iat[0] if not s.mode().empty else "Unknown").reset_index()
        )
        route_stats = route_stats.merge(zone_by_route, on="route_id", how="left")
        zones = list(route_stats["zone"].fillna("Unknown").unique())
        cmap = plt.cm.tab10
        zone_colors = {zone: cmap(i % 10) for i, zone in enumerate(zones)}
        for zone in zones:
            subset = route_stats[route_stats["zone"] == zone]
            axes[1, 1].scatter(
                subset["avg_delay"],
                subset["avg_passengers"],
                label=zone,
                color=zone_colors[zone],
                alpha=0.8,
            )
        top_routes = route_stats.sort_values("avg_passengers", ascending=False).head(10)
        for _, row in top_routes.iterrows():
            axes[1, 1].annotate(
                row["route_id"],
                (row["avg_delay"], row["avg_passengers"]),
                fontsize=8,
                xytext=(4, 4),
                textcoords="offset points",
            )
        axes[1, 1].set_title("Route Efficiency: Avg Passengers vs Avg Delay")
        axes[1, 1].set_xlabel("Avg Delay (min)")
        axes[1, 1].set_ylabel("Avg Passengers")
        axes[1, 1].legend(title="Zone")

        route_grp = (
            df.groupby(["route_id", "zone"])
            .agg(avg_pass=("passengers", "mean"), avg_delay=("delay_min", "mean"))
            .reset_index()
        )
        top10 = route_grp.nlargest(10, "avg_pass")["route_id"]
        zone_colors_plotly = {
            "Beach": "#ccd5ae",
            "Egmore": "#d4a373",
            "Tambaram": "#faedcd",
            "Avadi": "#e9edc9",
            "Chengalpattu": "#bc4749",
            "Unknown": "#7a7060",
        }
        plotly_scatter = go.Figure()
        for zone in route_grp["zone"].unique():
            sub = route_grp[route_grp["zone"] == zone]
            plotly_scatter.add_trace(
                go.Scatter(
                    x=sub["avg_delay"],
                    y=sub["avg_pass"],
                    mode="markers+text",
                    text=sub.apply(lambda r: r["route_id"] if r["route_id"] in top10.values else "", axis=1),
                    textposition="top center",
                    name=zone,
                    marker=dict(size=10, color=zone_colors_plotly.get(zone, "#d4a373"), opacity=0.8),
                    customdata=sub[["route_id"]],
                    hovertemplate="<b>%{customdata[0]}</b><br>Delay: %{x:.1f} min<br>Passengers: %{y:.0f}<extra></extra>",
                )
            )
        plotly_scatter.update_layout(
            title="Route Efficiency: Avg Passengers vs Avg Delay (Top 10 Labelled)",
            xaxis_title="Avg Delay (min)",
            yaxis_title="Avg Passengers",
            paper_bgcolor="#fefae0",
            plot_bgcolor="#e9edc9",
            font=dict(color="#3b3a2f"),
            legend=dict(bgcolor="#faedcd"),
        )
        pio.write_html(plotly_scatter, OUTPUT_DIR / "chart_route_scatter.html", include_plotlyjs="cdn")

    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
    plt.close()
