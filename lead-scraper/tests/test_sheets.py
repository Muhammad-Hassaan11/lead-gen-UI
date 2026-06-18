from __future__ import annotations

from types import SimpleNamespace

import gspread

from app.models import Lead
from app.sinks import sheets


def test_append_lead_writes_header_and_skips_duplicate(monkeypatch) -> None:
    spreadsheet = FakeSpreadsheet()
    _install_fake_client(monkeypatch, spreadsheet)

    sheets.append_lead(_lead("https://WWW.GOOGLE.com/maps/place/TestCo?utm_source=newsletter"))
    worksheet = spreadsheet.worksheets["Leads"]

    assert worksheet.rows[0] == sheets.HEADER_ROW
    assert len(worksheet.rows) == 2
    assert worksheet.rows[1][1] == "https://www.google.com/maps/place/TestCo"

    sheets.append_lead(_lead("https://www.google.com/maps/place/TestCo"))

    assert len(worksheet.rows) == 2


def test_append_lead_retries_429_and_eventually_succeeds(monkeypatch) -> None:
    worksheet = FakeWorksheet(
        rows=[sheets.HEADER_ROW],
        append_statuses=[429, 429, 429],
    )
    spreadsheet = FakeSpreadsheet({"Leads": worksheet})
    sleep_calls: list[int] = []

    _install_fake_client(monkeypatch, spreadsheet)
    monkeypatch.setattr(sheets.time, "sleep", lambda delay: sleep_calls.append(delay))

    sheets.append_lead(_lead("https://www.google.com/maps/place/RetryCo"))

    assert sleep_calls == [1, 4, 16]
    assert worksheet.append_calls == 4
    assert len(worksheet.rows) == 2
    assert worksheet.rows[1][1] == "https://www.google.com/maps/place/RetryCo"


class FakeClient:
    def __init__(self, spreadsheet: FakeSpreadsheet) -> None:
        self.spreadsheet = spreadsheet

    def open_by_key(self, _sheet_id: str) -> FakeSpreadsheet:
        return self.spreadsheet


class FakeSpreadsheet:
    def __init__(self, worksheets: dict[str, FakeWorksheet] | None = None) -> None:
        self.worksheets = worksheets or {}

    def worksheet(self, title: str) -> FakeWorksheet:
        try:
            return self.worksheets[title]
        except KeyError as exc:
            raise gspread.exceptions.WorksheetNotFound from exc

    def add_worksheet(self, title: str, rows: int, cols: int) -> FakeWorksheet:
        worksheet = FakeWorksheet()
        self.worksheets[title] = worksheet
        return worksheet


class FakeWorksheet:
    def __init__(
        self,
        rows: list[list[str]] | None = None,
        append_statuses: list[int] | None = None,
    ) -> None:
        self.rows = [list(row) for row in rows or []]
        self.append_statuses = list(append_statuses or [])
        self.append_calls = 0

    def row_values(self, row: int) -> list[str]:
        if row <= len(self.rows):
            return list(self.rows[row - 1])
        return []

    def col_values(self, col: int) -> list[str]:
        values: list[str] = []
        for row in self.rows:
            values.append(row[col - 1] if col <= len(row) else "")
        return values

    def append_row(self, row: list[str], value_input_option: str = "RAW") -> None:
        self.append_calls += 1
        if self.append_statuses:
            raise gspread.exceptions.APIError(FakeResponse(self.append_statuses.pop(0)))
        self.rows.append(list(row))


class FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        self.text = "rate limited"

    def json(self) -> dict[str, dict[str, int | str]]:
        return {
            "error": {
                "code": self.status_code,
                "message": self.text,
                "status": "RESOURCE_EXHAUSTED",
            }
        }


def _install_fake_client(monkeypatch, spreadsheet: FakeSpreadsheet) -> None:
    settings = SimpleNamespace(
        google_sheet_id="sheet-id",
        google_worksheet_name="Leads",
    )

    monkeypatch.setattr(sheets, "_get_client", lambda: FakeClient(spreadsheet))
    monkeypatch.setattr(sheets, "get_settings", lambda: settings)


def _lead(maps_url: str) -> Lead:
    return Lead(
        job_id=1,
        maps_url=maps_url,
        business_name="TestCo",
        address="42 Test Road",
        phone="+923001234567",
        website="https://testco.example",
        status="pushed",
        emails=["hello@testco.example"],
        source_pages=["https://testco.example/team"],
    )
