import typing as t

try:
    import bleach # type: ignore

except ImportError:
    import warnings

    class bleach:
        @staticmethod
        def clean(text: str, tags: list=[], attributes: list=[]):
            warnings.warn("Requested sanitization, but `bleach` is not installed. Not sanitizing...", UserWarning)
            return text


from dataclasses import dataclass
from .exceptions import EditorJsParseError


__all__ = [
    "EditorJsBlock",
    "HeaderBlock",
    "ParagraphBlock",
    "ListBlock",
    "TableBlock",
    "DelimiterBlock",
    "ImageBlock",
    "InnerLinkBlock",
    "OuterLinkBlock",
    "ColumnsBlock",
    "ExpandBlock",
    "AlertBlock",
]


def _sanitize(html: str) -> str:
    return bleach.clean(html, tags=['b', 'i', 'u', 'a', 'mark', 'code'], attributes=['class', 'data-placeholder', 'href'])


@dataclass
class EditorJsBlock:
    """
        A generic parsed Editor.js block
    """

    _data: dict
    """The raw JSON data of the entire block"""

    @property
    def id(self) -> t.Optional[str]:
        """
            Returns ID of the block, generated client-side.
        """

        return self._data.get("id", None)

    @property
    def type(self) -> t.Optional[str]:
        """
            Returns the type of the block.
        """

        return self._data.get("type", None)

    @property
    def data(self) -> dict:
        """
            Returns the actual block data.
        """

        return self._data.get("data", {})

    def html(self, sanitize: bool=False, service=None) -> str:
        """
            Returns the HTML representation of the block.

            ### Parameters:
            - `sanitize` - if `True`, then the block's text/contents will be sanitized.
        """

        raise NotImplementedError()


class HeaderBlock(EditorJsBlock):
    VALID_HEADER_LEVEL_RANGE = range(1, 7)
    """Valid range for header levels. Default is `range(1, 7)` - so, `0` - `6`."""

    @property
    def text(self) -> t.Optional[str]:
        """
            Returns the header's text.
        """

        return self.data.get("text", None)

    @property
    def level(self) -> int:
        """
            Returns the header's level (`0` - `6`).
        """

        _level = self.data.get("level", 1)

        if not isinstance(_level, int) or _level not in self.VALID_HEADER_LEVEL_RANGE:
            raise EditorJsParseError(f"`{_level}` is not a valid header level.")

        return _level

    def html(self, sanitize: bool=False, service=None) -> str:
        return rf'<h{self.level} class="cdx-block ce-header">{_sanitize(self.text) if sanitize else self.text}</h{self.level}>'


class ParagraphBlock(EditorJsBlock):
    @property
    def text(self) -> t.Optional[str]:
        """
            The text content of the paragraph.
        """

        return self.data.get("text", None)

    def html(self, sanitize: bool = False, service=None) -> str:
        _text = _sanitize(self.text) if sanitize else self.text
        if self.text == '':
            return rf'<p class="cdx-block ce-paragraph">{_text}</p><br/>'
        else:
            return rf'<p class="cdx-block ce-paragraph">{_text}</p>'


class ListBlock(EditorJsBlock):
    VALID_STYLES = ('unordered', 'ordered')
    """Valid list order styles."""

    @property
    def style(self) -> t.Optional[str]:
        """
            The style of the list. Can be `ordered` or `unordered`.
        """

        return self.data.get("style", None)

    @property
    def items(self) -> t.List[str]:
        """
            Returns the list's items, in raw format.
        """

        return self.data.get("items", [])

    def html(self, sanitize: bool=False, service=None) -> str:
        if self.style not in self.VALID_STYLES:
            raise EditorJsParseError(f"`{self.style}` is not a valid list style.")

        def content_from_item(item):
            content = ''
            if isinstance(item, str):
                content = _sanitize(item) if sanitize else item
            elif not isinstance(item, dict):
                raise ValueError("Expected 'string' or 'dict'")

            if 'content' in item:
                content = item['content']
                if sanitize:
                    content = _sanitize(content)

                nested_items = item.get('items', [])
                if len(nested_items) > 0:
                    data = {'style': self.style, **item}
                    nested_content = ListBlock(_data={'data': data}).html(sanitize)
                    content += nested_content

            return f"<li>{content}</li>"

        _items = [content_from_item(item) for item in self.items]
        _type = "ul" if self.style == "unordered" else "ol"
        _items_html = ''.join(_items)

        return rf'<{_type} class="cdx-block cdx-list cdx-list--{self.style}">{_items_html}</{_type}>'


class TableBlock(EditorJsBlock):
    @property
    def content(self) -> t.List[t.List[str]]:
        """
            Returns the list's items, in raw format.
        """

        return self.data.get("content", [])

    def html(self, sanitize: bool = False, service=None) -> str:
        rows = []
        for row in self.content:
            if row:
                val = [f"<td>{_sanitize(item) if sanitize else item}</td>" for item in row]
                val_html = f"<tr>{''.join(val)}</tr>"
                rows.append(val_html)

        if len(rows) == 0:
            return ''

        return f'<table class="cdx-block cdx-table"><tbody>{"".join(rows)}</tbody></table>'


class DelimiterBlock(EditorJsBlock):
    def html(self, sanitize: bool=False, service=None) -> str:
        return r'<div class="cdx-block ce-delimiter"></div>'


class InnerLinkBlock(EditorJsBlock):
    @property
    def href(self) -> str:
        return self.data.get('document_id', '')

    @property
    def text(self) -> t.Optional[str]:
        """
            The text content of the innerLink.
        """

        return self.data.get("text", None)

    def html(self, sanitize: bool=False, service=None) -> str:
        return rf'<div class="cdx-block ce-link"><a href="/{self.href}">{_sanitize(self.text) if sanitize else self.text}</a></div>'


class OuterLinkBlock(EditorJsBlock):
    @property
    def href(self) -> str:
        return self.data.get('href', '')

    @property
    def text(self) -> t.Optional[str]:
        """
            The text content of the innerLink.
        """

        return self.data.get("text", None)

    def html(self, sanitize: bool=False, service=None) -> str:
        return rf'<div class="cdx-block ce-link"><a href="{self.href}">{_sanitize(self.text) if sanitize else self.text}</a></div>'


class ColumnsBlock(EditorJsBlock):
    @property
    def cols(self) -> list[dict]:
        return self.data.get('cols', [])

    def html(self, sanitize: bool=False, service=None) -> str:
        cols_html = [service(content=x).html(sanitize) for x in self.cols]
        content = "\n".join(cols_html)
        return rf'<div class="cdx-block ce-cols">{content}</div>'


class ExpandBlock(EditorJsBlock):
    @property
    def title(self) -> str:
        return self.data.get('title', '')

    @property
    def content(self) -> list[dict]:
        return self.data.get('content', [])

    def html(self, sanitize: bool=False, service=None) -> str:
        data = {'blocks': self.content}
        htmls = [
            _sanitize(self.title) if sanitize else self.title,
            service(content=data).html(sanitize)
        ]
        content = "\n".join(htmls)
        return rf'<div class="cdx-block ce-expand">{content}</div><br/>'


class AlertBlock(EditorJsBlock):
    @property
    def blocks(self) -> list[dict]:
        return self.data.get('blocks', [])

    def html(self, sanitize: bool=False, service=None) -> str:
        data = {'blocks': self.blocks}
        content = service(content=data).html(sanitize)
        return rf'<div class="cdx-block ce-alert">{content}</div><br/>'


class ImageBlock(EditorJsBlock):
    @property
    def file_url(self) -> t.Optional[str]:
        """
            URL of the image file.
        """

        return self.data.get("file", {}).get("url", None)

    @property
    def caption(self) -> t.Optional[str]:
        """
            The image's caption.
        """

        return self.data.get("caption", 'Image')

    @property
    def with_border(self) -> bool:
        """
            Whether the image has a border.
        """

        return self.data.get("withBorder", False)

    @property
    def stretched(self) -> bool:
        """
            Whether the image is stretched.
        """

        return self.data.get("stretched", False)

    @property
    def with_background(self) -> bool:
        """
            Whether the image has a background.
        """

        return self.data.get("withBackground", False)

    def html(self, sanitize: bool=False, service=None) -> str:
        if self.file_url.startswith("data:image/"):
            _img = self.file_url
        else:
            _img = _sanitize(self.file_url) if sanitize else self.file_url

        _caption = _sanitize(self.caption) if sanitize else self.caption

        parts = [
            rf'<div class="cdx-block image-tool image-tool--filled {"image-tool--stretched" if self.stretched else ""} {"image-tool--withBorder" if self.with_border else ""} {"image-tool--withBackground" if self.with_background else ""}">'
            r'<div class="image-tool__image">',
            r'<div class="image-tool__image-preloader"></div>',
            rf'<img class="image-tool__image-picture" src="{_img}"/ alt="{_caption}">',
            r'</div>'
            rf'<div class="image-tool__caption" data-placeholder="{_caption}"></div>'
            r'</div>'
            r'</div>'
        ]

        return ''.join(parts)
