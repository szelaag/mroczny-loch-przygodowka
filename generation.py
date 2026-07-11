from items import ITEM_CATALOG, Item, ItemType
from combat import ENEMY_CATALOG


STATS_TOOL = {
    "name": "generuj_nieznane",
    "description": f"wygeneruj wartosci przedmiotu na podstawie jego nazwy oraz podanego obecnego katalogu znanych przedmiotow w celu zrozumienia SKALI i UTRZYMANIU BALANSU: katalog",
    "input_schema": {
        "type": "object",
        "properties": {
            "typ": {
                "type": "string",
                "enum": ["bron", "klucz", "narzedzie", "zuzywalny"],
                "description": """na podstawie nazwy dobierasz odpowiednio, bron dla czegos czym da sie walczyc. klucz = klucz, narzedzie -> cos co jest przedmiotem ani nie zuzywalnym ani NIE KLUCZEM ani nie bronia, uzywane dla np pochodnia"""
            },
            "wartosc": {
                "type": "integer",
                "description": "wartosc przedmiotu uzywana do handlu z kupcami. na podstawie wartosci katalogowych"
            },
            "attacks": {
                "type": "array",
                "description": "attacks JEDYNIE dla BRONI, wszystko inne pusta lista, przykladowe rozklady atakow w katalogu, dla zwyklych broni 2-3 ataki. dla lepszych ciekawszych, czyli dla np: magiczny miecz; nie poprostu miecz",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "nazwa ataku"
                        },
                        "dmg_min": {
                            "type": "integer",
                            "description": "minimalne obrazenie, a do randinta",
                        },
                        "dmg_max": {
                            "type": "integer",
                            "description": "maksymalne obrazenia - wieksze niz minimalne. b do randinta"
                        },
                        "miss_chance": {
                            "type": "number",
                            "description": "dla mocniejszych atakow w celu zbalansowania float od 0.0 do 1.0 szansa na nietrafienie - tradeoff dla mocniejszych atakow"
                        }
                    },
                    "required": ["name", "dmg_min", "dmg_max", "miss_chance"]
                }
            }
        },
        "required": ["typ", "wartosc", "attacks"]
    }
}

# ITEM_CATALOG: dict[str, Item] = {
#     "miecz": Item(
#         name="miecz", type=ItemType.BRON, value=50,
#         attacks=[
#             Attack("light", 4, 6),
#             Attack("heavy", 10, 16, miss_chance=0.4),
#             Attack("stab", 7, 10),
#         ],
#     ),
#     "sztylet": Item(          # druga broń do testów wyboru
#         name="sztylet", type=ItemType.BRON, value=20,
#         attacks=[
#             Attack("light", 3, 5),
#             Attack("stab", 6, 8),
#         ],
#     ),
#     "klucz": Item(name="klucz", type=ItemType.KLUCZ, value=0),
#     "pochodnia": Item(name="pochodnia", type=ItemType.NARZEDZIE, value=10),
#     "bandaz": Item(name="bandaz", type=ItemType.ZUZYWALNY, value=25)
# }

def catalog_to_examples(catalog: dict) -> str:
    """Zamienia katalog na czytelne przykłady dla generatora (skala/balans)."""
    linie = []
    for item in catalog.values():
        linia = f"{item.name} | typ: {item.type.value} | wartosc: {item.value}"
        if item.attacks:
            czesci = []
            for attack in item.attacks:
                tekst = f"{attack.name} ({attack.damage_min}-{attack.damage_max}"
                if attack.miss_chance > 0.0:
                    tekst += f", miss {attack.miss_chance}"
                tekst += ")"
                czesci.append(tekst)
            linia += " | akcje: " + ", ".join(czesci)
        else:
            linia += " | akcje: brak"
        linie.append(linia)
    return "\n".join(linie)

def generuj_statystyki():
    pass

def main() -> None:
    catalog_to_examples(ITEM_CATALOG)

if __name__ == "__main__":
    main()