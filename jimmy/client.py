"""jimmy.client — jedyne miejsce w projekcie, ktore wykonuje HTTP do Jimmy'ego.

Zasady (polityka "kochamy Jimmy'ego, nie naduzywamy"):
  - twardy limit wspolbieznosci (MAX_CONCURRENCY)
  - globalny sufit requestow na minute (RPM_CEILING)
  - kazde wywolanie parsuje blok <|stats|> jako darmowa telemetrie (ttft, decode_rate,
    liczby tokenow) i loguje ja, zeby miec dane o przepustowosci przez caly projekt.

Odpowiedz z API NIE jest JSON-em: to surowy tekst + doklejony na koncu blok
<|stats|>...<|/stats|>. Klient rozdziela `content` od `stats`.
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

import httpx

API_URL = "https://chatjimmy.ai/api/chat"
MODEL = "llama3.1-8B"

# --- Polityka bezpiecznego uzycia (wyznaczona empirycznie w Fazie 0, patrz CHARACTERIZATION.md) ---
# conc=8 daje ~38 req/s przy 0 bledach i stabilnym p50=134ms. Serwer bywa przejsciowo
# niestabilny (sporadyczne 500), stad retry z backoffem.
MAX_CONCURRENCY = 8           # bezpieczny, zmierzony punkt pracy (0 bledow)
RPM_CEILING = 2000            # globalny sufit requestow/min (miekki throttle, "kochamy Jimmy'ego")
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3               # retry na 500/timeout (przejsciowa niestabilnosc serwera)
USABLE_PREFILL_TOKENS = 6000  # sufit kontekstu: 6k OK, 8k+ pusta odpowiedz

_HEADERS = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://chatjimmy.ai",
    "referer": "https://chatjimmy.ai/",
    "user-agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
}

_STATS_RE = re.compile(r"<\|stats\|>(.*?)<\|/stats\|>", re.DOTALL)


@dataclass
class JimmyResponse:
    content: str                       # czysty tekst odpowiedzi (bez bloku stats)
    stats: dict[str, Any]              # sparsowany blok <|stats|>
    raw: str                           # pelna surowa odpowiedz
    wall_time: float                   # czas scienny mierzony po stronie klienta (s)
    ok: bool = True
    error: Optional[str] = None

    @property
    def decode_rate(self) -> float:
        return float(self.stats.get("decode_rate", 0.0))

    @property
    def total_tokens(self) -> int:
        return int(self.stats.get("total_tokens", 0))

    @property
    def ttft(self) -> float:
        return float(self.stats.get("ttft", 0.0))


def _split_stats(raw: str) -> tuple[str, dict[str, Any]]:
    m = _STATS_RE.search(raw)
    if not m:
        return raw.strip(), {}
    stats: dict[str, Any] = {}
    try:
        stats = json.loads(m.group(1))
    except json.JSONDecodeError:
        pass
    content = _STATS_RE.sub("", raw).strip()
    return content, stats


def build_payload(
    messages: list[dict[str, str]],
    system_prompt: str = "",
    top_k: int = 8,
    **extra_options: Any,
) -> dict[str, Any]:
    """Zbuduj payload. `extra_options` trafia do chatOptions (do sondowania parametrow)."""
    chat_options: dict[str, Any] = {
        "selectedModel": MODEL,
        "systemPrompt": system_prompt,
        "topK": top_k,
    }
    chat_options.update(extra_options)
    return {"messages": messages, "chatOptions": chat_options, "attachment": None}


class JimmyClient:
    """Async klient z pula wspolbieznosci i telemetria.

    Uzycie:
        async with JimmyClient() as jc:
            r = await jc.ask("Czesc")
            rs = await jc.map_prompts(["a", "b", "c"])
    """

    def __init__(
        self,
        max_concurrency: int = MAX_CONCURRENCY,
        timeout: float = DEFAULT_TIMEOUT,
        rpm_ceiling: int = RPM_CEILING,
    ):
        self._sem = asyncio.Semaphore(max_concurrency)
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._rpm_ceiling = rpm_ceiling
        self._req_times: list[float] = []
        self._lock = asyncio.Lock()
        # zbiorcza telemetria sesji
        self.n_requests = 0
        self.n_errors = 0
        self.total_decode_tokens = 0

    async def __aenter__(self) -> "JimmyClient":
        self._client = httpx.AsyncClient(
            timeout=self._timeout, headers=_HEADERS, http2=False
        )
        return self

    async def __aexit__(self, *exc) -> None:
        if self._client:
            await self._client.aclose()

    async def _throttle(self) -> None:
        """Miekki globalny sufit RPM."""
        async with self._lock:
            now = time.monotonic()
            self._req_times = [t for t in self._req_times if now - t < 60.0]
            if len(self._req_times) >= self._rpm_ceiling:
                sleep_for = 60.0 - (now - self._req_times[0])
                if sleep_for > 0:
                    await asyncio.sleep(sleep_for)
            self._req_times.append(time.monotonic())

    async def raw_post(self, payload: dict[str, Any], retries: int = MAX_RETRIES) -> JimmyResponse:
        assert self._client is not None, "uzyj jako async context manager"
        last_err = "unknown"
        for attempt in range(retries + 1):
            await self._throttle()
            async with self._sem:
                t0 = time.monotonic()
                try:
                    resp = await self._client.post(API_URL, json=payload)
                    wall = time.monotonic() - t0
                    resp.raise_for_status()
                    text = resp.text
                    content, stats = _split_stats(text)
                    self.n_requests += 1
                    self.total_decode_tokens += int(stats.get("decode_tokens", 0))
                    return JimmyResponse(
                        content=content, stats=stats, raw=text, wall_time=wall
                    )
                except Exception as e:  # noqa: BLE001
                    wall = time.monotonic() - t0
                    last_err = f"{type(e).__name__}: {e}"
            if attempt < retries:
                await asyncio.sleep(0.25 * (2 ** attempt))  # backoff: 0.25, 0.5, 1.0s
        self.n_errors += 1
        return JimmyResponse(content="", stats={}, raw="", wall_time=0.0,
                             ok=False, error=last_err)

    async def ask(
        self,
        prompt: str,
        system_prompt: str = "",
        top_k: int = 8,
        history: Optional[list[dict[str, str]]] = None,
        **extra_options: Any,
    ) -> JimmyResponse:
        messages = list(history or [])
        messages.append({"role": "user", "content": prompt})
        payload = build_payload(messages, system_prompt, top_k, **extra_options)
        return await self.raw_post(payload)

    async def map_prompts(
        self,
        prompts: list[str],
        system_prompt: str = "",
        top_k: int = 8,
        **extra_options: Any,
    ) -> list[JimmyResponse]:
        """Rownolegle N promptow (ograniczone semaforem)."""
        tasks = [
            self.ask(p, system_prompt=system_prompt, top_k=top_k, **extra_options)
            for p in prompts
        ]
        return await asyncio.gather(*tasks)

    async def sample_n(
        self,
        prompt: str,
        n: int,
        system_prompt: str = "",
        top_k: int = 8,
        **extra_options: Any,
    ) -> list[JimmyResponse]:
        """N niezaleznych probek tego samego promptu (best-of-N / glosowanie)."""
        tasks = [
            self.ask(prompt, system_prompt=system_prompt, top_k=top_k, **extra_options)
            for _ in range(n)
        ]
        return await asyncio.gather(*tasks)


# --- Prosty synchroniczny helper do szybkich sond ---
def ask_sync(prompt: str, system_prompt: str = "", top_k: int = 8, **extra) -> JimmyResponse:
    async def _run():
        async with JimmyClient() as jc:
            return await jc.ask(prompt, system_prompt=system_prompt, top_k=top_k, **extra)
    return asyncio.run(_run())


if __name__ == "__main__":
    r = ask_sync("Reply with exactly: OK", top_k=1)
    print("content:", repr(r.content))
    print("decode_rate:", r.decode_rate, "t/s | total_tokens:", r.total_tokens,
          "| wall:", round(r.wall_time * 1000), "ms")
