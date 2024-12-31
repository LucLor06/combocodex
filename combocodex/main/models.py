from django.db import models
from config.settings import STATIC_ROOT
from django.utils.text import slugify


class AbstractModel(models.Model):
    name = models.CharField(max_length=32)
    slug = models.SlugField(blank=True, editable=False)
    order = models.PositiveIntegerField(unique=True)

    class Meta:
        abstract = True
        ordering = ['order']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Weapon(AbstractModel):
    def icon(self):
        return f'{STATIC_ROOT}weapons/{self.slug}.png'


class Legend(AbstractModel):
    weapons = models.ManyToManyField('Weapon', related_name='legends')

    def icon(self):
        return f'{STATIC_ROOT}legends/{self.slug}.png'
    

class Guest(models.Model):
    username = models.CharField(max_length=32)
