# Generated by Django 5.1.4 on 2025-03-15 03:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0020_alter_guest_username'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='combo',
            options={'ordering': ['is_preferred', '-id']},
        ),
        migrations.AddField(
            model_name='combo',
            name='is_preferred',
            field=models.BooleanField(default=False),
        ),
    ]
