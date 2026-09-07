"""Rule-based SEO recommendations for the panel's "Isi dengan rekomendasi SEO"
button. Deterministic, offline, no API key — it just formats the content the
editor already typed into an ideal-length meta title + description. Output is
written into editable fields, so anything here is a starting point.

`lang` is "id" or "en"; values are read from the modeltranslation `_ind`/`_en`
columns with a fallback to the other language."""
import re

from item.templatetags.item_extras import specs

_STRIP_SUFFIXES = (" - lexia machinery", " - lexia", " – lexia", " — lexia", " | lexia")
_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_TAGS = re.compile(r"<[^>]+>")


def _squish(s):
    return " ".join((s or "").split())


def _val(obj, field, lang, fallback=True):
    """modeltranslation value for `field` in `lang`, falling back to the other."""
    prim = "en" if lang == "en" else "ind"
    alt = "ind" if prim == "en" else "en"
    v = _squish(getattr(obj, "%s_%s" % (field, prim), None) or "")
    if not v and fallback:
        v = _squish(getattr(obj, "%s_%s" % (field, alt), None) or "")
    return v


def _fit_title(s, limit=60):
    s = _squish(s)
    if len(s) <= limit:
        return s
    cut = s[:limit]
    sp = cut.rfind(" ")
    if sp > 40:
        cut = cut[:sp]
    return cut.rstrip(" -–—|,:;")


def _fit_desc(s, limit=160):
    s = _squish(_TAGS.sub(" ", s or ""))
    if len(s) <= limit:
        return s
    cut = s[:limit]
    sp = cut.rfind(" ")
    if sp > 90:
        cut = cut[:sp]
    return cut.rstrip(" -–—|,:;")


def _pick_title(candidates, base, limit=60):
    for c in candidates:
        c = _squish(c)
        if c and len(c) <= limit:
            return c
    return _fit_title(base, limit)


def _clean_name(name):
    n = _squish(name)
    low = n.lower()
    for suf in _STRIP_SUFFIXES:
        if low.endswith(suf):
            return n[: len(n) - len(suf)].strip(" -–—|")
    return n


def _spec_phrase(raw, n=2):
    pairs = specs(raw)[:n]
    return ", ".join("%s %s" % (k.strip().lower(), v.strip()) for k, v in pairs)


# --------------------------------------------------------------------------- #
def product_seo(item, lang):
    en = lang == "en"
    name = _clean_name(_val(item, "name", lang))
    cat = _val(item.Jenis, "jenis", lang)
    summary = _val(item, "summary", lang)
    desc = _val(item, "description", lang)
    spec_raw = _val(item, "specification", lang)

    if en:
        title_cands = ["%s — Price & Specifications" % name,
                       ("%s — %s" % (name, cat)) if cat else "",
                       "%s | Lexia Machinery" % name, name]
    else:
        title_cands = ["%s — Harga & Spesifikasi" % name,
                       ("%s — %s" % (name, cat)) if cat else "",
                       "%s | Lexia Machinery" % name, name]
    meta_title = _pick_title(title_cands, name)

    if len(summary) >= 40:
        meta_description = _fit_desc(summary)
    else:
        sp = _spec_phrase(spec_raw)
        first = _squish(_SENTENCE.split(_TAGS.sub(" ", desc))[0]) if desc else ""
        if en:
            if sp:
                body = ("%s — %s. Official Lexia Machinery distributor; ready stock "
                        "and free consultation." % (name, sp))
            elif first:
                body = "%s Contact Lexia Machinery for price and availability." % first
            else:
                body = ("%s from Lexia Machinery. Contact us for price, full "
                        "specifications, and availability." % name)
        else:
            if sp:
                body = ("%s — %s. Distributor resmi Lexia Machinery, stok siap kirim "
                        "& konsultasi gratis." % (name, sp))
            elif first:
                body = "%s Hubungi Lexia Machinery untuk harga dan ketersediaan." % first
            else:
                body = ("%s dari Lexia Machinery. Hubungi kami untuk harga, "
                        "spesifikasi lengkap, dan ketersediaan." % name)
        meta_description = _fit_desc(body)
    return {"meta_title": meta_title, "meta_description": meta_description}


def category_seo(cat, lang):
    en = lang == "en"
    jenis = _val(cat, "jenis", lang)
    intro = _val(cat, "intro", lang)
    count = cat.item_set.count()
    jl = jenis.lower()

    if en:
        title_cands = ["%s — Price & Specs" % jenis, "Buy %s | Lexia Machinery" % jenis,
                       "%s — Lexia Machinery" % jenis, jenis]
    else:
        title_cands = ["Jual %s — Harga & Spesifikasi" % jenis, "Jual %s | Lexia Machinery" % jenis,
                       "%s — Lexia Machinery" % jenis, jenis]
    meta_title = _pick_title(title_cands, jenis)

    if len(_TAGS.sub(" ", intro)) >= 50:
        meta_description = _fit_desc(intro)
    elif en:
        lead = ("Browse %d %s" % (count, jl)) if count else ("A range of %s" % jl)
        meta_description = _fit_desc("%s from Lexia Machinery — compare specifications and "
                                    "prices, ready stock, free consultation." % lead)
    else:
        lead = ("Daftar %d %s" % (count, jl)) if count else ("Pilihan %s" % jl)
        meta_description = _fit_desc("%s dari Lexia Machinery — bandingkan spesifikasi & "
                                    "harga, stok siap kirim, konsultasi gratis." % lead)
    return {"meta_title": meta_title, "meta_description": meta_description}


def post_seo(post, lang):
    title = _val(post, "title", lang)
    excerpt = _val(post, "excerpt", lang)
    body = _val(post, "body", lang)
    suffix = " | Blog Lexia"

    meta_title = _pick_title(["%s%s" % (title, suffix), title], title)
    if len(excerpt) >= 50:
        meta_description = _fit_desc(excerpt)
    elif body:
        meta_description = _fit_desc(body)
    else:
        meta_description = _fit_desc(title)
    return {"meta_title": meta_title, "meta_description": meta_description}


_DISPATCH = {"product": product_seo, "category": category_seo, "post": post_seo}


def suggest(kind, obj, lang):
    return _DISPATCH[kind](obj, "en" if lang == "en" else "id")
