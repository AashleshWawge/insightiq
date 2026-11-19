import time
from typing import Optional, Dict, Any
from groq import Groq, GroqError, AuthenticationError, RateLimitError, APIConnectionError

from app.config import GROQ_API_KEY, GROQ_MODEL

# Singleton Groq client instance
_groq_client: Optional[Groq] = None


def get_groq_client() -> Groq:
    """
    Initializes and returns a reusable Groq API client instance.
    Raises ValueError if the GROQ_API_KEY environment variable is not configured.
    """
    global _groq_client
    if _groq_client is None:
        if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
            raise ValueError("GROQ_API_KEY is not configured in backend/.env.")
        _groq_client = Groq(api_key=GROQ_API_KEY, timeout=15.0)
    return _groq_client


def generate_text(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 500,
) -> Dict[str, Any]:
    """
    Calls the Groq chat completions API with the given prompt and system instructions.
    Returns a dictionary containing:
    - text: The model's generated text
    - model: The model ID used
    - latency_ms: Round-trip API latency in milliseconds
    """
    client = get_groq_client()
    target_model = model or GROQ_MODEL

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    start_time = time.perf_counter()
    try:
        completion = client.chat.completions.create(
            model=target_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response_text = completion.choices[0].message.content or ""

        return {
            "text": response_text.strip(),
            "model": target_model,
            "latency_ms": latency_ms,
        }
    except AuthenticationError:
        raise ValueError("Invalid Groq API key. Please check your GROQ_API_KEY in .env.")
    except RateLimitError:
        raise RuntimeError("Groq API rate limit reached. Please wait a moment before trying again.")
    except APIConnectionError:
        raise RuntimeError("Could not connect to the Groq API server. Please check your network connection.")
    except GroqError as e:
        raise RuntimeError(f"Groq API error: {str(e)}")
