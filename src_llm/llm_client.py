from __future__ import annotations

import os
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "No se ha encontrado OPENAI_API_KEY. "
            "Añádela en el archivo .env o en las variables de entorno."
        )
    return OpenAI(api_key=api_key)


def simple_test(prompt: str) -> str:
    client = get_client()

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=prompt
    )

    return response.output_text