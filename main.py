from dataclasses import dataclass

from anthropic import Anthropic
from dotenv import load_dotenv

from prompts import SYSTEM_PROMPT, SUMMARY_PROMPT, GENESIS_PROMPT

load_dotenv()  # wczytuje klucz z .env
client = Anthropic()  # klucz brany automatycznie ze środowiska

MODEL = "claude-sonnet-4-6"
MODEL_PRICING = {"claude-sonnet-4-6": (3, 15)}
MAX_TOKENS = 1024
USD_PLN = 3.76


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

def ask_streaming(message_history: list[dict], system: str = SYSTEM_PROMPT) -> Response:
    full_response_parts = []
    print("Narrator: ", end="")
    with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=message_history,
    ) as stream:
        for text in stream.text_stream:
            print(text, flush=True, end="")
            full_response_parts.append(text)
        final = stream.get_final_message()
    print()
    return Response(
        text="".join(full_response_parts),
        input_tokens=final.usage.input_tokens,
        output_tokens=final.usage.output_tokens,
        stop_reason=final.stop_reason,
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
    response = ask_streaming(message_history)
    message_history.append({"role": "assistant", "content": response.text})

    add_usage(usage, response)

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
        if user.lower() in {"/cost", "/koszt"}:
            print("\n--- Koszt rozmowy ---")
            print(f" USD: {usage.total_cost:.6f} | PLN: {usage.total_cost * USD_PLN:.6f}\n")
            print("--- Tokeny ---")
            print(
                f" Input: {usage.total_input_tokens} | Output: {usage.total_output_tokens} | Suma: {usage.total_input_tokens + usage.total_output_tokens}\n"
            )
            continue

        message_history.append({"role": "user", "content": user})

        response = ask_streaming(message_history)
        message_history.append({"role": "assistant", "content": response.text})

        add_usage(usage, response)


if __name__ == "__main__":
    main()
