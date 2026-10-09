"""Validação e aplicação de manifestos de patch binário."""

from __future__ import annotations

import json
from itertools import pairwise
from pathlib import Path
from typing import Any


class PatchError(ValueError):
    """Erro de validação ao carregar ou aplicar um manifesto."""


def load_manifest(path: Path) -> list[dict[str, Any]]:
    """Carrega e valida a estrutura e codificação hexadecimal do manifesto."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PatchError(f"Não foi possível ler o manifesto: {exc}") from exc

    if not isinstance(data, dict) or set(data) != {"patches"}:
        raise PatchError("O manifesto deve conter apenas a chave 'patches'.")
    patches = data["patches"]
    if not isinstance(patches, list):
        raise PatchError("'patches' deve ser uma lista.")

    validated: list[dict[str, Any]] = []
    for index, patch in enumerate(patches):
        label = f"patches[{index}]"
        if not isinstance(patch, dict):
            raise PatchError(f"{label} deve ser um objeto.")
        if not {"offset", "original", "replacement"}.issubset(patch):
            raise PatchError(f"{label} precisa de offset, original e replacement.")
        offset = patch["offset"]
        if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
            raise PatchError(f"{label}.offset deve ser um inteiro não negativo.")
        try:
            original = bytes.fromhex(patch["original"])
            replacement = bytes.fromhex(patch["replacement"])
        except (TypeError, ValueError) as exc:
            raise PatchError(f"{label} contém hexadecimal inválido.") from exc
        if not original or not replacement:
            raise PatchError(f"{label}: original e replacement não podem ser vazios.")
        if len(original) != len(replacement):
            raise PatchError(f"{label}: original e replacement devem ter o mesmo tamanho.")
        validated.append({"offset": offset, "original": original, "replacement": replacement})

    validated.sort(key=lambda patch: patch["offset"])
    for previous, current in pairwise(validated):
        if current["offset"] < previous["offset"] + len(previous["original"]):
            raise PatchError("O manifesto contém alterações sobrepostas.")
    return validated


def apply_patches(rom: bytes, patches: list[dict[str, Any]]) -> bytes:
    """Aplica alterações somente se os bytes e limites corresponderem."""
    result = bytearray(rom)
    for index, patch in enumerate(patches):
        offset = patch["offset"]
        original = patch["original"]
        replacement = patch["replacement"]
        end = offset + len(original)
        if end > len(result):
            raise PatchError(f"patches[{index}] excede o tamanho da ROM.")
        if result[offset:end] != original:
            raise PatchError(f"patches[{index}]: bytes originais não correspondem no offset {offset}.")
        result[offset:end] = replacement
    return bytes(result)


def apply_manifest(rom_path: Path, manifest_path: Path, output_path: Path) -> int:
    """Valida e aplica um manifesto, retornando a quantidade de alterações."""
    if rom_path.resolve() == output_path.resolve():
        raise PatchError("O arquivo de saída não pode sobrescrever a ROM de entrada.")
    try:
        rom = rom_path.read_bytes()
    except OSError as exc:
        raise PatchError(f"Não foi possível ler a ROM: {exc}") from exc

    patches = load_manifest(manifest_path)
    patched_rom = apply_patches(rom, patches)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(patched_rom)
    except OSError as exc:
        raise PatchError(f"Não foi possível gravar a saída: {exc}") from exc
    return len(patches)
