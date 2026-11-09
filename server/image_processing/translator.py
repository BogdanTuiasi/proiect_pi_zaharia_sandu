import asyncio
from html import unescape
from threading import Thread
import urllib.parse
import aiohttp


class Translator:
    target_lang = 'ro'

    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    async def _try_mymemory(self, text: str) -> str:
        encoded = urllib.parse.quote(text)
        url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair=autodetect|{self.target_lang}"
        timeout = aiohttp.ClientTimeout(total=3)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                data = await resp.json(content_type=None)
                match = data.get("responseData", {}).get("translatedText")
                if match:
                    return unescape(match)
        return text

    async def _try_google(self, text: str) -> str:
        encoded = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={self.target_lang}&dt=t&q={encoded}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        timeout = aiohttp.ClientTimeout(total=3)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    return ''.join([s[0] for s in data[0] if s[0]])
        return text

    async def translate(self, text: str) -> str:
        clean = text.strip()
        # return text # debug
        if not clean: return text

        try:
            res = await self._try_mymemory(clean)
            if res and res.lower() != clean.lower():
                return res
        except Exception:
            pass

        try:
            return await self._try_google(clean)
        except Exception:
            return text

    def translate_async(self, text: str, callback):
        async def _coro():
            res = await self.translate(text)
            callback(res)

        asyncio.run_coroutine_threadsafe(_coro(), self._loop)


translator = Translator()
