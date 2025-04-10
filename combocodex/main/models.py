from django.db import models
from django.utils.text import slugify
from django.db.models import F, Q
from django.core.paginator import Paginator
from django.urls import reverse
from config.settings import BASE_DIR
from secrets import token_urlsafe
import io
from PIL import Image
import os
import imageio
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from datetime import datetime
from django.core.files.storage import default_storage
from lxml import etree
import portalocker

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
    username = models.CharField(max_length=32, unique=True)

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

        is_verified = False
        if (submitter and submitter.is_authenticated and submitter.is_trusted) or kwargs.get('is_recommended', False):
            is_verified = True

        users = []
        guests = []
        usernames = post.getlist('user') if not kwargs.get('users') else kwargs.pop('users')
        usernames = [username for username in usernames if username != ''][:2]
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
        video_data = Combo.process_video(video)

        combo = self.create(legend_one=legend_one, weapon_one=weapon_one, legend_two=legend_two, weapon_two=weapon_two, video=video, **video_data, **kwargs)
        combo.users.set(users)
        combo.guests.set(guests)

        if is_verified:
            combo = combo.verify()

        return combo

    def search(self, legends=[], weapons=[], users=[], **kwargs):
        from user.models import User

        DEFAULT_EXCLUDES = {'is_outdated': True, 'is_map_specific': True, 'is_verified': False}
        ignore_default_excludes = kwargs.pop('ignore_default_excludes', [])
        exclude_query = Q()
        for field, value in DEFAULT_EXCLUDES.items():
            if field not in ignore_default_excludes:
                exclude_query |= Q(**{field: value})

        legends = legends[:2]
        weapons = weapons[:2]
        paginate = kwargs.pop('paginate', True)
        page_number = kwargs.pop('page', 1)
        recommended_first = kwargs.pop('recommended_first', True)

        order_by = kwargs.pop('order_by', 'id')
        order_by_function = kwargs.pop('order_by_function', 'descending')
        if order_by_function == 'descending' and not order_by.startswith('-'):
            order_by = f'-{order_by}'

        combos = self.all().exclude(exclude_query)

        users = [user.strip() for user in users if user][:2]
        for username in users:
            try:
                user = User.objects.get(username__iexact=username)
                combos = combos.filter(users=user)
            except User.DoesNotExist:
                guest = Guest.objects.get(username__iexact=username)
                combos = combos.filter(guests=guest)

        legend_filter = Q()
        if len(legends) == 2 and legends[0] == legends[1]:
            legend_filter = Q(legend_one=legends[0], legend_two=legends[0])
        else:
            for legend in legends:
                legend_filter &= Q(legend_one=legend) | Q(legend_two=legend)

        weapon_filter = Q()
        if len(weapons) == 2 and weapons[0] == weapons[1]:
            weapon_filter = Q(weapon_one=weapons[0], weapon_two=weapons[0])
        else:
            for weapon in weapons:
                weapon_filter &= Q(weapon_one=weapon) | Q(weapon_two=weapon)

        kwarg_filter = Q(**kwargs)

        combos = combos.filter(legend_filter & weapon_filter & kwarg_filter)

        if recommended_first:
            combos = combos.order_by('-is_recommended', order_by)
        else:
            combos = combos.order_by(order_by)

        combo_count = combos.count()

        data = {'combo_count': combo_count, 'combos': combos}

        if paginate:
            paginator = Paginator(combos, 10)
            page = paginator.get_page(page_number)
            data.update({'combos': page.object_list, 'page': page})

        return data


class Combo(models.Model):
    CODEX_COINS = 5
    is_verified = models.BooleanField(default=False)
    is_recommended = models.BooleanField(default=False)
    is_outdated = models.BooleanField(default=False)
    is_map_specific = models.BooleanField(default=False)
    is_alternate_gamemode = models.BooleanField(default=False)
    created_on = models.DateField(default=datetime.today)
    legend_one = models.ForeignKey('Legend', related_name='combos_one', on_delete=models.CASCADE)
    weapon_one = models.ForeignKey('Weapon', related_name='combos_one', on_delete=models.CASCADE)
    legend_two = models.ForeignKey('Legend', related_name='combos_two', on_delete=models.CASCADE)
    weapon_two = models.ForeignKey('Weapon', related_name='combos_two', on_delete=models.CASCADE)
    users = models.ManyToManyField('user.User', blank=True, related_name='combos', editable=False)
    guests = models.ManyToManyField('Guest', blank=True, related_name='combos', editable=False)
    video = models.FileField(upload_to=combo_video_upload_to)
    video_duration = models.FloatField()
    poster = models.ImageField(blank=True, null=True, upload_to=combo_post_upload_to, editable=False)
    daily_challenge = models.ForeignKey('DailyChallenge', blank=True, null=True, related_name='combos', on_delete=models.SET_NULL, editable=False)
    views = models.PositiveIntegerField(default=0)
    objects = ComboManager()

    class Meta:
        ordering = ['-id']

    def get_absolute_url(self):
        return reverse('combos-combo', kwargs={'pk': self.pk})

    def get_admin_url(self):
        return reverse('admin:main_combo_change', args=[self.pk])

    def save(self, *args, skip_custom_logic=False, skip_validation=False, **kwargs):
        if not skip_validation:
            self.full_clean()

        if skip_custom_logic:
            return super().save(*args, **kwargs)

        previous_self = Combo.objects.get(pk=self.pk) if self.pk else None
        combos_with_matching_pairs = self.get_combos_with_matching_pairs()

        now_recommended = self.is_recommended and previous_self and not previous_self.is_recommended
        previously_recommended = not self.is_recommended and previous_self and previous_self.is_recommended
        if now_recommended or (self.is_recommended and not self.pk):
            has_matching_recommended = combos_with_matching_pairs.filter(is_recommended=True).exists()
            combos_with_matching_pairs.exclude(pk=self.pk).update(is_recommended=False)
            if not has_matching_recommended:
                self.update_spreadsheet()
        elif previously_recommended:
            self.update_spreadsheet()

        if previous_self and not self.has_matching_pairs(previous_self):
            previous_self.update_spreadsheet(deleting=True)
            previous_self.set_next_recommended()
            self.update_spreadsheet()
            self.is_recommended = False

        if previous_self and self.video.name != previous_self.video.name:
            previous_self.video.delete(save=False)
            previous_self.poster.delete(save=False)
            video_data = Combo.process_video(self.video)
            self.video_duration = video_data['video_duration']
            self.poster = video_data['poster']

        return super().save(*args, **kwargs)
    
    def clean(self):
        errors = {}

        if not self.legend_one.weapons.filter(pk=self.weapon_one.pk).exists() or not self.legend_two.weapons.filter(pk=self.weapon_two.pk).exists():
            errors.setdefault(NON_FIELD_ERRORS, []).append('Legends and weapons do not match')

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.legend_one.name} ({self.weapon_one.name}) {self.legend_two.name} ({self.weapon_two.name})'

    def value_has_changed(self, previous_self: 'Combo', field_name: str) -> bool:
        return getattr(self, field_name) != getattr(previous_self, field_name)

    def has_matching_pairs(self, combo: 'Combo') -> bool:
        return (
            (self.legend_one == combo.legend_one and self.weapon_one == combo.weapon_one and
            self.legend_two == combo.legend_two and self.weapon_two == combo.weapon_two)
            or
            (self.legend_one == combo.legend_two and self.weapon_one == combo.weapon_two and
            self.legend_two == combo.legend_one and self.weapon_two == combo.weapon_one)
        )

    def verify(self):
        if not self.is_verified:
            from user.models import Mail
            self.is_verified = True
            self.save(skip_custom_logic=True)
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
                daily_challenge = DailyChallenge.objects.filter(Q(legend_one=self.legend_one, weapon_one=self.weapon_one, legend_two=self.legend_two, weapon_two=self.weapon_two) | Q(legend_one=self.legend_two, weapon_one=self.weapon_two, legend_two=self.legend_one, weapon_two=self.weapon_one)).get(created_on=self.created_on)
                self.daily_challenge = daily_challenge
                self.users.update(codex_coins=F('codex_coins') + DailyChallenge.CODEX_COINS)
            except DailyChallenge.DoesNotExist:
                pass
            self.save(skip_custom_logic=True)
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

    def get_combos_with_matching_legends(self):
        return Combo.objects.verified().filter(Q(legend_one=self.legend_one, legend_two=self.legend_two) | Q(legend_one=self.legend_two, legend_two=self.legend_one)).exclude(id=self.id)

    def get_combos_with_matching_pairs(self, exclude_self=True):
        combos = Combo.objects.verified().filter(Q(legend_one=self.legend_one, weapon_one=self.weapon_one, legend_two=self.legend_two, weapon_two=self.weapon_two) | Q(legend_one=self.legend_two, weapon_one=self.weapon_two, legend_two=self.legend_one, weapon_two=self.weapon_one))
        if exclude_self:
            combos = combos.exclude(id=self.id)
        return combos

    def set_next_recommended(self):
        if self.is_recommended:
            combos = self.get_combos_with_matching_pairs()
            if combos.exists():
                combo = combos.first()
                combo.is_recommended = True
                combo.save(skip_custom_logic=True)
                return True
        return False

    @property
    def has_universal(self):
        return 'Universal' in [self.legend_one.name, self.legend_two.name]

    @property
    def has_unarmed(self):
        return 'Unarmed' in [self.weapon_one.name, self.weapon_two.name]

    def update_spreadsheet(self, deleting=False):
        if self.has_universal or self.is_outdated or self.has_unarmed:
            return
        spreadsheet_path = str(BASE_DIR / 'main/templates/combos/rendered_sheet.html')
        parser = etree.HTMLParser()
        with open(spreadsheet_path, 'r+', encoding='utf-8') as file:
            portalocker.lock(file, portalocker.LOCK_EX)
            tree = etree.parse(file, parser)
            root = tree.getroot()
            cell_id_one = f'{self.legend_one.slug}-{self.weapon_one.slug}-{self.legend_two.slug}-{self.weapon_two.slug}'
            cell_id_two = f'{self.legend_two.slug}-{self.weapon_two.slug}-{self.legend_one.slug}-{self.weapon_one.slug}'
            combos = self.get_combos_with_matching_pairs(exclude_self=True)
            combo_count = combos.count()
            if not deleting:
                combo_count += 1
            background_color = ''
            if combo_count > 0:
                background_color = 'var(--color-tertriary)'
                if combos.filter(is_recommended=True).exists() or self.is_recommended:
                    background_color = 'var(--color-primary)'
            for cell_id in [cell_id_one, cell_id_two]:
                cell = root.xpath(f'//a[@id="{cell_id}"]')
                if cell:
                    cell = cell[0]
                    cell.set('style', f'background-color: {background_color};')
                    cell.set('data-combo-count', str(combo_count))
            file.seek(0)
            file.write(etree.tostring(tree, pretty_print=True, encoding='utf-8', method='html').decode('utf-8'))
            file.truncate()
            file.flush()
            os.fsync(file.fileno())
            portalocker.unlock(file)

    @classmethod
    def process_video(cls, video):
        if not hasattr(video, 'read'):
            raise TypeError('Expected a file-like object with .read().')
        video_bytes = io.BytesIO(video.read())
        video_bytes.seek(0)
        reader = imageio.get_reader(video_bytes, format="mp4")
        frame = reader.get_next_data()
        image = io.BytesIO()
        Image.fromarray(frame).save(image, format='JPEG', optimize=True, quality=25)
        poster = ContentFile(image.getvalue(), name='temp.jpg')
        video_duration = reader.get_meta_data()['duration']
        video.seek(0)
        return {'poster': poster, 'video_duration': video_duration}


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
    combo = models.OneToOneField('Combo', blank=True, null=True, related_name='request', on_delete=models.CASCADE, editable=False)
    user = models.ForeignKey('user.User', blank=True, null=True, related_name='requests', on_delete=models.CASCADE)
    created_on = models.DateField(default=datetime.today)
    legend_one = models.ForeignKey('Legend', related_name='requests_one', on_delete=models.CASCADE)
    weapon_one = models.ForeignKey('Weapon', related_name='requests_one', on_delete=models.CASCADE)
    legend_two = models.ForeignKey('Legend', related_name='requests_two', on_delete=models.CASCADE)
    weapon_two = models.ForeignKey('Weapon', related_name='requests_two', on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    objects = RequestManager()

    class Meta:
        ordering = ['-id']

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
    created_on = models.DateField(default=datetime.today)
    legend_one = models.ForeignKey('Legend', related_name='daily_challenges_one', on_delete=models.CASCADE)
    weapon_one = models.ForeignKey('Weapon', related_name='daily_challenges_one', on_delete=models.CASCADE)
    legend_two = models.ForeignKey('Legend', related_name='daily_challenges_two', on_delete=models.CASCADE)
    weapon_two = models.ForeignKey('Weapon', related_name='daily_challenges_two', on_delete=models.CASCADE)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f'{self.legend_one.name} ({self.weapon_one.name}) {self.legend_two.name} ({self.weapon_two.name})'


class WebsiteSocial(AbstractModel):
    link = models.URLField()

    def icon(self):
        return f'/static/socials/{self.slug}.png'