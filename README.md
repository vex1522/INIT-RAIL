# 🚆 Chennai Suburban Rail — Traffic Analysis Dashboard
## Hackathon Set A | Team SetA

### Quick Start (Local)
```bash
pip install -r requirements.txt
python solution.py          # Run all 4 analysis tasks
python app.py               # Launch web dashboard → http://localhost:5000
```

### Quick Start (Docker)
```bash
docker compose up --build   # → http://localhost:5000
```

### Output Files
| File | Location | Description |
|---|---|---|
| `cleaned_ridership.csv` | `outputs/` | Cleaned 500-row dataset |
| `train_mobility_dashboard.png` | `outputs/` | 4-panel analytics figure (150 DPI) |
| `railway_mobility_map.html` | `outputs/` | Interactive Folium zone map |

### Architecture
```
Browser  ──GET/POST──►  Flask (app.py)
                            │
                     ┌──────┴──────┐
                     │  subprocess │
                     │ solution.py │
                     └──────┬──────┘
              task1  task2  task3  task4
                ↓      ↓      ↓      ↓
              CSV   stdout  PNG   HTML map
```

### Submission
Zip as: `Team_<Name>_SetA.zip`
Contains: all `.py` files, `cleaned_ridership.csv`, `train_mobility_dashboard.png`, `railway_mobility_map.html`
