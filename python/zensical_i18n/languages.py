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

# Titles of the admonition types of the theme, replacing the titles derived
# from types when no title is given. Can be overridden per language with
# `admonition_translations`.
ADMONITIONS = {
    "ar": {
        "note": "ملاحظة",
        "abstract": "ملخص",
        "info": "معلومات",
        "tip": "تلميح",
        "success": "نجاح",
        "question": "سؤال",
        "warning": "تحذير",
        "failure": "فشل",
        "danger": "خطر",
        "bug": "خلل",
        "example": "مثال",
        "quote": "اقتباس",
    },
    "ca": {
        "note": "Nota",
        "abstract": "Resum",
        "info": "Informació",
        "tip": "Consell",
        "success": "Èxit",
        "question": "Pregunta",
        "warning": "Advertència",
        "failure": "Fallada",
        "danger": "Perill",
        "bug": "Error",
        "example": "Exemple",
        "quote": "Cita",
    },
    "cs": {
        "note": "Poznámka",
        "abstract": "Shrnutí",
        "info": "Informace",
        "tip": "Tip",
        "success": "Úspěch",
        "question": "Otázka",
        "warning": "Varování",
        "failure": "Selhání",
        "danger": "Nebezpečí",
        "bug": "Chyba",
        "example": "Příklad",
        "quote": "Citace",
    },
    "da": {
        "note": "Bemærk",
        "abstract": "Resumé",
        "info": "Info",
        "tip": "Tip",
        "success": "Succes",
        "question": "Spørgsmål",
        "warning": "Advarsel",
        "failure": "Mislykket",
        "danger": "Fare",
        "bug": "Fejl",
        "example": "Eksempel",
        "quote": "Citat",
    },
    "de": {
        "note": "Hinweis",
        "abstract": "Zusammenfassung",
        "info": "Info",
        "tip": "Tipp",
        "success": "Erfolg",
        "question": "Frage",
        "warning": "Warnung",
        "failure": "Fehlschlag",
        "danger": "Gefahr",
        "bug": "Fehler",
        "example": "Beispiel",
        "quote": "Zitat",
    },
    "es": {
        "note": "Nota",
        "abstract": "Resumen",
        "info": "Información",
        "tip": "Consejo",
        "success": "Éxito",
        "question": "Pregunta",
        "warning": "Advertencia",
        "failure": "Fallo",
        "danger": "Peligro",
        "bug": "Error",
        "example": "Ejemplo",
        "quote": "Cita",
    },
    "fr": {
        "note": "Note",
        "abstract": "Résumé",
        "info": "Information",
        "tip": "Astuce",
        "success": "Succès",
        "question": "Question",
        "warning": "Avertissement",
        "failure": "Échec",
        "danger": "Danger",
        "bug": "Bogue",
        "example": "Exemple",
        "quote": "Citation",
    },
    "he": {
        "note": "הערה",
        "abstract": "תקציר",
        "info": "מידע",
        "tip": "טיפ",
        "success": "הצלחה",
        "question": "שאלה",
        "warning": "אזהרה",
        "failure": "כישלון",
        "danger": "סכנה",
        "bug": "באג",
        "example": "דוגמה",
        "quote": "ציטוט",
    },
    "hi": {
        "note": "टिप्पणी",
        "abstract": "सारांश",
        "info": "जानकारी",
        "tip": "सुझाव",
        "success": "सफलता",
        "question": "प्रश्न",
        "warning": "चेतावनी",
        "failure": "विफलता",
        "danger": "खतरा",
        "bug": "बग",
        "example": "उदाहरण",
        "quote": "उद्धरण",
    },
    "id": {
        "note": "Catatan",
        "abstract": "Ringkasan",
        "info": "Info",
        "tip": "Tips",
        "success": "Berhasil",
        "question": "Pertanyaan",
        "warning": "Peringatan",
        "failure": "Gagal",
        "danger": "Bahaya",
        "bug": "Bug",
        "example": "Contoh",
        "quote": "Kutipan",
    },
    "it": {
        "note": "Nota",
        "abstract": "Riepilogo",
        "info": "Informazioni",
        "tip": "Suggerimento",
        "success": "Successo",
        "question": "Domanda",
        "warning": "Avvertenza",
        "failure": "Fallimento",
        "danger": "Pericolo",
        "bug": "Bug",
        "example": "Esempio",
        "quote": "Citazione",
    },
    "ja": {
        "note": "注記",
        "abstract": "概要",
        "info": "情報",
        "tip": "ヒント",
        "success": "成功",
        "question": "質問",
        "warning": "警告",
        "failure": "失敗",
        "danger": "危険",
        "bug": "バグ",
        "example": "例",
        "quote": "引用",
    },
    "ko": {
        "note": "참고",
        "abstract": "요약",
        "info": "정보",
        "tip": "팁",
        "success": "성공",
        "question": "질문",
        "warning": "경고",
        "failure": "실패",
        "danger": "위험",
        "bug": "버그",
        "example": "예시",
        "quote": "인용",
    },
    "nl": {
        "note": "Opmerking",
        "abstract": "Samenvatting",
        "info": "Info",
        "tip": "Tip",
        "success": "Succes",
        "question": "Vraag",
        "warning": "Waarschuwing",
        "failure": "Mislukt",
        "danger": "Gevaar",
        "bug": "Bug",
        "example": "Voorbeeld",
        "quote": "Citaat",
    },
    "pl": {
        "note": "Uwaga",
        "abstract": "Streszczenie",
        "info": "Informacja",
        "tip": "Wskazówka",
        "success": "Sukces",
        "question": "Pytanie",
        "warning": "Ostrzeżenie",
        "failure": "Niepowodzenie",
        "danger": "Niebezpieczeństwo",
        "bug": "Błąd",
        "example": "Przykład",
        "quote": "Cytat",
    },
    "pt": {
        "note": "Nota",
        "abstract": "Resumo",
        "info": "Informação",
        "tip": "Dica",
        "success": "Sucesso",
        "question": "Pergunta",
        "warning": "Aviso",
        "failure": "Falha",
        "danger": "Perigo",
        "bug": "Bug",
        "example": "Exemplo",
        "quote": "Citação",
    },
    "ru": {
        "note": "Примечание",
        "abstract": "Аннотация",
        "info": "Информация",
        "tip": "Совет",
        "success": "Успех",
        "question": "Вопрос",
        "warning": "Предупреждение",
        "failure": "Неудача",
        "danger": "Опасность",
        "bug": "Ошибка",
        "example": "Пример",
        "quote": "Цитата",
    },
    "sv": {
        "note": "Notering",
        "abstract": "Sammanfattning",
        "info": "Info",
        "tip": "Tips",
        "success": "Lyckat",
        "question": "Fråga",
        "warning": "Varning",
        "failure": "Misslyckat",
        "danger": "Fara",
        "bug": "Bugg",
        "example": "Exempel",
        "quote": "Citat",
    },
    "tr": {
        "note": "Not",
        "abstract": "Özet",
        "info": "Bilgi",
        "tip": "İpucu",
        "success": "Başarılı",
        "question": "Soru",
        "warning": "Uyarı",
        "failure": "Başarısız",
        "danger": "Tehlike",
        "bug": "Hata",
        "example": "Örnek",
        "quote": "Alıntı",
    },
    "uk": {
        "note": "Примітка",
        "abstract": "Анотація",
        "info": "Інформація",
        "tip": "Порада",
        "success": "Успіх",
        "question": "Питання",
        "warning": "Попередження",
        "failure": "Невдача",
        "danger": "Небезпека",
        "bug": "Помилка",
        "example": "Приклад",
        "quote": "Цитата",
    },
    "vi": {
        "note": "Ghi chú",
        "abstract": "Tóm tắt",
        "info": "Thông tin",
        "tip": "Mẹo",
        "success": "Thành công",
        "question": "Câu hỏi",
        "warning": "Cảnh báo",
        "failure": "Thất bại",
        "danger": "Nguy hiểm",
        "bug": "Lỗi",
        "example": "Ví dụ",
        "quote": "Trích dẫn",
    },
    "zh": {
        "note": "注",
        "abstract": "摘要",
        "info": "信息",
        "tip": "提示",
        "success": "成功",
        "question": "问题",
        "warning": "警告",
        "failure": "失败",
        "danger": "危险",
        "bug": "缺陷",
        "example": "示例",
        "quote": "引用",
    },
    "zh-TW": {
        "note": "註",
        "abstract": "摘要",
        "info": "資訊",
        "tip": "提示",
        "success": "成功",
        "question": "問題",
        "warning": "警告",
        "failure": "失敗",
        "danger": "危險",
        "bug": "缺陷",
        "example": "範例",
        "quote": "引用",
    },
}

# Primary subtags of languages written from right to left.
RTL = frozenset(
    ("ar", "ckb", "dv", "fa", "he", "ku", "ps", "sd", "ug", "ur", "yi")
)

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


def admonitions(locale: str) -> dict[str, str]:
    """Return the default admonition titles for the given locale.

    Locales are matched exactly first, then by their primary subtag. There
    are no defaults for English, as titles are derived from the types.
    """
    primary = locale.replace("_", "-").split("-")[0]
    return dict(ADMONITIONS.get(locale, ADMONITIONS.get(primary, {})))


def hreflang(locale: str) -> str:
    """Return the language tag of a locale, e.g., `pt-BR` for `pt_BR`."""
    return locale.replace("_", "-")


def direction(locale: str) -> str:
    """Return the text direction of a locale, i.e., `ltr` or `rtl`."""
    primary = hreflang(locale).split("-")[0].lower()
    return "rtl" if primary in RTL else "ltr"
