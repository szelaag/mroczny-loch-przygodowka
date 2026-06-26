from dataclasses import dataclass

from anthropic import Anthropic
from anthropic.types import Message
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

@dataclass
class Response:
    text: str
    input_tokens: int
    output_tokens: int
    stop_reason: str

@dataclass
class Usage:
    total_cost: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0



def create_item(name: str) -> Item:
    name = name.lower()
    # create_item zwraca współdzielony obiekt z katalogu — kopia gdy Item stanie się mutowalny
    if name in ITEM_CATALOG:
        return ITEM_CATALOG[name]
    return Item(name=name, type="nieznany", value=0)

def ask_narrator(message_history: list[dict]) -> Message:
    """Woła narratora z narzędziem ekwipunku. Zwraca surową odpowiedź API."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        tools=[INVENTORY_TOOL],
        messages=message_history,
    )
    return response

def handle_response(response: Message, inventory: list[Item]) -> Response: 
    narracja = "" 
    for block in response.content:
        if block.type == "text":
            print(f"Narrator: {block.text}")
            narracja = block.text
        elif block.type == "tool_use" and block.name == "aktualizuj_ekwipunek":
            for item in block.input["dodane"]:
                inventory.append(create_item(item))
            for name in block.input["usuniete"]:
                for item in inventory:
                    if item.name == name:
                        inventory.remove(item)
                        break 
    return Response(
        text=narracja,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        stop_reason=response.stop_reason
    )


def history_to_text(message_history: list[dict]) -> str:
    ROLE_NAMES = {"user": "gracz", "assistant": "narrator"}
    full_history = []
    for msg in message_history[1:]:
        full_history.append(f"{ROLE_NAMES[msg['role']]}: {msg['content']}\n")
    return "".join(full_history)


def summarize_history(message_history: list[dict]) -> Response:
    zapis = history_to_text(message_history)
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SUMMARY_PROMPT,
        messages=[
            {"role": "user", "content": f"Oto zapis przygody: \n {zapis} \n Stresc go."}
        ],
    )
    return Response(
        text=response.content[0].text,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        stop_reason=response.stop_reason,
    )


def calculate_cost(input_tokens: int, output_tokens: int, model: str = MODEL) -> float:
    input_cost, output_cost = MODEL_PRICING[model]
    return (
        input_tokens / 1_000_000 * input_cost + output_tokens / 1_000_000 * output_cost
    )


def add_usage(usage: Usage, response: Response, model: str = MODEL) -> None:
    usage.total_input_tokens += response.input_tokens
    usage.total_output_tokens += response.output_tokens
    usage.total_cost += calculate_cost(response.input_tokens, response.output_tokens, model)


def main() -> None:
    usage = Usage()

    # Genesis prompt + append do histori
    message_history: list[dict] = [{"role": "user", "content": GENESIS_PROMPT}]
    inventory: list[Item] = []
    response = ask_narrator(message_history)
    result = handle_response(response, inventory)
    message_history.append({"role": "assistant", "content": result.text})

    add_usage(usage, result)

    while True:
        user = input("\n > ").strip()

        if not user:
            continue
        if user.lower() in {"/wyjdz", "/quit", "/exit"}:
            print("Koniec przygody.")
            break
        if user.lower() in {"/historia", "/history"}:
            summary = summarize_history(message_history)
            print(summary.text)
            add_usage(usage, summary)
            continue
        if user.lower() in {"/ekwipunek", "/eq"}:
            print("\n--- Ekwipunek ---")
            if not inventory:
                print(" Pusto")
            else:
                for i, item in enumerate(inventory):
                    print(f" {i+1}. {item.name} | Wartosc: {item.value}")
            continue
        if user.lower() in {"/cost", "/koszt"}:
            print("\n--- Koszt rozmowy ---")
            print(f" USD: {usage.total_cost:.6f} | PLN: {usage.total_cost * USD_PLN:.6f}\n")
            print("--- Tokeny ---")
            print(
                f" Input: {usage.total_input_tokens} | Output: {usage.total_output_tokens} | Suma: {usage.total_input_tokens + usage.total_output_tokens}\n"
            )
            continue

        message_history.append({"role": "user", "content": user})

        response = ask_narrator(message_history)
        result = handle_response(response, inventory)
        message_history.append({"role": "assistant", "content": result.text})

        add_usage(usage, result)


if __name__ == "__main__":
    main()
