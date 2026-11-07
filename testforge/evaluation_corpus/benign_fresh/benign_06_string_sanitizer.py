import html

def escape_user_html(raw_content: str) -> str:
    if not raw_content:
        return ''
    return html.escape(raw_content, quote=True)
