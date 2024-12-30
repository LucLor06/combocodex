from django.db import models

class AbstractModel(models.Model):
    name = models.CharField(max_length=32)
    order = models.PositiveIntegerField(unique=True)

    class Meta:
        abstract = True
        ordering = ['order']

    def __str__(self):
        return self.name
    
class Weapon(AbstractModel):
    ...

class Legend(AbstractModel):
    weapons = models.ManyToManyField('Weapon', related_name='legends')