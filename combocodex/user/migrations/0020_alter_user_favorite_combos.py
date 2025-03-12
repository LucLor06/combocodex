# Generated by Django 5.1.4 on 2025-03-10 22:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0018_alter_combo_guests_alter_combo_users_and_more"),
        ("user", "0019_user_theme_color_alter_user_user_theme"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="favorite_combos",
            field=models.ManyToManyField(
                blank=True,
                editable=False,
                related_name="favorite_users",
                to="main.combo",
            ),
        ),
    ]
