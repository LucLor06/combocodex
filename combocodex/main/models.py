from django.db import models
from django.utils.text import slugify
from django.db.models import F, Q
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.urls import reverse

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
        return f'/static/weapons/{self.slug}.png'


class Legend(AbstractModel):
    weapons = models.ManyToManyField('Weapon', related_name='legends')

    def icon(self):
        return f'/static/legends/{self.slug}.png'
    

class Guest(models.Model):
    username = models.CharField(max_length=32)

    def transfer_combos_to_user(self, user=None):
        from user.models import User
        user = User.objects.get(username=self.username) if not user else user
        combos = Combo.objects.filter(guests=self)
        self.combos.remove(combos)
        user.combos.set(combos)


def combo_video_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    return f'combos/{instance.legend_one.slug}_{instance.weapon_one.slug}|{instance.legend_two.slug}_{instance.weapon_two.slug}.{ext}'

class ComboManager(models.Manager):
    def select_weapons_legends(self):
        return self.select_related('legend_one', 'weapon_one', 'legend_two', 'weapon_two')
    
    def verified(self):
        return self.select_weapons_legends().filter(is_verified=True)

    def unverified(self):
        return self.select_weapons_legends().filter(is_verified=False)
    
    def create_from_post(self, post, files, submitter=None):
        from user.models import User
        users = []
        guests = []
        is_verified = False
        if submitter and submitter.is_authenticated:
            is_verified = submitter.is_trusted
        for username in post.getlist('user'):
            try:
                users.append(User.objects.get(username=username))
            except User.DoesNotExist:
                guest, created = Guest.objects.get_or_create(username=username, defaults={'username': username})
                guests.append(guest)
        legend_one = Legend.objects.get(id=post.get('legend_one'))
        weapon_one = Weapon.objects.get(id=post.get('weapon_one'))
        legend_two = Legend.objects.get(id=post.get('legend_two'))
        weapon_two = Weapon.objects.get(id=post.get('weapon_two'))
        video = files.get('video')
        combo = self.create(legend_one=legend_one, weapon_one=weapon_one, legend_two=legend_two, weapon_two=weapon_two, video=video, is_verified=is_verified)
        combo.users.set(users)
        combo.guests.set(guests)
        try:
            daily_challenge = DailyChallenge.objects.get(Q(legend_one=legend_one, weapon_one=weapon_one, legend_two=legend_two, weapon_two=weapon_two) | Q(legend_one=legend_two, weapon_one=weapon_two, legend_two=legend_one, weapon_two=weapon_one))
            if daily_challenge.created_on == combo.created_on:
                combo.daily_challenge = daily_challenge
                combo.save()
        except DailyChallenge.DoesNotExist:
            pass
        try:
           request = Request.objects.get(Q(legend_one=legend_one, weapon_one=weapon_one, legend_two=legend_two, weapon_two=weapon_two) | Q(legend_one=legend_two, weapon_one=weapon_two, legend_two=legend_one, weapon_two=weapon_one))
           request.combo = combo
           request.save()
        except Request.DoesNotExist:
            pass
        return combo
    
    def search(self, legends, weapons, users, ordering='created_on', show_unverified=False, page_number=1):
        from user.models import User
        combos = self.verified() if not show_unverified else self.all()
        for username in users:
            try:
                user = User.objects.get(username=username)
                combos = combos.filter(users=user)
            except User.DoesNotExist:
                guest = Guest.objects.get_or_create(username=username)
                combos = combos.filter(guests=guest)
        if len(legends) == 2 and legends[0] == legends[1]:
            combos = combos.filter(Q(legend_one=legends[0], legend_two=legends[0]))
        else:
            for legend in legends:
                combos = combos.filter(Q(legend_one=legend) | Q(legend_two=legend))
        if len(weapons) == 2 and weapons[0] == weapons[1]:
            combos = combos.filter(Q(weapon_one=weapons[0], weapon_two=weapons[0]))
        else:
            for weapon in weapons:
                combos = combos.filter(Q(weapon_one=weapon) | Q(weapon_two=weapon))
        combos = combos.order_by(ordering)
        paginator = Paginator(combos, 10)
        page = paginator.get_page(page_number)
        return page.object_list, page, combos.count()
    

class Combo(models.Model):
    CODEX_COINS = 5
    is_verified = models.BooleanField(default=False)
    is_outdated = models.BooleanField(default=False)
    is_map_specific = models.BooleanField(default=False)
    created_on = models.DateField(auto_now_add=True)
    legend_one = models.ForeignKey('Legend', related_name='combos_one', on_delete=models.CASCADE)
    weapon_one = models.ForeignKey('Weapon', related_name='combos_one', on_delete=models.CASCADE)
    legend_two = models.ForeignKey('Legend', related_name='combos_two', on_delete=models.CASCADE)
    weapon_two = models.ForeignKey('Weapon', related_name='combos_two', on_delete=models.CASCADE)
    users = models.ManyToManyField('user.User', blank=True, related_name='combos')
    guests = models.ManyToManyField('Guest', blank=True, related_name='combos')
    video = models.FileField(upload_to=combo_video_upload_to)
    daily_challenge = models.ForeignKey('DailyChallenge', blank=True, null=True, related_name='combos', on_delete=models.SET_NULL)
    views = models.PositiveIntegerField(default=0)
    objects = ComboManager()

    class Meta:
        ordering = ['is_outdated', '-created_on']

    def get_absolute_url(self):
        return reverse('combos-combo', kwargs={'pk': self.pk})

    def __str__(self):
        return f'{self.legend_one.name} ({self.weapon_one.name}) {self.legend_two.name} ({self.weapon_two.name})'

    def verify(self):
        if not self.is_verified:
            self.is_verified = True
            self.save()
            self.users.update(codex_coins=F('codex_coins') + Combo.CODEX_COINS)
            for user in self.users.all():
                user.check_trusted()
        return self
    
    def get_similar(self):
        return Combo.objects.select_weapons_legends().filter(Q(legend_one=self.legend_one, legend_two=self.legend_two) | Q(legend_one=self.legend_two, legend_two=self.legend_one)).exclude(id=self.id)

class RequestManager(models.Manager):
    def complete(self):
        return self.filter(combo__isnull=False)
    
    def incomplete(self):
        return self.filter(combo__isnull=True)
    

class Request(models.Model):
    CODEX_COINS = 5
    combo = models.OneToOneField('Combo', blank=True, null=True, related_name='request', on_delete=models.CASCADE)
    user = models.ForeignKey('user.User', blank=True, null=True, related_name='requests', on_delete=models.CASCADE)
    created_on = models.DateField(auto_now_add=True)
    legend_one = models.ForeignKey('Legend', related_name='requests_one', on_delete=models.CASCADE)
    weapon_one = models.ForeignKey('Weapon', related_name='requests_one', on_delete=models.CASCADE)
    legend_two = models.ForeignKey('Legend', related_name='requests_two', on_delete=models.CASCADE)
    weapon_two = models.ForeignKey('Weapon', related_name='requests_two', on_delete=models.CASCADE)
    objects = RequestManager()

    def __str__(self):
        return f'{self.legend_one.name} ({self.weapon_one.name}) {self.legend_two.name} ({self.weapon_two.name})'

    def display_name(self):
        return 'Guest' if not self.user else self.user.username
    
    
class DailyChallenge(models.Model):
    CODEX_COINS = 10
    created_on = models.DateField(auto_now_add=True)
    legend_one = models.ForeignKey('Legend', related_name='daily_challenges_one', on_delete=models.CASCADE)
    weapon_one = models.ForeignKey('Weapon', related_name='daily_challenges_one', on_delete=models.CASCADE)
    legend_two = models.ForeignKey('Legend', related_name='daily_challenges_two', on_delete=models.CASCADE)
    weapon_two = models.ForeignKey('Weapon', related_name='daily_challenges_two', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.legend_one.name} ({self.weapon_one.name}) {self.legend_two.name} ({self.weapon_two.name})'
    
class WebsiteSocial(AbstractModel):
    link = models.URLField()
    
    def icon(self):
        return f'/static/socials/{self.slug}.png'