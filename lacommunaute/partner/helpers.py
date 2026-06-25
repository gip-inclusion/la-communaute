import glob
import pathlib

import frontmatter
import markdown
from django.utils.safestring import mark_safe


def parse_partners():
    partners = {}
    filenames = glob.glob(r"lacommunaute/partner/data/*.md")
    for filename in filenames:
        obj = frontmatter.load(filename)
        partner = obj.metadata
        partner["html"] = mark_safe(markdown.markdown(obj.content, extensions=["nl2br"]))
        partner["slug"] = pathlib.Path(filename).stem
        partner["image"] = f"images/documentation/{partner['image']}"
        partners[partner["slug"]] = partner
    return {k: v for k, v in sorted(partners.items(), key=lambda item: item[1]["name"])}


PARTNERS = parse_partners()
