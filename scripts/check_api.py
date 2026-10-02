from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

key_file = Path.home() / ".config" / "computer-use-automation" / ".env"
load_dotenv(key_file, override=True)

client = OpenAI(max_retries=0, timeout=30.0)

response = client.responses.create(
    model="gpt-6-luna",
    input="Reply with exactly: API connection works.",
    reasoning={"effort": "none"},
    max_output_tokens=50,
    store=False,
)

print("Model used:", response.model)
print(response.output_text)
print(response.usage)