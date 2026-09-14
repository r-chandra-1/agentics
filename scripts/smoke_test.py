"""Manual end-to-end call. Requires Ollama to be running."""

import asyncio
import json

from recipe_agents.api import service


async def main() -> None:
    # Two items exercise both expert agents and the batch response contract.
    result = await service.create_recipe("Give me a simple sweet latte and tomato soup.")
    print(json.dumps(result.response.model_dump(), indent=2))
    print(f"session_id={result.session_id}")
    print(f"turn_id={result.turn_id}")


if __name__ == "__main__":
    asyncio.run(main())
