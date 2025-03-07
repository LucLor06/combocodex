from django.db import models
from django.utils.text import slugify
from django.db.models import F, Q
from django.core.paginator import Paginator
from django.urls import reverse
from config.settings import BASE_DIR
from secrets import token_urlsafe
import io
from PIL import Image
import imageio
from django.core.files.base import ContentFile

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

    def transfer_combos_to_user(self, user):
        from user.models import User
        user = User.objects.get(username__iexact=self.username)
        combos = Combo.objects.filter(guests=self)
        self.combos.remove(*combos)
        user.combos.set(combos)


def combo_video_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    token = token_urlsafe(6)
    return f'combos/videos/{instance.legend_one.slug}-{instance.weapon_one.slug}-{instance.legend_two.slug}-{instance.weapon_two.slug}-{token}.{ext}'

def combo_post_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    token = token_urlsafe(6)
    return f'combos/posters/{instance.legend_one.slug}-{instance.weapon_one.slug}-{instance.legend_two.slug}-{instance.weapon_two.slug}-{token}.{ext}'

class ComboManager(models.Manager):
    def select_weapons_legends(self):
        return self.select_related('legend_one', 'weapon_one', 'legend_two', 'weapon_two')
    
    def verified(self):
        return self.select_weapons_legends().filter(is_verified=True)

    def unverified(self):
        return self.select_weapons_legends().filter(is_verified=False)
    
    def create_from_post(self, post, files, submitter=None, **kwargs):
        from user.models import User
        users = []
        guests = []
        usernames = post.getlist('user') if not kwargs.get('users') else kwargs.get('users')
        is_verified = False
        if submitter and submitter.is_authenticated:
            is_verified = submitter.is_trusted
        for username in usernames:
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
        video_bytes = io.BytesIO(video.read())
        video_bytes.seek(0)
        frame = imageio.get_reader(video_bytes, format="mp4").get_next_data()
        image = io.BytesIO()
        Image.fromarray(frame).save(image, format='JPEG', optimize=True, quality=25)
        poster = ContentFile(image.getvalue(), name='temp.jpg')
        combo = self.create(legend_one=legend_one, weapon_one=weapon_one, legend_two=legend_two, weapon_two=weapon_two, video=video, poster=poster)
        combo.users.set(users)
        combo.guests.set(guests)
        if is_verified:
            combo = combo.verify()
        return combo
    
    def search(self, legends, weapons, users=[], ordering='-id', show_unverified=False, page_number=1, **kwargs):
        from user.models import User
        paginate = kwargs.pop('paginate', True)
        combos = self.verified() if not show_unverified else self.all()
        for username in users:
            try:
                user = User.objects.get(username__iexact=username)
                combos = combos.filter(users=user)
            except User.DoesNotExist:
                if username != '':
                    guest = Guest.objects.get_or_create(username__iexact=username)
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
        if paginate:
            paginator = Paginator(combos, 10)
            page = paginator.get_page(page_number)
            return page.object_list, page, combos.count()
        else:
            return combos, combos.count()
        
    def spreadsheet_data(self):
        combinations = {}
        combo_count = self.count()
        for legend_one in Legend.objects.prefetch_related('weapons'):
            for weapon_one in legend_one.weapons.all():
                for legend_two in Legend.objects.prefetch_related('weapons'):
                    for weapon_two in legend_two.weapons.all():
                        combos = self.filter(Q(legend_one=legend_one, weapon_one=weapon_one, legend_two=legend_two, weapon_two=weapon_two) | Q(legend_one=legend_two, weapon_one=weapon_two, legend_two=legend_one, weapon_two=weapon_one)).exclude(is_outdated=True)
                        count = combos.count()
                        link = ''
                        if count > 0:
                            link = combos.latest('id').get_absolute_url()
                        percent = round((count/combo_count) * 100, 2)
                        combinations[f'{legend_one.name}{weapon_one.name}{legend_two.name}{weapon_two.name}'] = {'count': count, 'link': link, 'percent': percent}
        return combinations
    
    
class Combo(models.Model):
    CODEX_COINS = 5
    is_verified = models.BooleanField(default=False)
    is_outdated = models.BooleanField(default=False)
    is_map_specific = models.BooleanField(default=False)
    is_alternate_gamemode = models.BooleanField(default=False)
    created_on = models.DateField(auto_now_add=True)
    legend_one = models.ForeignKey('Legend', related_name='combos_one', on_delete=models.CASCADE)
    weapon_one = models.ForeignKey('Weapon', related_name='combos_one', on_delete=models.CASCADE)
    legend_two = models.ForeignKey('Legend', related_name='combos_two', on_delete=models.CASCADE)
    weapon_two = models.ForeignKey('Weapon', related_name='combos_two', on_delete=models.CASCADE)
    users = models.ManyToManyField('user.User', blank=True, related_name='combos')
    guests = models.ManyToManyField('Guest', blank=True, related_name='combos')
    video = models.FileField(upload_to=combo_video_upload_to)
    poster = models.ImageField(upload_to=combo_post_upload_to)
    daily_challenge = models.ForeignKey('DailyChallenge', blank=True, null=True, related_name='combos', on_delete=models.SET_NULL)
    views = models.PositiveIntegerField(default=0)
    objects = ComboManager()

    class Meta:
        ordering = ['-id']

    def get_absolute_url(self):
        return reverse('combos-combo', kwargs={'pk': self.pk})

    def __str__(self):
        return f'{self.legend_one.name} ({self.weapon_one.name}) {self.legend_two.name} ({self.weapon_two.name})' 

    def verify(self):
        if not self.is_verified:
            from user.models import Mail
            self.is_verified = True
            self.save()
            self.users.update(codex_coins=F('codex_coins') + Combo.CODEX_COINS)
            self.update_spreadsheet()
            mail = Mail.objects.create(subject='Combo Verified', type='good', content=f'Your combo {self.legend_one.name} ({self.weapon_one.name}) {self.legend_two.name} ({self.weapon_two.name}) has been verified.', link=self.get_absolute_url())
            mail.users.set(self.users.all())
            try:
                request = Request.objects.incomplete().get(Q(legend_one=self.legend_one, weapon_one=self.weapon_one, legend_two=self.legend_two, weapon_two=self.weapon_two) | Q(legend_one=self.legend_two, weapon_one=self.weapon_two, legend_two=self.legend_one, weapon_two=self.weapon_one))
                request.complete(self)
            except Request.DoesNotExist:
                pass
            try:
                daily_challenge = DailyChallenge.objects.get(Q(legend_one=self.legend_one, weapon_one=self.weapon_one, legend_two=self.legend_two, weapon_two=self.weapon_two) | Q(legend_one=self.legend_two, weapon_one=self.weapon_two, legend_two=self.legend_one, weapon_two=self.weapon_one))
                if daily_challenge.created_on == self.created_on:
                    self.daily_challenge = daily_challenge
                    self.users.update(codex_coins=F('codex_coins') + DailyChallenge.CODEX_COINS)
            except DailyChallenge.DoesNotExist:
                pass
            self.save()
            for user in self.users.all():
                user.check_trusted()
        return self
    
    def reject(self, reasoning=None):
        if not self.is_verified:
            from user.models import Mail
            mail_content = f'Your combo {self.legend_one.name} ({self.weapon_one.name}) {self.legend_two.name} ({self.weapon_two.name}) has been rejected.'
            if reasoning:
                mail_content += f' The following reason(s) were provided: {reasoning}'
            mail = Mail.objects.create(subject='Combo Rejected', type='bad', content=mail_content)
            mail.users.set(self.users.all())
            self.delete()
            return True
        return False

    def get_similar(self):
        return Combo.objects.select_weapons_legends().filter(Q(legend_one=self.legend_one, legend_two=self.legend_two) | Q(legend_one=self.legend_two, legend_two=self.legend_one)).exclude(id=self.id)

    def get_exact(self, exclude_self=False):
        combos = Combo.objects.verified().filter(Q(legend_one=self.legend_one, weapon_one=self.weapon_one, legend_two=self.legend_two, weapon_two=self.weapon_two) | Q(legend_one=self.legend_two, weapon_one=self.weapon_two, legend_two=self.legend_one, weapon_two=self.weapon_one))
        if exclude_self:
            combos = combos.exclude(id=self.id)
        return combos
    
    def update_spreadsheet(self, deleting=False):
        from .apps import MainConfig
        if not self.is_outdated:
            spreadsheet_soup = MainConfig.get_spreadsheet()
            cell_id_one = f'{self.legend_one.slug}-{self.weapon_one.slug}-{self.legend_two.slug}-{self.weapon_two.slug}'
            cell_id_two = f'{self.legend_two.slug}-{self.weapon_two.slug}-{self.legend_one.slug}-{self.weapon_one.slug}'
            combos = self.get_exact(exclude_self=deleting)
            combo_count = combos.count()
            combo_percent = round((combo_count / Combo.objects.count()) * 100, 2)
            for cell_id in [cell_id_one, cell_id_two]:
                cell = spreadsheet_soup.find(id=cell_id)
                if combo_count > 0:
                    cell['style'] = 'background-color: green;'
                    link = self.get_absolute_url() if not deleting else combos.latest('id').get_absolute_url()
                    cell['href'] = link
                else:
                    del cell['style']
                    del cell['href']
                cell_count = cell.find(id=f'{cell_id}__combo-count')
                cell_count.string = f'{combo_count} combos'
            with open(str(BASE_DIR / 'main/templates/combos/rendered_sheet.html'), 'w') as sheet:
                sheet.write(spreadsheet_soup.prettify())


class RequestManager(models.Manager):
    def complete(self):
        return self.filter(combo__isnull=False)
    
    def incomplete(self):
        return self.filter(combo__isnull=True)
    
    def create_from_post(self, post, submitter):
        legend_one = Legend.objects.get(id=post.get('legend_one'))
        weapon_one = Weapon.objects.get(id=post.get('weapon_one'))
        legend_two = Legend.objects.get(id=post.get('legend_two'))
        weapon_two = Weapon.objects.get(id=post.get('weapon_two'))
        notes = post.get('notes')
        request = Request.objects.create(legend_one=legend_one, weapon_one=weapon_one, legend_two=legend_two, weapon_two=weapon_two, notes=notes, user=submitter)
        return request
    

class Request(models.Model):
    CODEX_COINS = 5
    combo = models.OneToOneField('Combo', blank=True, null=True, related_name='request', on_delete=models.CASCADE)
    user = models.ForeignKey('user.User', blank=True, null=True, related_name='requests', on_delete=models.CASCADE)
    created_on = models.DateField(auto_now_add=True)
    legend_one = models.ForeignKey('Legend', related_name='requests_one', on_delete=models.CASCADE)
    weapon_one = models.ForeignKey('Weapon', related_name='requests_one', on_delete=models.CASCADE)
    legend_two = models.ForeignKey('Legend', related_name='requests_two', on_delete=models.CASCADE)
    weapon_two = models.ForeignKey('Weapon', related_name='requests_two', on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    objects = RequestManager()

    def __str__(self):
        return f'{self.legend_one.name} ({self.weapon_one.name}) {self.legend_two.name} ({self.weapon_two.name})'

    def display_name(self):
        return 'Guest' if not self.user else self.user.username
    
    def complete(self, combo):
        self.combo = combo
        if self.user:
            from user.models import Mail
            mail = Mail.objects.create(subject='Request Completed', type='good', content=f'Your request for {combo.legend_one.name} ({combo.weapon_one.name}) {combo.legend_two.name} ({combo.weapon_two.name}) has been completed!', link=combo.get_absolute_url())
            mail.users.add(self.user)
            self.user.codex_coins += Request.CODEX_COINS
            self.user.save()
        self.save()
        return self
    
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