"""
Renderer: turns a set of fetched Sections + a subscriber's preferences into a
finished HTML email.

Per-subscriber logic lives here: we loop the subscriber's enabled modules in
registry order and render only those, skipping the rest. Core modules always
appear. Failed sections show a quiet "unavailable today" line rather than
breaking layout.

Design: warm editorial broadsheet feel. Serif display headline, clean sans body,
DC-flag-red accent, generous spacing. Inline styles only, because email clients
strip <style> blocks and external CSS. This is the morning object you actually
read, so it should feel like a publication, not a script output.
"""

import datetime
from config import MODULE_REGISTRY, PHYSICAL_ADDRESS, SENDER_NAME

RED = "#cf2027"        # DC flag red
INK = "#1a1a1a"
MUTE = "#6b6b6b"
LINE = "#e3e0d8"
PAPER = "#faf8f3"

FONT_DISPLAY = "'Georgia', 'Times New Roman', serif"
FONT_BODY = "'Helvetica Neue', Helvetica, Arial, sans-serif"


def render_email(sections_by_id: dict, subscriber: dict) -> str:
    enabled = subscriber["modules"]
    today = datetime.date.today().strftime("%A, %B %-d, %Y")
    name = subscriber.get("name", "")

    blocks = []
    for module_id, meta in MODULE_REGISTRY.items():
        if not (meta["core"] or module_id in enabled):
            continue
        section = sections_by_id.get(module_id)
        if section is None:
            continue
        blocks.append(_render_section(section, meta["title"]))

    body = "\n".join(blocks)

    return f"""\
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:{PAPER};">
  <div style="max-width:600px;margin:0 auto;background:{PAPER};
              font-family:{FONT_BODY};color:{INK};">

    <div style="padding:32px 28px 18px;border-bottom:3px double {INK};">
      <div style="font-family:{FONT_BODY};font-size:11px;letter-spacing:3px;
                  text-transform:uppercase;color:{RED};font-weight:700;">
        {SENDER_NAME}
      </div>
      <div style="font-family:{FONT_DISPLAY};font-size:34px;font-weight:700;
                  line-height:1.05;margin:6px 0 2px;">
        Good morning{', ' + name if name else ''}.
      </div>
      <div style="font-size:12px;color:{MUTE};letter-spacing:1px;">
        {today} &nbsp;&middot;&nbsp; Washington, DC
      </div>
    </div>

    <div style="padding:8px 28px 28px;">
      {body}
    </div>

    <div style="padding:20px 28px;border-top:1px solid {LINE};
                font-size:11px;color:{MUTE};line-height:1.6;">
      You're getting this because you asked to.
      <a href="{{{{unsubscribe}}}}" style="color:{MUTE};">Unsubscribe</a>.<br>
      {PHYSICAL_ADDRESS}
    </div>

  </div>
</body>
</html>"""


def _render_section(section, fallback_title) -> str:
    title = section.title or fallback_title
    header = f"""\
      <div style="font-family:{FONT_DISPLAY};font-size:13px;font-weight:700;
                  letter-spacing:2px;text-transform:uppercase;color:{RED};
                  margin:26px 0 10px;padding-bottom:6px;
                  border-bottom:1px solid {LINE};">{title}</div>"""

    if not section.ok:
        return header + f"""\
      <div style="font-size:14px;color:{MUTE};font-style:italic;
                  margin-bottom:8px;">{section.note or 'Unavailable today.'}</div>"""

    if not section.items:
        return header + f"""\
      <div style="font-size:14px;color:{MUTE};font-style:italic;
                  margin-bottom:8px;">Nothing new today.</div>"""

    rows = []
    for it in section.items:
        title_html = ""
        if it.title:
            if it.url:
                title_html = (f'<a href="{it.url}" style="color:{INK};'
                              f'text-decoration:none;font-weight:700;">{it.title}</a>')
            else:
                title_html = f'<span style="font-weight:700;">{it.title}</span>'
        # Recipe/history blurbs preserve line breaks; feed teasers are short.
        blurb_html = it.blurb.replace("\n", "<br>") if it.blurb else ""
        rows.append(f"""\
      <div style="margin:0 0 14px;font-size:15px;line-height:1.5;">
        {title_html}
        {('<div style="color:' + MUTE + ';font-size:14px;margin-top:2px;">' + blurb_html + '</div>') if blurb_html else ''}
      </div>""")
    return header + "\n".join(rows)
