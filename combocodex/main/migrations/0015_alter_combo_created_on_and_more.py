# Generated by Django 5.1.4 on 2025-03-09 05:58

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_alter_combo_poster'),
    ]

    operations = [
        migrations.AlterField(
            model_name='combo',
            name='created_on',
            field=models.DateField(default=datetime.datetime(2025, 3, 9, 0, 58, 7, 961281)),
        ),
        migrations.AlterField(
            model_name='dailychallenge',
            name='created_on',
            field=models.DateField(default=datetime.datetime(2025, 3, 9, 0, 58, 7, 963784)),
        ),
        migrations.AlterField(
            model_name='request',
            name='created_on',
            field=models.DateField(default=datetime.datetime(2025, 3, 9, 0, 58, 7, 962281)),
        ),
    ]
