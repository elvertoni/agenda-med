import re

from django.db import migrations


def normalize_existing(apps, schema_editor):
    PatientProfile = apps.get_model('accounts', 'PatientProfile')
    for profile in PatientProfile.objects.all():
        normalized = re.sub(r'\D', '', profile.whatsapp_number or '')
        if normalized != profile.whatsapp_number:
            profile.whatsapp_number = normalized
            profile.save(update_fields=['whatsapp_number'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(normalize_existing, migrations.RunPython.noop),
    ]
