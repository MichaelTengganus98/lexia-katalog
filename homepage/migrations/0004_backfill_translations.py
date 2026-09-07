from django.db import migrations
from django.db.models import F, Q

FIELDS = ["title", "description"]


def backfill(apps, schema_editor):
    Model = apps.get_model("homepage", "Brochure")
    for f in FIELDS:
        ind = f + "_ind"
        (Model.objects
         .filter(Q(**{ind + "__isnull": True}) | Q(**{ind: ""}))
         .exclude(**{f + "__isnull": True})
         .update(**{ind: F(f)}))


class Migration(migrations.Migration):

    dependencies = [
        ("homepage", "0003_auto_20260907_1437"),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
