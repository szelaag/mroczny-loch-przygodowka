from dataclasses import dataclass

from anthropic import Anthropic, APIResponse
from dotenv import load_dotenv

from prompts import NARRATOR_PROMPT, SUMMARY_PROMPT, GENESIS_PROMPT

load_dotenv()  # wczytuje klucz z .env
client = Anthropic()  # klucz brany automatycznie ze środowiska

MODEL = "claude-sonnet-4-6"
MODEL_PRICING = {"claude-sonnet-4-6": (3, 15)}
MAX_TOKENS = 1024
USD_PLN = 3.76

INVENTORY_TOOL = {
    "name": "aktualizuj_ekwipunek",
    "description": (
        "Wywołaj ZA KAŻDYM RAZEM, gdy gracz podnosi, zdobywa, traci, "
        "używa lub gubi przedmiot. Podaj listę przedmiotów dodanych i usuniętych."
        "Nazywaj PROSTO: nie 'zardzewialy miecz z lochow' tylko miecz BEZ POLSKICH ZNAKOW "
        "Wywołuj TYLKO gdy gracz AKTYWNIE zdobywa/traci przedmiot przez swoją akcję. NIE wywołuj dla przedmiotów, które jedynie istnieją w scenie, ale których gracz nie wziął."
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

@dataclass
class Item:
    name: str
    type: str
    value: int

ITEM_CATALOG: dict[str, Item] = {
    "klucz": Item(name="klucz", type="klucz", value=0),
    "miecz": Item(name="miecz", type="bron", value=50),
    "pochodnia": Item(name="pochodnia", type="narzedzie", value=10),
    "bandaz": Item(name="bandaz", type="uzywalne", value=25)
}

def create_item(name: str) -> Item:
    name = name.lower()
    if name in ITEM_CATALOG:
        return ITEM_CATALOG[name]
    return Item(name=name, type="nieznany", value=0)
    # create_item zwraca współdzielony obiekt z katalogu — kopia gdy Item stanie się mutowalny




def ask_with_tool(message: str) -> object:
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        tools=[INVENTORY_TOOL],
        system=NARRATOR_PROMPT,
        messages=[{"role": "user", "content": message}]
    )
    return response


def handle_response(response: object, inventory: list[Item]):
    for block in response.content:
        if block.type == "text":
            print(f"Narracja : {block.text}")
        elif block.type == "tool_use" and block.name == "aktualizuj_ekwipunek":
            for item in block.input["dodane"]:
                inventory.append(create_item(item))
            for name in block.input["usuniete"]:           # name to string
                for item in inventory:                      # przejdź Item-y w inventory
                    if item.name == name:                   # znajdź pasujący po nazwie
                        inventory.remove(item)              # usuń TEN obiekt
                        break                               # usuń jeden, przestań szukać

def main() -> None:
    inventory: list[Item] = []
    response = ask_with_tool("Rozglądam się po celi czy nie ma zadnych przedmiotow.")
    # print(f"stop reason: {response.stop_reason}")
    # for block in response.content:
    #     print("---")
    #     print(f"type: {block.type}")
    #     print(f"block: {block}")
    handle_response(response, inventory)
    print(f"Ekwipunek: {inventory}")

if __name__ == "__main__":
    main()