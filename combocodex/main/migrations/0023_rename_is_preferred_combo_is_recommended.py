# Generated by Django 5.1.4 on 2025-03-15 06:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0022_alter_combo_options_alter_combo_daily_challenge_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="combo",
            old_name="is_preferred",
            new_name="is_recommended",
        ),
    ]
