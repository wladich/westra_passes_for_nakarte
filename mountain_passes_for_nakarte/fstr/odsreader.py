# coding: utf-8
import typing
import xml.dom
from functools import cached_property

import odf.opendocument  # type: ignore[import-untyped]
from odf.element import Element  # type: ignore[import-untyped]
from odf.table import CoveredTableCell, Table, TableCell, TableRow  # type: ignore[import-untyped]
from odf.text import A, P, Span  # type: ignore[import-untyped]


def find_last_non_emtpy_cell_index(cells: list[Element]) -> int:  # type: ignore[no-any-unimported]
    for i in range(len(cells) - 1, -1, -1):
        if cells[i].hasChildNodes():
            return i
    return -1


def get_paragraph_text(paragraph: Element) -> str:  # type: ignore[no-any-unimported]
    text_parts = []
    for child in paragraph.childNodes:
        if child.nodeType == xml.dom.Node.TEXT_NODE:
            text_parts.append(child.data)
        elif child.nodeType == xml.dom.Node.ELEMENT_NODE:
            assert any(child.isInstanceOf(t) for t in [Span, A])
            text_parts.append(get_paragraph_text(child))
    return "".join(text_parts)


def get_cell_text(cell: Element) -> str:  # type: ignore[no-any-unimported]
    lines = []
    for child in cell.childNodes:
        assert child.nodeType == xml.dom.Node.ELEMENT_NODE, child.nodeType
        if child.isInstanceOf(P):
            lines.append(get_paragraph_text(child))
    return "\n".join(lines)


class OdsTable:
    def __init__(self, table_file: str | typing.BinaryIO):
        self.doc = odf.opendocument.load(table_file)
        self.sheets = self.doc.spreadsheet.getElementsByType(Table)

    @cached_property
    def sheet_names(self) -> list[str]:
        return [sheet.getAttribute("name") for sheet in self.sheets]

    def get_sheet_values(self, sheet_index: int) -> list[list[str]]:
        # pylint: disable=too-many-locals,too-many-branches
        sheet = self.sheets[sheet_index]
        rows = sheet.getElementsByType(TableRow)
        rows_values: list[list[str]] = []
        row_spans = []
        max_cells_in_row = 0
        for row in rows:
            cells_values: list[str] = []
            row_cells = row.childNodes
            col_count = find_last_non_emtpy_cell_index(row_cells)
            for cell in row_cells[: col_count + 1]:
                assert cell.nodeType == xml.dom.Node.ELEMENT_NODE

                columns_repeated_attr = cell.getAttribute("numbercolumnsrepeated")
                if columns_repeated_attr is None:
                    columns_repeated = 1
                else:
                    columns_repeated = int(columns_repeated_attr)

                if cell.isInstanceOf(TableCell):
                    cell_value = get_cell_text(cell)

                    rows_spanned_attr = cell.getAttribute("numberrowsspanned")
                    cols_spanned_attr = cell.getAttribute("numbercolumnsspanned")
                    if rows_spanned_attr:
                        rows_spanned = int(rows_spanned_attr)
                        if rows_spanned > 1:
                            assert cols_spanned_attr == "1"
                            row_spans.append(
                                (len(rows_values), len(cells_values), rows_spanned)
                            )
                elif cell.isInstanceOf(CoveredTableCell):
                    cell_value = ""
                else:
                    raise ValueError(f"Unexpected element type in row: {cell.qname}")
                cells_values += [cell_value] * int(columns_repeated)
            max_cells_in_row = max(max_cells_in_row, len(cells_values))
            rows_values.append(cells_values)

        while rows_values and not rows_values[-1]:
            rows_values.pop()
        for row in rows_values:
            if len(row) < max_cells_in_row:
                row += [""] * (max_cells_in_row - len(row))

        # This is risky, the line with covered cell at the bottom of the table could be removed
        for row_index, col_index, row_span_count in row_spans:
            cell_value = rows_values[row_index][col_index]
            for i in range(1, row_span_count):
                assert rows_values[row_index + i][col_index] == ""
                rows_values[row_index + i][col_index] = cell_value

        return rows_values
