from django.db import migrations
from django.db.models import F, Q

FIELDS = ["tagline", "default_meta_description",
          "home_kicker", "home_headline", "home_lead",
          "about_headline", "about_body", "contact_intro"]


def backfill(apps, schema_editor):
    Model = apps.get_model("seo", "SiteSettings")
    for f in FIELDS:
        ind = f + "_ind"
        (Model.objects
         .filter(Q(**{ind + "__isnull": True}) | Q(**{ind: ""}))
         .exclude(**{f + "__isnull": True})
         .update(**{ind: F(f)}))


class Migration(migrations.Migration):

    dependencies = [
        ("seo", "0003_auto_20260907_1437"),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
