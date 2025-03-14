from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.functional import cached_property
from django.db.models import Prefetch, Q, Count, F, Sum
from django.utils.text import slugify
from datetime import datetime, timedelta
from django.urls import reverse
from allauth.account.models import EmailAddress
from config.settings import TRUSTED_COMBO_REQUIREMENT

class User(AbstractUser):
    discord_id = models.BigIntegerField(blank=True, null=True, unique=True)
    is_trusted = models.BooleanField(default=False)
    codex_coins = models.PositiveIntegerField(default=0)
    user_color = models.ForeignKey('UserColor', blank=True, null=True, related_name='users_individual', on_delete=models.SET_NULL)
    user_colors = models.ManyToManyField('UserColor', blank=True, related_name='users')
    user_theme = models.ForeignKey('UserTheme', blank=True, null=True, related_name='users_individual', on_delete=models.SET_NULL)
    theme_color = models.CharField(max_length=7, default='#239063')
    user_themes = models.ManyToManyField('UserTheme', blank=True, related_name='users')
    user_background = models.ForeignKey('UserBackground', blank=True, null=True, related_name='users_individual', on_delete=models.SET_NULL)
    user_backgrounds = models.ManyToManyField('UserBackground', blank=True, related_name='users')
    favorite_combos = models.ManyToManyField('main.Combo', blank=True, related_name='favorite_users', editable=False)

    def get_absolute_url(self):
        return reverse('profile', kwargs={'pk': self.pk})

    def check_trusted(self):
        from main.models import Combo
        if not self.is_trusted:
            if Combo.objects.verified().filter(users=self).count() >= TRUSTED_COMBO_REQUIREMENT:
                self.is_trusted = True
                self.save()
        return self.is_trusted

    def transfer_combos_to_user(self, user):
        combos = self.combos.all()
        user.combos.add(combos)
        self.combos.remove(combos)

    def collect_codex_coins(self):
        from main.models import Combo, DailyChallenge, Request
        combos = self.combos.count() * Combo.CODEX_COINS
        requests = Request.objects.filter(combo__users=self).count() * Request.CODEX_COINS
        daily_challenges = DailyChallenge.objects.filter(combos__users=self).count() * DailyChallenge.CODEX_COINS
        self.codex_coins += (combos + requests + daily_challenges)
        self.save()

    @cached_property
    def legends(self):
        from main.models import Legend
        legend_count = Legend.objects.count()
        legends = set()
        for combo in self.combos.select_related('legend_one', 'legend_two').filter(users=self):
            legends.update([combo.legend_one.id, combo.legend_two.id])
            if len(legends) == legend_count:
                break
        return Legend.objects.filter(id__in=legends)

    @cached_property
    def weapons(self):
        from main.models import Weapon
        weapon_count = Weapon.objects.count()
        weapons = set()
        for combo in self.combos.select_related('weapon_one', 'weapon_two').filter(users=self):
            weapons.update([combo.weapon_one.id, combo.weapon_two.id])
            if len(weapons) == weapon_count:
                break
        return Weapon.objects.filter(id__in=weapons)



    @cached_property
    def daily_challenges(self):
        from main.models import DailyChallenge
        return DailyChallenge.objects.prefetch_related('combos').filter(combos__users=self).distinct()

    @cached_property
    def completed_requests(self):
        from main.models import Request
        return Request.objects.select_related('combo').filter(combo__users=self)

    @cached_property
    def email_address(self):
        return EmailAddress.objects.filter(user=self, primary=True).first()

    @cached_property
    def total_combo_views(self):
        return self.combos.aggregate(total_views=Sum('views'))['total_views']

    @classmethod
    def weekly_user(cls):
        today = datetime.now().date()
        date = today - timedelta(days=today.weekday())
        users = cls.objects.annotate(combo_count=Count('combos', filter=Q(combos__created_on__range=(date, date + timedelta(days=7)))))
        return users.order_by('-combo_count').first()

class AbstractShopItem(models.Model):
    name = models.CharField(max_length=32)
    price = models.PositiveSmallIntegerField(default=10)
    slug = models.SlugField(blank=True, editable=False)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class UserColor(AbstractShopItem):
    def css_class(self):
        return f'user-color--{self.slug}'

    def icon(self):
        return f'/static/user_colors/{self.slug}.png'

    def purchase(self, user):
        if user.codex_coins >= self.price:
            user.codex_coins -= self.price
            user.user_colors.add(self)
            user.save()

    def set(self, user):
        if user.user_colors.filter(id=self.id).exists():
            user.user_color = self
            user.save()


class UserTheme(AbstractShopItem):
    primary_color = models.CharField(max_length=7)

    def icon(self):
        return f'/static/user_themes/{self.slug}.png'

    def purchase(self, user):
        if user.codex_coins >= self.price:
            user.codex_coins -= self.price
            user.user_themes.add(self)
            user.save()

    def set(self, user):
        if user.user_themes.filter(id=self.id).exists():
            user.user_theme = self
            user.theme_color = self.primary_color
            user.save()


class UserBackground(AbstractShopItem):
    def image(self):
        return f'/static/user_backgrounds/{self.slug}.png'

    def purchase(self, user):
        if user.codex_coins >= self.price:
            user.codex_coins -= self.price
            user.user_backgrounds.add(self)
            user.save()

    def set(self, user):
        if user.user_backgrounds.filter(id=self.id).exists():
            user.user_background = self
            user.save()


class Mail(models.Model):
    users = models.ManyToManyField('User', blank=True, related_name='mail')
    TYPE_CHOICES = [
        ('good', 'Good'),
        ('bad', 'Bad')
    ]
    type = models.CharField(max_length=8, choices=TYPE_CHOICES, default='good')
    subject = models.TextField()
    content = models.TextField()
    link = models.CharField(blank=True, null=True, max_length=64)
    created_on = models.DateField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']