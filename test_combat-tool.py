from anthropic import Anthropic
from dotenv import load_dotenv

from combat import COMBAT_TOOL

load_dotenv()
client = Anthropic()

MODEL = "claude-sonnet-4-6"

# Krótki system prompt TESTOWY — mówi narratorowi o walce
TEST_SYSTEM = (
    "Jesteś narratorem mrocznej gry. Gdy zaczyna się walka (wróg atakuje "
    "lub gracz atakuje wroga), wywołaj narzędzie rozpocznij_walke z nazwą przeciwnika."
)

response = client.messages.create(
    model=MODEL,
    max_tokens=1024,
    system=TEST_SYSTEM,
    tools=[COMBAT_TOOL],
    messages=[{"role": "user", "content": "Atakuję goblina stojącego przede mną."}],
)

print(f"stop_reason: {response.stop_reason}")
for block in response.content:
    print("---")
    print(f"type: {block.type}")
    if block.type == "text":
        print(f"text: {block.text}")
    elif block.type == "tool_use":
        print(f"name: {block.name}")
        print(f"input: {block.input}")