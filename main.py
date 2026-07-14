from generation import generuj_statystyki
from helper import clear_system
from items import ITEM_CATALOG, create_item
from models import ItemType, Usage, GameState, Enemy
from config import USD_PLN
from api import ask_narrator, handle_response, summarize_history
from cost import add_usage
from prompts import GENESIS_PROMPT
from combat import create_enemy, prowadz_walke
from debug import modify_state
from save import cmd_zapisz, zapisz_gre
import random



def main() -> None:
    usage = Usage()
    # Genesis prompt + append do histori
    message_history: list[dict] = [{"role": "user", "content": GENESIS_PROMPT}]
    state = GameState()
    clear_system()
    print("=== Przygodowka ===")
    start = input("\nENTER aby rozpoczac ").lower().strip()

    if start == "$$":
        modify_state(state) # tryb debug

    if state.hp > 0: # hp w tym momencie moglo zostac zmienione jedynie modify state
        response = ask_narrator(message_history, state.inventory)
        result = handle_response(response, state.inventory)
        message_history.append({"role": "assistant", "content": result.text})
        
        add_usage(usage, result)


    while True:
        user = input("\n > ").strip().lower()
        cmd = user.lower()

        if not user:
            continue
        
        if cmd in {"/wyjdz", "/quit", "/exit"}:
            print("Koniec przygody.")
            break

        if cmd in {"/historia", "/history"}:
            summary = summarize_history(message_history)
            print(summary.text)
            add_usage(usage, summary)
            continue
        
        if cmd in {"/ekwipunek", "/eq"}:
            print("\n--- Ekwipunek ---")
            if not state.inventory:
                print(" Pusto")
            else:
                for i, item in enumerate(state.inventory):
                    print(f" {i+1}. {item.name} | Wartosc: {item.value}")
            continue 
            
        if cmd in {"/stan", "/hp"}:
            print("\n--- Stan ---")
            print(f" HP: {state.hp}")
            continue

        if cmd in {"/cost", "/koszt"}:
            print("\n--- Koszt rozmowy ---")
            print(f" USD: {usage.total_cost:.6f} | PLN: {usage.total_cost * USD_PLN:.6f}\n")
            print("--- Tokeny ---")
            print(
                f" Input: {usage.total_input_tokens} | Output: {usage.total_output_tokens} | Suma: {usage.total_input_tokens + usage.total_output_tokens}\n"
            )
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

        if cmd == "$cs": clear_system(); continue
            
        if cmd.startswith("/"):
            print("\n --- Lista dostepnych komend ---")
            print(" /ekwipunek | /stan | /historia | /koszt | /wyjdz ")
            continue
        if cmd.startswith("$"):
            print(f"$ komenda: {user} nie istnieje")
            continue
        if state.hp <= 0:
            print("Nie żyjesz. Możesz wyjść (/wyjdz) lub sprawdzic statystyki.")
            continue


        message_history.append({"role": "user", "content": user})

        response = ask_narrator(message_history, state.inventory)
        result = handle_response(response, state.inventory)
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
                )
            else:
                instrukcja = (
                    f"[INSTRUKCJA SYSTEMOWA, nie gracz]: Gracz przegrał walkę z {enemy.name} i ginie. "
                    f"Opisz jego śmierć jako narrator: w drugiej osobie, mrocznie i krótko, "
                    f"wplatając ją w fikcję, BEZ wspominania liczb, HP, systemu czy mechaniki."
                )

            message_history.append({"role": "user", "content": instrukcja})
            response = ask_narrator(message_history, state.inventory)
            result = handle_response(response, state.inventory)
            message_history.pop()  # USUŃ instrukcję — nie zostaje w historii (nie truje)
            message_history.append({"role": "assistant", "content": result.text})
            add_usage(usage, result)

if __name__ == "__main__":
    main()