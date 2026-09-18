"""
Read-only Google Drive/Sheets access. No Apps Script equivalent -- this
replaces DriveApp/SpreadsheetApp calls with a service-account-authenticated
Python client. Streamlit never writes anywhere; scopes are read-only.
"""

from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import gspread
import requests
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

_clock_corrected = False


def _correct_system_clock_skew() -> None:
    """Google rejects a service-account JWT whose iat/exp look wrong by even
    a few minutes ("invalid_grant: Invalid JWT..."). On a machine where the
    OS clock is drifted and the user has no admin rights to fix it, work
    around this IN-PROCESS instead: read the real time from a Date header on
    an HTTPS response, and monkeypatch google.auth's clock source so every
    JWT it signs uses the corrected time -- the OS clock itself is never
    touched.
    """
    global _clock_corrected
    if _clock_corrected:
        return
    _clock_corrected = True  # only ever attempt this once per process

    try:
        local_before = datetime.now(timezone.utc)
        resp = requests.head("https://www.googleapis.com/", timeout=5)
        server_time = parsedate_to_datetime(resp.headers["Date"])
        if server_time.tzinfo is None:
            server_time = server_time.replace(tzinfo=timezone.utc)
        local_after = datetime.now(timezone.utc)
        local_mid = local_before + (local_after - local_before) / 2
        offset = server_time - local_mid
    except Exception:
        return  # couldn't reach a time source -- leave the clock as-is

    if abs(offset.total_seconds()) < 5:
        return  # close enough, nothing to correct

    from google.auth import _helpers
    original_utcnow = _helpers.utcnow

    def _corrected_utcnow():
        return original_utcnow() + offset

    _helpers.utcnow = _corrected_utcnow


def _load_credentials() -> Credentials:
    _correct_system_clock_skew()
    info = dict(st.secrets["gcp_service_account"])
    return Credentials.from_service_account_info(info, scopes=SCOPES)


@st.cache_resource(show_spinner=False)
def get_drive_service():
    creds = _load_credentials()
    return build("drive", "v3", credentials=creds, cache_discovery=False)


@st.cache_resource(show_spinner=False)
def get_gspread_client() -> gspread.Client:
    creds = _load_credentials()
    return gspread.authorize(creds)


def list_files_in_folder(drive_service, folder_id: str) -> list[dict]:
    """Lists non-trashed files in a Drive folder, sorted by name (mirrors
    Apps Script's driveFiles.sort(localeCompare))."""
    files = []
    page_token = None
    query = f"'{folder_id}' in parents and trashed=false"
    while True:
        response = drive_service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, size, modifiedTime)",
            pageToken=page_token,
            pageSize=1000,
        ).execute()
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    files.sort(key=lambda f: f["name"])
    return files


def download_file_bytes(drive_service, file_id: str) -> bytes:
    request = drive_service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _status, done = downloader.next_chunk()
    return buf.getvalue()


def read_mapping_master_tabs(gspread_client: gspread.Client, spreadsheet_id: str) -> dict:
    """Returns raw row-lists (not dict-records) for each of the three
    Mapping Master tabs, so mapping_master.py can apply the exact same
    header-index lookup as the Apps Script original and control its own
    date-vs-string defense on the Period column."""
    ss = gspread_client.open_by_key(spreadsheet_id)
    return {
        "sku_rows": ss.worksheet("SKU_MAPPING_MASTER").get_all_values(),
        "bom_rows": ss.worksheet("BOM").get_all_values(),
        "cost_rows": ss.worksheet("COST_HISTORY").get_all_values(),
    }
