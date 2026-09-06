"""Seed example Brochure rows and example blog Posts (with generated cover art).
Idempotent-ish: skips creation when an object with the same title/slug exists.

Run (reads the file as UTF-8 so non-ASCII text survives on Windows):
    .venv/Scripts/python.exe manage.py shell -c "exec(open('scripts/seed_examples.py', encoding='utf-8').read())"
"""
import os
from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

from blog.models import Post
from homepage.models import Brochure
from page.models import Category

GRAPHITE = (27, 30, 34)
AMBER = (217, 164, 65)
PAPER = (241, 239, 232)


def _font(size):
    for path in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def cover(text, w=1200, h=800, sub=""):
    img = Image.new("RGB", (w, h), GRAPHITE)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 12], fill=AMBER)
    d.rectangle([0, h - 12, w, h], fill=AMBER)
    d.text((60, 60), "LEXIA MACHINERY", font=_font(34), fill=AMBER)
    # wrap the title crudely
    words, lines, cur = text.split(), [], ""
    f = _font(58)
    for wd in words:
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=f) > w - 120:
            lines.append(cur); cur = wd
        else:
            cur = t
    lines.append(cur)
    y = h // 2 - (len(lines) * 66) // 2
    for ln in lines:
        d.text((60, y), ln, font=f, fill=PAPER); y += 66
    if sub:
        d.text((60, h - 90), sub, font=_font(28), fill=AMBER)
    return img


def img_file(img, name, fmt="PNG"):
    buf = BytesIO()
    img.save(buf, format=fmt)
    return ContentFile(buf.getvalue(), name=name)


# ---- Brochures ---------------------------------------------------------------
BROCHURES = [
    ("Katalog Mesin Percetakan 2026",
     "Ringkasan seluruh lini mesin potong, laminating, dan jilid beserta spesifikasi utama."),
    ("Panduan Mesin Lem Binding Buku",
     "Perbandingan model 50R, 55H, 60R, dan F04: kapasitas, ketebalan, dan kebutuhan daya."),
    ("Brosur Mesin Laminating Kertas",
     "Seri 390 B, 520 A, dan 390AF Plus untuk kebutuhan finishing photocopy & percetakan."),
]
for i, (title, desc) in enumerate(BROCHURES, start=1):
    if Brochure.objects.filter(title=title).exists():
        print("brochure exists:", title); continue
    b = Brochure(title=title, description=desc, order=i, is_active=True)
    b.picture.save("brosur-%d.png" % i, img_file(cover(title, 1200, 900, "Brosur PDF"), "brosur-%d.png" % i), save=False)
    b.file.save("brosur-%d.pdf" % i, img_file(cover(title, 1240, 1754, "www.lexia.co.id"), "brosur-%d.pdf" % i, "PDF"), save=False)
    b.save()
    print("created brochure:", title)


# ---- Blog posts -----------------------------------------------------------
User = get_user_model()
author = User.objects.filter(is_superuser=True).order_by("pk").first()


def cat(name):
    return Category.objects.filter(jenis__icontains=name).first()


POSTS = [
    {
        "title": "Cara Memilih Mesin Potong Kertas untuk Percetakan",
        "slug": "cara-memilih-mesin-potong-kertas",
        "excerpt": ("Panduan singkat memilih mesin potong kertas: dari kapasitas ketebalan, "
                    "lebar potong, sistem pengaman, hingga jenis penggerak."),
        "category": "Potong Kertas",
        "body": """
<p>Mesin potong kertas adalah investasi inti bagi hampir semua usaha percetakan dan photocopy center.
Memilih model yang tepat sejak awal akan menghemat biaya operasional dan mengurangi risiko produk cacat.</p>

<h2>1. Tentukan lebar dan ketebalan potong</h2>
<p>Ukur pekerjaan terbesar yang biasa Anda tangani. Untuk kertas A3&ndash;Double Folio, lebar potong
minimal 460&nbsp;mm sudah memadai. Ketebalan potong 60&nbsp;mm cukup untuk mayoritas nota dan buku,
sementara produksi buku tebal membutuhkan 80&nbsp;mm ke atas.</p>

<h2>2. Perhatikan sistem pengaman</h2>
<p>Model modern memakai sensor fotoelektrik ganda yang menghentikan pisau begitu ada objek di area potong.
Fitur ini wajib bila mesin dioperasikan bergantian oleh beberapa staf.</p>

<h2>3. Semi-otomatis atau hidraulik?</h2>
<ul>
  <li><strong>Semi-otomatis</strong> &mdash; ukuran diatur manual, pemotongan otomatis. Ekonomis untuk volume kecil&ndash;menengah.</li>
  <li><strong>Hidraulik</strong> &mdash; tekanan dan potong bertenaga hidraulik, hasil lebih presisi dan konsisten untuk volume tinggi.</li>
</ul>

<h2>4. Layar dan kemudahan operasi</h2>
<p>Layar sentuh 7&Prime;&ndash;10&Prime; mempercepat setting ukuran berulang dan mengurangi kebutuhan pelatihan.</p>

<blockquote>Butuh rekomendasi model spesifik untuk kapasitas produksi Anda? Hubungi tim kami untuk konsultasi gratis.</blockquote>
""",
    },
    {
        "title": "Lem Panas vs Jahit Kawat: Mana yang Tepat untuk Buku Anda?",
        "slug": "lem-panas-vs-jahit-kawat",
        "excerpt": ("Dua metode penjilidan paling umum di percetakan Indonesia. Kenali kelebihan, "
                    "batasan, dan biaya masing-masing sebelum membeli mesin."),
        "category": "Lem Binding Buku",
        "body": """
<p>Saat menyiapkan lini penjilidan, dua pilihan pertama yang muncul biasanya adalah <em>binding lem panas</em>
(perfect binding) dan <em>jahit kawat</em> (saddle / side stitching). Keduanya menyelesaikan masalah berbeda.</p>

<h2>Binding lem panas</h2>
<p>Punggung buku dikikis lalu direkatkan dengan lem <em>hot melt</em>. Cocok untuk buku tebal tanpa batas
halaman praktis &mdash; skripsi, laporan tahunan, modul, majalah tebal. Hasil rapi dengan punggung rata
yang bisa dicetak judul.</p>
<ul>
  <li>Kelebihan: tampilan profesional, kapasitas halaman besar, punggung bisa dicetak.</li>
  <li>Batasan: perlu waktu pemanasan awal, buku sangat tipis kurang ideal.</li>
</ul>

<h2>Jahit kawat</h2>
<p>Lembaran disatukan dengan kawat menggunakan kepala Hohner. Ideal untuk booklet, buku tulis, dan majalah
tipis hingga sekitar 5&nbsp;mm.</p>
<ul>
  <li>Kelebihan: cepat, murah per unit, tidak perlu pemanasan.</li>
  <li>Batasan: terbatas pada ketebalan tipis, punggung tidak rata.</li>
</ul>

<h2>Rekomendasi singkat</h2>
<p>Percetakan yang melayani skripsi dan laporan sebaiknya memulai dengan mesin lem binding.
Jika pekerjaan Anda didominasi booklet dan buku tulis, mesin jahit kawat lebih hemat.
Banyak percetakan pada akhirnya memiliki keduanya.</p>
""",
    },
]

for i, p in enumerate(POSTS, start=1):
    if Post.objects.filter(slug=p["slug"]).exists():
        print("post exists:", p["slug"]); continue
    post = Post(
        title=p["title"], slug=p["slug"], excerpt=p["excerpt"], body=p["body"].strip(),
        status=Post.PUBLISHED, author=author, related_category=cat(p["category"]),
    )
    post.cover_image.save(
        "%s.png" % p["slug"],
        img_file(cover(p["title"], 1200, 675, "Blog Lexia Machinery"), "%s.png" % p["slug"]),
        save=False,
    )
    post.save()
    print("created post:", p["slug"], "| category:", post.related_category)

print("\nBrochures:", Brochure.objects.count(), "| Posts published:", Post.published.count())
