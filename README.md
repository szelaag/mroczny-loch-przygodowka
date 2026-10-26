# Mroczny Loch — tekstowa przygodówka z AI-narratorem

Tekstowa gra RPG w terminalu, w której Claude jest narratorem prowadzącym gracza
przez mroczny loch. Gracz wpisuje akcje zwykłym tekstem, narrator opisuje ich skutki,
a twarda mechanika (ekwipunek, HP, walka, statystyki przedmiotów) żyje w kodzie.

Projekt służyl do nauki AI engineeringu na czystym Anthropic SDK (bez LangChain itp.):
multi-turn, tool use, wymuszone structured outputs z walidacją Pydantic i pętlą
naprawczą, liczenie kosztu, persystencja stanu.

**Zasada architektury: „kod liczy, model maluje”.** Model decyduje *kiedy* coś się
dzieje (gracz podniósł przedmiot, zaczęła się walka) i opisuje to w fikcji. Kod
decyduje *ile* (obrażenia, HP, statystyki) i pilnuje stanu.

## Funkcje

- **Narrator AI** z system promptem definiującym ton, łuk rozdziału (przebudzenie →
  eksploracja → bestia przy wyjściu) i zasady narracji (2–4 zdania, druga osoba,
  zawsze kończy wezwaniem do działania).
- **Tool use**: narrator zgłasza zmiany ekwipunku (`aktualizuj_ekwipunek`) i początek
  walki (`rozpocznij_walke`); kod aktualizuje stan.
- **Generowanie przedmiotów**: przedmiot spoza katalogu dostaje statystyki od
  osobnego wywołania modelu z wymuszonym narzędziem (`generuj_nieznane`). Wynik
  przechodzi walidację Pydantic; przy błędzie trafia do modelu jako `tool_result`
  do poprawy (do 3 prób, potem fallback).
- **Turowa walka**: wybór broni i ataku (każdy z zakresem obrażeń i szansą chybienia),
  kontratak wroga, panel HP. Po walce narrator opisuje finał na podstawie
  tymczasowej instrukcji systemowej (z `tool_choice: none`), usuwanej z historii.
- **Archiwista**: osobny prompt streszczający dotychczasową przygodę.
- **Koszt sesji**: tokeny input/output i koszt w USD/PLN.
- **Zapis/odczyt gry** do JSON (stan, koszt, historia rozmowy, katalog przedmiotów
  razem z wygenerowanymi), ekran startowy z listą zapisów.
- **UI w `rich`**: panele, tabele, kolorowanie przedmiotów/wrogów/akcji w narracji
  (narrator wstawia tagi kolorów `rich`).
- **Tryb debug** do ręcznej edycji stanu i testowania walki.

## Wymagania

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Klucz API Anthropic (https://console.anthropic.com)

## Instalacja

```bash
uv sync
cp .env.example .env
# w .env wpisz: ANTHROPIC_API_KEY=sk-ant-...
```

## Uruchomienie

```bash
uv run main.py           # zwykła gra
uv run main.py --debug   # otwiera edytor stanu przed startem gry
```

Na ekranie startowym: `1` nowa gra, `2` wczytanie zapisu (jeśli istnieją).
Po wczytaniu gra pyta, czy przypomnieć historię (streszczenie archiwisty kosztuje
jedno wywołanie API, ostatnia scena wyświetla się zawsze).

## Sterowanie

Akcje wpisujesz zwykłym tekstem (`rozglądam się`, `podnoszę miecz`, `atakuję szczura`).

| Komenda | Działanie |
|---------|-----------|
| `/pomoc` | lista komend |
| `/ekwipunek`, `/eq` | ekwipunek |
| `/stan`, `/hp` | zdrowie |
| `/historia` | streszczenie przygody (archiwista) |
| `/koszt` | tokeny i koszt sesji |
| `/zapisz` | zapis gry do `saves/<nazwa>.json` |
| `/wyjdz` | koniec gry |

W walce wybierasz broń i atak numerem. Bez broni walczysz gołymi rękami.

### Komendy deweloperskie (`$`)

Dostępne w trakcie gry:

| Komenda | Działanie |
|---------|-----------|
| `$$`, `$state`, `$debug` | edytor stanu (patrz niżej) |
| `$sethp <liczba>` | ustawia HP |
| `$spawn <nazwa>` | dodaje przedmiot do ekwipunku |
| `$kill` | ustawia HP na 0 |

Edytor stanu (`debug.py`) ma własne komendy, m.in. `$walka <przeciwnik>` (symulacja
walki), `$show <hp|eq|state|catalog>`, `$testset` (zestaw testowych przedmiotów),
`$create` (kreator przedmiotu do katalogu). W edytorze `$$` anuluje, `$$$` cofa krok.

## Struktura projektu

```
mroczny-loch/
├── main.py          # pętla gry, obsługa komend, orkiestracja tury i finału walki
├── api.py           # wywołania narratora i archiwisty, parsowanie tool_use
├── prompts.py       # NARRATOR_PROMPT, SUMMARY_PROMPT, GENERATOR_PROMPT, GENESIS_PROMPT
├── models.py        # dataclassy: Item, Attack, GameState, Enemy, Response, Usage; ItemType
├── items.py         # ITEM_CATALOG, INVENTORY_TOOL, create_item
├── combat.py        # ENEMY_CATALOG, COMBAT_TOOL, pętla walki
├── generation.py    # generowanie statystyk przedmiotów (STATS_TOOL + Pydantic + retry)
├── cost.py          # liczenie kosztu z tokenów
├── save.py          # serializacja do JSON, zapis/odczyt, ekran startowy
├── ui.py            # cały interfejs w rich
├── debug.py         # edytor stanu / narzędzia testowe
├── config.py        # model, cennik, max_tokens, kurs USD/PLN
└── pyproject.toml
```

Katalogi `saves/` i `md_logs/` oraz `.env` są w `.gitignore`.

## Jak działa tura

1. Akcja gracza trafia do `message_history` jako wiadomość `user`.
2. `ask_narrator` wysyła historię z system promptem narratora, do którego doklejony
   jest aktualny ekwipunek, oraz z narzędziami ekwipunku i walki.
3. `handle_response` wyciąga narrację, dodaje/usuwa przedmioty (pomijając duplikaty)
   i zbiera nazwy nieznanych przedmiotów oraz ewentualnego przeciwnika.
4. Nieznane przedmioty dostają statystyki z `generuj_statystyki` i trafiają do
   `ITEM_CATALOG`, a egzemplarze w ekwipunku są podmieniane.
5. Jeśli narrator rozpoczął walkę, toczy się ona w kodzie (`prowadz_walke`).
   Potem narrator dostaje tymczasową instrukcję z wynikiem i opisuje finał bez
   liczb i mechaniki. Instrukcja jest usuwana z historii.

Stan świata to `message_history` (pamięć narratora) plus `GameState` (HP i
ekwipunek w kodzie). Pierwsza scena powstaje z `GENESIS_PROMPT` wstrzykniętego jako
pierwsza wiadomość `user`; gracz widzi tylko odpowiedź.

## Konfiguracja

`config.py`:

| Stała | Znaczenie |
|-------|-----------|
| `MODEL` | model używany przez narratora, archiwistę i generator |
| `MODEL_PRICING` | cena za 1M tokenów (input, output) w USD per model |
| `MAX_TOKENS` | limit tokenów odpowiedzi |
| `USD_PLN` | kurs do przeliczania kosztu |

Po zmianie `MODEL` dopisz jego cennik do `MODEL_PRICING`, inaczej liczenie kosztu
rzuci `KeyError`.
