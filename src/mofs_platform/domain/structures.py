"""Structure index domain (issue #24, D12 slice 1).

A generic, provider-attributed index of structure records (CoRE MOF 2019
first; QMOF/DigiMOF/COD reuse the same table). Imports come from files the
researcher supplies — there is no fetch route. Capturing a structure's
reference goes through the attributed reference flow; the index row stays
as provenance and is never modified by a capture.
"""

import csv
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

PROVIDERS = ("core_mof_2019", "qmof", "digimof", "cod", "other")

# Flexible header mapping: a CSV column whose (lowercased) header contains a
# key maps to that field. Order matters — first match wins.
_HEADER_ALIASES = {
    "external_id": ("refcode", "mofid", "mofkey", "id", "identifier"),
    "name": ("name", "mof name", "mofname", "title", "compound"),
    "formula": ("formula", "composition"),
    "doi": ("doi",),
    "file_ref": ("file", "filename", "cif", "path"),
}

_NEEDED = ("name",)


class StructureValidationError(ValueError):
    """The import/search/capture cannot be applied (requirements listed)."""


class StructurePersistenceError(RuntimeError):
    """Saving failed; previously saved records are unchanged."""


@dataclass(frozen=True)
class StructureRecord:
    id: int
    provider: str
    external_id: str | None
    name: str
    formula: str | None
    doi: str | None
    file_ref: str | None
    extra_json: str | None


def _row_to_record(row: sqlite3.Row) -> StructureRecord:
    return StructureRecord(
        id=row["id"], provider=row["provider"], external_id=row["external_id"],
        name=row["name"], formula=row["formula"], doi=row["doi"],
        file_ref=row["file_ref"], extra_json=row["extra_json"],
    )


def _clean(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _map_headers(fieldnames: list[str]) -> dict[str, str]:
    """Map CSV headers to fields via the alias table. Raises when no name
    column exists — a row without a name cannot be indexed."""
    lowered = {h.strip().lower(): h for h in fieldnames if h and h.strip()}
    mapping: dict[str, str] = {}
    for field, aliases in _HEADER_ALIASES.items():
        for alias in aliases:
            for header, original in lowered.items():
                # exact or startswith only — loose substring matching would
                # map adversarial headers like "not-a-name" to the name field
                if header == alias or header.startswith(alias):
                    if field not in mapping:
                        mapping[field] = original
                    break
    missing = [f for f in _NEEDED if f not in mapping]
    if missing:
        raise StructureValidationError(
            "CSV import rejected — no column matched: "
            + ", ".join(missing)
            + ". Expected headers containing: name/title/compound, doi, "
            "formula, id/refcode, file. Found: " + ", ".join(fieldnames)
        )
    return mapping


def import_structure_csv(
    conn: sqlite3.Connection, csv_path: str | Path, provider: str,
    contributor: str | None,
) -> dict:
    """Import a provider CSV into the index. Rows update matching
    (provider, external_id) records idempotently; rows without an external_id
    are always appended. Returns a report; nothing is written when any
    structural problem aborts the import."""
    if provider not in PROVIDERS:
        raise StructureValidationError(
            f"Provider must be one of {PROVIDERS!r} — got {provider!r}."
        )
    clean_contributor = (contributor or "").strip()
    if not clean_contributor:
        raise StructureValidationError("Import rejected — missing: who is importing.")
    path = Path(csv_path)
    if not path.is_file():
        raise StructureValidationError(f"CSV file not found: {path}")

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise StructureValidationError("CSV import rejected — the file has no header row.")
        mapping = _map_headers(reader.fieldnames)
        rows: list[dict] = []
        for line_no, raw in enumerate(reader, start=2):
            record = {field: _clean(raw.get(original)) for field, original in mapping.items()}
            extra = {
                h: _clean(raw.get(h)) for h in reader.fieldnames
                if h not in mapping.values() and _clean(raw.get(h))
            }
            if not record.get("name"):
                raise StructureValidationError(
                    f"CSV import rejected — line {line_no} has no name value."
                )
            record["extra_json"] = json.dumps(extra, ensure_ascii=False) if extra else None
            rows.append(record)

    inserted = updated = 0
    try:
        with conn:
            for record in rows:
                existing = None
                if record.get("external_id"):
                    existing = conn.execute(
                        "SELECT id FROM structure_index WHERE provider = ? AND external_id = ?",
                        (provider, record["external_id"]),
                    ).fetchone()
                if existing is not None:
                    conn.execute(
                        "UPDATE structure_index SET name = ?, formula = ?, doi = ?, "
                        "file_ref = ?, extra_json = ? WHERE id = ?",
                        (record["name"], record.get("formula"), record.get("doi"),
                         record.get("file_ref"), record.get("extra_json"),
                         existing["id"]),
                    )
                    updated += 1
                else:
                    conn.execute(
                        "INSERT INTO structure_index (provider, external_id, name, "
                        "formula, doi, file_ref, extra_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (provider, record.get("external_id"), record["name"],
                         record.get("formula"), record.get("doi"),
                         record.get("file_ref"), record.get("extra_json")),
                    )
                    inserted += 1
            conn.execute(
                "INSERT INTO identity_event (action, entity_id, detail) "
                "VALUES ('structure_imported', 0, ?)",
                (json.dumps({
                    "provider": provider, "contributor": clean_contributor,
                    "inserted": inserted, "updated": updated, "csv": str(path),
                }),),
            )
    except sqlite3.Error as exc:
        raise StructurePersistenceError(
            f"Import failed; the index is unchanged. ({exc})"
        ) from exc
    return {
        "provider": provider, "inserted": inserted, "updated": updated,
        "contributor": clean_contributor,
    }


def search_structures(
    conn: sqlite3.Connection, query: str, provider: str | None = None
) -> list[StructureRecord]:
    clean = (query or "").strip()
    if len(clean) < 2:
        raise StructureValidationError("Enter at least 2 characters to search the index.")
    like = f"%{clean}%"
    if provider:
        rows = conn.execute(
            "SELECT * FROM structure_index WHERE provider = ? AND "
            "(name LIKE ? OR formula LIKE ? OR external_id LIKE ?) "
            "ORDER BY name LIMIT 25",
            (provider, like, like, like),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM structure_index WHERE "
            "(name LIKE ? OR formula LIKE ? OR external_id LIKE ?) "
            "ORDER BY name LIMIT 25",
            (like, like, like),
        ).fetchall()
    return [_row_to_record(row) for row in rows]


def get_structure(conn: sqlite3.Connection, structure_id: int) -> StructureRecord | None:
    row = conn.execute(
        "SELECT * FROM structure_index WHERE id = ?", (structure_id,)
    ).fetchone()
    return None if row is None else _row_to_record(row)


def count_structures(conn: sqlite3.Connection, provider: str | None = None) -> int:
    if provider:
        return int(conn.execute(
            "SELECT COUNT(*) FROM structure_index WHERE provider = ?", (provider,)
        ).fetchone()[0])
    return int(conn.execute("SELECT COUNT(*) FROM structure_index").fetchone()[0])


def capture_structure_reference(
    conn: sqlite3.Connection, structure_id: int, contributor: str | None
) -> tuple[StructureRecord, int]:
    """Capture the structure's DOI as an attributed reference (existing
    re-capture semantics). Provenance names the provider and the structure
    record. The index row is untouched; the reference is a lead like any
    other."""
    from mofs_platform.domain.references import add_manual_reference

    record = get_structure(conn, structure_id)
    if record is None:
        raise StructureValidationError(f"Structure #{structure_id} does not exist.")
    clean_contributor = (contributor or "").strip()
    if not clean_contributor:
        raise StructureValidationError("Capture rejected — missing: who is capturing.")
    if not record.doi:
        raise StructureValidationError(
            f"Structure #{structure_id} has no DOI in the index — capture the "
            "reference manually from its source."
        )
    provenance = (
        f"Captured from structure index [{record.provider}] record "
        f"#{record.id} ({record.name})."
    )
    ref = add_manual_reference(
        conn,
        doi=record.doi,
        title=record.name,
        supplied_input=provenance,
        contributor=clean_contributor,
        inspected_level="metadata",
    )
    return record, ref.id
