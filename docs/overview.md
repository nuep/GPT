# Przewodnik po repozytorium GPT

Ten dokument ma na celu szybkie wprowadzenie nowych użytkowników w strukturę repozytorium i dobre praktyki pracy.

## Aktualny stan

Repozytorium zaczyna jako lekki szkielet – w momencie dołączenia może zawierać jedynie dokumentację. Wraz z rozwojem projektu zachęcamy do budowania następującej struktury:

```
GPT/
├── README.md          # Główny przewodnik po repozytorium
├── docs/              # Dokumentacja dodatkowa, standardy, specyfikacje
├── src/               # Kod źródłowy aplikacji lub bibliotek
├── tests/             # Testy jednostkowe, integracyjne i e2e
├── scripts/           # Narzędzia pomocnicze (np. migracje, CI)
└── examples/          # Przykłady użycia lub notatniki demonstracyjne
```

Dodawaj katalogi w miarę potrzeb; ważne, aby utrzymywać spójność w całym zespole.

## Kluczowe zasady

1. **Dokumentuj zmiany** – każda większa funkcjonalność powinna być opisana w dokumentacji oraz w logu zmian (CHANGELOG lub release notes).
2. **Testuj kod** – nawet proste moduły warto pokryć testami, aby ułatwić refaktoryzację.
3. **Dbaj o styl** – ustal lintery i formatery (np. `black`, `eslint`, `ruff`) odpowiednie dla używanego języka.
4. **Automatyzuj** – konfiguruj CI/CD, aby testy i analizy jakości uruchamiały się automatycznie.
5. **Przeglądaj PR-y** – code review zwiększa jakość kodu i ułatwia dzielenie się wiedzą.

## Co warto znać

- **Git i GitHub/GitLab** – podstawy pracy z gałęziami, PR-ami i tagami.
- **Język implementacji** – w zależności od projektu (Python, TypeScript, Go itd.).
- **Testowanie** – narzędzia takie jak `pytest`, `unittest`, `jest`, `go test`.
- **Konteneryzacja** – Docker lub alternatywy ułatwiające powtarzalne środowiska.
- **CI/CD** – GitHub Actions, GitLab CI, CircleCI lub inne systemy automatyzacji.

## Następne kroki dla nowych członków

1. Skonfiguruj środowisko deweloperskie zgodnie z przyjętymi standardami.
2. Zapoznaj się z backlogiem zadań (np. Issues/Stories) i wybierz pierwsze zadanie.
3. Wprowadź drobną zmianę, aby przećwiczyć proces PR i code review.
4. Zadawaj pytania! Lepsze jest wczesne uzgadnianie założeń niż późniejsze poprawki.

Witamy w projekcie i powodzenia w pracy nad GPT!
