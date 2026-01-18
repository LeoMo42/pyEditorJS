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
    VALID_STYLES = ('unordered', 'ordered', 'checklist')
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

                # Handle checklist checkbox
                if self.style == 'checklist':
                    checked = item.get('meta', {}).get('checked', False)
                    checkbox = f'<input type="checkbox" {"checked" if checked else ""} disabled> '
                    content = checkbox + content

                nested_items = item.get('items', [])
                if len(nested_items) > 0:
                    data = {'style': self.style, **item}
                    nested_content = ListBlock(_data={'data': data}).html(sanitize)
                    content += nested_content

            return f"<li>{content}</li>"

        _items = [content_from_item(item) for item in self.items]
        _type = "ul" if self.style in ("unordered", "checklist") else "ol"
        _items_html = ''.join(_items)

        return rf'<{_type} class="cdx-block cdx-list cdx-list--{self.style}">{_items_html}</{_type}>'


class TableBlock(EditorJsBlock):
    @property
    def content(self) -> t.List[t.List[str]]:
        """
            Returns the list's items, in raw format (old table format).
        """

        return self.data.get("content", [])

    @property
    def grid(self) -> t.List[t.List[str]]:
        """
            Returns the grid of cell IDs (new table format).
        """
        return self.data.get("grid", [])

    @property
    def merges(self) -> t.List[dict]:
        """
            Returns the list of merged cells info.
        """
        return self.data.get("merges", [])

    @property
    def cell_docs(self) -> dict:
        """
            Returns the cell documents (content for each cell).
        """
        return self.data.get("cellDocs", {})

    @property
    def cell_meta(self) -> dict:
        """
            Returns the cell metadata (styling, classes, etc).
        """
        return self.data.get("cellMeta", {})

    @property
    def column_widths(self) -> t.List[t.Optional[int]]:
        """
            Returns column widths.
        """
        return self.data.get("columnWidths", [])

    @property
    def row_heights(self) -> t.List[t.Optional[int]]:
        """
            Returns row heights.
        """
        return self.data.get("rowHeights", [])

    def _is_new_format(self) -> bool:
        """
            Check if this is the new table format (with grid) or old format (with content).
        """
        return "grid" in self.data

    def _render_old_format(self, sanitize: bool) -> str:
        """
            Render old table format (simple content array).
        """
        rows = []
        for row in self.content:
            if row:
                val = [f"<td>{_sanitize(item) if sanitize else item}</td>" for item in row]
                val_html = f"<tr>{''.join(val)}</tr>"
                rows.append(val_html)

        if len(rows) == 0:
            return ''

        return f'<table class="cdx-block cdx-table"><tbody>{"".join(rows)}</tbody></table>'

    def _render_new_format(self, sanitize: bool, service) -> str:
        """
            Render new table format (with grid, cellDocs, merges, etc).
        """
        if not self.grid:
            return ''

        # Build a map of merged cells
        merge_map = {}  # cell_id -> {rowspan, colspan}
        skip_cells = set()  # cell IDs that should be skipped (they're part of a merge)

        for merge in self.merges:
            anchor_id = merge.get("anchorCellId")
            rowspan = merge.get("rowspan", 1)
            colspan = merge.get("colspan", 1)
            merge_map[anchor_id] = {"rowspan": rowspan, "colspan": colspan}

            # Find the anchor cell position
            anchor_row = -1
            anchor_col = -1
            for r_idx, row in enumerate(self.grid):
                if anchor_id in row:
                    anchor_row = r_idx
                    anchor_col = row.index(anchor_id)
                    break

            # Mark cells that should be skipped
            if anchor_row >= 0 and anchor_col >= 0:
                for r in range(anchor_row, min(anchor_row + rowspan, len(self.grid))):
                    for c in range(anchor_col, min(anchor_col + colspan, len(self.grid[r]))):
                        if r != anchor_row or c != anchor_col:
                            cell_id = self.grid[r][c]
                            skip_cells.add(cell_id)

        # Build table HTML
        rows_html = []
        for row_idx, row in enumerate(self.grid):
            cells_html = []
            for col_idx, cell_id in enumerate(row):
                if cell_id in skip_cells:
                    continue

                # Get cell content
                cell_doc = self.cell_docs.get(cell_id, {})
                cell_blocks = cell_doc.get("blocks", [])

                if cell_blocks and service:
                    # Render nested blocks using service
                    cell_content = service(content={"blocks": cell_blocks}).html(sanitize)
                else:
                    cell_content = ""

                # Get cell styling
                meta = self.cell_meta.get(cell_id, {})
                classes = meta.get("classes", "")
                background = meta.get("background")
                borders = meta.get("borders", {})

                # Build cell style
                styles = []
                if background:
                    styles.append(f"background-color: {background}")

                if borders:
                    for side in ["top", "right", "bottom", "left"]:
                        if side in borders:
                            styles.append(f"border-{side}: 2px solid {borders[side]}")

                # Add column width if available
                if col_idx < len(self.column_widths) and self.column_widths[col_idx]:
                    styles.append(f"width: {self.column_widths[col_idx]}px")

                style_attr = f' style="{"; ".join(styles)}"' if styles else ""
                class_attr = f' class="{classes}"' if classes else ""

                # Check if this cell is merged
                merge_info = merge_map.get(cell_id)
                if merge_info:
                    rowspan_attr = f' rowspan="{merge_info["rowspan"]}"' if merge_info["rowspan"] > 1 else ""
                    colspan_attr = f' colspan="{merge_info["colspan"]}"' if merge_info["colspan"] > 1 else ""
                else:
                    rowspan_attr = ""
                    colspan_attr = ""

                cells_html.append(
                    f"<td{class_attr}{style_attr}{rowspan_attr}{colspan_attr}>{cell_content}</td>"
                )

            # Add row height if available
            row_style = ""
            if row_idx < len(self.row_heights) and self.row_heights[row_idx]:
                row_style = f' style="height: {self.row_heights[row_idx]}px"'

            rows_html.append(f"<tr{row_style}>{''.join(cells_html)}</tr>")

        return f'<table class="cdx-block cdx-table"><tbody>{"".join(rows_html)}</tbody></table>'

    def html(self, sanitize: bool = False, service=None) -> str:
        if self._is_new_format():
            return self._render_new_format(sanitize, service)
        else:
            return self._render_old_format(sanitize)


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

    def html(self, sanitize: bool = False, service=None) -> str:
        data = {'blocks': self.content}
        htmls = []
        if self.title:
            htmls.append(rf'<h3>{_sanitize(self.title) if sanitize else self.title}</h3>')

        htmls.append(service(content=data).html(sanitize))
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
