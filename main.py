from generation import generuj_statystyki
from items import ITEM_CATALOG, create_item
from models import ItemType
from api import ask_narrator, handle_response, summarize_history
from cost import add_usage
from combat import create_enemy, prowadz_walke
from debug import modify_state
from save import cmd_zapisz, ekran_startowy
from ui import pokaz_eq, pokaz_narracje, pokaz_koszt, pokaz_komendy, pokaz_stan_hp, pokaz_komunikat, pokaz_tytul, pokaz_smierc, pokaz_sam_tytul
from ui import console

import sys

DEBUG = "--debug" in sys.argv


def main() -> None:
    pokaz_tytul()

    state, usage, message_history, nowa_gra = ekran_startowy()

    if DEBUG:
        modify_state(state)

    pokaz_sam_tytul()

    if nowa_gra:
        if state.hp > 0:
            response = ask_narrator(message_history, state.inventory)
            result = handle_response(response, state.inventory)
            pokaz_narracje(result.text)
            message_history.append({"role": "assistant", "content": result.text})
            add_usage(usage, result)
    else:
        chce = console.input("\n[dim]Przypomniec historie? (ENTER = tak | n = nie)[/] ").strip().lower()

        if chce != "n":
            summary = summarize_history(message_history)
            pokaz_narracje(summary.text, "[orange1]Archiwista[/]")
            add_usage(usage, summary)
        
        pokaz_narracje(message_history[-1]["content"])     # ← ZAWSZE (darmowe)

    while True:
        user = console.input("\n[bold cyan]     > [/]").strip().lower()
        cmd = user.lower()

        if not user:
            continue
        
        if cmd in {"/wyjdz", "/quit", "/exit"}: # do zrobienia w ui
            print("Koniec przygody.")
            break

        if cmd == "/pomoc":
            pokaz_komendy()
            continue

        if cmd in {"/historia", "/history"}:
            summary = summarize_history(message_history)
            pokaz_narracje(summary.text, "[orange1]Archiwista[/]")
            add_usage(usage, summary)
            continue
        
        if cmd in {"/ekwipunek", "/eq"}:
            pokaz_eq(state.inventory)
            continue 
            
        if cmd in {"/stan", "/hp"}: 
            pokaz_stan_hp(state)
            continue

        if cmd in {"/cost", "/koszt"}:
            pokaz_koszt(usage)
            continue

        if cmd in {"/zapisz", "$zapisz"}:
            cmd_zapisz(state, usage, message_history, ITEM_CATALOG)
            continue

        if cmd == "$kill":
            state.hp = 0
            print(f"\n$ wykonano {cmd} | hp = {state.hp}")
            continue

        if cmd.startswith("$sethp"):
            parts = cmd.split()
            if len(parts) != 2:
                print("$ uzycie: $sethp <liczba>")
                continue
            try:
                nowe_hp = int(parts[1])
            except ValueError:
                print(f" '{parts[1]}' to nie liczba")
                continue
            state.hp = nowe_hp
            print(f"$ wykonano: hp = {state.hp}")
            continue

        if cmd.startswith("$spawn"):
            parts = cmd.split()
            if len(parts) != 2:
                print("$ uzycie: $spawn <nazwa_itema>")
                continue
            item = create_item(parts[1])
            state.inventory.append(item)
            print(f"$ wykonano: dodano {item.name}")
            continue

        if cmd in {"$state", "$debug", "$$"}:
            modify_state(state)
            continue
            
        if cmd.startswith("/"):
            pokaz_komendy()
            continue
        if cmd.startswith("$"):
            print(f"$ komenda: {user} nie istnieje")
            continue
        if state.hp <= 0:
            pokaz_smierc()
            continue


        message_history.append({"role": "user", "content": user})

        response = ask_narrator(message_history, state.inventory)
        result = handle_response(response, state.inventory)

        

        pokaz_narracje(result.text)

        message_history.append({"role": "assistant", "content": result.text})

        add_usage(usage, result)

        for nazwa in set(result.nowe_nieznane):
            item = generuj_statystyki(nazwa, usage)
            ITEM_CATALOG[nazwa] = item
        
        
        for item in state.inventory[:]:
            if item.type == ItemType.NIEZNANY and item.name in ITEM_CATALOG:
                state.inventory.remove(item)
                state.inventory.append(ITEM_CATALOG[item.name])


        if result.combat_with:
            enemy = create_enemy(result.combat_with)
            wygrana = prowadz_walke(state, enemy)

            # Instrukcja finału: TYMCZASOWA (usuwana), z pełnym kontekstem + przypomnieniem roli
            if wygrana:
                instrukcja = (
                    f"[INSTRUKCJA SYSTEMOWA, nie gracz]: Walka rozstrzygnięta. "
                    f"Gracz pokonał przeciwnika ({enemy.name}), odnosząc rany — ma teraz {state.hp} HP. "
                    f"Opisz zakończenie walki i chwilę po niej jako narrator: w drugiej osobie, "
                    f"wplatając wynik w fikcję (przeciwnik pada), BEZ wspominania liczb, HP, systemu czy mechaniki. "
                    f"Zakończ wezwaniem do dalszego działania."
                    f"ZAWSZE odpowiedz tekstem, nawet jeśli uważasz, że nie ma co dodać "
                    f"Opisz JEDNYM-DWOMA zdaniami fizyczny obraz martwego przeciwnika i stan gracza. "
                    f"Potem WEZWANIE do dalszego dzialania (pytanie)."
                )
            else:
                instrukcja = (
                    f"[INSTRUKCJA SYSTEMOWA, nie gracz]: Gracz przegrał walkę z {enemy.name} i ginie. "
                    f"Opisz jego śmierć jako narrator: w drugiej osobie, mrocznie i krótko, "
                    f"wplatając ją w fikcję, BEZ wspominania liczb, HP, systemu czy mechaniki."
                    f"ZAWSZE odpowiedz tekstem, nawet jeśli uważasz, że nie ma co dodać"
                )

            message_history.append({"role": "user", "content": instrukcja})
            response = ask_narrator(message_history, state.inventory, tool_choice={"type": "none"})
            result = handle_response(response, state.inventory)
            add_usage(usage, result)

            if not result.text:
                response = ask_narrator(message_history, state.inventory, tool_choice={"type": "none"})
                result = handle_response(response, state.inventory)
                add_usage(usage, result)


            if result.text:
                pokaz_narracje(result.text)
            else:
                tekst = f"{enemy.name.capitalize()} pada." if wygrana else "Ciemność cię pochłania."
                pokaz_narracje(tekst)

            message_history.pop()  # USUŃ instrukcję — nie zostaje w historii (nie truje)
            message_history.append({"role": "assistant", "content": result.text})

if __name__ == "__main__":
    main()