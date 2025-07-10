import json

from pathlib import Path
from markdownify import markdownify as md
from pyeditorjs.parser import EditorJsParserVv

EXAMPLE_JSON = json.loads((Path(__file__).parent / 'example2.json').read_text(encoding='utf-8'))
PARSER = EditorJsParserVv(content=EXAMPLE_JSON)


def test_parser():
    """
        Tests HTML rendering.
    """

    html = PARSER.html(True)

    print(html)
#     assert html == """<h1 class="cdx-block ce-header">Editor.js</h1>
# <p class="cdx-block ce-paragraph">Hey. Meet the new Editor. On this page you can see it in action — try to edit this text.</p>
# <h3 class="cdx-block ce-header">Key features</h3>
# <ul class="cdx-block cdx-list cdx-list--unordered"><li>{'content': 'It is a block-styled editor'}</li><li>{'content': 'It returns clean data output in JSON'}</li><li>{'content': 'Designed to be extendable and pluggable with a simple API', 'items': [{'content': "nested item on 'Designed to be extendable and pluggable with a simple API'"}, {'content': "nested item2 on 'Designed to be extendable and pluggable with a simple API'"}]}</li></ul>
# <h3 class="cdx-block ce-header">What does it mean «block-styled editor»</h3>
# <p class="cdx-block ce-paragraph">Workspace in classic editors is made of a single contenteditable element, used to create different HTML markups. Editor.js <mark class="cdx-marker">workspace consists of separate Blocks: paragraphs, headings, images, lists, quotes, etc</mark>. Each of them is an independent contenteditable element (or more complex structure) provided by Plugin and united by Editor's Core.</p>
# <p class="cdx-block ce-paragraph">There are dozens of <a href="https://github.com/editor-js">ready-to-use Blocks</a> and the <a href="https://editorjs.io/creating-a-block-tool">simple API</a> for creation any Block you need. For example, you can implement Blocks for Tweets, Instagram posts, surveys and polls, CTA-buttons and even games.</p>
# <h3 class="cdx-block ce-header">What does it mean clean data output</h3>
# <p class="cdx-block ce-paragraph">Classic WYSIWYG-editors produce raw HTML-markup with both content data and content appearance. On the contrary, Editor.js outputs JSON object with data of each Block. You can see an example below</p>
# <p class="cdx-block ce-paragraph">Given data can be used as you want: render with HTML for <code class="inline-code">Web clients</code>, render natively for <code class="inline-code">mobile apps</code>, create markup for <code class="inline-code">Facebook Instant Articles</code> or <code class="inline-code">Google AMP</code>, generate an <code class="inline-code">audio version</code> and so on.</p>
# <p class="cdx-block ce-paragraph">Clean data is useful to sanitize, validate and process on the backend.</p>
# <div class="cdx-block ce-delimiter"></div>
# <p class="cdx-block ce-paragraph">We have been working on this project more than three years. <script>document.write('AHAHAHAHA INJECTION')</script> Several large media projects help us to test and debug the Editor, to make it's core more stable. At the same time we significantly improved the API. Now, it can be used to create any plugin for any task. Hope you enjoy. 😏</p>
# <div class="cdx-block image-tool image-tool--filled   "><div class="image-tool__image"><div class="image-tool__image-preloader"></div><img class="image-tool__image-picture" src="https://codex.so/public/app/img/external/codex2x.png"/></div><div class="image-tool__caption" data-placeholder="Caption"></div></div></div>
# <table class="cdx-block cdx-table"><tbody><tr><td>row 1 column 1</td><td>row 1 column 2</td><td>row 1 column 3</td></tr><tr><td></td><td>row 2 column 2</td><td></td></tr></tbody></table>
# """
    (Path(__file__).parent / 'example2.html').write_text(html + '\n', encoding='utf-8')


    # parser = EditorJsParserVv({'blocks': blocks})
    # html = parser.html()
    data = md(html, heading_style='ATX')
    data = data.replace('\n\n', '\n')
    print(data)


def test_extra():
    """
        Obtains text only from the blocks.

        WARNING: This does not sanitize the texts.
    """

    all_texts = []

    for block in PARSER:
        text = getattr(block, 'text', None)
        if text:
            all_texts.append(text)

    # print(all_texts)


if __name__ == '__main__':
    test_parser()
    test_extra()
