#!/usr/bin/env python3
"""
Heurystyczny parser backupów Siemens ProSave (np. OP17).

Funkcje:
- odczyt surowego pliku backupu lub archiwum (ZIP/TAR/GZIP),
- ekstrakcja ciągów ASCII i UTF-16LE,
- wyszukiwanie adresów tagów Siemens (DB, I, Q, M, T, C),
- eksport wyników do stdout / JSON / CSV.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import re
import sys
import tarfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


ASCII_MIN_LEN = 4
UTF16_MIN_LEN = 4


@dataclass(frozen=True, order=True)
class TagHit:
    tag: str
    source_file: str
    encoding: str
    context: str


DB_PATTERN = re.compile(
    r"\bDB\s*\d+\s*\.\s*DB[XBWD]\s*\d+(?:\s*\.\s*\d+)?\b",
    re.IGNORECASE,
)

AREA_PATTERN = re.compile(
    r"\b(?:[IQM](?:\s*[XBWD])?\s*\d+(?:\s*\.\s*\d+)?)\b",
    re.IGNORECASE,
)

COUNTER_TIMER_PATTERN = re.compile(
    r"\b(?:T|C)\s*\d+\b",
    re.IGNORECASE,
)

KNOWN_PREFIXES = ("DB", "I", "Q", "M", "T", "C")
COMMON_BACKUP_EXTENSIONS = (".psb", ".fwd", ".bak", ".bin", ".zip", ".tar", ".gz", ".tgz")


def normalize_tag(tag: str) -> str:
    t = re.sub(r"\s+", "", tag.upper())
    return t


def sniff_and_collect_payloads(backup_file: Path) -> list[tuple[str, bytes]]:
    """
    Zwraca listę (nazwa_logicza, bytes) do dalszego skanowania.
    Obsługiwane:
    - raw bin,
    - zip,
    - tar/tgz/tar.gz,
    - gzip pojedynczego pliku.
    """
    raw = backup_file.read_bytes()
    payloads: list[tuple[str, bytes]] = []

    # ZIP
    if zipfile.is_zipfile(backup_file):
        with zipfile.ZipFile(backup_file, "r") as zf:
            for name in zf.namelist():
                if name.endswith("/"):
                    continue
                payloads.append((name, zf.read(name)))
        return payloads

    # TAR (także skompresowane)
    try:
        with tarfile.open(backup_file, "r:*") as tf:
            members = [m for m in tf.getmembers() if m.isfile()]
            if members:
                for m in members:
                    extracted = tf.extractfile(m)
                    if extracted:
                        payloads.append((m.name, extracted.read()))
                return payloads
    except tarfile.TarError:
        pass

    # GZIP single-stream
    try:
        with gzip.open(io.BytesIO(raw), "rb") as gz:
            unpacked = gz.read()
        if unpacked:
            payloads.append((f"{backup_file.name}::gunzip", unpacked))
            return payloads
    except OSError:
        pass

    # fallback raw
    payloads.append((backup_file.name, raw))
    return payloads


def extract_ascii_strings(data: bytes, min_len: int = ASCII_MIN_LEN) -> list[str]:
    pattern = rb"[\x20-\x7E]{" + str(min_len).encode("ascii") + rb",}"
    return [m.decode("ascii", errors="ignore") for m in re.findall(pattern, data)]


def extract_utf16le_strings(data: bytes, min_len: int = UTF16_MIN_LEN) -> list[str]:
    # Sekwencje "A\0B\0C\0..."
    pattern = rb"(?:[\x20-\x7E]\x00){" + str(min_len).encode("ascii") + rb",}"
    chunks = re.findall(pattern, data)
    out: list[str] = []
    for chunk in chunks:
        try:
            out.append(chunk.decode("utf-16le", errors="ignore"))
        except UnicodeDecodeError:
            continue
    return out


def iter_tag_candidates(s: str) -> Iterable[str]:
    for patt in (DB_PATTERN, AREA_PATTERN, COUNTER_TIMER_PATTERN):
        for m in patt.finditer(s):
            normalized = normalize_tag(m.group(0))
            if normalized.startswith(KNOWN_PREFIXES):
                yield normalized


def extract_tags_from_payload(name: str, data: bytes) -> list[TagHit]:
    hits: list[TagHit] = []

    for enc_name, strings in (
        ("ascii", extract_ascii_strings(data)),
        ("utf16le", extract_utf16le_strings(data)),
    ):
        for s in strings:
            for tag in iter_tag_candidates(s):
                context = s[:200]
                hits.append(TagHit(tag=tag, source_file=name, encoding=enc_name, context=context))
    return hits


def dedupe_hits(hits: list[TagHit]) -> list[TagHit]:
    # dedupe po pełnym rekordzie
    unique = sorted(set(hits))
    return unique


def write_csv(hits: list[TagHit], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["tag", "source_file", "encoding", "context"])
        w.writeheader()
        for hit in hits:
            w.writerow(asdict(hit))


def write_json(hits: list[TagHit], path: Path) -> None:
    data = [asdict(h) for h in hits]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_input_files(input_path: Path, recursive: bool = False) -> list[Path]:
    """
    Rozwiązuje wejście:
    - plik => [plik]
    - katalog => lista potencjalnych backupów
    """
    if input_path.is_file():
        return [input_path]

    if input_path.is_dir():
        pattern = "**/*" if recursive else "*"
        candidates: list[Path] = []
        for p in input_path.glob(pattern):
            if not p.is_file():
                continue
            if p.suffix.lower() in COMMON_BACKUP_EXTENSIONS:
                candidates.append(p)
        return sorted(candidates)

    return []


def print_path_help(input_path: Path) -> None:
    print(f"[ERR] Nie znaleziono pliku/katalogu: {input_path}", file=sys.stderr)
    print(
        "[TIP] Jeśli ścieżka ma spacje, podaj ją w cudzysłowie, np.: "
        'python3 decode_prosave_tags.py "C:\\Moje backupy\\Panel OP17.psb"',
        file=sys.stderr,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dekoduje backup ProSave i wyciąga adresację tagów Siemens."
    )
    parser.add_argument(
        "backup",
        type=Path,
        help="Ścieżka do pliku backupu ProSave lub katalogu z backupami.",
    )
    parser.add_argument("--json", dest="json_out", type=Path, help="Zapisz wynik do JSON.")
    parser.add_argument("--csv", dest="csv_out", type=Path, help="Zapisz wynik do CSV.")
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Przy wejściu będącym katalogiem skanuj rekurencyjnie podkatalogi.",
    )
    args = parser.parse_args()

    if not args.backup.exists():
        print_path_help(args.backup)
        return 2

    input_files = resolve_input_files(args.backup, recursive=args.recursive)
    if not input_files:
        if args.backup.is_dir():
            print(
                f"[ERR] W katalogu nie znaleziono backupów z rozszerzeniami: "
                f"{', '.join(COMMON_BACKUP_EXTENSIONS)}",
                file=sys.stderr,
            )
        else:
            print_path_help(args.backup)
        return 2

    all_hits: list[TagHit] = []
    processed_files: list[str] = []
    for backup_file in input_files:
        payloads = sniff_and_collect_payloads(backup_file)
        for name, data in payloads:
            all_hits.extend(extract_tags_from_payload(name, data))
        processed_files.append(str(backup_file))

    hits = dedupe_hits(all_hits)

    if args.json_out:
        write_json(hits, args.json_out)
    if args.csv_out:
        write_csv(hits, args.csv_out)

    # stdout summary
    if len(processed_files) == 1:
        print(f"Plik: {processed_files[0]}")
    else:
        print(f"Przetworzone pliki: {len(processed_files)}")
    print(f"Znaleziono tagów: {len(hits)}")
    for h in hits:
        print(f"- {h.tag} [{h.source_file}/{h.encoding}]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
