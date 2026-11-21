import asyncio
from html import unescape
from threading import Lock, Thread
from typing import Optional
import urllib.parse
import aiohttp


class Translator:
    def __init__(self):
        self.target_lang = 'ro'
        self._cache: dict[tuple[str, str], str] = {}
        self._cache_lock = Lock()
        self._loop = asyncio.new_event_loop()
        self._thread = Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def set_target_language(self, target_lang: str):
        if target_lang:
            self.target_lang = target_lang

    async def _try_mymemory(self, text: str, target_lang: str) -> str:
        encoded = urllib.parse.quote(text)
        url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair=autodetect|{target_lang}"
        timeout = aiohttp.ClientTimeout(total=3)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)

                # MyMemory can return quota/error messages in translatedText
                # while the HTTP response itself is still 200. Do not expose
                # those messages as translations; let translate() try Google.
                if data.get("quotaFinished") or str(data.get("responseStatus")) != "200":
                    details = data.get("responseDetails") or "MyMemory translation failed"
                    raise RuntimeError(details)

                response_data = data.get("responseData") or {}
                match = response_data.get("translatedText")
                if match:
                    return unescape(match)
        return text

    async def _try_google(self, text: str, target_lang: str) -> str:
        encoded = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={encoded}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        timeout = aiohttp.ClientTimeout(total=3)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    return ''.join([s[0] for s in data[0] if s[0]])
        return text

    async def translate(self, text: str, target_lang: Optional[str] = None) -> str:
        clean = text.strip()
        if not clean: return text

        language = target_lang or self.target_lang
        cache_key = (language, clean.casefold())
        with self._cache_lock:
            cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            res = await self._try_mymemory(clean, language)
            if res and res.lower() != clean.lower():
                translated = res
            else:
                translated = None
        except Exception:
            translated = None

        if translated is None:
            try:
                translated = await self._try_google(clean, language)
            except Exception:
                translated = text

        if translated.casefold() != clean.casefold():
            with self._cache_lock:
                self._cache[cache_key] = translated
        return translated

    def translate_async(self, text: str, callback):
        async def _coro():
            language = self.target_lang
            res = await self.translate(text, language)
            callback(res)

        asyncio.run_coroutine_threadsafe(_coro(), self._loop)


translator = Translator()
