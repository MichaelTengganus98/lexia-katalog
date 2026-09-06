"""Helpers that build schema.org JSON-LD dicts for pages. Views assemble a list
of these and pass ``json.dumps(...)`` to the template, so no template-side JSON
escaping is needed."""
import json


AVAILABILITY_URL = {
    "InStock": "https://schema.org/InStock",
    "PreOrder": "https://schema.org/PreOrder",
    "OutOfStock": "https://schema.org/OutOfStock",
    "Discontinued": "https://schema.org/Discontinued",
}


def _abs(request, path):
    return request.build_absolute_uri(path)


def breadcrumb(request, crumbs):
    """crumbs: list of (name, path-or-None). Last item usually has no path."""
    items = []
    for i, (name, path) in enumerate(crumbs, start=1):
        entry = {"@type": "ListItem", "position": i, "name": name}
        if path:
            entry["item"] = _abs(request, path)
        items.append(entry)
    return {"@type": "BreadcrumbList", "itemListElement": items}


def product(request, item, spec):
    data = {
        "@type": "Product",
        "name": item.name,
        "url": _abs(request, item.get_absolute_url()),
        "image": [_abs(request, p.url) for p in item.images],
        "description": item.seo_description,
        "brand": {"@type": "Brand", "name": item.brand or "Lexia"},
        "category": item.Jenis.jenis,
    }
    if item.model_code:
        data["sku"] = item.model_code
        data["mpn"] = item.model_code
    if spec:
        data["additionalProperty"] = [
            {"@type": "PropertyValue", "name": k, "value": v} for k, v in spec.items()
        ]
    if item.price and not item.price_on_request:
        data["offers"] = {
            "@type": "Offer",
            "url": _abs(request, item.get_absolute_url()),
            "priceCurrency": "IDR",
            "price": str(item.price),
            "availability": AVAILABILITY_URL.get(item.availability, AVAILABILITY_URL["InStock"]),
            "seller": {"@type": "Organization", "name": "Lexia Machinery"},
        }
    return data


def local_business(request, site):
    data = {
        "@type": "LocalBusiness",
        "name": site.site_name,
        "url": _abs(request, "/"),
        "image": _abs(request, "/static/img/logo-lexia-machinery.png"),
        "address": {
            "@type": "PostalAddress",
            "streetAddress": site.address,
            "addressLocality": site.city,
            "addressRegion": site.region,
            "postalCode": site.postal_code,
            "addressCountry": site.country,
        },
    }
    if site.phone_primary:
        data["telephone"] = site.phone_primary
    if site.opening_hours:
        data["openingHours"] = site.opening_hours
    if site.latitude and site.longitude:
        data["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": site.latitude,
            "longitude": site.longitude,
        }
    sameas = [u for u in (site.facebook_url, site.instagram_url,
                          site.youtube_url, site.tokopedia_url) if u]
    if sameas:
        data["sameAs"] = sameas
    return data


def blog_posting(request, post):
    data = {
        "@type": "BlogPosting",
        "headline": post.title,
        "description": post.seo_description,
        "url": _abs(request, post.get_absolute_url()),
        "mainEntityOfPage": _abs(request, post.get_absolute_url()),
        "inLanguage": "id-ID",
        "publisher": {
            "@type": "Organization",
            "name": "Lexia Machinery",
            "logo": {
                "@type": "ImageObject",
                "url": _abs(request, "/static/img/logo-lexia-machinery.png"),
            },
        },
    }
    if post.cover_image:
        data["image"] = _abs(request, post.cover_image.url)
    if post.published_at:
        data["datePublished"] = post.published_at.isoformat()
    if post.updated:
        data["dateModified"] = post.updated.isoformat()
    if post.author and post.author.get_full_name():
        data["author"] = {"@type": "Person", "name": post.author.get_full_name()}
    else:
        data["author"] = {"@type": "Organization", "name": "Lexia Machinery"}
    return data


def graph(request, *nodes):
    return json.dumps(
        {"@context": "https://schema.org", "@graph": [n for n in nodes if n]},
        ensure_ascii=False,
    )
