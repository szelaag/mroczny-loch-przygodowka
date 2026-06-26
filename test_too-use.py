from dataclasses import dataclass

from anthropic import Anthropic, APIResponse
from dotenv import load_dotenv

from prompts import SYSTEM_PROMPT, SUMMARY_PROMPT, GENESIS_PROMPT

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

def ask_with_tool(message: str) -> object:
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        tools=[INVENTORY_TOOL],
        messages=[{"role": "user", "content": message}]
    )
    return response


def handle_response(response: object, inventory: list[str]):
    for block in response.content:
        if block.type == "text":
            print(f"Narracja : {block.text}")
        elif block.type == "tool_use" and block.name == "aktualizuj_ekwipunek":
            for item in block.input["dodane"]:
                inventory.append(item)
            for item in block.input["usuniete"]:
                if item in inventory:       # swiadomie nie komplikuje ale powiedz mi czy tutaj najbardizej profesjonalnym rozwiazaniem nie przy wersji uproszczonej nie byloby zrobienie try except i zwracac modelowi ze nie ma takiego przedmiotu?
                    inventory.remove(item)

def main() -> None:
    inventory: list[str] = []
    response = ask_with_tool("Rozglądam się i podnoszę zardzewiały klucz ze stołu. I odkladam go znowu na stol")
    # print(f"stop reason: {response.stop_reason}")
    # for block in response.content:
    #     print("---")
    #     print(f"type: {block.type}")
    #     print(f"block: {block}")
    handle_response(response, inventory)
    print(f"Ekwipunek: {inventory}")

if __name__ == "__main__":
    main()