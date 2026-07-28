#!/usr/bin/env python3

import os
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials


class SheetsLogger:
    def __init__(self):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        credential_file = os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_FILE",
            "service_account.json"
        )

        spreadsheet_id = os.getenv("GOOGLE_SHEET_ID")

        if not spreadsheet_id:
            raise Exception("GOOGLE_SHEET_ID belum diset pada file .env")

        creds = Credentials.from_service_account_file(
            credential_file,
            scopes=scopes
        )

        client = gspread.authorize(creds)

        self.sheet = client.open_by_key(spreadsheet_id).sheet1

    def _existing_keys(self):
        rows = self.sheet.get_all_values()

        if len(rows) <= 1:
            return set()

        return set(row[0] for row in rows[1:] if row)

    def log_batch(self, inside_alerts, near_alerts):

        existing = self._existing_keys()

        rows = []

        ditulis = 0
        dilewati = 0

        now = datetime.now(
            ZoneInfo("Asia/Jakarta")
        ).strftime("%Y-%m-%d %H:%M:%S")

        # HOTSPOT DALAM KAWASAN
        for properties, area, lat, lon in inside_alerts:

            hotspot_id = (
                f"{properties.get('latitude', lat)}_"
                f"{properties.get('longitude', lon)}_"
                f"{properties.get('tanggal', '')}"
            )

            if hotspot_id in existing:
                dilewati += 1
                continue

            rows.append([
                hotspot_id,
                now,
                "DALAM KAWASAN",
                area,
                properties.get("provinsi", ""),
                properties.get("kabupaten", ""),
                properties.get("kecamatan", ""),
                properties.get("desa", ""),
                lat,
                lon,
                properties.get("confidence", ""),
                properties.get("satelit", ""),
                properties.get("tanggal", "")
            ])

            existing.add(hotspot_id)
            ditulis += 1

        # HOTSPOT DEKAT BATAS
        for properties, area, lat, lon, distance in near_alerts:

            hotspot_id = (
                f"{properties.get('latitude', lat)}_"
                f"{properties.get('longitude', lon)}_"
                f"{properties.get('tanggal', '')}"
            )

            if hotspot_id in existing:
                dilewati += 1
                continue

            rows.append([
                hotspot_id,
                now,
                f"DEKAT BATAS ({distance} m)",
                area,
                properties.get("provinsi", ""),
                properties.get("kabupaten", ""),
                properties.get("kecamatan", ""),
                properties.get("desa", ""),
                lat,
                lon,
                properties.get("confidence", ""),
                properties.get("satelit", ""),
                properties.get("tanggal", "")
            ])

            existing.add(hotspot_id)
            ditulis += 1

        if rows:
            self.sheet.append_rows(rows)

        logging.info(
            f"Google Sheet: {ditulis} ditambahkan, {dilewati} dilewati"
        )

        return ditulis, dilewati