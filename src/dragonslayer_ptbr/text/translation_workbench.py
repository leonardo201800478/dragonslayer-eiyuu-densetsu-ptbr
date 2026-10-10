from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

DEFAULT_SOURCE_ENCODING = "cp932"
JAPANESE_TEXT = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
INLINE_TAG = re.compile(r"<[^<>\r\n]+>")
CATALOG_VERSION = 1


def _source_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1], line[-1:]
    return line, ""


def _has_translatable_text(line: str) -> bool:
    return bool(JAPANESE_TEXT.search(INLINE_TAG.sub("", line)))


def _tags(line: str) -> list[str]:
    return INLINE_TAG.findall(line)


def export_catalog(
    source_dir: Path,
    catalog_path: Path,
    *,
    source_encoding: str = DEFAULT_SOURCE_ENCODING,
) -> int:
    """Exporta linhas japonesas para JSON UTF-8 sem alterar os arquivos de origem."""
    root = source_dir.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Pasta de scripts não encontrada: {root}")

    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.txt")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        content = path.read_bytes().decode(source_encoding)
        for line_number, raw_line in enumerate(content.splitlines(keepends=True), start=1):
            line, _ending = _split_line_ending(raw_line)
            if not _has_translatable_text(line):
                continue
            entries.append(
                {
                    "id": f"{relative}:{line_number}",
                    "file": relative,
                    "line": line_number,
                    "source": line,
                    "translation": "",
                    "source_sha256": _source_hash(line),
                    "tags": _tags(line),
                    "status": "PENDENTE",
                }
            )

    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(
        json.dumps(
            {
                "catalog_version": CATALOG_VERSION,
                "source_encoding": source_encoding,
                "entries": entries,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return len(entries)


def _load_catalog(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("catalog_version") != CATALOG_VERSION:
        raise ValueError(f"Versão de catálogo não suportada: {payload.get('catalog_version')!r}")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Catálogo inválido: campo 'entries' deve ser uma lista")
    return entries


def apply_catalog(
    source_dir: Path,
    catalog_path: Path,
    output_dir: Path,
    *,
    source_encoding: str = DEFAULT_SOURCE_ENCODING,
    output_encoding: str = "utf-8",
) -> tuple[int, int]:
    """Aplica traduções numa cópia, validando fonte e tags antes de gravar.

    UTF-8 destina-se à revisão humana. CP932 pode ser selecionado, mas caracteres
    não representáveis causam erro explícito. Compatibilidade com Atlas não é presumida.
    """
    root = source_dir.resolve()
    target = output_dir.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Pasta de scripts não encontrada: {root}")
    if target == root or root in target.parents:
        raise ValueError("A pasta de saída não pode ser a pasta de origem nem ficar dentro dela.")
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(
            f"A pasta de saída não está vazia: {target}. Use uma pasta nova para evitar sobrescrita."
        )

    entries = _load_catalog(catalog_path)
    replacements: dict[str, dict[int, dict[str, Any]]] = {}
    for entry in entries:
        relative = entry.get("file")
        line_number = entry.get("line")
        if not isinstance(relative, str) or not isinstance(line_number, int) or line_number < 1:
            raise ValueError(f"Entrada inválida no catálogo: {entry.get('id', '<sem id>')}")
        relative_path = PurePosixPath(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts or not relative_path.parts:
            raise ValueError(f"Caminho inseguro no catálogo: {relative!r}")
        translation = entry.get("translation", "")
        if not isinstance(translation, str):
            raise ValueError(f"Tradução inválida em {entry.get('id', relative)}")
        if "\n" in translation or "\r" in translation:
            raise ValueError(f"Tradução não pode conter quebra de linha: {entry.get('id', relative)}")
        if not translation.strip():
            continue
        if _tags(translation) != entry.get("tags", []):
            raise ValueError(
                f"Tags/controles inline foram alterados em {entry.get('id', relative)}. "
                "Preserve todos os marcadores <...> e sua ordem."
            )
        file_replacements = replacements.setdefault(relative, {})
        if line_number in file_replacements:
            raise ValueError(f"Entrada duplicada no catálogo: {relative}:{line_number}")
        file_replacements[line_number] = entry

    written = 0
    pending = 0
    current_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*.txt")
        if path.is_file()
    }
    catalog_files = {entry.get("file") for entry in entries if isinstance(entry.get("file"), str)}
    missing = sorted(catalog_files - current_files)
    if missing:
        raise FileNotFoundError("Arquivos do catálogo ausentes: " + ", ".join(missing))

    for path in sorted(root.rglob("*.txt")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        original = path.read_bytes().decode(source_encoding)
        lines = original.splitlines(keepends=True)
        by_line = replacements.get(relative, {})
        updated_lines: list[str] = []
        for line_number, raw_line in enumerate(lines, start=1):
            line, ending = _split_line_ending(raw_line)
            entry = by_line.get(line_number)
            if entry is not None:
                if _source_hash(line) != entry.get("source_sha256") or line != entry.get("source"):
                    raise ValueError(
                        f"O texto de origem mudou desde a exportação: {relative}:{line_number}. "
                        "Exporte um catálogo novo antes de aplicar."
                    )
                line = entry["translation"]
                written += 1
            updated_lines.append(line + ending)

        for line_number in by_line:
            if line_number > len(lines):
                raise ValueError(f"Linha não encontrada no arquivo: {relative}:{line_number}")
        pending += sum(
            1
            for entry in entries
            if entry.get("file") == relative and not entry.get("translation", "").strip()
        )

        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            destination.write_bytes("".join(updated_lines).encode(output_encoding))
        except UnicodeEncodeError as exc:
            raise ValueError(
                f"Não é possível gravar {relative} em {output_encoding}: há caracteres não "
                "representáveis. Use UTF-8 para revisão ou resolva o mapeamento de glifos "
                "antes de gerar arquivos para inserção."
            ) from exc

    return written, pending


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m dragonslayer_ptbr.text.translation_workbench",
        description="Exporta e valida traduções sem modificar os arquivos de origem.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    export = commands.add_parser("export", help="gera catálogo JSON editável em UTF-8")
    export.add_argument("--source-dir", type=Path, required=True)
    export.add_argument("--catalog", type=Path, required=True)
    export.add_argument("--source-encoding", default=DEFAULT_SOURCE_ENCODING)

    apply = commands.add_parser("apply", help="aplica traduções numa pasta nova")
    apply.add_argument("--source-dir", type=Path, required=True)
    apply.add_argument("--catalog", type=Path, required=True)
    apply.add_argument("--output-dir", type=Path, required=True)
    apply.add_argument("--source-encoding", default=DEFAULT_SOURCE_ENCODING)
    apply.add_argument(
        "--output-encoding",
        choices=("utf-8", "cp932"),
        default="utf-8",
        help="UTF-8 para revisão; CP932 somente se todos os caracteres forem representáveis",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "export":
        count = export_catalog(
            args.source_dir,
            args.catalog,
            source_encoding=args.source_encoding,
        )
        print(f"Catálogo salvo: {args.catalog}")
        print(f"Linhas japonesas catalogadas: {count}")
        print("Os arquivos de origem não foram modificados.")
        return 0

    written, pending = apply_catalog(
        args.source_dir,
        args.catalog,
        args.output_dir,
        source_encoding=args.source_encoding,
        output_encoding=args.output_encoding,
    )
    print(f"Cópia de revisão criada em: {args.output_dir}")
    print(f"Linhas traduzidas aplicadas: {written}")
    print(f"Linhas ainda pendentes no catálogo: {pending}")
    print("Compatibilidade com Atlas/inserção na ROM ainda precisa ser validada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
