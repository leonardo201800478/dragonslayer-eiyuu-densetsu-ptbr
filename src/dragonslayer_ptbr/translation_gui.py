from __future__ import annotations

import argparse
import csv
import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from .translation_catalog import (
    import_external_dump,
    load_catalog,
    save_catalog,
    validate_entry,
    write_qa_report,
)

class TranslationWorkbench(tk.Tk):
    """Interface desktop simples para revisar dumps extraídos por ferramentas externas."""

    def __init__(self, catalog_path: Path) -> None:
        super().__init__()
        self.title("Dragon Slayer — Bancada de Tradução PT-BR")
        self.geometry("1180x760")
        self.minsize(900, 600)
        self.catalog_path = catalog_path
        self.payload, self.entries = load_catalog(catalog_path)
        self.visible_indices: list[int] = []
        self.current_index: int | None = None
        self._build_ui()
        self._refresh_list()
        if self.visible_indices:
            self._select_entry(0)

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self, padding=8)
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Abrir catálogo", command=self._open_catalog).pack(side="left")
        ttk.Button(toolbar, text="Importar dump JSON/CSV", command=self._import_dump).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Salvar", command=self._save).pack(side="left")
        ttk.Button(toolbar, text="Validar catálogo", command=self._validate).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Exportar CSV", command=self._export_csv).pack(side="left")
        self.status_var = tk.StringVar(value="")
        ttk.Label(toolbar, textvariable=self.status_var).pack(side="right")

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        left = ttk.Frame(body, padding=4)
        right = ttk.Frame(body, padding=8)
        body.add(left, weight=1)
        body.add(right, weight=3)

        filters = ttk.Frame(left)
        filters.pack(fill="x", pady=(0, 6))
        self.search_var = tk.StringVar()
        search = ttk.Entry(filters, textvariable=self.search_var)
        search.pack(fill="x")
        search.bind("<KeyRelease>", lambda _event: self._refresh_list())
        self.pending_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            filters, text="Somente pendentes", variable=self.pending_only,
            command=self._refresh_list,
        ).pack(anchor="w", pady=(4, 0))

        list_frame = ttk.Frame(left)
        list_frame.pack(fill="both", expand=True)
        self.entry_list = tk.Listbox(list_frame, exportselection=False, width=38)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.entry_list.yview)
        self.entry_list.configure(yscrollcommand=scroll.set)
        self.entry_list.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.entry_list.bind("<<ListboxSelect>>", self._on_select)

        ttk.Label(right, text="Origem (somente leitura)", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        self.source_text = tk.Text(right, height=8, wrap="word", state="disabled")
        self.source_text.pack(fill="x", pady=(4, 10))
        ttk.Label(right, text="Tradução / adaptação PT-BR", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        self.translation_text = tk.Text(right, height=12, wrap="word", undo=True)
        self.translation_text.pack(fill="both", expand=True, pady=(4, 8))
        self.translation_text.bind("<KeyRelease>", lambda _event: self._update_quality())
        controls = ttk.Frame(right)
        controls.pack(fill="x")
        ttk.Button(controls, text="Anterior", command=lambda: self._move(-1)).pack(side="left")
        ttk.Button(controls, text="Próximo", command=lambda: self._move(1)).pack(side="left", padx=6)
        ttk.Button(controls, text="Salvar esta entrada", command=self._save_current).pack(side="left")
        self.quality_var = tk.StringVar(value="")
        ttk.Label(right, textvariable=self.quality_var, wraplength=760).pack(anchor="w", pady=(8, 0))

    def _refresh_list(self) -> None:
        query = self.search_var.get().casefold() if hasattr(self, "search_var") else ""
        only_pending = self.pending_only.get() if hasattr(self, "pending_only") else False
        previous = self.current_index
        self.visible_indices = []
        self.entry_list.delete(0, tk.END)
        for index, entry in enumerate(self.entries):
            haystack = " ".join(
                str(entry.get(key, "")) for key in ("id", "file", "source", "translation", "context")
            ).casefold()
            if query and query not in haystack:
                continue
            if only_pending and str(entry.get("translation", "")).strip():
                continue
            self.visible_indices.append(index)
            label = f"{entry.get('id', index)}  [{'✓' if str(entry.get('translation', '')).strip() else '…'}]"
            self.entry_list.insert(tk.END, label)
        self.status_var.set(f"{len(self.entries)} entradas · {len(self.visible_indices)} exibidas")
        if previous in self.visible_indices:
            position = self.visible_indices.index(previous)
            self.entry_list.selection_set(position)
            self.entry_list.see(position)

    def _on_select(self, _event: Any = None) -> None:
        selected = self.entry_list.curselection()
        if selected:
            self._select_entry(int(selected[0]))

    def _select_entry(self, visible_position: int) -> None:
        if visible_position >= len(self.visible_indices):
            return
        self._save_current(silent=True)
        index = self.visible_indices[visible_position]
        self.current_index = index
        entry = self.entries[index]
        self.source_text.configure(state="normal")
        self.source_text.delete("1.0", tk.END)
        self.source_text.insert("1.0", str(entry.get("source", "")))
        self.source_text.configure(state="disabled")
        self.translation_text.delete("1.0", tk.END)
        self.translation_text.insert("1.0", str(entry.get("translation", "")))
        self._update_quality()

    def _save_current(self, silent: bool = False) -> None:
        if self.current_index is None:
            return
        entry = self.entries[self.current_index]
        entry["translation"] = self.translation_text.get("1.0", "end-1c")
        entry["status"] = "TRADUZIDO" if entry["translation"].strip() else "PENDENTE"
        self._update_quality()
        if not silent:
            self._refresh_list()

    def _update_quality(self) -> None:
        if self.current_index is None:
            self.quality_var.set("")
            return
        entry = self.entries[self.current_index]
        entry["translation"] = self.translation_text.get("1.0", "end-1c")
        problems = validate_entry(entry)
        if not problems:
            self.quality_var.set("QA textual: sem divergências de marcadores detectadas.")
        else:
            self.quality_var.set("QA textual: " + " | ".join(problems))

    def _move(self, direction: int) -> None:
        if not self.visible_indices:
            return
        selected = self.entry_list.curselection()
        position = selected[0] if selected else 0
        next_position = max(0, min(len(self.visible_indices) - 1, position + direction))
        self.entry_list.selection_clear(0, tk.END)
        self.entry_list.selection_set(next_position)
        self.entry_list.see(next_position)
        self._select_entry(next_position)

    def _save(self) -> None:
        self._save_current(silent=True)
        save_catalog(self.catalog_path, self.payload, self.entries)
        self._refresh_list()
        self.status_var.set(f"Salvo: {self.catalog_path}")

    def _validate(self) -> None:
        self._save_current(silent=True)
        report_path = self.catalog_path.with_name("translation-qa-report.json")
        report = write_qa_report(report_path, self.entries)
        messagebox.showinfo(
            "Validação textual",
            f"Entradas: {report['entries_total']}\n"
            f"Traduzidas: {report['translated']}\n"
            f"Pendentes: {report['pending']}\n"
            f"Com erros de marcadores: {report['with_errors']}\n\n"
            f"Relatório: {report_path}\n\n"
            "Isso não comprova que os textos possam ser reinseridos na ROM.",
        )
        self.status_var.set(f"QA salvo: {report_path}")

    def _open_catalog(self) -> None:
        selected = filedialog.askopenfilename(
            title="Abrir catálogo de tradução",
            filetypes=[("Catálogo JSON", "*.json"), ("Todos os arquivos", "*.*")],
        )
        if not selected:
            return
        try:
            self._save_current(silent=True)
            self.catalog_path = Path(selected)
            self.payload, self.entries = load_catalog(self.catalog_path)
            self.current_index = None
            self._refresh_list()
            if self.visible_indices:
                self._select_entry(0)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Não foi possível abrir", str(exc))

    def _import_dump(self) -> None:
        selected = filedialog.askopenfilename(
            title="Importar saída de ferramenta externa",
            filetypes=[("JSON/CSV", "*.json *.csv"), ("JSON", "*.json"), ("CSV", "*.csv")],
        )
        if not selected:
            return
        destination = filedialog.asksaveasfilename(
            title="Salvar como catálogo normalizado",
            defaultextension=".json",
            filetypes=[("Catálogo JSON", "*.json")],
        )
        if not destination:
            return
        try:
            count = import_external_dump(Path(selected), Path(destination))
            self.catalog_path = Path(destination)
            self.payload, self.entries = load_catalog(self.catalog_path)
            self.current_index = None
            self._refresh_list()
            if self.visible_indices:
                self._select_entry(0)
            messagebox.showinfo("Importação concluída", f"{count} entradas importadas.")
        except (OSError, ValueError, TypeError, json.JSONDecodeError, csv.Error) as exc:
            messagebox.showerror("Falha na importação", str(exc))

    def _export_csv(self) -> None:
        self._save_current(silent=True)
        destination = filedialog.asksaveasfilename(
            title="Exportar catálogo para CSV",
            defaultextension=".csv",
            filetypes=[("CSV UTF-8", "*.csv")],
        )
        if not destination:
            return
        fields = ("id", "file", "line", "source", "translation", "status")
        with Path(destination).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for entry in self.entries:
                writer.writerow({key: entry.get(key, "") for key in fields})
        self.status_var.set(f"CSV exportado: {destination}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Interface desktop da bancada de tradução PT-BR.")
    parser.add_argument(
        "--catalog",
        type=Path,
        help="catálogo JSON para abrir; se omitido, escolha um arquivo ou crie/importando um dump",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        catalog = args.catalog
        if catalog is None:
            root = tk.Tk()
            root.withdraw()
            selected = filedialog.askopenfilename(
                title="Abrir catálogo de tradução",
                filetypes=[("Catálogo JSON", "*.json"), ("Todos os arquivos", "*.*")],
            )
            root.destroy()
            if not selected:
                return 0
            catalog = Path(selected)
        app = TranslationWorkbench(catalog)
        app.mainloop()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        messagebox.showerror("Erro na bancada de tradução", str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
