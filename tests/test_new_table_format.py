"""
Test for new table format with grid, cellDocs, merges, etc.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for direct script execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyeditorjs.parser import EditorJsParserVv


def test_new_table_with_grid():
    """
    Test new table format with grid structure, merged cells, cell metadata, and nested blocks.
    """
    table_data = {
        "time": 1672531200000,
        "blocks": [
            {
                "id": "new-table-grid-test",
                "type": "table",
                "data": {
                    "grid": [
                        ["cell-1-1", "cell-1-2", "cell-1-3"],
                        ["cell-2-1", "cell-2-2", "cell-2-3"],
                        ["cell-3-1", "cell-3-2", "cell-3-3"]
                    ],
                    "merges": [
                        {
                            "anchorCellId": "cell-1-1",
                            "rowspan": 1,
                            "colspan": 2
                        }
                    ],
                    "columnWidths": [150, 150, 200],
                    "rowHeights": [None, 80, None],
                    "cellDocs": {
                        "cell-1-3": {
                            "blocks": [
                                {
                                    "type": "header",
                                    "data": {
                                        "text": "Header in cell",
                                        "level": 4
                                    }
                                }
                            ]
                        },
                        "cell-2-1": {
                            "blocks": [
                                {
                                    "type": "list",
                                    "data": {
                                        "style": "checklist",
                                        "items": [
                                            {
                                                "content": "Task 1",
                                                "meta": {"checked": True},
                                                "items": []
                                            },
                                            {
                                                "content": "Task 2",
                                                "meta": {"checked": False},
                                                "items": []
                                            }
                                        ]
                                    }
                                }
                            ]
                        },
                        "cell-2-2": {
                            "blocks": [
                                {
                                    "type": "paragraph",
                                    "data": {
                                        "text": "Cell with <b>bold</b> text"
                                    }
                                }
                            ]
                        }
                    },
                    "cellMeta": {
                        "cell-1-1": {
                            "classes": "header-cell"
                        },
                        "cell-2-2": {
                            "classes": "highlighted-cell",
                            "background": "#fff3cd"
                        },
                        "cell-2-3": {
                            "classes": "bordered-cell",
                            "borders": {
                                "top": "#dc3545",
                                "right": "#dc3545",
                                "bottom": "#dc3545",
                                "left": "#dc3545"
                            }
                        }
                    }
                }
            }
        ],
        "version": "2.31.0-rc.7"
    }

    parser = EditorJsParserVv(content=table_data)
    html = parser.html(sanitize=False)

    # Check for table element
    if '<table class="cdx-block cdx-table">' not in html:
        print("ERROR: Table element not found in HTML!")
        print("Generated HTML:")
        print(html)
        print("\n" + "="*60 + "\n")

    assert '<table class="cdx-block cdx-table">' in html

    # Check for merged cell with colspan
    assert 'colspan="2"' in html

    # Check for cell background color
    assert 'background-color: #fff3cd' in html

    # Check for cell borders
    assert 'border-top: 2px solid #dc3545' in html
    assert 'border-right: 2px solid #dc3545' in html

    # Check for nested header in cell
    assert '<h4 class="cdx-block ce-header">Header in cell</h4>' in html

    # Check for nested checklist in cell
    assert '<ul class="cdx-block cdx-list cdx-list--checklist">' in html
    assert '<input type="checkbox" checked disabled>' in html
    assert '<input type="checkbox"  disabled>' in html

    # Check for nested paragraph in cell
    assert '<p class="cdx-block ce-paragraph">Cell with <b>bold</b> text</p>' in html

    # Check for CSS classes
    assert 'class="header-cell"' in html
    assert 'class="highlighted-cell"' in html
    assert 'class="bordered-cell"' in html

    # Check for column widths
    assert 'width: 150px' in html
    assert 'width: 200px' in html

    # Check for row height
    assert 'height: 80px' in html

    print("✓ All new table format tests passed!")
    return html


def test_old_table_format_compatibility():
    """
    Test that old table format (simple content array) still works.
    """
    old_table_data = {
        "time": 1672531200000,
        "blocks": [
            {
                "id": "old-table-test",
                "type": "table",
                "data": {
                    "withHeadings": False,
                    "content": [
                        ["row 1 col 1", "row 1 col 2", "row 1 col 3"],
                        ["row 2 col 1", "row 2 col 2", "row 2 col 3"]
                    ]
                }
            }
        ],
        "version": "2.24.3"
    }

    parser = EditorJsParserVv(content=old_table_data)
    html = parser.html(sanitize=False)

    # Check for table element
    assert '<table class="cdx-block cdx-table">' in html

    # Check for content
    assert 'row 1 col 1' in html
    assert 'row 2 col 2' in html

    print("✓ Old table format compatibility test passed!")
    return html


def test_combined_example():
    """
    Test the combined example from example.json to ensure both formats work together.
    """
    example_path = Path(__file__).parent / 'example.json'
    if not example_path.exists():
        print("⚠ example.json not found, skipping combined test")
        return

    example_data = json.loads(example_path.read_text(encoding='utf-8'))
    parser = EditorJsParserVv(content=example_data)
    html = parser.html(sanitize=True)

    # Should contain both old and new format tables
    assert html.count('<table class="cdx-block cdx-table">') >= 2

    # Write output for inspection
    output_path = Path(__file__).parent / 'example_with_new_table.html'
    output_path.write_text(html + '\n', encoding='utf-8')

    print(f"✓ Combined example test passed! Output written to {output_path}")
    return html


if __name__ == '__main__':
    print("Running new table format tests...\n")

    print("1. Testing new table format with grid...")
    test_new_table_with_grid()
    print()

    print("2. Testing old table format compatibility...")
    test_old_table_format_compatibility()
    print()

    print("3. Testing combined example...")
    test_combined_example()
    print()

    print("=" * 60)
    print("All tests completed successfully!")
