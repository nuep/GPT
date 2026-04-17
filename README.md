# GPT

## Siemens OP17 / ProSave backup parser

Repo zawiera skrypt `decode_prosave_tags.py`, który:

1. próbuje "rozpakować"/odczytać backup ProSave (`.psb`, `.fwd`, binarny dump),
2. wyciąga ciągi tekstowe (ASCII + UTF-16LE),
3. wyszukuje adresację tagów Siemens (np. `DB10.DBW4`, `I0.0`, `Q4.1`, `MW20`),
4. zapisuje wynik do JSON i/lub CSV.

### Uruchomienie

```bash
python3 decode_prosave_tags.py /ścieżka/do/backupu.psb --json tags.json --csv tags.csv
```

Możesz też podać katalog (np. gdy nie możesz wskazać pojedynczego pliku):

```bash
python3 decode_prosave_tags.py /ścieżka/do/katalogu_z_backupami -r --json tags.json
```

### Uwagi

- Format backupu ProSave bywa częściowo binarny i/lub zależny od wersji panelu.
- Skrypt działa heurystycznie: wyciąga realnie znalezione adresy ze strumienia danych.
- Jeśli plik jest dodatkowo szyfrowany hasłem/kluczem producenta, konieczne może być
  wcześniejsze odszyfrowanie narzędziem serwisowym.
- Jeśli dostajesz błąd „brak pliku”, sprawdź ścieżkę i użyj cudzysłowów dla ścieżek ze spacjami.
