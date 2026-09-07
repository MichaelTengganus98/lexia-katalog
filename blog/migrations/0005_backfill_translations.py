from django.db import migrations
from django.db.models import F, Q

FIELDS = ["title", "excerpt", "body", "cta_label",
          "meta_title", "meta_description"]


def backfill(apps, schema_editor):
    Model = apps.get_model("blog", "Post")
    for f in FIELDS:
        ind = f + "_ind"
        (Model.objects
         .filter(Q(**{ind + "__isnull": True}) | Q(**{ind: ""}))
         .exclude(**{f + "__isnull": True})
         .update(**{ind: F(f)}))


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0004_auto_20260907_1437"),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
