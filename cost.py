from config import MODEL, MODEL_PRICING
from models import Usage, Response


def calculate_cost(input_tokens: int, output_tokens: int, model: str = MODEL) -> float:
    input_cost, output_cost = MODEL_PRICING[model]
    return (
        input_tokens / 1_000_000 * input_cost + output_tokens / 1_000_000 * output_cost
    )


def add_usage(usage: Usage, response: Response, model: str = MODEL) -> None:
    usage.total_input_tokens += response.input_tokens
    usage.total_output_tokens += response.output_tokens
    usage.total_cost += calculate_cost(
        response.input_tokens, response.output_tokens, model
    )
