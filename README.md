# fastapi-and-streamlit
# Automated Data Analytics Dashboard

An interactive, full-stack data analysis dashboard built with **Streamlit** (frontend) and **FastAPI** (backend). Upload any CSV dataset and instantly get an overview, statistical summary, missing-value and duplicate analysis, correlation analysis, outlier detection, interactive Plotly visualizations, automatically generated insights, and data-cleaning tools — all without writing a single line of code.

## Description

This project combines **Streamlit** and **FastAPI** to provide an end-to-end, interactive CSV data-analysis dashboard. Streamlit handles the user interface, while FastAPI handles all the actual data-processing logic (statistics, missing-value analysis, correlation, insights, and cleaning) and exposes it as a REST API with automatic Swagger documentation. The two communicate over HTTP using the `requests` library, so the analysis logic is fully decoupled from the presentation layer.

## Features

- 📤 CSV upload (any dataset — no hardcoded columns)
- 📋 Dataset overview (rows, columns, types, missing values, duplicates)
- 👁️ Dataset preview
- 🔤 Data types breakdown
- ❓ Missing-value analysis
- 🔁 Duplicate row analysis
- 📈 Statistical summary (mean, std, quartiles, etc.)
- 🔢 Numerical column analysis (distribution, box plot)
- 🏷️ Categorical column analysis (value counts)
- 🔗 Correlation analysis (interactive heatmap)
- 🎯 Outlier detection (IQR method)
- 📊 Interactive visualizations (scatter, line, bar, histogram, box)
- 💡 Automatically generated key insights
- 🧹 Data cleaning (duplicates, missing values, type conversion)
- ⬇️ Download cleaned dataset as CSV
- ⚡ FastAPI REST API with full error handling
- 📚 Interactive Swagger API documentation

## Technologies Used

- Python
- FastAPI
- Streamlit
- Pandas
- NumPy
- Plotly
- Requests
- Pydantic
- Uvicorn

## Project Structure

```
data-analytics-dashboard/
│
├── app.py            # Streamlit frontend (dashboard UI)
├── api.py             # FastAPI backend (analysis + cleaning logic)
├── requirements.txt   # Python dependencies
└── README.md          # Project documentation
```

## Installation

Clone the repository and set up a virtual environment:

```bash
git clone <repository-url>
cd data-analytics-dashboard
python -m venv venv
```

Activate the virtual environment:

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Running the Project

The FastAPI backend and Streamlit frontend run as two separate processes, so you'll need **two terminals** (both with the virtual environment activated).

**Terminal 1 — start the backend:**
```bash
uvicorn api:app --reload
```

**Terminal 2 — start the frontend:**
```bash
streamlit run app.py
```

Default URLs:

| Service            | URL                              |
|--------------------|-----------------------------------|
| FastAPI backend    | http://localhost:8000            |
| Swagger API docs   | http://localhost:8000/docs       |
| Streamlit dashboard| http://localhost:8501            |

> If your backend runs on a different host or port, update the `API_URL` constant at the top of `app.py`.

## How It Works

```
CSV Upload
    ↓
Streamlit (app.py)
    ↓  (HTTP request via `requests`)
FastAPI (api.py)
    ↓
Pandas / NumPy processing
    ↓
Data Analysis (stats, missing values, duplicates, correlation, insights)
    ↓
FastAPI JSON Response
    ↓
Streamlit Dashboard (tables, metrics, Plotly charts)
```

The uploaded file is sent to the FastAPI `/upload` endpoint and stored server-side. Every subsequent dashboard section (overview, missing values, duplicates, summary, correlation, insights) calls a dedicated FastAPI GET endpoint and renders the returned JSON. Cleaning operations are sent to the `/clean` POST endpoint, which always operates on a fresh copy of the original upload — the source data is never mutated.

## API Endpoints

| Method | Endpoint          | Description                                              |
|--------|-------------------|------------------------------------------------------------|
| GET    | `/`               | Basic API info                                            |
| GET    | `/health`         | Health check + whether a dataset is currently loaded      |
| POST   | `/upload`         | Upload a CSV file                                          |
| GET    | `/overview`       | Row/column counts, column types, missing values, duplicates|
| GET    | `/summary`        | Descriptive statistics for numeric columns                 |
| GET    | `/missing-values` | Per-column missing value counts and percentages            |
| GET    | `/duplicates`     | Duplicate row count and sample duplicate rows               |
| GET    | `/correlation`    | Correlation matrix for numeric columns                     |
| GET    | `/insights`       | Automatically generated, plain-language insights            |
| POST   | `/clean`          | Apply cleaning operations and return the cleaned dataset    |

Full interactive documentation (with request/response schemas) is available at `/docs` while the backend is running.

## Error Handling

- **Invalid CSV files**: rejected with a clear `400` error if the file can't be parsed or isn't a `.csv`.
- **Empty datasets**: rejected if the file has no rows or columns.
- **Missing columns**: analysis endpoints gracefully report "no numeric/categorical columns found" instead of crashing.
- **Unsupported data types**: type-conversion errors return a descriptive `400` error naming the offending column.
- **FastAPI connection failure**: the Streamlit app detects connection errors and shows a friendly message with the exact command to start the backend, instead of crashing.
- **Invalid cleaning operations**: caught and returned as a `400` error with details, without corrupting the in-memory dataset.

## Future Improvements

- 🤖 Machine Learning predictions (regression/classification on the uploaded data)
- 🔐 User authentication
- 🗄️ Database integration (persist datasets between sessions)
- 📄 Export full analysis reports as PDF
- 📊 Advanced dashboards (multi-dataset comparison, time-series analysis)
- 🐳 Deployment using Docker
- ☁️ Cloud deployment (AWS / GCP / Azure)

## Screenshots

_Add screenshots of the dashboard here once you have it running, e.g.:_

```
screenshots/
├── overview.png
├── correlation.png
└── insights.png
```

## License

This project is licensed under the MIT License.

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
