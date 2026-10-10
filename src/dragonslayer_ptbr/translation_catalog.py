from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

CATALOG_VERSION = 1
TAG_PATTERN = re.compile(r"<[^<>\r\n]+>")
SOURCE_KEYS = ("source", "original", "japanese", "text", "original_text", "jp")
TRANSLATION_KEYS = ("translation", "translated", "portuguese", "pt_br", "target")
ID_KEYS = ("id", "key", "label", "name")
FILE_KEYS = ("file", "script", "filename")
LINE_KEYS = ("line", "line_number", "row")


def _first_string(record: dict[str, Any], candidates: tuple[str, ...]) -> str | None:
    for key in candidates:
        value = record.get(key)
        if isinstance(value, str):
            return value
    return None


def _source_hash(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _make_entry(record: dict[str, Any], index: int, source_path: Path) -> dict[str, Any]:
    source = _first_string(record, SOURCE_KEYS)
    if source is None:
        raise ValueError(
            f"Registro {index}: não encontrei um campo de texto de origem. "
            f"Campos aceitos: {', '.join(SOURCE_KEYS)}."
        )
    entry = dict(record)
    entry["id"] = _first_string(record, ID_KEYS) or f"{source_path.stem}:{index}"
    entry["source"] = source
    entry["translation"] = _first_string(record, TRANSLATION_KEYS) or ""
    entry["tags"] = TAG_PATTERN.findall(source)
    entry["source_sha256"] = _source_hash(source)
    entry["status"] = "TRADUZIDO" if entry["translation"].strip() else "PENDENTE"
    filename = _first_string(record, FILE_KEYS)
    if filename:
        entry["file"] = filename
    line = next((record.get(key) for key in LINE_KEYS if isinstance(record.get(key), int)), None)
    if line is not None:
        entry["line"] = line
    entry.setdefault("_imported_from", source_path.name)
    return entry


def import_external_dump(source_path: Path, catalog_path: Path) -> int:
    """Normaliza dumps JSON/CSV comuns sem descartar os campos originais."""
    suffix = source_path.suffix.casefold()
    if suffix == ".json":
        payload = json.loads(source_path.read_text(encoding="utf-8-sig"))
        if isinstance(payload, dict):
            records = payload.get("entries", payload.get("texts", payload.get("strings")))
            if records is None and all(isinstance(value, str) for value in payload.values()):
                records = [{"id": key, "source": value} for key, value in payload.items()]
        else:
            records = payload
        if not isinstance(records, list):
            raise ValueError(
                "JSON não reconhecido: esperava uma lista de registros, "
                "ou um objeto com 'entries', 'texts' ou 'strings'."
            )
        raw_records = records
    elif suffix == ".csv":
        with source_path.open("r", encoding="utf-8-sig", newline="") as stream:
            raw_records = list(csv.DictReader(stream))
        if not raw_records:
            raise ValueError("CSV vazio ou sem linha de dados.")
    else:
        raise ValueError("Formato externo não suportado. A importação direta aceita JSON ou CSV.")

    entries: list[dict[str, Any]] = []
    for index, record in enumerate(raw_records, start=1):
        if not isinstance(record, dict):
            raise TypeError(f"Registro {index} não é um objeto/cabeçalho de CSV.")
        entries.append(_make_entry(record, index, source_path))

    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(
        json.dumps(
            {"catalog_version": CATALOG_VERSION, "imported_from": source_path.name, "entries": entries},
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    return len(entries)


def load_catalog(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, list):
        payload = {"catalog_version": CATALOG_VERSION, "entries": payload}
    if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
        raise TypeError("Catálogo inválido: esperado objeto com uma lista 'entries'.")
    entries = payload["entries"]
    seen: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict) or not isinstance(entry.get("source"), str):
            raise TypeError(f"Entrada {index} precisa ser um objeto com campo 'source' textual.")
        entry.setdefault("id", f"entry:{index}")
        entry.setdefault("translation", "")
        entry.setdefault("tags", TAG_PATTERN.findall(entry["source"]))
        entry.setdefault("source_sha256", _source_hash(entry["source"]))
        entry["status"] = "TRADUZIDO" if str(entry["translation"]).strip() else "PENDENTE"
        identifier = str(entry["id"])
        if identifier in seen:
            entry["id"] = f"{identifier}#{index}"
        seen.add(str(entry["id"]))
    return payload, entries


def save_catalog(path: Path, payload: dict[str, Any], entries: list[dict[str, Any]]) -> None:
    for entry in entries:
        entry["status"] = "TRADUZIDO" if str(entry.get("translation", "")).strip() else "PENDENTE"
    payload["catalog_version"] = CATALOG_VERSION
    payload["entries"] = entries
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_entry(entry: dict[str, Any]) -> list[str]:
    """Valida marcadores inline sem afirmar que o formato pode ser inserido na ROM."""
    source = str(entry.get("source", ""))
    translation = str(entry.get("translation", ""))
    if not translation.strip():
        return ["Tradução pendente."]
    problems: list[str] = []
    if TAG_PATTERN.findall(source) != TAG_PATTERN.findall(translation):
        problems.append("Marcadores <...> diferentes da origem ou em ordem diferente.")
    if "\r" in translation or "\n" in translation:
        problems.append("A tradução contém quebra de linha; confirme se o formato permite isso.")
    if "\ufffd" in translation:
        problems.append("A tradução contém o caractere de substituição Unicode (�).")
    return problems


def write_qa_report(path: Path, entries: list[dict[str, Any]]) -> dict[str, Any]:
    results = []
    for entry in entries:
        problems = validate_entry(entry)
        status = "OK" if not problems else "PENDENTE" if problems == ["Tradução pendente."] else "ERRO"
        results.append({"id": entry.get("id"), "status": status, "problems": problems})
    report = {
        "entries_total": len(entries),
        "translated": sum(bool(str(item.get("translation", "")).strip()) for item in entries),
        "pending": sum(not str(item.get("translation", "")).strip() for item in entries),
        "with_errors": sum(item["status"] == "ERRO" for item in results),
        "rom_insertion_ready": False,
        "results": results,
        "note": (
            "QA textual apenas. Não comprova codificação de glifos, limite de caixa, "
            "formato de reinserção, ponteiros ou compatibilidade com a ROM."
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
