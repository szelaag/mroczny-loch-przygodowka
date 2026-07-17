from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv

from config import MODEL, MAX_TOKENS
from models import ItemType, Response, Item
from prompts import GENERATOR_PROMPT, NARRATOR_PROMPT, SUMMARY_PROMPT
from items import INVENTORY_TOOL, ITEM_CATALOG, create_item, inventory_to_text
from combat import COMBAT_TOOL
from generation import STATS_TOOL, catalog_to_examples

load_dotenv()
client = Anthropic(max_retries=3)


def ask_narrator(
    message_history: list[dict],
    inventory: list[Item],
    tool_choice: dict | None = None,
) -> Message:
    kwargs = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": NARRATOR_PROMPT + "\n\n" + inventory_to_text(inventory),
        "tools": [INVENTORY_TOOL, COMBAT_TOOL],
        "messages": message_history,
    }
    if tool_choice:
        kwargs["tool_choice"] = tool_choice
    return client.messages.create(**kwargs)


def handle_response(response: Message, inventory: list[Item]) -> Response:
    narracja = ""
    combat_with = None 
    nowe_nieznane = []
    for block in response.content:
        if block.type == "text":
            narracja = block.text
        elif block.type == "tool_use" and block.name == "aktualizuj_ekwipunek":
            for item in block.input["dodane"]:
                nazwa = item.lower()
                if any(i.name == nazwa for i in inventory):    # ← KOD sprawdza # rozwiazanie tymczasowe pozbycia sie duplikatow
                    continue                                    # już ma, pomijamy
                nowy = create_item(nazwa)
                inventory.append(nowy)
                if nowy.type == ItemType.NIEZNANY:
                    nowe_nieznane.append(nowy.name)
            for name in block.input["usuniete"]:
                for item in inventory:
                    if item.name == name:
                        inventory.remove(item)
                        break
        elif block.type == "tool_use" and block.name == "rozpocznij_walke":
            combat_with = block.input["przeciwnik"]
    return Response(
        text=narracja,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        stop_reason=response.stop_reason,
        combat_with=combat_with,
        nowe_nieznane=nowe_nieznane
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


# w api.py, tymczasowo w __main__
msg = ask_narrator(
    [{"role": "user", "content": "[INSTRUKCJA] Opisz koniec walki."}],
    [],
    tool_choice={"type": "none"},
)
print([b.type for b in msg.content])     # ma być ['text'], nigdy 'tool_use'