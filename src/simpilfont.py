# Library used from https://github.com/OneMadGypsy/SimPIL-Font with small fixes for extra font paths
# and styles

# MIT License

# Copyright (c) 2024 Michael Guidry

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations
from glob import iglob
from PIL import ImageFont

import os, sys, json, functools, re

__all__ = ('Font',)

# common font directories for major systems
SYSTEMDIRS = dict(
    win32  = ('C:/Windows/Fonts', ),
    linux  = ('/usr/share/fonts', '/usr/local/share/fonts', '~/.local/share/fonts', '~/.fonts'),
    linux2 = ('/usr/share/fonts', '/usr/local/share/fonts', '~/.local/share/fonts', '~/.fonts'),
    darwin = ('/Library/Fonts', '/System/Library/Fonts', '/System/Library/Fonts/Supplemental', '~/Library/Fonts'),
).get(sys.platform, tuple())

STYLE_WORDS = {
    # weights
    "thin","extralight","ultralight","light","book","regular","normal","medium",
    "semibold","demibold","bold","extrabold","ultrabold","black","heavy",
    # slants
    "italic","oblique",
    # widths (help pick specific faces if present)
    "condensed","narrow","expanded","extended",
}

EXTENSIONS = (".ttf", ".otf", ".ttc", ".otc")


class Font:
    # https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.truetype
    ENCODINGS  = "unic", "symb", "lat1", "DOB", "ADBE", "ADBC", "armn", "sjis", "gb", "big5", "ans", "joha"
    ENC_EXCEPT = "Unable to encode font:\n\t({})"
    DNE_EXCEPT = ("Requested font family does not exist.\n"
                  "Call sf.export(), and check the resulting './fonts.json' file for your font request.")

    @property
    def family(self) -> str:
        return getattr(self, '_family', 'Arial') or 'Arial'

    @property
    def style(self) -> str:
        return getattr(self, '_style', 'regular') or 'regular'

    @property
    def size(self) -> int:
        return getattr(self, '_size', 12) or 12

    @property
    def path(self) -> str:
        return getattr(self, '_path', None)

    @property  # supported styles for the current font
    def styles(self) -> tuple:
        return tuple(getattr(self, '_styles', ()))

    @property
    def font(self) -> ImageFont.FreeTypeFont:
        return getattr(self, '_font', None)

    def __init__(self, *args) -> None:
        # expand ~, then abspath, then unique
        dirs = []
        for p in args + SYSTEMDIRS:
            p = os.path.abspath(os.path.expanduser(p))
            if p not in dirs:
                dirs.append(p)
        self._fontdirs = tuple(dirs)

    def __str__(self) -> str:
        return ' '.join((self.family, f'{self.size}', self.style))

    def __call__(self, *request) -> Font:
        family_tokens, style_tokens, size = [], [], 0

        # normalize and split; allow hyphen-separated styles like "Bold-Italic"
        raw = ' '.join(map(str, request)).replace('-', ' ')
        for part in raw.split():
            if part.isdigit():
                size = int(part)
                continue

            pl = part.lower()

            # match compound single tokens like "BoldItalic" or "SemiBoldItalic"
            m = re.fullmatch(
                r'(thin|extralight|ultralight|light|book|regular|normal|medium|semibold|demibold|bold|extrabold|ultrabold|black|heavy)?'
                r'(italic|oblique)?', pl
            )
            if pl in STYLE_WORDS:
                style_tokens.append(pl)
            elif m and (m.group(1) or m.group(2)):
                if m.group(1): style_tokens.append(m.group(1))
                if m.group(2): style_tokens.append(m.group(2))
            else:
                # everything else is part of the family name (preserve original case for display;
                # we'll normalize when matching)
                family_tokens.append(part)

        _family_req = (' '.join(family_tokens) or self.family)
        _style_req  = ' '.join(style_tokens) or self.style
        _family_key = _family_req.lower().replace(' ', '')
        _style_key  = _style_req.lower().replace(' ', '')

        font = self.__get(_family_key)
        _faces = font.get('faces', {})

        self._family = font['family']
        self._styles = font['styles']  # original style strings as reported by PIL
        self._size   = size or self.size

        # choose style: requested if present, else 'regular'/'book', else first available
        chosen_style = None
        for s in self._styles:
            if _style_key == s.replace(' ', '').lower():
                chosen_style = s
                break
        if not chosen_style:
            for fallback in ('regular', 'book'):
                for s in self._styles:
                    if fallback == s.replace(' ', '').lower():
                        chosen_style = s
                        break
                if chosen_style:
                    break
        if not chosen_style and self._styles:
            chosen_style = self._styles[0]

        self._style = chosen_style or 'regular'

        # get and use path
        style_key = self._style.replace(' ', '').lower()
        self._path = _faces.get(style_key, '')
        if not self._path:
            raise Exception(Font.DNE_EXCEPT)

        self._font = ImageFont.truetype(self._path, self._size, encoding=font['encoding'])

        return self

    @functools.cache
    def __enc(self, fn: str) -> tuple:
        """
        Determine an encoding Pillow accepts for this font file and return (encoding, family, style).
        Cached to avoid re-opening the same file repeatedly.
        """
        for encoding in Font.ENCODINGS:
            try:
                ttf = ImageFont.truetype(font=fn, encoding=encoding)
            except Exception:
                continue
            else:
                family, style = ttf.getname()
                return encoding, family, style
        raise Exception(Font.ENC_EXCEPT.format(fn))

    @functools.cache
    def __get(self, fam: str) -> dict:
        """
        Build the face map for a family key like 'arial' (lower, no spaces).
        Returns dict(family=<Display Name>, styles=[...], faces={style_key: path}, encoding=<enc>)
        """
        t_family: str = ''
        t_styles: list[str] = []
        t_faces: dict[str, str] = {}
        chosen_encoding: str | None = None

        # Scan all candidate font files and keep those where PIL reports the same family
        for directory in self._fontdirs:
            if not os.path.isdir(directory):
                continue

            # We scan all font files to avoid case-sensitivity misses on Linux
            pattern = os.path.join(directory, '**', '*')
            for path in iglob(pattern, recursive=True):
                if not isinstance(path, str):
                    continue
                if not path.lower().endswith(EXTENSIONS):
                    continue

                fn = os.path.abspath(path)
                try:
                    encoding, family, style = self.__enc(fn)
                except Exception:
                    continue

                fam_key = family.lower().replace(' ', '')
                if fam_key != fam:
                    continue

                # Normalize keys for matching, keep original for display list
                style_key = style.lower().replace(' ', '')
                t_faces[style_key] = fn
                if style not in t_styles:
                    t_styles.append(style)

                t_family = family
                chosen_encoding = chosen_encoding or encoding

        if not t_faces:
            raise Exception(Font.DNE_EXCEPT)

        return dict(family=t_family, styles=t_styles, faces=t_faces, encoding=chosen_encoding or 'unic')

    def export(self) -> None:
        """
        Export a JSON listing of all discoverable fonts grouped by encoding,
        e.g., {"unic": ["Arial regular", "Arial bold", ...], ...}
        """
        out = {k: [] for k in Font.ENCODINGS}

        for directory in self._fontdirs:
            if not os.path.isdir(directory):
                continue
            for path in iglob(os.path.join(directory, '**', '*'), recursive=True):
                if not isinstance(path, str) or not path.lower().endswith(EXTENSIONS):
                    continue
                fn = os.path.abspath(path)
                try:
                    encoding, family, style = self.__enc(fn)
                except Exception:
                    continue
                out.setdefault(encoding, []).append(f'{family} {style.lower()}')

        with open('fonts.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(out, indent=4, ensure_ascii=False))

        return self

    # basic bbox
    def bbox(self, text: str) -> tuple:
        return self._font.getbbox(text)

    # smallest possible bbox
    def min_bbox(self, text: str) -> tuple:
        x, y, w, h = self._font.getbbox(text)
        return -x, -y, w - x, h - y

    # (right/bottom) margins mirror the (left/top) margins, respectively
    def max_bbox(self, text: str) -> tuple:
        x, y, w, h = self._font.getbbox(text)
        return 0, 0, w + x, h + y
