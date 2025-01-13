from django.db import models
from django.utils.text import slugify
from django.db.models import F, Q
from user.models import User
from django.core.exceptions import ValidationError

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
    def verified(self):
        return self.filter(is_verified=True)

    def unverified(self):
        return self.filter(is_verified=False)
    
    def create_from_post(self, post, files):
        users = []
        guests = []
        for user in post.getlist('user'):
            try:
                users.append(User.objects.get(username=user))
            except User.DoesNotExist:
                guest, created = Guest.objects.get_or_create(username=user, defaults={'username': user})
                guests.append(guest)
        legend_one = Legend.objects.get(id=post.get('legend_one'))
        weapon_one = Weapon.objects.get(id=post.get('weapon_one'))
        legend_two = Legend.objects.get(id=post.get('legend_two'))
        weapon_two = Weapon.objects.get(id=post.get('weapon_two'))
        video = files.get('video')
        print(video)
        combo = self.create(legend_one=legend_one, weapon_one=weapon_one, legend_two=legend_two, weapon_two=weapon_two, video=video)
        print(combo.video)
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

    def __str__(self):
        return f'{self.legend_one.name} ({self.weapon_one.name}) {self.legend_two.name} ({self.weapon_two.name})'

    def verify(self):
        if not self.is_verified:
            self.is_verified = True
            self.save()
            self.users.update(codex_coins=F('codex_coins') + Combo.CODEX_COINS)
        return self
    

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