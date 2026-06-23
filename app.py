import hashlib
import html
import json
import re
import time
from datetime import date, datetime
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

CUSTOMER_EXPORT_VERSION = "Customer export v8"
FIXED_REPORT_START_DATE = "09/01/2025"
APP_CACHE_VERSION = "full-transactions-v24-site-persist-compare"


st.set_page_config(
    page_title="Inventory Shortage Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        :root { --soft-bg:#F5F5F7; --card:#FFFFFF; --text:#111827; --muted:#6B7280; --line:rgba(17,24,39,.10); }
        .main .block-container {
            padding-top: 0.65rem;
            padding-bottom: 1.15rem;
            max-width: 1500px;
            animation: fadeIn 0.35s ease-in-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }
        header, footer {visibility: hidden;}
        .page-header {
            margin: 0 0 0.75rem 0;
            padding-bottom: 0.45rem;
            border-bottom: 1px solid rgba(17,24,39,.07);
        }
        .page-title {
            font-size: 1.82rem;
            font-weight: 850;
            color: #111827;
            letter-spacing: -0.035em;
            line-height: 1.12;
            margin-bottom: 0.18rem;
        }
        .page-subtitle {
            font-size: 0.88rem;
            color: #6B7280;
            line-height: 1.35;
        }
        .section-block {
            margin-top: 1.05rem;
        }
        .section-divider {
            height: 1px;
            background: rgba(17,24,39,.08);
            margin: 1.18rem 0 0.85rem 0;
        }
        .kpi-row-gap { height: 0.58rem; }
        .kpi-card {
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 14px 15px 12px 15px;
            background: rgba(255,255,255,0.88);
            box-shadow: 0 7px 24px rgba(16, 24, 40, 0.065);
            min-height: 96px;
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }
        .kpi-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(16, 24, 40, 0.10);
            border-color: rgba(0,0,0,0.12);
        }
        .kpi-label {font-size: 0.80rem; color:#6B7280; font-weight: 650; margin-bottom: 6px;}
        .kpi-value {font-size: 1.62rem; color:#111827; font-weight: 800; line-height: 1.08; letter-spacing:-0.03em;}
        .kpi-help {font-size: 0.74rem; color:#9CA3AF; margin-top: 7px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
        .section-title {font-size:1.11rem; font-weight:820; color:#111827; margin: 0 0 0.18rem 0; line-height:1.25;}
        .section-subtitle {font-size:0.84rem; color:#6B7280; margin: 0 0 0.55rem 0; line-height:1.35;}
        .small-note {
            display: inline-block;
            font-size:0.81rem;
            color:#6B7280;
            background: rgba(255,255,255,0.74);
            border: 1px solid rgba(17,24,39,.07);
            border-radius: 999px;
            padding: 6px 10px;
            margin: 0.15rem 0 0.75rem 0;
        }
        .health-summary-card {
            border: 1px solid rgba(17,24,39,.08);
            border-radius: 18px;
            background: rgba(255,255,255,.92);
            box-shadow: 0 8px 26px rgba(16,24,40,.055);
            padding: 14px 16px;
            margin: 0.10rem 0 0.85rem 0;
        }
        .health-summary-title {
            font-size: .82rem;
            color: #6B7280;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: .055em;
            margin-bottom: 4px;
        }
        .health-summary-text {
            font-size: 1.02rem;
            color: #111827;
            font-weight: 400;
            line-height: 1.38;
        }
        .selected-sku-card {
            border: 1px solid rgba(17,24,39,.09);
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(255,255,255,.96), rgba(245,245,247,.90));
            box-shadow: 0 12px 36px rgba(16,24,40,.09);
            padding: 22px 24px;
            margin: 0.20rem 0 1.05rem 0;
            position: relative;
            overflow: hidden;
        }
        .selected-sku-card::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 6px;
            background: #111827;
        }
        .selected-sku-label {
            font-size: .82rem;
            color: #6B7280;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: .055em;
            margin-bottom: 8px;
        }
        .selected-sku-value {
            font-size: 2.35rem;
            color: #111827;
            font-weight: 900;
            line-height: 1.05;
            letter-spacing: -0.045em;
            word-break: break-word;
        }
        .selected-sku-description {
            font-size: 1.12rem;
            color: #374151;
            margin-top: 10px;
            line-height: 1.35;
            font-weight: 650;
            word-break: break-word;
        }
        .sidebar-note {
            background: #FFFFFF;
            border: 1px solid rgba(17,24,39,.08);
            border-radius: 16px;
            padding: 12px 13px 10px 13px;
            margin-top: 0.18rem;
            box-shadow: 0 4px 18px rgba(16,24,40,.05);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
            line-height: 1.42;
        }
        .sidebar-note:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(16,24,40,.08);
            border-color: rgba(17,24,39,.12);
        }
        .sidebar-section-title {
            font-size: .78rem;
            font-weight: 850;
            color: #111827;
            text-transform: uppercase;
            letter-spacing: .06em;
            margin: .10rem 0 .42rem 0;
            line-height: 1.2;
        }
        .sidebar-section-gap { height: .18rem; }
        div[data-testid="stDataFrame"] {border-radius: 14px; overflow: hidden; margin-top: 0.15rem;}
        div[data-testid="stSidebar"] {background:#F5F5F7; transition: background 0.25s ease;}
        div[data-testid="stSidebar"] > div:first-child {
            padding-top: 1.0rem;
            padding-left: 1.05rem;
            padding-right: 1.05rem;
        }
        div[data-testid="stSidebar"] h1 {
            font-size: 1.28rem;
            line-height: 1.16;
            margin: 0 0 .55rem 0;
        }
        div[data-testid="stSidebar"] hr {
            margin: .72rem 0 .66rem 0;
        }
        div[data-testid="stSidebar"] label {
            font-size: .82rem !important;
            font-weight: 720 !important;
            color: #374151 !important;
            margin-bottom: .20rem !important;
        }
        div[data-testid="stSidebar"] .stSelectbox,
        div[data-testid="stSidebar"] .stMultiSelect,
        div[data-testid="stSidebar"] .stNumberInput,
        div[data-testid="stSidebar"] .stTextInput {
            margin-bottom: .52rem;
        }
        div[data-testid="stSidebar"] .stSelectbox > div,
        div[data-testid="stSidebar"] .stMultiSelect > div,
        div[data-testid="stSidebar"] .stNumberInput > div,
        div[data-testid="stSidebar"] .stTextInput > div {
            margin-top: .10rem;
        }
        div[data-testid="stFileUploader"] section {
            border: 1.5px dashed rgba(17,24,39,.18);
            border-radius: 16px;
            background: rgba(255,255,255,0.86);
            padding: 16px;
            box-shadow: 0 8px 26px rgba(16,24,40,.06);
            transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease, background .18s ease;
        }
        div[data-testid="stFileUploader"] section:hover {
            transform: translateY(-2px);
            border-color: rgba(17,24,39,.34);
            background: #FFFFFF;
            box-shadow: 0 12px 34px rgba(16,24,40,.10);
        }
        .upload-title {
            font-size: 1.02rem;
            font-weight: 800;
            color: #111827;
            margin-top: .45rem;
            margin-bottom: .2rem;
        }
        .upload-subtitle {
            font-size: .86rem;
            color: #6B7280;
            margin-bottom: .75rem;
        }
        .loading-card {
            margin-top: .85rem;
            margin-bottom: .65rem;
            border: 1px solid rgba(17,24,39,.08);
            border-radius: 16px;
            background: rgba(255,255,255,.92);
            box-shadow: 0 6px 22px rgba(16,24,40,.06);
            padding: 14px 16px;
            animation: fadeIn .22s ease-in-out;
        }
        .loading-title {font-size:.95rem; font-weight:800; color:#111827;}
        .loading-subtitle {font-size:.82rem; color:#6B7280; margin-top:4px;}
        .stButton > button, .stDownloadButton > button {
            transition: all 0.18s ease;
            border-radius: 12px;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(16, 24, 40, 0.10);
        }
        div[data-testid="stTabs"] button {
            transition: color 0.18s ease, border-color 0.18s ease, background 0.18s ease;
        }
        div[data-testid="stExpander"] {
            transition: box-shadow 0.18s ease, border-color 0.18s ease;
        }
        div[data-testid="stExpander"]:hover {
            box-shadow: 0 6px 18px rgba(16, 24, 40, 0.06);
        }

        @keyframes uploadPulse {
            0% { box-shadow: 0 8px 26px rgba(16,24,40,.06), 0 0 0 0 rgba(17,24,39,.10); }
            50% { box-shadow: 0 14px 38px rgba(16,24,40,.12), 0 0 0 7px rgba(17,24,39,.035); }
            100% { box-shadow: 0 8px 26px rgba(16,24,40,.06), 0 0 0 0 rgba(17,24,39,.10); }
        }
        @keyframes cardEnter {
            from { opacity: 0; transform: translateY(10px) scale(.99); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        @keyframes shimmerMove {
            from { transform: translateX(-100%); }
            to { transform: translateX(260%); }
        }
        @keyframes dotPulse {
            0%, 80%, 100% { opacity: .25; transform: translateY(0); }
            40% { opacity: 1; transform: translateY(-3px); }
        }
        @keyframes checkPop {
            0% { transform: scale(.75); opacity: 0; }
            55% { transform: scale(1.12); opacity: 1; }
            100% { transform: scale(1); opacity: 1; }
        }
        @keyframes softGlow {
            0%, 100% { box-shadow: 0 8px 26px rgba(16,24,40,.06); }
            50% { box-shadow: 0 14px 34px rgba(16,24,40,.11); }
        }

        div[data-testid="stFileUploader"] section {
            animation: uploadPulse 2.2s ease-in-out infinite;
        }
        div[data-testid="stFileUploader"] section:hover {
            animation: none;
        }

        .upload-hero {
            border: 1px solid rgba(17,24,39,.08);
            border-radius: 18px;
            background: rgba(255,255,255,.82);
            box-shadow: 0 7px 22px rgba(16,24,40,.045);
            padding: 12px 15px;
            margin: .1rem 0 .55rem 0;
            animation: cardEnter .35s ease-out;
        }
        .upload-hero-title {
            font-size: 1.03rem;
            font-weight: 850;
            color: #111827;
            margin-bottom: 3px;
        }
        .upload-hero-subtitle {
            font-size: .86rem;
            color: #6B7280;
        }

        .loading-stage-card, .ready-stage-card {
            margin-top: .65rem;
            margin-bottom: .65rem;
            border: 1px solid rgba(17,24,39,.08);
            border-radius: 18px;
            background: rgba(255,255,255,.94);
            box-shadow: 0 10px 30px rgba(16,24,40,.08);
            padding: 16px 18px;
            animation: cardEnter .28s ease-out, softGlow 1.8s ease-in-out infinite;
        }
        .loading-row, .ready-row {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .loader-ring {
            width: 26px;
            height: 26px;
            border-radius: 50%;
            border: 3px solid rgba(17,24,39,.12);
            border-top-color: rgba(17,24,39,.72);
            animation: spin .75s linear infinite;
            flex: 0 0 auto;
        }
        .ready-check {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #111827;
            color: #FFFFFF;
            font-weight: 900;
            animation: checkPop .45s ease-out;
            flex: 0 0 auto;
        }
        .stage-title {
            font-size: .96rem;
            font-weight: 850;
            color: #111827;
            line-height: 1.25;
        }
        .stage-subtitle {
            font-size: .82rem;
            color: #6B7280;
            margin-top: 2px;
        }
        .animated-progress {
            position: relative;
            overflow: hidden;
            height: 9px;
            border-radius: 999px;
            background: rgba(17,24,39,.08);
            margin-top: 13px;
        }
        .animated-progress::before {
            content: "";
            position: absolute;
            inset: 0;
            width: 45%;
            border-radius: 999px;
            background: linear-gradient(90deg, transparent, rgba(17,24,39,.62), transparent);
            animation: shimmerMove 1.05s ease-in-out infinite;
        }
        .dots span {
            display: inline-block;
            animation: dotPulse 1.2s ease-in-out infinite;
        }
        .dots span:nth-child(2) { animation-delay: .15s; }
        .dots span:nth-child(3) { animation-delay: .30s; }
    </style>
    """,
    unsafe_allow_html=True,
)


FORMAT_CONFIGS = {
    "Newark": {
        "title": "Inventory Shortage",
        "sidebar_title": "📦 Inventory Dashboard",
        "caption": "Upload an Item Activity Report Excel file to generate the shortage dashboard.",
        "upload_label": "Drop Item Activity Report here",
        "placeholder": "Search SKU...",
        "help": "Select the matching report format before uploading the Excel file.",
        "cols": {
            "sku": 0,
            "description": 2,
            "activity_date": 7,
            "trans_no": 9,
            "ref_no": 10,
            "qty_in": 12,
            "qty_out": 14,
            "balance": 19,
            "ctn_balance": 20,
        },
        "total_rule": "ref_total",
        "total_source": "Ref # = Total",
        "wrong_format_warning": "Wrong file format for Newark. Switch to Carson or upload the Newark report.",
    },
    "Carson": {
        "title": "Inventory Shortage",
        "sidebar_title": "📦 Inventory Dashboard",
        "caption": "Upload an Item Activity Report Excel file to generate the shortage dashboard.",
        "upload_label": "Drop Item Activity Report here",
        "placeholder": "Search SKU...",
        "help": "Select the matching report format before uploading the Excel file.",
        "cols": {
            "sku": 1,
            "description": 3,
            "activity_date": 5,
            "trans_no": 6,
            "ref_no": 7,
            "qty_in": 8,
            "qty_out": 10,
            "balance": 12,
            "ctn_balance": 13,
        },
        "total_rule": "sku_totals",
        "total_source": "Column B = Totals:",
        "wrong_format_warning": "Wrong file format for Carson. Switch to Newark or upload the Carson report.",
    },
}


def clean_text(value) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    return str(value).replace("\u00a0", " ").replace("\u200b", "").strip()


def get_cell(row, col_idx):
    if col_idx is None:
        return None
    return row.iloc[col_idx] if len(row) > col_idx else None


def first_qty_number(value) -> float:
    text = clean_text(value)
    if not text:
        return 0.0
    text = text.replace(",", "")
    before_slash = text.split("/")[0]
    match = re.search(r"-?\d+(?:\.\d+)?", before_slash)
    return float(match.group()) if match else 0.0


def parse_excel_or_text_date(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return pd.NaT

    if isinstance(value, (datetime, pd.Timestamp)):
        return pd.to_datetime(value).normalize()

    if isinstance(value, date):
        return pd.to_datetime(value).normalize()

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value > 30000:
            return pd.to_datetime(value, unit="D", origin="1899-12-30").normalize()
        return pd.NaT

    text = clean_text(value)
    if not text:
        return pd.NaT

    text = re.sub(r"\s*\([^)]*\)", "", text).strip()
    parsed = pd.to_datetime(text, errors="coerce")
    return parsed.normalize() if not pd.isna(parsed) else pd.NaT


class WrongFileFormatError(ValueError):
    pass


PERSISTENT_UPLOAD_DIR = Path.home() / ".inventory_dashboard_uploads"


def stable_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def safe_format_slug(format_name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(format_name)).strip("_") or "report"


def persistent_upload_paths(format_name: str) -> tuple[Path, Path]:
    slug = safe_format_slug(format_name)
    return (
        PERSISTENT_UPLOAD_DIR / f"{slug}_upload.bin",
        PERSISTENT_UPLOAD_DIR / f"{slug}_upload.json",
    )

def save_persistent_upload(format_name: str, file_name: str, file_bytes: bytes) -> None:
    try:
        PERSISTENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        data_path, meta_path = persistent_upload_paths(format_name)
        data_path.write_bytes(file_bytes)
        meta = {
            "last_selected_format": format_name,
            "file_name": file_name,
            "size": len(file_bytes),
            "sha256": stable_file_hash(file_bytes),
            "saved_at": datetime.now().isoformat(timespec="seconds"),
        }
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
    except Exception:

        pass


def load_persistent_upload(format_name: str):
    try:
        data_path, meta_path = persistent_upload_paths(format_name)
        if not data_path.exists() or not meta_path.exists():
            return None
        file_bytes = data_path.read_bytes()
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("sha256") != stable_file_hash(file_bytes):
            return None
        return {
            "file_bytes": file_bytes,
            "file_name": meta.get("file_name", "Saved report.xlsx"),
            "size": meta.get("size", len(file_bytes)),
            "saved_at": meta.get("saved_at", ""),
            "last_selected_format": meta.get("last_selected_format", ""),
        }
    except Exception:
        return None


def find_header_row(raw: pd.DataFrame) -> int:
    for idx in range(len(raw)):
        row_values = [clean_text(x).lower() for x in raw.iloc[idx].tolist()]
        has_sku = "sku" in row_values
        has_activity = "activity date" in row_values
        has_ref = "ref #" in row_values
        if has_sku and has_activity and has_ref:
            return idx
    raise ValueError("Cannot find a header row with SKU / Activity Date / Ref #.")


def validate_selected_format(raw: pd.DataFrame, config: dict):
    header_idx = find_header_row(raw)
    header_row = raw.iloc[header_idx]
    cols = config["cols"]
    required_headers = {
        "sku": "sku",
        "activity_date": "activity date",
        "ref_no": "ref #",
        "qty_in": "qty",
        "qty_out": "qty",
        "balance": "balance",
    }

    for key, expected_text in required_headers.items():
        actual_header = clean_text(get_cell(header_row, cols[key])).lower()
        if expected_text not in actual_header:
            raise WrongFileFormatError(config["wrong_format_warning"])

    return header_idx


def extract_report_range(raw: pd.DataFrame):
    start_dt, end_dt = pd.NaT, pd.NaT

    for r in range(min(15, len(raw))):
        row = raw.iloc[r].tolist()
        row_text_original = " | ".join(clean_text(x) for x in row)
        row_text = row_text_original.lower()
        if "item activity from" not in row_text:
            continue


        match = re.search(
            r"item\s+activity\s+from:\s*(.*?)\s+to\s+(.*)$",
            row_text_original,
            flags=re.IGNORECASE,
        )
        if match:
            start_dt = parse_excel_or_text_date(match.group(1))
            end_dt = parse_excel_or_text_date(match.group(2))
            break


        to_index = None
        for i, value in enumerate(row):
            if clean_text(value).lower() == "to":
                to_index = i
                break

        dates_before_to, dates_after_to = [], []
        for i, value in enumerate(row):
            parsed = parse_excel_or_text_date(value)
            if not pd.isna(parsed):
                if to_index is not None and i > to_index:
                    dates_after_to.append(parsed)
                else:
                    dates_before_to.append(parsed)

        if dates_before_to:
            start_dt = dates_before_to[0]
        if dates_after_to:
            end_dt = dates_after_to[0]
        elif len(dates_before_to) >= 2:
            end_dt = dates_before_to[1]
        break

    return start_dt, end_dt


@st.cache_data(show_spinner=False)
def load_excel_to_raw(file_bytes: bytes) -> pd.DataFrame:
    return pd.read_excel(BytesIO(file_bytes), sheet_name=0, header=None, dtype=object)


@st.cache_data(show_spinner=False)
def process_excel_file(file_bytes: bytes, format_name: str, cache_version: str = APP_CACHE_VERSION) -> dict:
    raw_df = load_excel_to_raw(file_bytes)
    config = FORMAT_CONFIGS[format_name]
    validate_selected_format(raw_df, config)
    return build_inventory_model(raw_df, config, format_name)


def last_data_activity_dates(tx_df: pd.DataFrame, end_date, count: int) -> list:
    if tx_df.empty:
        return []
    end_date = pd.to_datetime(end_date).normalize()
    valid_dates = (
        pd.to_datetime(tx_df.loc[tx_df["Activity Date"].notna(), "Activity Date"])
        .dt.normalize()
        .drop_duplicates()
        .sort_values()
    )
    valid_dates = valid_dates[valid_dates <= end_date]
    return valid_dates.tail(count).tolist()


def add_calendar_days(start_date, days):
    if pd.isna(days) or not np.isfinite(days):
        return pd.NaT
    if days > 365:
        return pd.NaT
    return pd.to_datetime(start_date).normalize() + pd.Timedelta(days=int(np.floor(days)))


def build_inventory_model(raw: pd.DataFrame, config: dict, format_name: str) -> dict:
    header_idx = find_header_row(raw)
    report_start, report_end = extract_report_range(raw)
    rows = raw.iloc[header_idx + 1 :].copy()
    cols = config["cols"]

    current_sku = ""
    current_desc = ""
    sku_records = {}
    transactions = []
    official_total_rows = []
    official_ending_rows = []
    beginning_balance_rows = []
    not_shipped_rows = []
    cancelled_rows = []

    def ensure_sku_record(sku, desc):
        sku_records.setdefault(
            sku,
            {
                "SKU": sku,
                "Description": desc,
                "Official Total Inbound": 0.0,
                "Official Total Outbound": 0.0,
                "Ending Balance": 0.0,
                "Ctn Balance": 0.0,
                "Beginning Balance": 0.0,
                "Official Ending Row": None,
                "Official Total Row": None,
                "Last Activity Date": pd.NaT,
            },
        )
        if desc:
            sku_records[sku]["Description"] = desc

    for excel_row_num, row in rows.iterrows():
        sku_cell = clean_text(get_cell(row, cols["sku"]))
        desc_cell = clean_text(get_cell(row, cols["description"]))
        activity_raw = get_cell(row, cols["activity_date"])
        activity_text = clean_text(activity_raw)
        ref_text = clean_text(get_cell(row, cols["ref_no"]))
        trans_no = clean_text(get_cell(row, cols["trans_no"]))
        qty_in_raw = clean_text(get_cell(row, cols["qty_in"]))
        qty_out_raw = clean_text(get_cell(row, cols["qty_out"]))
        qty_in = first_qty_number(get_cell(row, cols["qty_in"]))
        qty_out = first_qty_number(get_cell(row, cols["qty_out"]))
        balance = first_qty_number(get_cell(row, cols["balance"]))
        ctn_balance = first_qty_number(get_cell(row, cols["ctn_balance"])) if cols.get("ctn_balance") is not None else 0.0

        sku_lower = sku_cell.lower()
        activity_lower = activity_text.lower()
        ref_lower = ref_text.lower()

        if config["total_rule"] == "sku_totals" and sku_lower == "totals:":
            if current_sku:
                ensure_sku_record(current_sku, current_desc)
                sku_records[current_sku]["Official Total Inbound"] = qty_in
                sku_records[current_sku]["Official Total Outbound"] = qty_out
                sku_records[current_sku]["Ending Balance"] = balance
                sku_records[current_sku]["Ctn Balance"] = ctn_balance
                sku_records[current_sku]["Official Total Row"] = excel_row_num + 1
                official_total_rows.append(
                    {
                        "Excel Row": excel_row_num + 1,
                        "SKU": current_sku,
                        "Description": sku_records[current_sku]["Description"],
                        "Source": config["total_source"],
                        "Official Total Inbound": qty_in,
                        "Official Total Outbound": qty_out,
                        "Balance": balance,
                        "Ctn Balance": ctn_balance,
                    }
                )
            continue


        if sku_cell and sku_lower != "sku" and not (config["total_rule"] == "ref_total" and ref_lower == "total"):
            current_sku = sku_cell
            if desc_cell:
                current_desc = desc_cell
            ensure_sku_record(current_sku, current_desc)
            continue

        if not current_sku:
            continue

        ensure_sku_record(current_sku, current_desc)

        if activity_lower == "beginning balance":
            sku_records[current_sku]["Beginning Balance"] = balance
            beginning_balance_rows.append(
                {
                    "Excel Row": excel_row_num + 1,
                    "SKU": current_sku,
                    "Description": sku_records[current_sku]["Description"],
                    "Activity Date": activity_text,
                    "Balance": balance,
                    "Ctn Balance": ctn_balance,
                }
            )
            continue

        if activity_lower == "ending balance":
            sku_records[current_sku]["Ending Balance"] = balance
            sku_records[current_sku]["Ctn Balance"] = ctn_balance
            sku_records[current_sku]["Official Ending Row"] = excel_row_num + 1
            official_ending_rows.append(
                {
                    "Excel Row": excel_row_num + 1,
                    "SKU": current_sku,
                    "Description": sku_records[current_sku]["Description"],
                    "Activity Date": activity_text,
                    "Balance": balance,
                    "Ctn Balance": ctn_balance,
                }
            )
            continue

        if config["total_rule"] == "ref_total" and ref_lower == "total":
            sku_records[current_sku]["Official Total Inbound"] = qty_in
            sku_records[current_sku]["Official Total Outbound"] = qty_out
            sku_records[current_sku]["Official Total Row"] = excel_row_num + 1
            official_total_rows.append(
                {
                    "Excel Row": excel_row_num + 1,
                    "SKU": current_sku,
                    "Description": sku_records[current_sku]["Description"],
                    "Source": config["total_source"],
                    "Official Total Inbound": qty_in,
                    "Official Total Outbound": qty_out,
                    "Balance": balance,
                    "Ctn Balance": ctn_balance,
                }
            )
            continue

        activity_dt = parse_excel_or_text_date(activity_raw)
        is_cancelled = "cancel" in ref_lower
        is_not_shipped = "not shipped" in activity_lower

        if is_cancelled:
            cancelled_rows.append(
                {
                    "Excel Row": excel_row_num + 1,
                    "SKU": current_sku,
                    "Description": sku_records[current_sku]["Description"],
                    "Activity Date": activity_dt,
                    "Ref #": ref_text,
                    "Qty Out": qty_out,
                }
            )

        if is_not_shipped:
            not_shipped_rows.append(
                {
                    "Excel Row": excel_row_num + 1,
                    "SKU": current_sku,
                    "Description": sku_records[current_sku]["Description"],
                    "Activity Date": activity_dt,
                    "Ref #": ref_text,
                    "Qty Out": qty_out,
                }
            )


        if not pd.isna(activity_dt):
            has_inbound = qty_in > 0
            has_outbound = qty_out > 0

            if has_inbound and has_outbound:
                transaction_type = "Inbound / Outbound"
            elif has_inbound:
                transaction_type = "Inbound"
            elif has_outbound:
                transaction_type = "Outbound"
            elif is_cancelled:
                transaction_type = "Cancelled / No Qty"
            else:
                transaction_type = "No Qty"

            transactions.append(
                {
                    "Excel Row": excel_row_num + 1,
                    "SKU": current_sku,
                    "Description": sku_records[current_sku]["Description"],
                    "Activity Date": activity_dt,
                    "Transaction Type": transaction_type,
                    "Trans. #": trans_no,
                    "Ref #": ref_text,
                    "Qty In / Ctn Raw": qty_in_raw,
                    "Qty Out / Ctn Raw": qty_out_raw,
                    "Qty In": qty_in,
                    "Qty Out": qty_out,
                    "Balance After Transaction": balance,
                    "Ctn Balance After Transaction": ctn_balance,
                    "Is Not Shipped": is_not_shipped,
                    "Is Cancelled": is_cancelled,
                }
            )


            if has_inbound or has_outbound:
                existing_last = sku_records[current_sku]["Last Activity Date"]
                if pd.isna(existing_last) or activity_dt > existing_last:
                    sku_records[current_sku]["Last Activity Date"] = activity_dt

    sku_df = pd.DataFrame(sku_records.values())
    tx_df = pd.DataFrame(transactions)
    outbound_tx_df = (
        tx_df[tx_df["Qty Out"] > 0].copy()
        if not tx_df.empty and "Qty Out" in tx_df.columns
        else pd.DataFrame(columns=tx_df.columns)
    )
    official_total_df = pd.DataFrame(official_total_rows)
    official_ending_df = pd.DataFrame(official_ending_rows)
    beginning_balance_df = pd.DataFrame(beginning_balance_rows)
    not_shipped_df = pd.DataFrame(not_shipped_rows)
    cancelled_df = pd.DataFrame(cancelled_rows)

    if sku_df.empty:
        raise ValueError(f"No SKU sections were found in the {format_name} file.")

    if pd.isna(report_end):
        report_end = tx_df["Activity Date"].max() if not tx_df.empty else pd.Timestamp.today().normalize()
    if pd.isna(report_start):
        report_start = tx_df["Activity Date"].min() if not tx_df.empty else report_end

    report_end = pd.to_datetime(report_end).normalize()
    report_start = pd.to_datetime(report_start).normalize()


    window_dates = {
        "Outbound Last 30 Days": last_data_activity_dates(outbound_tx_df, report_end, 30),
        "Outbound Last 14 Days": last_data_activity_dates(outbound_tx_df, report_end, 14),
        "Outbound Last 7 Days": last_data_activity_dates(outbound_tx_df, report_end, 7),
    }
    windows = {
        label: (dates[0], dates[-1]) if dates else (pd.NaT, pd.NaT)
        for label, dates in window_dates.items()
    }

    for label, dates in window_dates.items():
        if outbound_tx_df.empty or not dates:
            sku_df[label] = 0.0
        else:
            mask = outbound_tx_df["Activity Date"].isin(dates)
            agg = outbound_tx_df.loc[mask].groupby("SKU", as_index=True)["Qty Out"].sum()
            sku_df[label] = sku_df["SKU"].map(agg).fillna(0.0)

    valid_30d_count = max(len(window_dates["Outbound Last 30 Days"]), 1)
    sku_df["Avg Daily Usage 30D"] = sku_df["Outbound Last 30 Days"] / valid_30d_count
    sku_df["Days Remaining"] = np.where(
        sku_df["Avg Daily Usage 30D"] > 0,
        sku_df["Ending Balance"] / sku_df["Avg Daily Usage 30D"],
        np.inf,
    )

    demand_exists = (
        (sku_df["Outbound Last 30 Days"] > 0)
        | (sku_df["Outbound Last 14 Days"] > 0)
        | (sku_df["Outbound Last 7 Days"] > 0)
    )
    conditions = [
        (sku_df["Ending Balance"] <= 0) & demand_exists,
        (sku_df["Outbound Last 7 Days"] > 0) & (sku_df["Days Remaining"] <= 7),
        (sku_df["Outbound Last 14 Days"] > 0) & (sku_df["Days Remaining"] <= 14),
        (sku_df["Outbound Last 30 Days"] > 0) & (sku_df["Days Remaining"] <= 30),
    ]
    sku_df["Risk Level"] = np.select(conditions, ["Critical", "Critical", "Warning", "Watch"], default="Healthy")
    sku_df["Recommended Action"] = sku_df["Risk Level"].map(
        {
            "Critical": "Prepare inbound / allocate stock immediately",
            "Warning": "Review inbound ETA and reserve inventory",
            "Watch": "Monitor weekly usage and upcoming orders",
            "Healthy": "No immediate action",
        }
    )
    sku_df["Forecast Stockout Date"] = sku_df["Days Remaining"].map(lambda x: add_calendar_days(report_end, x))

    risk_order = {"Critical": 0, "Warning": 1, "Watch": 2, "Healthy": 3}
    sku_df["Risk Sort"] = sku_df["Risk Level"].map(risk_order).fillna(9)
    sku_df = sku_df.sort_values(
        by=["Risk Sort", "Days Remaining", "Outbound Last 14 Days", "Outbound Last 30 Days"],
        ascending=[True, True, False, False],
    ).reset_index(drop=True)

    if outbound_tx_df.empty:
        trend_df = pd.DataFrame(columns=["Activity Date", "Qty Out"])
    else:
        trend_df = outbound_tx_df.groupby("Activity Date", as_index=False)["Qty Out"].sum().sort_values("Activity Date")

    return {
        "format_name": format_name,
        "sku_df": sku_df,
        "tx_df": tx_df,
        "trend_df": trend_df,
        "official_total_df": official_total_df,
        "official_ending_df": official_ending_df,
        "beginning_balance_df": beginning_balance_df,
        "not_shipped_df": not_shipped_df,
        "cancelled_df": cancelled_df,
        "report_start": report_start,
        "report_end": report_end,
        "windows": windows,
        "window_dates": window_dates,
        "header_idx": header_idx,
        "config": config,
    }


def fmt_num(value, decimals=0):
    if value is None or pd.isna(value):
        return "-"
    if value == np.inf:
        return "∞"
    return f"{value:,.{decimals}f}"


def fmt_date(value):
    if value is None or pd.isna(value):
        return "-"
    return pd.to_datetime(value).strftime("%m/%d/%Y")


def risk_badge_text(level: str) -> str:
    return {
        "Critical": "🔴 Critical",
        "Warning": "🟠 Warning",
        "Watch": "🟡 Watch",
        "Healthy": "🟢 Healthy",
    }.get(level, level)


def metric_card(label, value, help_text=""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def round_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    numeric_cols = out.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        if str(col) == "Avg Daily Usage 30D":
            out[col] = out[col].round(2)
        else:
            out[col] = out[col].replace(np.inf, np.nan).round(0)
    return out


def format_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    date_keywords = ("date", "activity date", "forecast stockout", "last activity")
    for col in out.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in date_keywords):
            parsed = pd.to_datetime(out[col], errors="coerce")
            if parsed.notna().any():
                out[col] = parsed.dt.strftime("%m/%d/%Y").replace("NaT", "")
    return out


def display_table(df: pd.DataFrame) -> pd.DataFrame:
    return format_date_columns(round_numeric_columns(df))


def prepare_display(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "Risk Level" in out.columns:
        out["Risk Level"] = out["Risk Level"].map(risk_badge_text)
    integer_metric_cols = [
        "Beginning Balance",
        "Ending Balance",
        "Ctn Balance",
        "Official Total Inbound",
        "Official Total Outbound",
        "Outbound Last 30 Days",
        "Outbound Last 14 Days",
        "Outbound Last 7 Days",
        "Days Remaining",
        "Official Total Row",
        "Official Ending Row",
    ]
    for c in integer_metric_cols:
        if c in out.columns:
            out[c] = out[c].replace(np.inf, np.nan).round(0).astype("Int64")
    if "Avg Daily Usage 30D" in out.columns:
        out["Avg Daily Usage 30D"] = out["Avg Daily Usage 30D"].round(2)
    for c in ["Forecast Stockout Date", "Last Activity Date"]:
        if c in out.columns:
            out[c] = pd.to_datetime(out[c], errors="coerce").dt.strftime("%m/%d/%Y").replace("NaT", "")
    return out


def prepare_customer_export(df: pd.DataFrame) -> pd.DataFrame:
    customer_cols = [
        "SKU",
        "Description",
        "Risk Level",
        "Recommended Action",
        "Ending Balance",
        "Last Activity Date",
        "Official Total Outbound",
        "Outbound Last 30 Days",
        "Outbound Last 14 Days",
        "Outbound Last 7 Days",
        "Avg Daily Usage 30D",
        "Days Remaining",
        "Forecast Stockout Date",
    ]
    out = df[customer_cols].copy()

    integer_cols = [
        "Ending Balance",
        "Official Total Outbound",
        "Outbound Last 30 Days",
        "Outbound Last 14 Days",
        "Outbound Last 7 Days",
        "Days Remaining",
    ]
    for col in integer_cols:
        if col in out.columns:
            out[col] = out[col].replace(np.inf, np.nan).round(0)

    if "Avg Daily Usage 30D" in out.columns:
        out["Avg Daily Usage 30D"] = out["Avg Daily Usage 30D"].replace(np.inf, np.nan).round(2)

    for col in ["Forecast Stockout Date", "Last Activity Date"]:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce")

    return out


def report_download_filename(format_name: str, report_end) -> str:
    try:
        date_part = pd.to_datetime(report_end).strftime("%m%d%Y")
    except Exception:
        date_part = datetime.today().strftime("%m%d%Y")
    clean_format = re.sub(r"[^A-Za-z0-9]+", "_", str(format_name)).strip("_") or "Inventory"
    return f"{clean_format}_Inventory_Shortage_Report_{date_part}.xlsx"

def prepare_transaction_export(tx_df: pd.DataFrame) -> pd.DataFrame:
    export_cols = [
        "SKU",
        "Description",
        "Activity Date",
        "Transaction Type",
        "Trans. #",
        "Ref #",
        "Qty In",
        "Qty Out",
        "Balance After Transaction",
        "Is Not Shipped",
        "Is Cancelled",
    ]
    out = tx_df.copy()
    for col in export_cols:
        if col not in out.columns:
            if col in ["Qty In", "Qty Out", "Balance After Transaction"]:
                out[col] = 0.0
            elif col in ["Is Not Shipped", "Is Cancelled"]:
                out[col] = False
            elif col == "Activity Date":
                out[col] = pd.NaT
            else:
                out[col] = ""

    out = out[export_cols].copy()
    out["Activity Date"] = pd.to_datetime(out["Activity Date"], errors="coerce")
    for col in ["Qty In", "Qty Out", "Balance After Transaction"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).round(0)

    out = out.sort_values(["SKU", "Activity Date"], ascending=[True, False]).reset_index(drop=True)
    return out


def transaction_download_filename(format_name: str, report_end) -> str:
    try:
        date_part = pd.to_datetime(report_end).strftime("%m%d%Y")
    except Exception:
        date_part = datetime.today().strftime("%m%d%Y")
    clean_format = re.sub(r"[^A-Za-z0-9]+", "_", str(format_name)).strip("_") or "Inventory"
    return f"{clean_format}_Full_Transaction_History_{date_part}.xlsx"


@st.cache_data(show_spinner=False)
def to_transaction_excel_bytes(model: dict, format_name: str, cache_version: str = APP_CACHE_VERSION) -> bytes:
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    report_end = model.get("report_end")
    export_df = prepare_transaction_export(model.get("tx_df", pd.DataFrame()))

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, sheet_name="Transaction History", startrow=4, index=False)
        worksheet = writer.sheets["Transaction History"]

        last_col = max(export_df.shape[1], 1)
        last_row = len(export_df) + 5
        header_row = 5

        worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
        title_cell = worksheet.cell(row=1, column=1)
        title_cell.value = "Full Transaction History"
        title_cell.font = Font(bold=True, size=18, color="111827")
        title_cell.alignment = Alignment(horizontal="left", vertical="center")
        worksheet.row_dimensions[1].height = 26

        worksheet.merge_cells(start_row=2, start_column=1, end_row=2, end_column=last_col)
        range_cell = worksheet.cell(row=2, column=1)
        range_cell.value = f"Report Date: {fmt_date(report_end)}"
        range_cell.font = Font(size=10, color="4B5563")
        range_cell.alignment = Alignment(horizontal="left", vertical="center")

        header_fill = PatternFill("solid", fgColor="111827")
        header_font = Font(bold=True, color="FFFFFF")
        thin_gray = Side(style="thin", color="E5E7EB")
        border = Border(left=thin_gray, right=thin_gray, top=thin_gray, bottom=thin_gray)

        for cell in worksheet[header_row]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border
        worksheet.row_dimensions[header_row].height = 30

        integer_columns = {"Qty In", "Qty Out", "Balance After Transaction"}
        date_columns = {"Activity Date"}
        text_columns = {"SKU", "Description", "Transaction Type", "Trans. #", "Ref #", "Is Not Shipped", "Is Cancelled"}

        type_styles = {
            "Inbound": {"fill": "DFF3E3", "font": "067647"},
            "Outbound": {"fill": "FDE2E1", "font": "B42318"},
            "Inbound / Outbound": {"fill": "E0F2FE", "font": "026AA2"},
            "Adjustment / No Qty": {"fill": "F3F4F6", "font": "4B5563"},
            "No Qty / Adjustment": {"fill": "F3F4F6", "font": "4B5563"},
            "Cancelled / No Qty": {"fill": "F3F4F6", "font": "4B5563"},
            "No Qty": {"fill": "F3F4F6", "font": "4B5563"},
        }
        tx_type_col_idx = list(export_df.columns).index("Transaction Type") + 1 if "Transaction Type" in export_df.columns else None

        for row in worksheet.iter_rows(min_row=header_row + 1, max_row=last_row, min_col=1, max_col=last_col):
            for cell in row:
                header = worksheet.cell(row=header_row, column=cell.column).value
                cell.border = border
                cell.alignment = Alignment(
                    horizontal="left" if header in text_columns else "right",
                    vertical="center",
                    wrap_text=header in {"Description"},
                )
                if header in integer_columns:
                    cell.number_format = "#,##0"
                elif header in date_columns:
                    cell.number_format = "mm/dd/yyyy"

            if tx_type_col_idx:
                tx_cell = row[tx_type_col_idx - 1]
                style = type_styles.get(str(tx_cell.value), None)
                if style:
                    tx_cell.fill = PatternFill("solid", fgColor=style["fill"])
                    tx_cell.font = Font(bold=True, color=style["font"])
                    tx_cell.alignment = Alignment(horizontal="center", vertical="center")

        preferred_widths = {
            "SKU": 24,
            "Description": 42,
            "Activity Date": 16,
            "Transaction Type": 20,
            "Trans. #": 18,
            "Ref #": 24,
            "Qty In": 14,
            "Qty Out": 14,
            "Balance After Transaction": 24,
            "Is Not Shipped": 16,
            "Is Cancelled": 14,
        }
        for idx, col_name in enumerate(export_df.columns, start=1):
            worksheet.column_dimensions[get_column_letter(idx)].width = preferred_widths.get(col_name, 16)

        worksheet.freeze_panes = "A6"
        worksheet.auto_filter.ref = f"A{header_row}:{get_column_letter(last_col)}{last_row}"
        worksheet.sheet_view.showGridLines = False
        worksheet.sheet_properties.pageSetUpPr.fitToPage = True
        worksheet.page_setup.fitToWidth = 1
        worksheet.page_setup.fitToHeight = 0
        worksheet.page_margins.left = 0.25
        worksheet.page_margins.right = 0.25
        worksheet.page_margins.top = 0.5
        worksheet.page_margins.bottom = 0.5

    return output.getvalue()


@st.cache_data(show_spinner=False)
def to_excel_bytes(model: dict, format_name: str) -> bytes:
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    report_start = model.get("report_start")
    report_end = model.get("report_end")
    export_df = prepare_customer_export(model["sku_df"])

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, sheet_name="Shortage Priority", startrow=4, index=False)
        worksheet = writer.sheets["Shortage Priority"]

        last_col = export_df.shape[1]
        last_row = len(export_df) + 5
        header_row = 5


        worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
        title_cell = worksheet.cell(row=1, column=1)
        title_cell.value = "Inventory Status Report"
        title_cell.font = Font(bold=True, size=18, color="111827")
        title_cell.alignment = Alignment(horizontal="left", vertical="center")
        worksheet.row_dimensions[1].height = 26

        worksheet.merge_cells(start_row=2, start_column=1, end_row=2, end_column=last_col)
        range_cell = worksheet.cell(row=2, column=1)
        range_cell.value = f"Report Range: {FIXED_REPORT_START_DATE} - {fmt_date(report_end)}"
        range_cell.font = Font(size=10, color="4B5563")
        range_cell.alignment = Alignment(horizontal="left", vertical="center")

        worksheet.merge_cells(start_row=3, start_column=1, end_row=3, end_column=last_col)
        note_cell = worksheet.cell(row=3, column=1)
        note_cell.value = ""
        note_cell.font = Font(size=10, italic=True, color="6B7280")
        note_cell.alignment = Alignment(horizontal="left", vertical="center")


        header_fill = PatternFill("solid", fgColor="111827")
        header_font = Font(bold=True, color="FFFFFF")
        thin_gray = Side(style="thin", color="E5E7EB")
        border = Border(left=thin_gray, right=thin_gray, top=thin_gray, bottom=thin_gray)
        body_alignment = Alignment(vertical="center", wrap_text=False)
        text_alignment = Alignment(vertical="center", wrap_text=True)

        risk_styles = {
            "Critical": {"fill": "FDE2E1", "font": "B42318"},
            "Warning": {"fill": "FFE7C2", "font": "B54708"},
            "Watch": {"fill": "FEF7C3", "font": "854D0E"},
            "Healthy": {"fill": "DFF3E3", "font": "067647"},
        }


        for cell in worksheet[header_row]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border
        worksheet.row_dimensions[header_row].height = 30


        risk_col_idx = list(export_df.columns).index("Risk Level") + 1
        date_columns = {"Forecast Stockout Date", "Last Activity Date"}
        decimal_columns = {"Avg Daily Usage 30D"}
        integer_columns = {
            "Ending Balance",
            "Official Total Outbound",
            "Outbound Last 30 Days",
            "Outbound Last 14 Days",
            "Outbound Last 7 Days",
            "Days Remaining",
        }
        text_columns = {"SKU", "Description", "Risk Level", "Recommended Action"}

        for row in worksheet.iter_rows(min_row=header_row + 1, max_row=last_row, min_col=1, max_col=last_col):
            for cell in row:
                header = worksheet.cell(row=header_row, column=cell.column).value
                cell.border = border
                cell.alignment = text_alignment if header in text_columns else body_alignment
                if header in integer_columns:
                    cell.number_format = "#,##0"
                elif header in decimal_columns:
                    cell.number_format = "#,##0.00"
                elif header in date_columns:
                    cell.number_format = "mm/dd/yyyy"

            risk_cell = row[risk_col_idx - 1]
            style = risk_styles.get(str(risk_cell.value), None)
            if style:
                risk_cell.fill = PatternFill("solid", fgColor=style["fill"])
                risk_cell.font = Font(bold=True, color=style["font"])
                risk_cell.alignment = Alignment(horizontal="center", vertical="center")


        preferred_widths = {
            "SKU": 24,
            "Description": 42,
            "Risk Level": 16,
            "Recommended Action": 42,
            "Ending Balance": 16,
            "Last Activity Date": 18,
            "Official Total Outbound": 22,
            "Outbound Last 30 Days": 22,
            "Outbound Last 14 Days": 22,
            "Outbound Last 7 Days": 20,
            "Avg Daily Usage 30D": 22,
            "Days Remaining": 18,
            "Forecast Stockout Date": 22,
        }
        for idx, col_name in enumerate(export_df.columns, start=1):
            letter = get_column_letter(idx)
            worksheet.column_dimensions[letter].width = preferred_widths.get(col_name, 16)


        worksheet.freeze_panes = "A6"
        worksheet.auto_filter.ref = f"A{header_row}:{get_column_letter(last_col)}{last_row}"
        worksheet.sheet_view.showGridLines = False

        worksheet.sheet_view.showRowColHeaders = False
        worksheet.sheet_properties.pageSetUpPr.fitToPage = True
        worksheet.page_setup.fitToWidth = 1
        worksheet.page_setup.fitToHeight = 0
        worksheet.page_margins.left = 0.25
        worksheet.page_margins.right = 0.25
        worksheet.page_margins.top = 0.5
        worksheet.page_margins.bottom = 0.5

    return output.getvalue()

def show_limited_dataframe(df: pd.DataFrame, height: int = 420, limit: int = 500):
    total_rows = len(df)
    if total_rows > limit:
        st.caption(f"Showing first {limit:,} rows out of {total_rows:,} rows for faster loading. Download export for full data.")
    else:
        st.caption(f"Showing {total_rows:,} rows.")
    st.dataframe(display_table(df.head(limit)), use_container_width=True, hide_index=True, height=height)


def show_transaction_dataframe(df: pd.DataFrame, height: int = 420, limit: int = 500):
    total_rows = len(df)
    if total_rows > limit:
        st.caption(f"Showing first {limit:,} rows out of {total_rows:,} rows for faster loading.")
    else:
        st.caption(f"Showing {total_rows:,} rows.")

    display_df = df.head(limit).copy()

    if "Activity Date" in display_df.columns:
        display_df["Activity Date"] = pd.to_datetime(display_df["Activity Date"], errors="coerce").dt.strftime("%m/%d/%Y").replace("NaT", "")

    integer_cols = ["Excel Row", "Qty In", "Qty Out", "Balance After Transaction"]
    for col in integer_cols:
        if col in display_df.columns:
            display_df[col] = pd.to_numeric(display_df[col], errors="coerce").round(0).astype("Int64")

    for col in ["Is Not Shipped", "Is Cancelled"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].fillna(False).astype(bool)

    def highlight_transaction_type(row):
        styles = ["" for _ in row]
        if "Transaction Type" not in row.index:
            return styles
        tx_type = str(row["Transaction Type"]).lower()
        if "inbound" in tx_type and "outbound" not in tx_type:
            style = "background-color: #DFF3E3; color: #067647; font-weight: 700; text-align: center;"
        elif "outbound" in tx_type and "inbound" not in tx_type:
            style = "background-color: #FDE2E1; color: #B42318; font-weight: 700; text-align: center;"
        elif "inbound" in tx_type and "outbound" in tx_type:
            style = "background-color: #E0F2FE; color: #026AA2; font-weight: 700; text-align: center;"
        else:
            style = "background-color: #F3F4F6; color: #4B5563; font-weight: 700; text-align: center;"
        styles[list(row.index).index("Transaction Type")] = style
        return styles

    numeric_subset = [col for col in ["Excel Row", "Qty In", "Qty Out", "Balance After Transaction"] if col in display_df.columns]
    center_subset = [col for col in ["Activity Date", "Transaction Type", "Is Not Shipped", "Is Cancelled"] if col in display_df.columns]
    left_subset = [col for col in ["Trans. #", "Ref #"] if col in display_df.columns]

    styled_df = display_df.style.apply(highlight_transaction_type, axis=1)
    if numeric_subset:
        styled_df = styled_df.set_properties(subset=numeric_subset, **{"text-align": "right"})
    if center_subset:
        styled_df = styled_df.set_properties(subset=center_subset, **{"text-align": "center"})
    if left_subset:
        styled_df = styled_df.set_properties(subset=left_subset, **{"text-align": "left"})

    column_config = {}
    if "Is Not Shipped" in display_df.columns:
        column_config["Is Not Shipped"] = st.column_config.CheckboxColumn(
            "Is Not Shipped",
            help="Checked when the transaction is marked Not Shipped.",
            disabled=True,
        )
    if "Is Cancelled" in display_df.columns:
        column_config["Is Cancelled"] = st.column_config.CheckboxColumn(
            "Is Cancelled",
            help="Checked when the transaction is marked Cancelled.",
            disabled=True,
        )

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=height,
        column_config=column_config,
    )


def reset_sidebar_filters(site_key):
    st.session_state[f"{site_key}_filter_risk_levels"] = ["Critical", "Warning", "Watch", "Healthy"]
    st.session_state[f"{site_key}_filter_min_usage"] = 0
    st.session_state[f"{site_key}_sku_select_combined"] = ""


st.sidebar.title("📦 Inventory Dashboard")
format_name = st.sidebar.selectbox("Report Format", options=["Newark", "Carson"], index=0, key="report_format")
config = FORMAT_CONFIGS[format_name]
site_key = safe_format_slug(format_name).lower()
risk_filter_key = f"{site_key}_filter_risk_levels"
min_usage_filter_key = f"{site_key}_filter_min_usage"
sku_select_key = f"{site_key}_sku_select_combined"

saved_newark = load_persistent_upload("Newark")
saved_carson = load_persistent_upload("Carson")
st.sidebar.caption(f"Newark: {saved_newark['file_name'] if saved_newark else 'No saved report'}")
st.sidebar.caption(f"Carson: {saved_carson['file_name'] if saved_carson else 'No saved report'}")

st.sidebar.divider()
st.sidebar.markdown('<div class="sidebar-section-title">Filters</div>', unsafe_allow_html=True)
show_risks = st.sidebar.multiselect(
    "Risk Level",
    options=["Critical", "Warning", "Watch", "Healthy"],
    default=["Critical", "Warning", "Watch", "Healthy"],
    key=risk_filter_key,
)
min_usage = st.sidebar.number_input(
    "Min 30D Outbound",
    min_value=0,
    value=0,
    step=1,
    key=min_usage_filter_key,
)

sku_sidebar_slot = st.sidebar.empty()
st.sidebar.button("Reset Filters", use_container_width=True, on_click=reset_sidebar_filters, args=(site_key,))

st.sidebar.divider()
st.sidebar.markdown(
    """
    <div class="sidebar-note">
    <b>Risk Level Notes</b><br>
    🔴 <b>Critical:</b> 0–7 days remaining<br>
    🟠 <b>Warning:</b> 8–14 days remaining<br>
    🟡 <b>Watch:</b> 15–30 days remaining<br>
    🟢 <b>Healthy:</b> More than 30 days remaining
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    f"""
    <div class="page-header">
        <div class="page-title">{config["title"]}</div>
        <div class="page-subtitle">{config["caption"]}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="upload-hero">
        <div class="upload-hero-title">Upload report</div>
        <div class="upload-hero-subtitle">Drag and drop the Item Activity Report Excel file below.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded = st.file_uploader(
    config["upload_label"],
    type=["xlsx", "xls"],
    help=config["help"],
    label_visibility="collapsed",
    key=f"{format_name.lower()}_report_uploader",
)

status_box = st.empty()
progress_box = st.empty()

using_saved_report = False
active_file_name = ""

if uploaded is not None:
    file_bytes = uploaded.getvalue()
    active_file_name = uploaded.name
    save_persistent_upload(format_name, active_file_name, file_bytes)
else:
    saved_upload = load_persistent_upload(format_name)
    if saved_upload is None:
        st.info(f"No saved {format_name} report yet. Select {format_name}, then upload the matching Item Activity Report once.")
        st.stop()
    file_bytes = saved_upload["file_bytes"]
    active_file_name = saved_upload["file_name"]
    using_saved_report = True
    st.caption(f"Using saved {format_name} report: {active_file_name}")

uploaded_key = f"{format_name}|{active_file_name}|{len(file_bytes)}|{stable_file_hash(file_bytes)}"
loaded_file_keys = st.session_state.setdefault("loaded_file_keys", set())
first_file_load = uploaded_key not in loaded_file_keys

try:
    if first_file_load:
        with status_box.container():
            st.markdown(
                """
                <div class="loading-stage-card">
                    <div class="loading-row">
                        <div class="loader-ring"></div>
                        <div>
                            <div class="stage-title">Processing file<span class="dots"><span>.</span><span>.</span><span>.</span></span></div>
                            <div class="stage-subtitle">Reading the upload, checking the selected format, and building the dashboard.</div>
                        </div>
                    </div>
                    <div class="animated-progress"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        progress_bar = progress_box.progress(8, text="Starting upload check...")
        time.sleep(0.45)
        progress_bar.progress(28, text="Reading Excel file...")
        time.sleep(0.55)
        progress_bar.progress(52, text="Checking selected report format...")
        time.sleep(0.55)

    model = process_excel_file(file_bytes, format_name, APP_CACHE_VERSION)

    if first_file_load:
        progress_bar.progress(76, text="Building shortage dashboard...")
        time.sleep(0.55)
        progress_bar.progress(100, text="Dashboard ready")
        time.sleep(0.55)
        status_box.markdown(
            """
            <div class="ready-stage-card">
                <div class="ready-row">
                    <div class="ready-check">✓</div>
                    <div>
                        <div class="stage-title">Dashboard ready</div>
                        <div class="stage-subtitle">The file loaded successfully.</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.toast("Dashboard loaded successfully.", icon="✅")
        loaded_file_keys.add(uploaded_key)
    else:
        status_box.empty()
        progress_box.empty()
except WrongFileFormatError as exc:
    progress_box.empty()
    status_box.warning(str(exc))
    st.stop()
except Exception as exc:
    progress_box.empty()
    status_box.error("File could not be processed. Please check the selected format and upload a valid Item Activity Report file.")
    st.exception(exc)
    st.stop()

sku_df = model["sku_df"].copy()

sku_option_source = sku_df.copy()
if show_risks:
    sku_option_source = sku_option_source[sku_option_source["Risk Level"].isin(show_risks)]
sku_option_source = sku_option_source[sku_option_source["Outbound Last 30 Days"] >= min_usage]
sku_options = [""] + sku_option_source["SKU"].astype(str).dropna().tolist()

with sku_sidebar_slot.container():
    st.markdown('<div class="sidebar-section-gap"></div>', unsafe_allow_html=True)

    if st.session_state.get(sku_select_key) not in sku_options:
        st.session_state[sku_select_key] = ""

    selected_sku = st.selectbox(
        "Search / Select SKU",
        options=sku_options,
        index=0,
        key=sku_select_key,
        format_func=lambda x: "" if x == "" else x,
        help="Select a SKU to show only that SKU. Leave blank to use Risk Level filters.",
    )

selected_sku = clean_text(selected_sku)

if selected_sku:
    priority_filtered = sku_df[sku_df["SKU"].astype(str) == str(selected_sku)].copy()
else:
    priority_filtered = sku_option_source.copy()

report_start = model["report_start"]
report_end = model["report_end"]
windows = model["windows"]

st.markdown(
    f"<div class='small-note'>Report Range: <b>{FIXED_REPORT_START_DATE}</b> to <b>{fmt_date(report_end)}</b></div>",
    unsafe_allow_html=True,
)

critical_count = int((sku_df["Risk Level"] == "Critical").sum())
warning_count = int((sku_df["Risk Level"] == "Warning").sum())
watch_count = int((sku_df["Risk Level"] == "Watch").sum())
healthy_count = int((sku_df["Risk Level"] == "Healthy").sum())

review_count = critical_count + warning_count + watch_count
if review_count > 0:
    health_summary_detail = (
        f"{critical_count:,} Critical SKUs, "
        f"{warning_count:,} Warning SKUs, and {watch_count:,} Watch SKUs need review."
    )
else:
    health_summary_detail = "no Critical, Warning, or Watch SKUs need review."

st.markdown(
    f"""
    <div class="health-summary-card">
        <div class="health-summary-title">Inventory Health Summary</div>
        <div class="health-summary-text"><b>Inventory health:</b> {html.escape(health_summary_detail)}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_card("Total SKUs", fmt_num(len(sku_df)), f"Healthy: {healthy_count:,}")
with k2:
    metric_card("Critical SKUs", fmt_num(critical_count), "Need immediate inventory action")
with k3:
    metric_card("Warning SKUs", fmt_num(warning_count), "Need ETA / reserve review")
with k4:
    metric_card("Watch SKUs", fmt_num(watch_count), "Monitor usage trend")

st.markdown("<div class='kpi-row-gap'></div>", unsafe_allow_html=True)

k5, k6, k7, k8 = st.columns(4)
with k5:
    metric_card("Ending Balance", fmt_num(sku_df["Ending Balance"].sum()), "From official Ending Balance rows")
with k6:
    metric_card("Official Total Outbound", fmt_num(sku_df["Official Total Outbound"].sum()), f"From {config['total_source']} rows")
with k7:
    metric_card("Recent Outbound 30D", fmt_num(sku_df["Outbound Last 30 Days"].sum()), f"{fmt_date(windows['Outbound Last 30 Days'][0])} - {fmt_date(windows['Outbound Last 30 Days'][1])}")
with k8:
    metric_card("Recent Outbound 14D / 7D", f"{fmt_num(sku_df['Outbound Last 14 Days'].sum())} / {fmt_num(sku_df['Outbound Last 7 Days'].sum())}", "Dated Qty Out rows only")

st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Shortage Priority List</div>", unsafe_allow_html=True)
st.markdown("<div class='section-subtitle'>Sorted by risk level, lowest days remaining, and recent outbound demand.</div>", unsafe_allow_html=True)

priority_cols = [
    "SKU",
    "Description",
    "Risk Level",
    "Recommended Action",
    "Ending Balance",
    "Last Activity Date",
    "Official Total Outbound",
    "Outbound Last 30 Days",
    "Outbound Last 14 Days",
    "Outbound Last 7 Days",
    "Avg Daily Usage 30D",
    "Days Remaining",
    "Forecast Stockout Date",
]
priority_display = prepare_display(priority_filtered[priority_cols])
show_limited_dataframe(priority_display, height=440, limit=250)

st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Customer Report Export</div>", unsafe_allow_html=True)
export_file_name = report_download_filename(format_name, report_end)
transaction_file_name = transaction_download_filename(format_name, report_end)
export_col_1, export_col_2 = st.columns(2)
with export_col_1:
    st.download_button(
        "⬇️ Download Inventory Status Report",
        data=to_excel_bytes(model, format_name),
        file_name=export_file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.caption(f"File name: {export_file_name}")
with export_col_2:
    st.download_button(
        "⬇️ Download Full Transaction History",
        data=to_transaction_excel_bytes(model, format_name, APP_CACHE_VERSION),
        file_name=transaction_file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.caption(f"File name: {transaction_file_name}")

st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

sku_tab, trend_tab, audit_tab, guide_tab = st.tabs(["SKU Detail", "Trend", "Audit", "Guide"])

with sku_tab:
    if not selected_sku:
        st.info("Select a SKU to view SKU Detail.")
    elif priority_filtered.empty:
        st.warning("No SKU matches the current filters.")
    else:
        selected = sku_df[sku_df["SKU"].astype(str) == str(selected_sku)].iloc[0]
        selected_sku_safe = html.escape(str(selected_sku))
        selected_description_safe = html.escape(clean_text(selected["Description"]))
        st.markdown(
            f"""
            <div class="selected-sku-card">
                <div class="selected-sku-label">Selected SKU</div>
                <div class="selected-sku-value">{selected_sku_safe}</div>
                <div class="selected-sku-description">{selected_description_safe}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        ending_balance_value = pd.to_numeric(pd.Series([selected["Ending Balance"]]), errors="coerce").fillna(0).iloc[0]
        if ending_balance_value <= 0:
            st.warning("This SKU has zero or negative ending balance. Please review inbound allocation.")

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            metric_card("Risk Level", risk_badge_text(selected["Risk Level"]), selected["Recommended Action"])
        with d2:
            metric_card("Ending Balance", fmt_num(selected["Ending Balance"]), "Official ending balance")
        with d3:
            metric_card("Days Remaining", fmt_num(selected["Days Remaining"]), "Based on Avg Daily Usage 30D")
        with d4:
            metric_card("Forecast Stockout", fmt_date(selected["Forecast Stockout Date"]), "Calendar date estimate")

        st.markdown("<div class='section-block'></div>", unsafe_allow_html=True)
        st.subheader("SKU metrics")
        detail_cols = [
            "Official Total Inbound",
            "Official Total Outbound",
            "Outbound Last 30 Days",
            "Outbound Last 14 Days",
            "Outbound Last 7 Days",
            "Avg Daily Usage 30D",
            "Last Activity Date",
            "Official Total Row",
            "Official Ending Row",
        ]
        detail = selected[detail_cols].to_frame("Value")
        detail["Value"] = detail.apply(
            lambda r: fmt_date(r["Value"]) if "date" in str(r.name).lower()
            else (
                fmt_num(r["Value"], 2) if str(r.name) == "Avg Daily Usage 30D"
                else (fmt_num(r["Value"]) if isinstance(r["Value"], (int, float, np.integer, np.floating)) and np.isfinite(r["Value"]) else r["Value"])
            ),
            axis=1,
        )
        st.dataframe(detail, use_container_width=True)

        tx_sku = model["tx_df"].copy()
        if not tx_sku.empty:
            tx_sku = tx_sku[tx_sku["SKU"] == selected_sku].copy()
            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
            st.subheader("Full transaction history")
            full_tx_cols = [
                "Excel Row",
                "Activity Date",
                "Transaction Type",
                "Trans. #",
                "Ref #",
                "Qty In",
                "Qty Out",
                "Balance After Transaction",
                "Is Not Shipped",
                "Is Cancelled",
            ]
            for col in full_tx_cols:
                if col not in tx_sku.columns:
                    if col in ["Qty In", "Qty Out", "Balance After Transaction"]:
                        tx_sku[col] = 0.0
                    elif col in ["Is Not Shipped", "Is Cancelled"]:
                        tx_sku[col] = False
                    elif col == "Activity Date":
                        tx_sku[col] = pd.NaT
                    else:
                        tx_sku[col] = ""

            if tx_sku.empty:
                st.info("No transaction history found for this SKU.")
            else:
                total_qty_in = pd.to_numeric(tx_sku["Qty In"], errors="coerce").fillna(0).sum()
                total_qty_out = pd.to_numeric(tx_sku["Qty Out"], errors="coerce").fillna(0).sum()

                s1, s2, s3 = st.columns(3)
                with s1:
                    metric_card("Total Qty In", fmt_num(total_qty_in), "Inbound transaction total")
                with s2:
                    metric_card("Total Qty Out", fmt_num(total_qty_out), "Outbound transaction total")
                with s3:
                    metric_card("Current Balance", fmt_num(selected["Ending Balance"]), "Official ending balance")

                st.markdown("<div class='kpi-row-gap'></div>", unsafe_allow_html=True)

                sku_filter_key = re.sub(r"[^A-Za-z0-9_]+", "_", f"{format_name}_{selected_sku}")[:55]
                tx_filtered = tx_sku.copy()

                f1, f2 = st.columns([2, 1])
                tx_search = f1.text_area(
                    "Search Ref # / Trans. #",
                    placeholder="Example:\nPO_0090\nPO_0086\nAXIA_2484",
                    key=f"tx_search_{sku_filter_key}",
                    height=110,
                )

                tx_dates = pd.to_datetime(tx_sku["Activity Date"], errors="coerce").dropna()
                if not tx_dates.empty:
                    tx_min_date = tx_dates.min().date()
                    tx_max_date = tx_dates.max().date()
                else:
                    tx_min_date = None
                    tx_max_date = None

                activity_date_mode = f2.selectbox(
                    "Activity Date Filter",
                    options=["All Dates", "Single Date", "Date Range"],
                    key=f"tx_date_mode_{sku_filter_key}",
                )

                selected_tx_date = None
                selected_tx_date_range = None

                if activity_date_mode == "Single Date":
                    selected_tx_date = f2.date_input(
                        "Activity Date",
                        value=None,
                        min_value=tx_min_date,
                        max_value=tx_max_date,
                        key=f"tx_date_{sku_filter_key}",
                    )
                elif activity_date_mode == "Date Range":
                    default_tx_date_range = (tx_min_date, tx_max_date) if tx_min_date is not None and tx_max_date is not None else None
                    selected_tx_date_range = f2.date_input(
                        "Activity Date Range",
                        value=default_tx_date_range,
                        min_value=tx_min_date,
                        max_value=tx_max_date,
                        key=f"tx_date_range_{sku_filter_key}",
                    )

                tx_terms = []
                if tx_search.strip():
                    tx_terms = [x.strip() for x in re.split(r"[\n,;]+", tx_search) if x.strip()]
                    tx_pattern = "|".join(re.escape(x.lower()) for x in tx_terms)
                    tx_filtered = tx_filtered[
                        tx_filtered["Ref #"].astype(str).str.lower().str.contains(tx_pattern, na=False, regex=True)
                        | tx_filtered["Trans. #"].astype(str).str.lower().str.contains(tx_pattern, na=False, regex=True)
                    ]

                if activity_date_mode == "Single Date" and selected_tx_date is not None:
                    selected_date_value = pd.to_datetime(selected_tx_date).normalize()
                    tx_activity_dates = pd.to_datetime(tx_filtered["Activity Date"], errors="coerce").dt.normalize()
                    tx_filtered = tx_filtered[tx_activity_dates == selected_date_value]
                elif activity_date_mode == "Date Range" and selected_tx_date_range is not None:
                    if isinstance(selected_tx_date_range, tuple) and len(selected_tx_date_range) == 2:
                        range_start = pd.to_datetime(selected_tx_date_range[0]).normalize()
                        range_end = pd.to_datetime(selected_tx_date_range[1]).normalize()
                        if range_start > range_end:
                            range_start, range_end = range_end, range_start
                        tx_activity_dates = pd.to_datetime(tx_filtered["Activity Date"], errors="coerce").dt.normalize()
                        tx_filtered = tx_filtered[(tx_activity_dates >= range_start) & (tx_activity_dates <= range_end)]
                    else:
                        st.warning("Please select both start and end date for Activity Date Range.")

                if tx_terms:
                    tx_result_text = (
                        tx_filtered["Ref #"].astype(str).str.lower()
                        + " "
                        + tx_filtered["Trans. #"].astype(str).str.lower()
                    )
                    tx_missing_terms = [
                        term for term in tx_terms
                        if not tx_result_text.str.contains(re.escape(term.lower()), na=False, regex=True).any()
                    ]
                    if tx_missing_terms:
                        st.error("Not found in results: " + ", ".join(tx_missing_terms))
                    else:
                        st.success("All searched Ref # / Trans. # were found.")

                st.markdown("<div class='kpi-row-gap'></div>", unsafe_allow_html=True)


                tx_filtered = tx_filtered.sort_values(["Activity Date", "Excel Row"], ascending=[False, False])

                show_transaction_dataframe(tx_filtered[full_tx_cols], height=420, limit=500)

with trend_tab:
    st.subheader("Outbound Trend")
    trend_df = model["trend_df"]
    if trend_df.empty:
        st.info("No dated outbound transactions found.")
    else:
        trend_plot = trend_df.copy()
        trend_plot["Activity Date"] = pd.to_datetime(trend_plot["Activity Date"])
        st.line_chart(trend_plot, x="Activity Date", y="Qty Out", height=360, use_container_width=True)

        top_usage = sku_df.sort_values("Outbound Last 30 Days", ascending=False).head(20)[["SKU", "Outbound Last 30 Days"]]
        st.bar_chart(top_usage, x="SKU", y="Outbound Last 30 Days", height=360, use_container_width=True)

with audit_tab:
    st.subheader("Audit Checks")
    st.caption("Verify recent outbound calculations and official source rows.")

    st.markdown("**Recent Outbound Audit**")
    r1, r2, r3 = st.columns(3)
    recent_labels = ["Outbound Last 30 Days", "Outbound Last 14 Days", "Outbound Last 7 Days"]
    recent_card_labels = ["Recent Outbound 30D", "Recent Outbound 14D", "Recent Outbound 7D"]
    for col, label, card_label in zip([r1, r2, r3], recent_labels, recent_card_labels):
        start, end = windows[label]
        valid_dates = model["window_dates"][label]
        with col:
            metric_card(card_label, fmt_num(sku_df[label].sum()), f"{fmt_date(start)} - {fmt_date(end)} | {len(valid_dates)} data dates")

    st.markdown("**Official Total Rows**")
    show_limited_dataframe(model["official_total_df"], height=260, limit=250)

    st.markdown("**Official Ending Balance Rows**")
    show_limited_dataframe(model["official_ending_df"], height=260, limit=250)

    with st.expander("Not Shipped Rows", expanded=False):
        show_limited_dataframe(model["not_shipped_df"], height=260, limit=250)

    with st.expander("Cancelled Rows", expanded=False):
        show_limited_dataframe(model["cancelled_df"], height=260, limit=250)

    if not model["beginning_balance_df"].empty:
        with st.expander("Beginning Balance Rows", expanded=False):
            show_limited_dataframe(model["beginning_balance_df"], height=260, limit=250)

with guide_tab:
    st.subheader("How to Use")
    st.markdown(
        f"""
        1. Select the matching **Report Format** in the sidebar.
        2. Upload the matching **Item Activity Report** Excel file.
        3. Review **Critical**, **Warning**, and **Watch** SKUs first.
        4. Use **SKU Detail** to drill into one SKU and review transaction history.
        5. Use **Audit** to verify official total rows, ending balance rows, Not Shipped rows, and Cancelled rows.        """
    )
