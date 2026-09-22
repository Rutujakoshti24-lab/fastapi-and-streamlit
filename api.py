
"""
Automated Data Analytics Dashboard - FastAPI Backend
------------------------------------------------------
Handles CSV upload, statistical analysis, and data-cleaning operations.
Run with: uvicorn api:app --reload
Swagger docs available at: http://localhost:8000/docs
"""

import io
from typing import Optional, List, Dict, Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

<<<<<<< HEAD

=======
>>>>>>> 71a641bc34554c88333d62ef8698f2241a3337c1
# --------------------------------------------------------------------------
# App setup
# --------------------------------------------------------------------------

app = FastAPI(
    title="Automated Data Analytics Dashboard API",
    description="REST API for uploading, analyzing, and cleaning CSV datasets.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# In-memory dataset store
# --------------------------------------------------------------------------

class DataStore:
    """Holds the currently uploaded dataset in memory for this simple,
    single-session demo app. The original upload is kept separate from the
    current (possibly cleaned) version so cleaning never mutates the source.
    """
    original_df: Optional[pd.DataFrame] = None
    current_df: Optional[pd.DataFrame] = None
    filename: Optional[str] = None


store = DataStore()


def _ensure_dataset_loaded() -> None:
    if store.current_df is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No dataset uploaded yet. Please upload a CSV file via /upload first.",
        )


def _safe_json(obj: Any) -> Any:
    """Recursively convert numpy/pandas types into plain, JSON-safe Python
    types (NaN/NaT become None)."""
    if isinstance(obj, dict):
        return {str(k): _safe_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_json(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return None if np.isnan(obj) else float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if obj is pd.NaT:
        return None
    if isinstance(obj, pd.Timestamp):
        return None if pd.isna(obj) else obj.isoformat()
    if isinstance(obj, float) and np.isnan(obj):
        return None
    return obj


# --------------------------------------------------------------------------
# Pydantic models
# --------------------------------------------------------------------------

class CleaningOptions(BaseModel):
    remove_duplicates: bool = False
    fill_numeric_method: Optional[str] = Field(
        default=None, description="One of 'mean', 'median', or null/None."
    )
    fill_categorical_mode: bool = False
    drop_missing_rows: bool = False
    convert_types: Optional[Dict[str, str]] = Field(
        default=None,
        description=(
            "Mapping of column name -> target dtype. "
            "Supported types: 'int', 'float', 'str', 'category', 'datetime'."
        ),
    )


class UploadResponse(BaseModel):
    filename: str
    rows: int
    columns: int
    message: str


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@app.get("/", tags=["General"])
def root():
    """Basic API info."""
    return {
        "message": "Automated Data Analytics Dashboard API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["General"])
def health():
    """Simple health check used by the frontend to verify the API is up."""
    return {"status": "ok", "dataset_loaded": store.current_df is not None}


@app.post("/upload", response_model=UploadResponse, tags=["Dataset"])
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file. Replaces any previously loaded dataset."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV file: {exc}")

    if df.shape[0] == 0 or df.shape[1] == 0:
        raise HTTPException(status_code=400, detail="The uploaded CSV contains no data.")

    store.original_df = df.copy()
    store.current_df = df.copy()
    store.filename = file.filename

    return UploadResponse(
        filename=file.filename,
        rows=df.shape[0],
        columns=df.shape[1],
        message="File uploaded and processed successfully.",
    )


@app.get("/overview", tags=["Analysis"])
def overview():
    """Row/column counts, column types, total missing values, and duplicates."""
    _ensure_dataset_loaded()
    df = store.current_df
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

    return _safe_json({
        "filename": store.filename,
        "rows": df.shape[0],
        "columns": df.shape[1],
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "total_missing_values": int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "column_dtypes": {c: str(t) for c, t in df.dtypes.items()},
    })


@app.get("/summary", tags=["Analysis"])
def summary():
    """Descriptive statistics (count, mean, std, min, quartiles, max) for numeric columns."""
    _ensure_dataset_loaded()
    df = store.current_df
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return {"message": "No numerical columns found in this dataset.", "summary": {}}
    return _safe_json({"summary": numeric_df.describe().to_dict()})


@app.get("/missing-values", tags=["Analysis"])
def missing_values():
    """Per-column missing value counts and percentages."""
    _ensure_dataset_loaded()
    df = store.current_df
    counts = df.isnull().sum()
    percentages = (df.isnull().mean() * 100).round(2)

    result = {
        col: {
            "missing_count": int(counts[col]),
            "missing_percentage": float(percentages[col]),
        }
        for col in df.columns
    }
    return _safe_json({"missing_values": result, "total_missing": int(counts.sum())})


@app.get("/duplicates", tags=["Analysis"])
def duplicates():
    """Duplicate row count plus a small sample of duplicate rows."""
    _ensure_dataset_loaded()
    df = store.current_df
    dup_mask = df.duplicated()
    sample = df[dup_mask].head(10).to_dict(orient="records")
    return _safe_json({"duplicate_count": int(dup_mask.sum()), "sample_duplicates": sample})


@app.get("/correlation", tags=["Analysis"])
def correlation():
    """Pearson correlation matrix across all numeric columns."""
    _ensure_dataset_loaded()
    df = store.current_df
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        return {
            "message": "Not enough numerical columns for correlation analysis.",
            "correlation": {},
        }
    return _safe_json({"correlation": numeric_df.corr().round(3).to_dict()})


@app.get("/insights", tags=["Analysis"])
def insights():
    """Automatically generated, plain-language insights about the dataset."""
    _ensure_dataset_loaded()
    df = store.current_df
    generated: List[str] = []

    generated.append(f"The dataset contains {df.shape[0]} rows and {df.shape[1]} columns.")

    missing_total = int(df.isnull().sum().sum())
    if missing_total > 0:
        worst_col = df.isnull().sum().idxmax()
        worst_pct = round(df[worst_col].isnull().mean() * 100, 1)
        generated.append(
            f"The dataset has {missing_total} missing values in total; "
            f"'{worst_col}' has the most missing data ({worst_pct}%)."
        )
    else:
        generated.append("The dataset has no missing values.")

    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        generated.append(f"There are {dup_count} duplicate rows in the dataset.")
    else:
        generated.append("No duplicate rows were found.")

    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        for col in numeric_df.columns[:5]:
            skew = numeric_df[col].skew()
            if pd.notna(skew) and abs(skew) > 1:
                direction = "right" if skew > 0 else "left"
                generated.append(f"Column '{col}' is heavily skewed to the {direction}.")

        if numeric_df.shape[1] >= 2:
            corr = numeric_df.corr().abs()
            np.fill_diagonal(corr.values, 0)
            if corr.max().max() > 0.7:
                max_pair = corr.stack().idxmax()
                generated.append(
                    f"Strong correlation detected between '{max_pair[0]}' and "
                    f"'{max_pair[1]}' ({corr.loc[max_pair[0], max_pair[1]]:.2f})."
                )

    categorical_df = df.select_dtypes(exclude=[np.number])
    if not categorical_df.empty:
        for col in categorical_df.columns[:5]:
            unique_count = df[col].nunique()
            if unique_count == 1:
                generated.append(f"Column '{col}' has only a single unique value.")
            elif unique_count == df.shape[0]:
                generated.append(f"Column '{col}' looks like a unique identifier column.")

    return {"insights": generated}


@app.post("/clean", tags=["Cleaning"])
def clean_dataset(options: CleaningOptions):
    """Apply selected cleaning operations to a COPY of the original upload
    and store the result as the current dataset. The original upload is
    never modified, so cleaning options can be re-applied freely."""
    _ensure_dataset_loaded()
    df = store.original_df.copy()

    try:
        if options.remove_duplicates:
            df = df.drop_duplicates()

        if options.fill_numeric_method in ("mean", "median"):
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if df[col].isnull().any():
                    value = (
                        df[col].mean()
                        if options.fill_numeric_method == "mean"
                        else df[col].median()
                    )
                    df[col] = df[col].fillna(value)

        if options.fill_categorical_mode:
            categorical_cols = df.select_dtypes(exclude=[np.number]).columns
            for col in categorical_cols:
                if df[col].isnull().any() and not df[col].mode().empty:
                    df[col] = df[col].fillna(df[col].mode()[0])

        if options.drop_missing_rows:
            df = df.dropna()

        if options.convert_types:
            for col, dtype in options.convert_types.items():
                if col not in df.columns:
                    continue
                try:
                    if dtype == "int":
                        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
                    elif dtype == "float":
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                    elif dtype == "str":
                        df[col] = df[col].astype(str)
                    elif dtype == "category":
                        df[col] = df[col].astype("category")
                    elif dtype == "datetime":
                        df[col] = pd.to_datetime(df[col], errors="coerce")
                    else:
                        raise ValueError(f"Unsupported target type '{dtype}'.")
                except Exception as exc:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Could not convert column '{col}' to {dtype}: {exc}",
                    )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cleaning operation failed: {exc}")

    store.current_df = df

    return _safe_json({
        "message": "Cleaning operations applied successfully.",
        "rows": df.shape[0],
        "columns": df.shape[1],
        "remaining_missing_values": int(df.isnull().sum().sum()),
        "column_dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "data": df.to_dict(orient="records"),
<<<<<<< HEAD
    })
=======
    })
>>>>>>> 71a641bc34554c88333d62ef8698f2241a3337c1
