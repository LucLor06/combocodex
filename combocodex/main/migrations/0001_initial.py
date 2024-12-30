# Generated by Django 5.1.4 on 2024-12-30 20:24

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Weapon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32)),
                ('order', models.PositiveIntegerField(unique=True)),
            ],
            options={
                'ordering': ['order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Legend',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32)),
                ('order', models.PositiveIntegerField(unique=True)),
                ('weapons', models.ManyToManyField(related_name='legends', to='main.weapon')),
            ],
            options={
                'ordering': ['order'],
                'abstract': False,
            },
        ),
    ]