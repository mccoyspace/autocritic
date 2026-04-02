"""
LLM provider routing for autocritic.

Supports multiple providers via model string prefixes:
    "openai:gpt-4o"                        → OpenAI
    "anthropic:claude-sonnet-4-20250514"          → Anthropic (also the default for bare names)
    "google:gemini-2.5-pro"                → Google Gemini
    "xai:grok-3"                           → xAI (OpenAI-compatible)
    "ollama:llama3"                        → local Ollama (OpenAI-compatible)
    "openrouter:meta-llama/llama-3-70b"    → OpenRouter (OpenAI-compatible)
    "mlx:mlx-community/Meta-Llama-3-8B"   → local MLX via mlx_lm.server
    "llamacpp:model"                       → local llama.cpp server
    "local:my-model"                       → any local OpenAI-compatible server

Required env vars per provider:
- Anthropic:   ANTHROPIC_API_KEY
- OpenAI:      OPENAI_API_KEY
- Google:      GOOGLE_API_KEY
- xAI:         XAI_API_KEY
- Ollama:      (none — localhost:11434)
- OpenRouter:  OPENROUTER_API_KEY
- mlx:         (none — localhost:8080)
- llamacpp:    (none — localhost:8080)
- local:       LOCAL_LLM_URL (default http://localhost:8080/v1)
               LOCAL_LLM_API_KEY (optional, default "none")
"""

from __future__ import annotations

import base64
import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Provider configs
# ---------------------------------------------------------------------------

# prefix → (base_url, api_key_env)
_OPENAI_COMPAT_PROVIDERS: dict[str, tuple[str | None, str | None]] = {
    "openai":      (None, "OPENAI_API_KEY"),
    "xai":         ("https://api.x.ai/v1", "XAI_API_KEY"),
    "ollama":      ("http://localhost:11434/v1", None),
    "openrouter":  ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "mlx":         ("http://localhost:8080/v1", None),
    "llamacpp":    ("http://localhost:8080/v1", None),
}


def _parse_provider(model: str) -> tuple[str, str]:
    """Split 'provider:model_name' → (provider, model_name).

    Bare model strings (no colon) default to 'anthropic'.
    """
    if ":" in model:
        provider, _, model_name = model.partition(":")
        return provider.lower(), model_name
    return "anthropic", model


# ---------------------------------------------------------------------------
# Text-only calls
# ---------------------------------------------------------------------------

def _call_anthropic(model: str, system: str, user: str,
                    max_tokens: int, temperature: float) -> str:
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "anthropic package required for Anthropic models. "
            "Install with: pip install 'autocritic[anthropic]'"
        )
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def _call_openai_compat(model: str, system: str, user: str,
                        max_tokens: int, temperature: float,
                        base_url: str | None, api_key_env: str | None,
                        api_key_override: str | None = None) -> str:
    try:
        import openai
    except ImportError:
        raise ImportError(
            "openai package required for OpenAI-compatible models. "
            "Install with: pip install 'autocritic[openai]'"
        )
    if api_key_override is not None:
        api_key = api_key_override
    elif api_key_env:
        api_key = os.environ.get(api_key_env)
    else:
        api_key = "ollama"
    client = openai.OpenAI(base_url=base_url, api_key=api_key)
    token_kwarg = (
        {"max_completion_tokens": max_tokens}
        if base_url is None
        else {"max_tokens": max_tokens}
    )
    response = client.chat.completions.create(
        model=model,
        **token_kwarg,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content


def _call_google(model: str, system: str, user: str,
                 max_tokens: int, temperature: float) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError(
            "google-genai package required for Google models. "
            "Install with: pip install 'autocritic[google]'"
        )
    client = genai.Client()
    response = client.models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            temperature=temperature,
        ),
    )
    return response.text


def _call_llm(model: str, system: str, user: str,
              max_tokens: int = 2048, temperature: float = 0.0) -> str:
    """Route a model string to the appropriate LLM provider and return text."""
    provider, model_name = _parse_provider(model)

    if provider == "anthropic":
        return _call_anthropic(model_name, system, user, max_tokens, temperature)
    elif provider == "google":
        return _call_google(model_name, system, user, max_tokens, temperature)
    elif provider == "local":
        base_url = os.environ.get("LOCAL_LLM_URL", "http://localhost:8080/v1")
        api_key = os.environ.get("LOCAL_LLM_API_KEY", "none")
        return _call_openai_compat(
            model_name, system, user, max_tokens, temperature,
            base_url=base_url, api_key_env=None,
            api_key_override=api_key,
        )
    elif provider in _OPENAI_COMPAT_PROVIDERS:
        base_url, api_key_env = _OPENAI_COMPAT_PROVIDERS[provider]
        return _call_openai_compat(
            model_name, system, user, max_tokens, temperature,
            base_url, api_key_env,
        )
    else:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Supported: anthropic, google, local, {', '.join(_OPENAI_COMPAT_PROVIDERS)}"
        )


# ---------------------------------------------------------------------------
# Image loading
# ---------------------------------------------------------------------------

def _load_image(image_path: str | Path) -> tuple[str, str]:
    """Load an image file and return (base64_data, media_type)."""
    path = Path(image_path)
    suffix = path.suffix.lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(suffix, "image/png")
    b64 = base64.b64encode(path.read_bytes()).decode()
    return b64, media_type


# ---------------------------------------------------------------------------
# Vision calls (text + image)
# ---------------------------------------------------------------------------

def _call_anthropic_with_image(
    model: str, system: str, user: str,
    image_b64: str, media_type: str,
    max_tokens: int, temperature: float,
) -> str:
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "anthropic package required for Anthropic models. "
            "Install with: pip install 'autocritic[anthropic]'"
        )
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_b64,
                    },
                },
                {"type": "text", "text": user},
            ],
        }],
    )
    return response.content[0].text


def _call_openai_compat_with_image(
    model: str, system: str, user: str,
    image_b64: str, media_type: str,
    max_tokens: int, temperature: float,
    base_url: str | None, api_key_env: str | None,
    api_key_override: str | None = None,
) -> str:
    try:
        import openai
    except ImportError:
        raise ImportError(
            "openai package required for OpenAI-compatible models. "
            "Install with: pip install 'autocritic[openai]'"
        )
    if api_key_override is not None:
        api_key = api_key_override
    elif api_key_env:
        api_key = os.environ.get(api_key_env)
    else:
        api_key = "ollama"
    client = openai.OpenAI(base_url=base_url, api_key=api_key)
    image_url = f"data:{media_type};base64,{image_b64}"
    token_kwarg = (
        {"max_completion_tokens": max_tokens}
        if base_url is None
        else {"max_tokens": max_tokens}
    )
    response = client.chat.completions.create(
        model=model,
        **token_kwarg,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": user},
            ]},
        ],
    )
    return response.choices[0].message.content


def _call_google_with_image(
    model: str, system: str, user: str,
    image_b64: str, media_type: str,
    max_tokens: int, temperature: float,
) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError(
            "google-genai package required for Google models. "
            "Install with: pip install 'autocritic[google]'"
        )
    client = genai.Client()
    image_part = types.Part.from_bytes(
        data=base64.b64decode(image_b64),
        mime_type=media_type,
    )
    response = client.models.generate_content(
        model=model,
        contents=[image_part, user],
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            temperature=temperature,
        ),
    )
    return response.text


def _call_llm_with_image(
    model: str, system: str, user: str,
    image_path: str | Path,
    max_tokens: int = 4096, temperature: float = 0.0,
) -> str:
    """Route a model string to the appropriate LLM provider with image input."""
    provider, model_name = _parse_provider(model)
    image_b64, media_type = _load_image(image_path)

    if provider == "anthropic":
        return _call_anthropic_with_image(
            model_name, system, user, image_b64, media_type,
            max_tokens, temperature,
        )
    elif provider == "google":
        return _call_google_with_image(
            model_name, system, user, image_b64, media_type,
            max_tokens, temperature,
        )
    elif provider == "local":
        base_url = os.environ.get("LOCAL_LLM_URL", "http://localhost:8080/v1")
        api_key = os.environ.get("LOCAL_LLM_API_KEY", "none")
        return _call_openai_compat_with_image(
            model_name, system, user, image_b64, media_type,
            max_tokens, temperature,
            base_url=base_url, api_key_env=None,
            api_key_override=api_key,
        )
    elif provider in _OPENAI_COMPAT_PROVIDERS:
        base_url, api_key_env = _OPENAI_COMPAT_PROVIDERS[provider]
        return _call_openai_compat_with_image(
            model_name, system, user, image_b64, media_type,
            max_tokens, temperature, base_url, api_key_env,
        )
    else:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Supported: anthropic, google, local, {', '.join(_OPENAI_COMPAT_PROVIDERS)}"
        )


# ---------------------------------------------------------------------------
# Two-image comparison calls
# ---------------------------------------------------------------------------

def _call_llm_with_two_images(
    model: str, system: str, user: str,
    prev_b64: str, prev_mt: str,
    curr_b64: str, curr_mt: str,
    max_tokens: int = 4096, temperature: float = 0.0,
) -> str:
    """Route a two-image comparison call to the appropriate LLM provider."""
    provider, model_name = _parse_provider(model)

    if provider == "anthropic":
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package required. "
                "Install with: pip install 'autocritic[anthropic]'"
            )
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Previous iteration:"},
                    {"type": "image", "source": {
                        "type": "base64", "media_type": prev_mt, "data": prev_b64,
                    }},
                    {"type": "text", "text": "Current iteration:"},
                    {"type": "image", "source": {
                        "type": "base64", "media_type": curr_mt, "data": curr_b64,
                    }},
                    {"type": "text", "text": user},
                ],
            }],
        )
        return response.content[0].text

    elif provider == "google":
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ImportError(
                "google-genai package required. "
                "Install with: pip install 'autocritic[google]'"
            )
        client = genai.Client()
        prev_part = types.Part.from_bytes(
            data=base64.b64decode(prev_b64), mime_type=prev_mt,
        )
        curr_part = types.Part.from_bytes(
            data=base64.b64decode(curr_b64), mime_type=curr_mt,
        )
        response = client.models.generate_content(
            model=model_name,
            contents=[
                "Previous iteration:", prev_part,
                "Current iteration:", curr_part,
                user,
            ],
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )
        return response.text

    else:
        # OpenAI-compatible (covers openai, xai, ollama, mlx, llamacpp, local)
        try:
            import openai
        except ImportError:
            raise ImportError(
                "openai package required. "
                "Install with: pip install 'autocritic[openai]'"
            )

        if provider == "local":
            base_url = os.environ.get("LOCAL_LLM_URL", "http://localhost:8080/v1")
            api_key = os.environ.get("LOCAL_LLM_API_KEY", "none")
        elif provider in _OPENAI_COMPAT_PROVIDERS:
            base_url, api_key_env = _OPENAI_COMPAT_PROVIDERS[provider]
            api_key = os.environ.get(api_key_env) if api_key_env else "ollama"
        else:
            raise ValueError(f"Unknown provider: {provider}")

        client = openai.OpenAI(base_url=base_url, api_key=api_key)
        prev_url = f"data:{prev_mt};base64,{prev_b64}"
        curr_url = f"data:{curr_mt};base64,{curr_b64}"
        token_kwarg = (
            {"max_completion_tokens": max_tokens}
            if base_url is None
            else {"max_tokens": max_tokens}
        )
        response = client.chat.completions.create(
            model=model_name,
            **token_kwarg,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": [
                    {"type": "text", "text": "Previous iteration:"},
                    {"type": "image_url", "image_url": {"url": prev_url}},
                    {"type": "text", "text": "Current iteration:"},
                    {"type": "image_url", "image_url": {"url": curr_url}},
                    {"type": "text", "text": user},
                ]},
            ],
        )
        return response.choices[0].message.content
