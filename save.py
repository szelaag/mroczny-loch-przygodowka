from ast import Tuple
from dataclasses import asdict
import json
from queue import Empty
from items import create_item, ITEM_CATALOG
from prompts import GENESIS_PROMPT
import os
from datetime import datetime


from models import Attack, GameState, Item, ItemType, Usage

WERSJA_SAVE = 1

def attack_to_dict(attack: Attack) -> dict:
    """Zamienia Attack na dict"""
    return asdict(attack)

def item_to_dict(item: Item) -> dict:
    """Zamienia Item na dict"""
    return {
        "name": item.name,
        "type": item.type.value,
        "value":item.value,
        "attacks": [attack_to_dict(atak) for atak in item.attacks]
    }

def state_to_dict(state: GameState) -> dict:
    """Zamienia GameState na dict"""
    return {
        "hp": state.hp,
        "inventory": [item_to_dict(item) for item in state.inventory]
    }

def usage_to_dict(usage: Usage) -> dict:
    """Zamienia Usage na dict"""
    return asdict(usage)

def item_catalog_to_dict(catalog: dict[str, Item]) -> dict:
    """Zamienia ITEM_CATALOG na serializowalny dict"""
    return {klucz: item_to_dict(item) for klucz, item in catalog.items()}


def zbuduj_save(state: GameState, usage: Usage, message_history: list[dict], item_catalog: dict[str, Item]) -> dict:
    return {
        "wersja": WERSJA_SAVE,
        "state": state_to_dict(state),
        "usage": usage_to_dict(usage),
        "message_history": message_history,
        "item_catalog": item_catalog_to_dict(item_catalog),
    }

def zapisz_gre(state: GameState, usage: Usage, message_history: list[dict], item_catalog: dict[str, Item], nazwa_save: str = "save01") -> None:
    dane = zbuduj_save(state, usage, message_history, item_catalog)
    os.makedirs("saves", exist_ok=True)
    with open(f"saves/{nazwa_save}.json", "w", encoding="utf-8") as f:
        json.dump(dane, f, ensure_ascii=False, indent=2) 

def dict_to_attack(dane: dict) -> Attack:
    """Odtwarza Attack z dict"""
    return Attack(
        name=dane["name"],
        damage_min=dane["damage_min"],
        damage_max=dane["damage_max"],
        miss_chance=dane["miss_chance"]
    )

def dict_to_item(dane: dict) -> Item:
    """Odtwarza Item z dict"""
    return Item(
        name=dane["name"],
        type=ItemType(dane["type"]),
        value=dane["value"],
        attacks=[dict_to_attack(atak) for atak in dane["attacks"]] 
    )

def dict_to_usage(dane: dict) -> Usage:
    """Odtwarza Usage z dict"""
    return Usage(
        total_cost=dane["total_cost"],
        total_input_tokens=dane["total_input_tokens"],
        total_output_tokens=dane["total_output_tokens"]
    )

def dict_to_state(dane: dict) -> GameState:
    """Odtwarza GameState z dict"""
    return GameState(
        hp=dane["hp"],
        inventory=[dict_to_item(item) for item in dane["inventory"]]
    )

def dict_to_item_catalog(dane: dict) -> dict:
    """Odtwarza ITEM_CATALOG z dicta"""
    return {klucz: dict_to_item(item) for klucz, item in dane.items()}

def wczytaj_gre(nazwa_save: str) -> tuple[GameState, Usage, list[dict], dict[str, Item]]:
    """Wczytuje stan gry z pliku JSON."""
    with open(f"saves/{nazwa_save}.json", "r", encoding="utf-8") as f:
        dane = json.load(f)
    if dane.get("wersja") != WERSJA_SAVE:
        print(f"Uwaga: save w wersji {dane.get('wersja')}, kod oczekuje {WERSJA_SAVE}")
    return (
        dict_to_state(dane["state"]),
        dict_to_usage(dane["usage"]),
        dane["message_history"],
        dict_to_item_catalog(dane["item_catalog"])
    )


def lista_saveow() -> list[str]:
    """Zwraca nazwy dostępnych save'ów (bez rozszerzenia)."""
    if not os.path.exists("saves"):
        return []
    pliki = os.listdir("saves")
    zwalidowane = []
    for plik in pliki:
        if plik.endswith(".json"):
            zwalidowane.append(os.path.splitext(plik)[0])
    return zwalidowane
    

def cmd_zapisz(
    state: GameState,
    usage: Usage,
    message_history: list[dict],
    item_catalog: dict[str, Item],
) -> None:
    """Pyta o nazwę, waliduje, zapisuje save."""
    stempel = datetime.now().strftime("%Y%m%d_%H%M")
    sugerowana = f"save{stempel}"

    zapytana = input("Wybierz nazwe save ($$ aby anulowac zapis | ENTER dla domyslnej): ").strip().lower()

    if zapytana == "$$":
        print("Anulowano zapis")
        return
    
    nazwa_save = zapytana or sugerowana

    if any(zn in nazwa_save for zn in "/\\."):
        print("Niedozwolona nazwa")
        return
    

    if nazwa_save in lista_saveow():
        potwierdzenie = input(f"Zapis o nazwie: {nazwa_save} czy nadpisac? (tak | ENTER aby anulowac)")
        if potwierdzenie != "tak":
            print("Anulowano zapis")
            return

    zapisz_gre(state, usage, message_history, item_catalog, nazwa_save)
    print(f"Zapisano stan gry pod nazwa: {nazwa_save}")

def wybierz_save(savy: list[str]) -> str:
    """Pyta o numer save'a z listy. Zwraca nazwę."""
    print("\n=== Dostepne save'y ===")
    for i, nazwa in enumerate(savy):
        print(f"{i+1}. {nazwa}")

    while True:
        user = input("\n > ").strip()
        if not user.isdigit():
            print("Podaj liczbe")
            continue
        wybor = int(user)
        if 1 <= wybor <= len(savy):
            return savy[wybor - 1]
        print("Numer poza zakresem")

def ekran_startowy() -> tuple[GameState, Usage, list[dict], bool]:
    savy = lista_saveow()
    print("\n1. NOWA GRA")
    if savy:                          # pusta lista jest fałszywa — nie potrzeba `!= []`
        print("2. WCZYTAJ GRE")

    while True:
        user = input("\nWybierz: ").strip()
        if user == "1":
            state = GameState()
            usage = Usage()
            message_history = [{"role": "user", "content": GENESIS_PROMPT}]
            nowa_gra = True
            break
        if user == "2" and savy:      # "2" ma sens TYLKO gdy są save'y
            nazwa = wybierz_save(savy)
            state, usage, message_history, katalog = wczytaj_gre(nazwa)
            ITEM_CATALOG.clear()
            ITEM_CATALOG.update(katalog)
            nowa_gra = False
            break
        print("Nieprawidlowy wybor")
    return (
        state,
        usage,
        message_history,
        nowa_gra
    )



def main() -> None:
    # state = GameState(hp=73, inventory=[create_item("miecz"), create_item("klucz")])
    # usage = Usage(total_cost=0.02, total_input_tokens=1500, total_output_tokens=300)
    # history = [{"role": "user", "content": "Rozpocznij przygode"}]

    # zapisz_gre(state, usage, history, ITEM_CATALOG, "test")
    # state2, usage2, history2, catalog2 = wczytaj_gre("test")

    # print(state == state2)          # ma być True
    # print(usage == usage2)          # ma być True
    # print(history == history2)      # ma być True
    # print(ITEM_CATALOG == catalog2) # ma być True
    ekran_startowy()

if __name__ == "__main__":
    main()