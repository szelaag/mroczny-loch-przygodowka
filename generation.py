from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv
from cost import add_usage
from items import ITEM_CATALOG
from combat import ENEMY_CATALOG
from prompts import GENERATOR_PROMPT
from models import Attack, Item, ItemType, Usage, Response

from config import MODEL, MAX_TOKENS
load_dotenv()
client = Anthropic(max_retries=3)


STATS_TOOL = {
    "name": "generuj_nieznane",
    "description": f"wygeneruj wartosci przedmiotu na podstawie jego nazwy oraz podanego obecnego katalogu znanych przedmiotow w celu zrozumienia SKALI i UTRZYMANIU BALANSU",
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
                "description": "attacks JEDYNIE dla BRONI, wszystko inne pusta lista, przykladowe rozklady atakow w katalogu, dla zwyklych broni 2-3 ataki.",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "nazwa ataku"
                        },
                        "damage_min": {
                            "type": "integer",
                            "description": "minimalne obrazenie, a do randinta",
                        },
                        "damage_max": {
                            "type": "integer",
                            "description": "maksymalne obrazenia - wieksze niz minimalne. b do randinta"
                        },
                        "miss_chance": {
                            "type": "number",
                            "description": "dla mocniejszych atakow w celu zbalansowania float od 0.0 do 1.0 szansa na nietrafienie - tradeoff dla mocniejszych atakow"
                        }
                    },
                    "required": ["name", "damage_min", "damage_max", "miss_chance"]
                }
            }
        },
        "required": ["typ", "wartosc", "attacks"]
    }
}


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


def ask_for_item_stats(item_name: str) -> Message:
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=GENERATOR_PROMPT + catalog_to_examples(ITEM_CATALOG),
        tools=[STATS_TOOL],
        tool_choice={"type": "tool", "name": "generuj_nieznane"},
        messages=[{"role": "user", "content": f"Wygeneruj statystyki dla: {item_name}"}],
    )
    return response


def generuj_statystyki(nazwa: str, usage: Usage) -> Item:
    message = ask_for_item_stats(nazwa)
    block = message.content[0]
    stats = block.input
    
    typ = ItemType(stats["typ"])
    wartosc = int(stats["wartosc"])
    ataki = []
    if stats["attacks"]:
        for atak in stats["attacks"]:
            ataki.append(Attack(
                name=atak["name"],
                damage_min=atak["damage_min"],     
                damage_max=atak["damage_max"],
                miss_chance=atak["miss_chance"],
            ))

    resp = Response(
        text="",
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
        stop_reason=message.stop_reason,
    )
    add_usage(usage, resp)

    return Item(name = nazwa, type=typ, value=wartosc, attacks=ataki)



def main() -> None:
    testy = ["noz"]
    for test in testy:
        print(generuj_statystyki(test))

if __name__ == "__main__":
    main()