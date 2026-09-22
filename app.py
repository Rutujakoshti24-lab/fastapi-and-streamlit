
"""
Automated Data Analytics Dashboard - Streamlit Frontend
----------------------------------------------------------
Uploads a CSV to the FastAPI backend and renders an interactive analytics
dashboard from the JSON it returns.
Run with: streamlit run app.py
(Make sure the FastAPI backend is already running: uvicorn api:app --reload)
"""

import io

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# --------------------------------------------------------------------------
# Configuration - change this if your FastAPI backend runs elsewhere
# --------------------------------------------------------------------------
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Automated Data Analytics Dashboard", layout="wide")


# --------------------------------------------------------------------------
# Helpers for talking to the FastAPI backend
# --------------------------------------------------------------------------

def api_get(endpoint: str, params: dict | None = None):
    try:
        resp = requests.get(f"{API_URL}{endpoint}", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "connection"
    except requests.exceptions.HTTPError:
        try:
            return None, resp.json().get("detail", "Unknown error.")
        except Exception:
            return None, str(resp.status_code)
    except Exception as exc:
        return None, str(exc)


def api_post_file(endpoint: str, file_bytes: bytes, filename: str):
    try:
        files = {"file": (filename, file_bytes, "text/csv")}
        resp = requests.post(f"{API_URL}{endpoint}", files=files, timeout=60)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "connection"
    except requests.exceptions.HTTPError:
        try:
            return None, resp.json().get("detail", "Unknown error.")
        except Exception:
            return None, str(resp.status_code)
    except Exception as exc:
        return None, str(exc)


def api_post_json(endpoint: str, payload: dict):
    try:
        resp = requests.post(f"{API_URL}{endpoint}", json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "connection"
    except requests.exceptions.HTTPError:
        try:
            return None, resp.json().get("detail", "Unknown error.")
        except Exception:
            return None, str(resp.status_code)
    except Exception as exc:
        return None, str(exc)


def show_connection_error():
    st.error(
        f"⚠️ Could not connect to the FastAPI backend at `{API_URL}`.\n\n"
        "Make sure it is running in a separate terminal:\n\n"
        "```bash\nuvicorn api:app --reload\n```"
    )


# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------
if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "cleaned_df" not in st.session_state:
    st.session_state.cleaned_df = None

# --------------------------------------------------------------------------
# Header + upload
# --------------------------------------------------------------------------
st.title("📊 Automated Data Analytics Dashboard")
st.caption("Upload any CSV file to get an instant, interactive data analysis report.")

uploaded_file = st.file_uploader("Upload a CSV dataset", type=["csv"])

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()

    if st.session_state.uploaded_filename != uploaded_file.name:
        with st.spinner("Uploading and processing dataset..."):
            result, error = api_post_file("/upload", file_bytes, uploaded_file.name)

        if error == "connection":
            show_connection_error()
            st.stop()
        elif error:
            st.error(f"Upload failed: {error}")
            st.stop()
        else:
            try:
                parsed_df = pd.read_csv(io.BytesIO(file_bytes))
            except Exception as exc:
                st.error(f"Could not read CSV for preview: {exc}")
                st.stop()

            st.session_state.uploaded_filename = uploaded_file.name
            st.session_state.raw_df = parsed_df
            st.session_state.cleaned_df = None
            st.success(f"✅ {result['message']} ({result['rows']} rows, {result['columns']} columns)")

if st.session_state.raw_df is None:
    st.info("👆 Upload a CSV file to get started.")
    st.stop()

df = st.session_state.raw_df

# --------------------------------------------------------------------------
# Overview (from FastAPI)
# --------------------------------------------------------------------------
overview_data, error = api_get("/overview")
if error == "connection":
    show_connection_error()
    st.stop()
elif error:
    st.error(f"Could not fetch overview: {error}")
    st.stop()

st.subheader("Dataset Overview")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Rows", overview_data["rows"])
c2.metric("Columns", overview_data["columns"])
c3.metric("Numeric Cols", len(overview_data["numeric_columns"]))
c4.metric("Categorical Cols", len(overview_data["categorical_columns"]))
c5.metric("Missing Values", overview_data["total_missing_values"])
c6.metric("Duplicate Rows", overview_data["duplicate_rows"])

numeric_cols = overview_data["numeric_columns"]
categorical_cols = overview_data["categorical_columns"]

tabs = st.tabs([
    "Preview", "Data Types", "Missing Values", "Duplicates",
    "Statistical Summary", "Numerical Analysis", "Categorical Analysis",
    "Correlation", "Outliers", "Visualizations", "Insights", "Data Cleaning",
])

# ---------------- Preview ----------------
with tabs[0]:
    st.dataframe(df.head(50), use_container_width=True)

# ---------------- Data types ----------------
with tabs[1]:
    dtype_df = pd.DataFrame({
        "Column": list(overview_data["column_dtypes"].keys()),
        "Data Type": list(overview_data["column_dtypes"].values()),
    })
    st.dataframe(dtype_df, use_container_width=True)

# ---------------- Missing values ----------------
with tabs[2]:
    mv_data, error = api_get("/missing-values")
    if error == "connection":
        show_connection_error()
    elif error:
        st.error(error)
    else:
        mv_df = pd.DataFrame([
            {"Column": col, **vals} for col, vals in mv_data["missing_values"].items()
        ])
        st.dataframe(mv_df, use_container_width=True)
        nonzero = mv_df[mv_df["missing_count"] > 0]
        if not nonzero.empty:
            fig = px.bar(nonzero, x="Column", y="missing_count", title="Missing Values per Column")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("No missing values detected.")

# ---------------- Duplicates ----------------
with tabs[3]:
    dup_data, error = api_get("/duplicates")
    if error == "connection":
        show_connection_error()
    elif error:
        st.error(error)
    else:
        st.metric("Duplicate Rows", dup_data["duplicate_count"])
        if dup_data["sample_duplicates"]:
            st.write("Sample duplicate rows:")
            st.dataframe(pd.DataFrame(dup_data["sample_duplicates"]), use_container_width=True)
        else:
            st.success("No duplicate rows detected.")

# ---------------- Statistical summary ----------------
with tabs[4]:
    summary_data, error = api_get("/summary")
    if error == "connection":
        show_connection_error()
    elif error:
        st.error(error)
    elif summary_data.get("summary"):
        st.dataframe(pd.DataFrame(summary_data["summary"]), use_container_width=True)
    else:
        st.info(summary_data.get("message", "No numerical columns."))

# ---------------- Numerical analysis ----------------
with tabs[5]:
    if numeric_cols:
        col_choice = st.selectbox("Select a numeric column", numeric_cols, key="num_col")
        fig_hist = px.histogram(df, x=col_choice, marginal="box", title=f"Distribution of {col_choice}")
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("No numeric columns found in this dataset.")

# ---------------- Categorical analysis ----------------
with tabs[6]:
    if categorical_cols:
        cat_choice = st.selectbox("Select a categorical column", categorical_cols, key="cat_col")
        value_counts = df[cat_choice].value_counts().head(20).reset_index()
        value_counts.columns = [cat_choice, "count"]
        fig_bar = px.bar(value_counts, x=cat_choice, y="count", title=f"Top values in {cat_choice}")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No categorical columns found in this dataset.")

# ---------------- Correlation ----------------
with tabs[7]:
    corr_data, error = api_get("/correlation")
    if error == "connection":
        show_connection_error()
    elif error:
        st.error(error)
    elif corr_data.get("correlation"):
        corr_df = pd.DataFrame(corr_data["correlation"])
        fig_corr = px.imshow(corr_df, text_auto=True, aspect="auto", title="Correlation Heatmap")
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info(corr_data.get("message", "Not enough numeric columns for correlation analysis."))

# ---------------- Outliers ----------------
with tabs[8]:
    if numeric_cols:
        outlier_col = st.selectbox(
            "Select a numeric column for outlier analysis", numeric_cols, key="outlier_col"
        )
        series = df[outlier_col].dropna()
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = series[(series < lower) | (series > upper)]
        st.write(
            f"IQR bounds: **[{lower:.2f}, {upper:.2f}]** — "
            f"**{len(outliers)}** outliers detected out of {len(series)} values."
        )
        fig_box = px.box(df, y=outlier_col, title=f"Outliers in {outlier_col} (IQR method)")
        st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("No numeric columns found in this dataset.")

# ---------------- Visualizations ----------------
with tabs[9]:
    st.write("Build your own interactive chart:")
    chart_type = st.selectbox("Chart type", ["Scatter", "Line", "Bar", "Histogram", "Box"])
    all_cols = df.columns.tolist()

    if chart_type in ("Scatter", "Line"):
        x_axis = st.selectbox("X axis", all_cols, key="viz_x")
        y_axis = st.selectbox("Y axis", numeric_cols if numeric_cols else all_cols, key="viz_y")
        color_col = st.selectbox("Color by (optional)", ["None"] + all_cols, key="viz_color")
        color_arg = None if color_col == "None" else color_col
        fig = (
            px.scatter(df, x=x_axis, y=y_axis, color=color_arg)
            if chart_type == "Scatter"
            else px.line(df, x=x_axis, y=y_axis, color=color_arg)
        )
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Bar":
        x_axis = st.selectbox("X axis", all_cols, key="viz_bar_x")
        y_axis = st.selectbox("Y axis", numeric_cols if numeric_cols else all_cols, key="viz_bar_y")
        fig = px.bar(df, x=x_axis, y=y_axis)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Histogram":
        col = st.selectbox("Column", numeric_cols if numeric_cols else all_cols, key="viz_hist")
        fig = px.histogram(df, x=col)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Box":
        col = st.selectbox("Column", numeric_cols if numeric_cols else all_cols, key="viz_box")
        fig = px.box(df, y=col)
        st.plotly_chart(fig, use_container_width=True)

# ---------------- Insights ----------------
with tabs[10]:
    insights_data, error = api_get("/insights")
    if error == "connection":
        show_connection_error()
    elif error:
        st.error(error)
    else:
        for point in insights_data["insights"]:
            st.markdown(f"- {point}")

# ---------------- Data cleaning ----------------
with tabs[11]:
    st.write("Configure cleaning operations. These are always applied to a **copy** "
             "of the original uploaded data, never to the original file.")

    col_a, col_b = st.columns(2)
    with col_a:
        remove_duplicates = st.checkbox("Remove duplicate rows")
        fill_method = st.selectbox("Fill missing numeric values using", ["None", "Mean", "Median"])
        fill_categorical = st.checkbox("Fill missing categorical values with Mode")
        drop_missing = st.checkbox("Drop rows with any missing values")
    with col_b:
        st.write("Convert a column's data type (optional):")
        convert_col = st.selectbox("Column", ["None"] + df.columns.tolist(), key="convert_col")
        convert_type = st.selectbox(
            "Target type", ["int", "float", "str", "category", "datetime"], key="convert_type"
        )

    if st.button("Apply Cleaning", type="primary"):
        options = {
            "remove_duplicates": remove_duplicates,
            "fill_numeric_method": None if fill_method == "None" else fill_method.lower(),
            "fill_categorical_mode": fill_categorical,
            "drop_missing_rows": drop_missing,
            "convert_types": {convert_col: convert_type} if convert_col != "None" else None,
        }
        with st.spinner("Applying cleaning operations..."):
            result, error = api_post_json("/clean", options)

        if error == "connection":
            show_connection_error()
        elif error:
            st.error(f"Cleaning failed: {error}")
        else:
            st.session_state.cleaned_df = pd.DataFrame(result["data"])
            st.success(
                f"✅ Cleaning applied. Rows: {result['rows']}, "
                f"Remaining missing values: {result['remaining_missing_values']}"
            )

    if st.session_state.cleaned_df is not None:
        st.write("Cleaned dataset preview:")
        st.dataframe(st.session_state.cleaned_df.head(50), use_container_width=True)
        csv_bytes = st.session_state.cleaned_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Cleaned Dataset (CSV)",
            data=csv_bytes,
            file_name="cleaned_dataset.csv",
            mime="text/csv",
        )