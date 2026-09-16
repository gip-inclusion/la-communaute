import re
from itertools import chain

from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter


def remove_static_hash(content):
    return re.sub(r"\.[\da-f]{12}\.(svg|png|jpg|pdf)\b", r".\1", content)


def parse_response(response, selector=None, replace_img_src=False):
    soup = BeautifulSoup(response.content, "html.parser", from_encoding=response.charset or "utf-8")
    if selector is not None:
        [soup] = soup.select(selector)
    for csrf_token_input in soup.find_all("input", attrs={"name": "csrfmiddlewaretoken"}):
        csrf_token_input["value"] = "NORMALIZED_CSRF_TOKEN"
    if "nonce" in soup.attrs:
        soup["nonce"] = "NORMALIZED_CSP_NONCE"
    for csp_nonce_script in soup.find_all("script", {"nonce": True}):
        csp_nonce_script["nonce"] = "NORMALIZED_CSP_NONCE"
    for img in chain(
        soup.find_all("img", attrs={"src": True}), soup.find_all("input", attrs={"type": "image", "src": True})
    ):
        img["src"] = remove_static_hash(img["src"])
    if replace_img_src:
        for attr in ["src"]:
            for links in soup.find_all("img", attrs={attr: True}):
                links.attrs.update({attr: "[img src]"})
    return soup.prettify(formatter=HTMLFormatter(indent=4))
