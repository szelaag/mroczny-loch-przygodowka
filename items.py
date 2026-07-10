from models import Item, ItemType, Attack
from dataclasses import replace

INVENTORY_TOOL = {
    "name": "aktualizuj_ekwipunek",
    "description": (
        "Wywołaj ZA KAŻDYM RAZEM, gdy gracz podnosi, zdobywa, traci, "
        "używa lub gubi przedmiot. Podaj listę przedmiotów dodanych i usuniętych."
        "Nazywaj PROSTO: nie 'zardzewialy miecz z lochow' tylko miecz BEZ POLSKICH ZNAKOW "
        "Wywołuj TYLKO gdy gracz AKTYWNIE zdobywa/traci przedmiot przez swoją akcję. NIE wywołuj dla przedmiotów, które jedynie istnieją w scenie, ale których gracz nie wziął. "
        "Wywołuj gdy gracz ZDOBYWA przedmiot. NIE wywołuj gdy gracz UŻYWA przedmiotu, który już ma (otwieranie zamka kluczem to użycie, nie zdobycie)."
        "Sprawdź, czy gracz już posiada przedmiot — jeśli tak, NIE dodawaj go ponownie, nawet jeśli akcja brzmi jak podnoszenie"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "dodane": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Przedmioty, które gracz zdobył w tej turze",
            },
            "usuniete": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Przedmioty, które gracz stracił w tej turze",
            },
        },
        "required": ["dodane", "usuniete"],
    },
}


ITEM_CATALOG: dict[str, Item] = {
    "miecz": Item(
        name="miecz", type=ItemType.BRON, value=50,
        attacks=[
            Attack("light", 4, 6),
            Attack("heavy", 10, 16, miss_chance=0.4),
            Attack("stab", 7, 10),
        ],
    ),
    "sztylet": Item(          # druga broń do testów wyboru
        name="sztylet", type=ItemType.BRON, value=20,
        attacks=[
            Attack("light", 3, 5),
            Attack("stab", 6, 8),
        ],
    ),
    "klucz": Item(name="klucz", type=ItemType.KLUCZ, value=0),
    "pochodnia": Item(name="pochodnia", type=ItemType.NARZEDZIE, value=10),
    "bandaz": Item(name="bandaz", type=ItemType.ZUZYWALNY, value=25)
}

def create_item(name: str) -> Item:
    name = name.lower()
    if name in ITEM_CATALOG:
        return replace(ITEM_CATALOG[name])
    return Item(name=name, type=ItemType.NIEZNANY, value=0)  # attacks puste (default) — bez akcji

def inventory_to_text(inventory: list[Item]) -> str:
    """Zamienia ekwipunek na czytelny opis dla narratora."""
    if not inventory:
        return "Gracz nie ma żadnych przedmiotów."
    nazwy = [item.name for item in inventory]
    return "Gracz posiada: " + ", ".join(nazwy)

