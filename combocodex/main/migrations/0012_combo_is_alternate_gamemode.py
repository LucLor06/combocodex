# Generated by Django 5.1.4 on 2025-02-01 22:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_alter_combo_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='combo',
            name='is_alternate_gamemode',
            field=models.BooleanField(default=False),
        ),
    ]
