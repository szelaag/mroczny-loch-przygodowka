# Mroczny Loch — tekstowa przygodówka z AI-narratorem

Tekstowa gra przygodowa, w której model Claude pełni rolę narratora prowadzącego
gracza przez mroczny loch. Stan świata żyje w historii rozmowy (multi-turn),
narracja leci na żywo (streaming), a gracz działa akcjami wpisywanymi w terminalu.

Projekt nauki AI engineering — integruje pracę z Anthropic SDK (streaming,
multi-turn, koszt, error handling), projektowanie system promptów i stopniowo
budowaną architekturę (dataclassy, podział na moduły, persystencja).

## Wymagania

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) jako menedżer pakietów
- Klucz API Anthropic (https://console.anthropic.com)

## Setup od zera

Projekt ma własne, izolowane środowisko (`.venv`) z zależnościami zarządzanymi
przez `uv`. Jeśli stawiasz go na nowej maszynie albo po sklonowaniu repo:

```bash
# 1. Wejdź do folderu projektu
cd przygodowka

# 2. Zainstaluj zależności (uv utworzy .venv i pobierze pakiety z pyproject.toml)
uv sync

# 3. Skopiuj szablon zmiennych środowiskowych i wpisz swój klucz API
cp .env.example .env
# następnie otwórz .env i wpisz: ANTHROPIC_API_KEY=sk-ant-...
```

Jeśli zakładasz projekt **całkiem od nowa** (bez istniejącego `pyproject.toml`):

```bash
uv init                            # inicjalizuje projekt
uv add anthropic python-dotenv     # dodaje zależności do .venv
```

## Uruchomienie

```bash
uv run main.py
```

`uv run` automatycznie używa lokalnego `.venv` projektu — nie trzeba aktywować
środowiska ręcznie.

## Konfiguracja edytora (VS Code)

Jeśli Pylance podkreśla importy (`anthropic`, `dotenv`) mimo działającego kodu,
to znak, że VS Code wskazuje zły interpreter. Napraw:

`Cmd+Shift+P` → **Python: Select Interpreter** → wybierz interpreter z
`./.venv/bin/python` tego projektu.

## Sterowanie w grze

Akcje wpisujesz zwykłym tekstem (np. `rozglądam się`, `podnoszę klucz`).
Komendy systemowe zaczynają się od `/`:

| Komenda | Działanie |
|---------|-----------|
| `/historia` | streszczenie dotychczasowej przygody (osobny model-archiwista) |
| `/koszt` | koszt sesji (tokeny input/output, USD/PLN) |
| `/wyjdz` | zakończenie gry |

## Struktura projektu

```
przygodowka/
├── main.py            # pętla gry, funkcje API, dataclassy, orkiestracja
├── prompts.py         # SYSTEM_PROMPT (narrator), SUMMARY_PROMPT (archiwista), GENESIS_PROMPT
├── system_prompts.md  # warsztat promptów (iteracje, notatki — NIE importowany)
├── pyproject.toml     # zależności i metadane projektu (zarządzane przez uv)
├── .env               # klucz API (NIE commitowany — w .gitignore)
├── .env.example       # szablon .env do skopiowania
└── .gitignore
```

## Bezpieczeństwo

- `.env` (z kluczem API) jest w `.gitignore` — **nigdy nie trafia do gita**.
- Przed pierwszym commitem sprawdź `git status` — `.env` nie powinien się pojawić.

## Architektura — notatki

- **Stan świata** żyje w `message_history` (lista wiadomości multi-turn), nie
  w zmiennych kodu. Narrator "pamięta" przez kontekst wysyłany przy każdym callu.
- **Dwa system prompty**: narrator (tworzy fikcję, streaming, czysty tekst) oraz
  archiwista (destyluje fakty do dziennika, zwykły call, struktura OK).
- **Genesis**: pierwsza scena generowana na starcie przez wstrzyknięcie
  `GENESIS_PROMPT` jako pierwsza wiadomość `user`; gracz widzi tylko odpowiedź.
- **Rozróżnienie historia vs ekran**: pełna historia (z genesis-poleceniem) idzie
  do modelu; graczowi wyświetlana jest tylko narracja.

## Roadmap (etapy)

- [x] Etap 1 — rdzeń grywalny (genesis, multi-turn, streaming, system prompt)
- [x] Etap 2 — komendy systemowe + koszt + streszczacz (`/historia`, `/koszt`)
- [ ] Etap 2.5 — `Usage` (liczenie kosztu dla genesis i streszczacza)
- [ ] Etap 3 — twardy stan gry: ekwipunek, potem HP/walka (`GameState`)
- [ ] Etap 4 — persystencja: save files (zapis/odczyt stanu, ekran startowy,
      wybór świata i modelu)
- [ ] Rich — kolory narracji, render markdown dziennika, tabela kosztu
- [ ] Kompresja kontekstu — automatyczne streszczanie dla oszczędności tokenów
