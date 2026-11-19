"""Japanese input for the on-screen keyboard: romaji -> hiragana, and kanji
conversion through Google's transliterate endpoint (needs the network)."""

import json
import urllib.parse
import urllib.request

_BASE = {
    "a": "あ", "i": "い", "u": "う", "e": "え", "o": "お",
    "ka": "か", "ki": "き", "ku": "く", "ke": "け", "ko": "こ",
    "sa": "さ", "si": "し", "shi": "し", "su": "す", "se": "せ", "so": "そ",
    "ta": "た", "ti": "ち", "chi": "ち", "tu": "つ", "tsu": "つ", "te": "て", "to": "と",
    "na": "な", "ni": "に", "nu": "ぬ", "ne": "ね", "no": "の",
    "ha": "は", "hi": "ひ", "hu": "ふ", "fu": "ふ", "he": "へ", "ho": "ほ",
    "ma": "ま", "mi": "み", "mu": "む", "me": "め", "mo": "も",
    "ya": "や", "yu": "ゆ", "yo": "よ",
    "ra": "ら", "ri": "り", "ru": "る", "re": "れ", "ro": "ろ",
    "wa": "わ", "wi": "うぃ", "we": "うぇ", "wo": "を", "nn": "ん", "n'": "ん",
    "ga": "が", "gi": "ぎ", "gu": "ぐ", "ge": "げ", "go": "ご",
    "za": "ざ", "zi": "じ", "ji": "じ", "zu": "ず", "ze": "ぜ", "zo": "ぞ",
    "da": "だ", "di": "ぢ", "du": "づ", "de": "で", "do": "ど",
    "ba": "ば", "bi": "び", "bu": "ぶ", "be": "べ", "bo": "ぼ",
    "pa": "ぱ", "pi": "ぴ", "pu": "ぷ", "pe": "ぺ", "po": "ぽ",
    "va": "ゔぁ", "vi": "ゔぃ", "vu": "ゔ", "ve": "ゔぇ", "vo": "ゔぉ",
    "fa": "ふぁ", "fi": "ふぃ", "fe": "ふぇ", "fo": "ふぉ",
    "ja": "じゃ", "ju": "じゅ", "je": "じぇ", "jo": "じょ",
    "sha": "しゃ", "shu": "しゅ", "she": "しぇ", "sho": "しょ",
    "cha": "ちゃ", "chu": "ちゅ", "che": "ちぇ", "cho": "ちょ",
    "tha": "てゃ", "thi": "てぃ", "thu": "てゅ", "dhi": "でぃ", "dhu": "でゅ",
    "twu": "とぅ", "dwu": "どぅ",
    "xa": "ぁ", "xi": "ぃ", "xu": "ぅ", "xe": "ぇ", "xo": "ぉ",
    "la": "ぁ", "li": "ぃ", "lu": "ぅ", "le": "ぇ", "lo": "ぉ",
    "xya": "ゃ", "xyu": "ゅ", "xyo": "ょ", "lya": "ゃ", "lyu": "ゅ", "lyo": "ょ",
    "xtu": "っ", "ltu": "っ", "xtsu": "っ", "xwa": "ゎ",
    "-": "ー", ".": "。", ",": "、", ":": "：", "/": "・",
}
# kya, sya, ... : consonant + y + vowel -> i-row kana + small ya/yu/yo
for _c, _i in {"k": "き", "s": "し", "t": "ち", "c": "ち", "n": "に", "h": "ひ",
               "m": "み", "r": "り", "g": "ぎ", "z": "じ", "j": "じ", "d": "ぢ",
               "b": "び", "p": "ぴ"}.items():
    for _v, _s in (("a", "ゃ"), ("u", "ゅ"), ("o", "ょ"), ("e", "ぇ")):
        _BASE.setdefault(_c + "y" + _v, _i + _s)
_MAX = max(len(k) for k in _BASE)
_CONSONANTS = set("bcdfghjklmpqrstvwxyz")


def to_hiragana(romaji, final=False):
    """Convert as much of `romaji` as possible.  Returns (kana, pending) where
    pending is the unconverted tail still being typed.  final=True flushes a
    trailing lone 'n' to ん."""
    out = []
    i = 0
    s = romaji.lower()
    while i < len(s):
        # small tsu: doubled consonant (not n)
        if (i + 1 < len(s) and s[i] == s[i + 1] and s[i] in _CONSONANTS
                and s[i] != "n"):
            out.append("っ")
            i += 1
            continue
        # "nn": ん.  "nna" / "nni" ... : ん + な / に (konnichiha -> こんにちは)
        if s[i] == "n" and i + 1 < len(s) and s[i + 1] == "n":
            out.append("ん")
            i += 1 if (i + 2 < len(s) and s[i + 2] in "aiueoy") else 2
            continue
        # n before a consonant (not y / n) is ん
        if (s[i] == "n" and i + 1 < len(s) and s[i + 1] not in "aiueoyn'"):
            out.append("ん")
            i += 1
            continue
        for length in range(min(_MAX, len(s) - i), 0, -1):
            kana = _BASE.get(s[i:i + length])
            if kana is not None:
                out.append(kana)
                i += length
                break
        else:
            rest = s[i:]
            # could this tail still become a syllable?
            if any(k.startswith(rest) for k in _BASE):
                if final and rest == "n":
                    out.append("ん")
                    return "".join(out), ""
                return "".join(out), rest
            out.append(s[i])        # not romaji: pass it through
            i += 1
    return "".join(out), ""


def katakana(text):
    return "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in text)


def candidates(hiragana, timeout=4.0):
    """Whole-text candidates: the n-th choice of every segment joined, then the
    plain hiragana and katakana.  Never raises; offline gives kana only."""
    result = []
    try:
        url = ("https://www.google.com/transliterate?langpair="
               + urllib.parse.quote("ja-Hira|ja") + "&text="
               + urllib.parse.quote(hiragana))
        with urllib.request.urlopen(url, timeout=timeout) as response:
            segments = json.loads(response.read().decode("utf-8"))
        depth = max(len(choices) for _, choices in segments)
        for n in range(depth):
            result.append("".join(choices[n] if n < len(choices) else choices[0]
                                  for _, choices in segments))
    except Exception:
        pass
    result += [hiragana, katakana(hiragana)]
    seen, unique = set(), []
    for text in result:
        if text and text not in seen:
            seen.add(text)
            unique.append(text)
    return unique
