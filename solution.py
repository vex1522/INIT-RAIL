#!/usr/bin/env python3
"""Chennai Suburban Rail Traffic Analysis - Hackathon Set A."""

import sys
from pathlib import Path


def main() -> None:
    """Run all analysis tasks in sequence."""
    Path("data").mkdir(exist_ok=True)
    Path("outputs").mkdir(exist_ok=True)

    from tasks import task1_cleaning, task2_ranking, task3_visualization, task4_map

    print("=" * 60)
    print("TASK 1 | Data Ingestion & Cleaning")
    print("=" * 60)
    df = task1_cleaning.run()
    print("OK Saved: outputs/cleaned_ridership.csv")

    print("\n" + "=" * 60)
    print("TASK 2 | Route Efficiency Ranking (Merge Sort)")
    print("=" * 60)
    ranked = task2_ranking.run(df)
    print(f"OK Ranked {len(ranked)} routes")

    print("\n" + "=" * 60)
    print("TASK 3 | Statistical Visualization")
    print("=" * 60)
    task3_visualization.run(df)
    print("OK Saved: outputs/train_mobility_dashboard.png")

    print("\n" + "=" * 60)
    print("TASK 4 | Interactive Zone Map")
    print("=" * 60)
    task4_map.run(df)
    print("OK Saved: outputs/railway_mobility_map.html")

    print("\n" + "=" * 60)
    print("ALL TASKS COMPLETE. See /outputs/ directory.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
