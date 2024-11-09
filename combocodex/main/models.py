from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models import F
from django.http import HttpRequest
from django.utils.text import slugify
from django.utils.functional import cached_property
from config.settings import STATIC_URL
import uuid

class User(AbstractUser):
    discord_id = models.CharField(blank=True, null=True, max_length=64)
    codex_coins = models.IntegerField(default=0)

class AbstractBaseModel(models.Model):
    name = models.CharField(max_length=64)

    def slug_name(self):
        return slugify(self.name)

    @cached_property
    def icon(self):
        return f'/{STATIC_URL}icons/{self.__class__.__name__.lower()}s/{self.slug_name()}.png'

    def __str__(self) -> str:
        return self.name
    
    class Meta:
        abstract = True
        

class Guest(AbstractBaseModel):
    ...
    

class Weapon(AbstractBaseModel):
    ...


class Legend(AbstractBaseModel):
    weapons = models.ManyToManyField('Weapon', related_name='legends')

class LegendWeaponPair(models.Model):
    legend = models.ForeignKey('Legend', related_name='pairs', on_delete=models.CASCADE)
    weapon = models.ForeignKey('Weapon', related_name='pairs', on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f'{self.legend.name} - {self.weapon.name}'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['legend', 'weapon'], name='legend_weapon_unique')
        ]

ACCEPTED_VIDEO_FORMATS = ['mp4', 'mov']

def upload_to_combo(instance: "Combo", filename: str) -> str:
    ext = filename.split('.')[-1]
    if ext not in ACCEPTED_VIDEO_FORMATS:
        raise ValidationError(f'Incorrect file format. Must be of the following {", ".join(ACCEPTED_VIDEO_FORMATS)}.')
    video_id = uuid.uuid4()
    return f'combos/{video_id}.{ext}'


class ComboManager(models.Manager):
    def verified(self) -> models.QuerySet:
        return self.filter(is_verified=True)
    

class Combo(models.Model):
    is_verified = models.BooleanField(default=False, editable=False)
    upload_date = models.DateField(auto_now_add=True)
    outdated = models.BooleanField(default=False)
    map_specific = models.BooleanField(default=False)
    video = models.FileField(upload_to=upload_to_combo)
    legends_weapons = models.ManyToManyField('LegendWeaponPair', related_name='combos')
    users = models.ManyToManyField('User', blank=True, related_name='combos')
    guests = models.ManyToManyField('Guest', blank=True, related_name='combos')
    challenge = models.ForeignKey('DailyChallenge', blank=True, null=True, related_name='combos', on_delete=models.SET_NULL)

    objects = ComboManager()


    @classmethod
    def create_from_request(cls, request: HttpRequest) -> "Combo":
        ...

    def verify(self) -> "Combo":
        if self.is_verified:
            return self
        self.users.update(codex_coins=F('codex_coins') + 5)
        self.is_verified = True
        self.save()
        return self

    def __str__(self) -> str:
        pairs = [f'{pair.legend.name}_{pair.weapon.name}' for pair in self.legends_weapons.all()]
        return '-'.join(pairs)
    
    class Meta:
        ordering = ['upload_date', 'outdated']


class RequestManager(models.Manager):
    def incompleted(self) -> models.QuerySet:
        return self.filter(combo__isnull=True)
    
    def completed(self) -> models.QuerySet:
        return self.filter(combo__isnull=False)


class Request(models.Model):
    weapons_legends = models.ManyToManyField('LegendweaponPair', related_name='requests')
    combo = models.OneToOneField('Combo', blank=True, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey('User', blank=True, null=True, related_name='requests', on_delete=models.SET_NULL)

    objects = RequestManager()

class DailyChallenge(models.Model):
    date = models.DateField(auto_now_add=True)
    legends_weapons = models.ManyToManyField('LegendWeaponPair', related_name='daily_challenges')

class Social(AbstractBaseModel):
    link = models.URLField()