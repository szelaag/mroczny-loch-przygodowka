from dataclasses import replace
import time
from models import Attack, Enemy, GameState, Item
import random
from ui import panel_tury, pokaz_bronie, pokaz_komunikat, pusty_print, pokaz_wynik, pokaz_gole_rece, input_walki


ENEMY_CATALOG: dict[str, Enemy] = {
    "szczur": Enemy(name="szczur", hp=30, hp_max=30, damage_min=1, damage_max=5),
    "goblin": Enemy(name="goblin", hp=35, hp_max=35, damage_min=4, damage_max=8),
    "szkielet": Enemy(name="szkielet", hp=45, hp_max=45, damage_min=6, damage_max=12)
}

GOLE_RECE = Attack("cios", 1, 2)
PUDLO = object()


def create_enemy(name: str) -> Enemy:
    name = name.lower()
    if name in ENEMY_CATALOG:
        return replace(ENEMY_CATALOG[name])     
    return Enemy(name=name, hp=30, hp_max=30, damage_min=3, damage_max=6)


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
        pokaz_gole_rece()
        time.sleep(0.3)
        return [GOLE_RECE]

    pokaz_bronie(bronie)

    while True:
        user = input_walki()
        if not user.isdigit():
            pokaz_komunikat("Podaj poprawna liczbe")
            continue
        wybor = int(user)
        if 1 <= wybor <= len(bronie):
            pokaz_komunikat(f"Wybrana bron: [bold cyan]{bronie[wybor - 1].name}[/]")
            return bronie[wybor - 1].attacks
        pokaz_komunikat("Numer poza zakresem")


def wybierz_akcje(akcje: list[Attack]) -> Attack:
    """Pyta o numer akcji. NIE wyswietla tabeli — robi to panel_tury."""
    while True:
        user = input_walki()
        if not user.isdigit():
            pokaz_komunikat("Podaj poprawna liczbe")
            continue
        wybor = int(user)
        if 1 <= wybor <= len(akcje):
            return akcje[wybor - 1]
        pokaz_komunikat("Numer poza zakresem")


def policz_obrazenia(akcja: Attack) -> int | object:
    """Zwraca losowe obrazenia wramach ataku"""
    if random.random() < akcja.miss_chance:
        return PUDLO
    return random.randint(akcja.damage_min, akcja.damage_max)


def prowadz_walke(state: GameState, enemy: Enemy) -> bool:
    """Petla walki. Zwraca True (wygrana) / False (przegrana)."""
    time.sleep(2)
    
    akcje = wybierz_bron(state)
    wynik = ""                                  # ← przeżywa iteracje

    while enemy.hp > 0 and state.hp > 0:
        time.sleep(0.5)
        pusty_print()
        pusty_print()
        panel_tury(state, enemy, akcje, wynik)  # ← wynik POPRZEDNIEJ tury
        atak = wybierz_akcje(akcje)

        # --- atak gracza ---
        obrazenia = policz_obrazenia(atak)
        if obrazenia is PUDLO:
            czesc_gracza = "[dim]Chybiles[/]"
        else:
            enemy.hp -= obrazenia
            czesc_gracza = f"Zadales [bold]{obrazenia}[/] dmg"

        # --- wrog padl? ---
        if enemy.hp <= 0:
            wynik = f"{czesc_gracza}  ·  [green]{enemy.name.capitalize()} pada[/]"
            break

        # --- kontratak ---
        kontra = random.randint(enemy.damage_min, enemy.damage_max)
        state.hp -= kontra
        wynik = f"{czesc_gracza}  ·  [red]{enemy.name.capitalize()} zadal {kontra} dmg[/]"

        if state.hp <= 0:
            break

    # --- OSTATNI wynik nie zdazyl sie wyswietlic ---
    pokaz_wynik(wynik)

    return state.hp > 0