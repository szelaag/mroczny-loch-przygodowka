from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator, model_validator, ValidationError
from cost import add_usage
from items import ITEM_CATALOG, create_item
from combat import ENEMY_CATALOG
from prompts import GENERATOR_PROMPT
from models import Attack, Item, ItemType, Usage, Response

from config import MODEL, MAX_TOKENS
load_dotenv()
client = Anthropic(max_retries=3)

class AttackStats(BaseModel):
    name: str
    damage_min: int
    damage_max: int
    miss_chance: float

    @field_validator("miss_chance")
    @classmethod
    def miss_w_zakresie(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("miss_chance musi byc miedzy 0.0 a 1.0")
        return v
    
    @model_validator(mode="after")
    def min_mniejszy_od_max(self):
        if self.damage_min > self.damage_max:
            raise ValueError(f"damage_min {self.damage_min} > damage_max {self.damage_max}")
        return self

class ItemStats(BaseModel):
    typ: str
    wartosc: int
    attacks: list[AttackStats]

    @field_validator("wartosc")
    @classmethod
    def wartosc_nieujemna(cls, v: int) -> int:
        if v < 0:
            raise ValueError("wartosc nie moze byc ujemna")
        return v

LIMIT = 3

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


def ask_for_item_stats(messages: list[dict]) -> Message:
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=GENERATOR_PROMPT + catalog_to_examples(ITEM_CATALOG),
        tools=[STATS_TOOL],
        tool_choice={"type": "tool", "name": "generuj_nieznane"},
        messages=messages,
    )
    return response


def generuj_statystyki(nazwa: str, usage: Usage) -> Item:
    messages = [{"role": "user", "content": f"Wygeneruj statystyki dla: {nazwa}"}]

    for proba in range(LIMIT):
        message = ask_for_item_stats(messages)
        block = message.content[0]
        stats = block.input

        resp = Response(
            text="",
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            stop_reason=message.stop_reason,
        )
        add_usage(usage, resp)


        try:
            zwalidowane = ItemStats(**stats)
        except ValidationError as e:
            
            print(f"Proba {proba + 1}: walidacja nie przeszla: {e}")
            messages.append({"role": "assistant", "content": message.content})
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"Statystyki niepoprawne: {e}. Popraw i wygeneruj ponownie.",
                }],
            })
            continue   

        typ = ItemType(zwalidowane.typ)
        wartosc = zwalidowane.wartosc
        ataki = []
        if zwalidowane.attacks:
            for atak in zwalidowane.attacks:
                ataki.append(Attack(
                    name=atak.name,
                    damage_min=atak.damage_min,
                    damage_max=atak.damage_max,
                    miss_chance=atak.miss_chance,
                ))
        return Item(name=nazwa, type=typ, value=wartosc, attacks=ataki)

    print(f"Limit prob ({LIMIT}) wyczerpany, fallback dla: {nazwa}")
    return create_item(nazwa)

def main() -> None:
    usage = Usage()
    # test = ["wielki magiczny miecz", "maly noz kuchenny", "szczotka do zebow"]
    # for item in test:
    #     wygenerowany = generuj_statystyki(item, usage)
    #     print(wygenerowany)

if __name__ == "__main__":
    main()