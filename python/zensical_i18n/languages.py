# Copyright (c) 2026 Humberto Sandmann and contributors

# SPDX-License-Identifier: MIT
# All contributions are certified under the DCO

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

from __future__ import annotations

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Notice shown on pages that fall back to the default language, in the
# language of the site they're shown on, with `{language}` being the name of
# the default language. Can be overridden with `untranslated_notice`.
NOTICES = {
    "ar": "لم تتم ترجمة هذه الصفحة بعد، أنت تقرأ النص الأصلي بـ{language}.",
    "ca": "Aquesta pàgina encara no s'ha traduït. Esteu llegint l'original en {language}.",
    "cs": "Tato stránka zatím nebyla přeložena. Čtete originál v jazyce {language}.",
    "da": "Denne side er endnu ikke oversat. Du læser originalen på {language}.",
    "de": "Diese Seite wurde noch nicht übersetzt. Sie lesen das Original auf {language}.",
    "en": "This page hasn't been translated yet. You're reading the original in {language}.",
    "es": "Esta página aún no se ha traducido. Estás leyendo el original en {language}.",
    "fr": "Cette page n'a pas encore été traduite. Vous lisez l'original en {language}.",
    "he": "דף זה טרם תורגם. אתם קוראים את המקור ב{language}.",
    "hi": "इस पृष्ठ का अभी अनुवाद नहीं हुआ है। आप मूल {language} में पढ़ रहे हैं।",
    "id": "Halaman ini belum diterjemahkan. Anda membaca versi asli dalam {language}.",
    "it": "Questa pagina non è ancora stata tradotta. Stai leggendo l'originale in {language}.",
    "ja": "このページはまだ翻訳されていません。{language}の原文を表示しています。",
    "ko": "이 페이지는 아직 번역되지 않았습니다. {language} 원문을 보고 있습니다.",
    "nl": "Deze pagina is nog niet vertaald. Je leest het origineel in het {language}.",
    "pl": "Ta strona nie została jeszcze przetłumaczona. Czytasz oryginał w języku {language}.",
    "pt": "Esta página ainda não foi traduzida. Você está lendo o original em {language}.",
    "pt-PT": "Esta página ainda não foi traduzida. Está a ler o original em {language}.",
    "ru": "Эта страница ещё не переведена. Вы читаете оригинал на языке {language}.",
    "sv": "Den här sidan har inte översatts än. Du läser originalet på {language}.",
    "tr": "Bu sayfa henüz çevrilmedi. Orijinalini {language} dilinde okuyorsunuz.",
    "uk": "Цю сторінку ще не перекладено. Ви читаєте оригінал мовою {language}.",
    "vi": "Trang này chưa được dịch. Bạn đang đọc bản gốc bằng {language}.",
    "zh": "此页面尚未翻译，您正在阅读{language}原文。",
    "zh-TW": "此頁面尚未翻譯，您正在閱讀{language}原文。",
}

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------


def notice(locale: str, language: str, template: str | None = None) -> str:
    """Return the untranslated page notice for the given locale.

    Locales are matched exactly first, then by their primary subtag, so that
    `pt-BR` uses `pt`, falling back to English.
    """
    if template is None:
        primary = locale.replace("_", "-").split("-")[0]
        template = NOTICES.get(locale, NOTICES.get(primary, NOTICES["en"]))
    return template.replace("{language}", language)
