from dataclasses import replace
import enum
import time
from models import Attack, Enemy, GameState, Item, ItemType
import random

ENEMY_CATALOG: dict[str, Enemy] = {
    "szczur": Enemy(name="szczur", hp=10, damage_min=1, damage_max=5),
    "goblin": Enemy(name="goblin", hp=25, damage_min=4, damage_max=8),
    "szkielet": Enemy(name="szkielet", hp=40, damage_min=6, damage_max=12)
}

GOLE_RECE = Attack("cios", 1, 2)
PUDLO = object()


def create_enemy(name: str) -> Enemy:
    name = name.lower()
    if name in ENEMY_CATALOG:
        return replace(ENEMY_CATALOG[name])     
    return Enemy(name=name, hp=20, damage_min=3, damage_max=6)


COMBAT_TOOL = {
    "name": "rozpocznij_walke",
    "description": (
        "Wywołaj, gdy rozpoczyna się walka — gdy wróg atakuje gracza lub gracz "
        "atakuje wroga. Podaj nazwę przeciwnika PROSTO, małą literą, bez polskich "
        "znaków (np. goblin, szczur, szkielet)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "przeciwnik": {
                "type": "string",
                "description": "Nazwa przeciwnika, z którym zaczyna się walka",
            },
        },
        "required": ["przeciwnik"],
    },
}

def wybierz_bron(state: GameState) -> list[Attack]:
    """Wybieranie broni, zwraca liste atakow wybranej broni"""
    bronie: list[Item] = []
    for item in state.inventory:
        if item.attacks:
            bronie.append(item)

    if not bronie:
        print("\nNie masz broni, walczysz golymi rekoma.")
        return [GOLE_RECE]

    print("\n=== Wybor broni ===\n")
    print("Dostepne bronie: ")
    for i, bron in enumerate(bronie):
        print(f"{i+1}. Bron: {bron.name}")

    while True:
        user = input("\n > ").strip()
        if not user.isdigit():
            print("Podaj liczbe")
            continue
        wybor = int(user)
        if 1 <= wybor <= len(bronie):
            print(f"\nWybrana bron: {bronie[wybor - 1].name}")
            return bronie[wybor - 1].attacks
        print("Numer poza zakresem")

def wybierz_akcje(akcje: list[Attack]) -> Attack:
    """Wybor akcji, zwraca Attack"""
    print("Twoja tura, wybierz atak:")

    for i, akcja in enumerate(akcje):
        print(f"{i+1}. {akcja.name} | Obrazenia: {akcja.damage_min} - {akcja.damage_max}",end="")
        if akcja.miss_chance: print(f" | Szansa na chybienie: {akcja.miss_chance}", end="")
        print()

    while True:
        user = input("\n > ").strip()
        if not user.isdigit():
            print("Podaj liczbe")
            continue
        wybor = int(user)
        if 1 <= wybor <= len(akcje):
            return akcje[wybor - 1]
        print("Numer poza zakresem")

def policz_obrazenia(akcja: Attack) -> int | object:
    """Zwraca losowe obrazenia wramach ataku"""
    if random.random() < akcja.miss_chance:
        return PUDLO
    return random.randint(akcja.damage_min, akcja.damage_max)

def prowadz_walke(state: GameState, enemy: Enemy) -> bool:
    """Odpala petle walki zwraca true - wygrana; false - przegrana"""
    print("\n=== Walka ===\n")
    print(f"Walczysz z {enemy.name} | Twoje HP: {state.hp} | HP Wroga: {enemy.hp}")

    akcje: list[Attack] = wybierz_bron(state)

    while enemy.hp > 0 and state.hp > 0:
        time.sleep(0.5)
        atak = wybierz_akcje(akcje)
        obrazenia = policz_obrazenia(atak)
        
        if obrazenia is PUDLO:
            print(f"Nie trafiles! | Wrogowi pozostalo: {enemy.hp}")
        else:
            enemy.hp -= obrazenia
            time.sleep(0.5)
            print(f"\nZadales {obrazenia} dmg | Pozostalo mu: {enemy.hp}")
        

        if enemy.hp <= 0:
            # print("Wrog padl")
            break 

        obrazenia = random.randint(enemy.damage_min, enemy.damage_max)
        state.hp -= obrazenia
        time.sleep(0.5)
        print(f"\nWrog zadal: {obrazenia} dmg | Pozostalo Ci: {state.hp}")

        if state.hp <= 0:
            # print("Przegrales")
            break
        print()
    return state.hp > 0