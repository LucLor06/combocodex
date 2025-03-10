from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import User, UserTheme, UserBackground, UserColor
from main.models import Guest

@receiver(post_save, sender=User)
def user_post_save(sender, instance: User, created, **kwargs):
    if created:
        try:
            guest = Guest.objects.get(username__iexact=instance.username)
            guest.transfer_combos_to_user(instance)
        except Guest.DoesNotExist:
            pass
        instance.collect_codex_coins()
        instance.check_trusted()
        classic_theme = UserTheme.objects.get(name='Classic')
        instance.user_themes.add(classic_theme)
        classic_theme.set(instance)
        classic_background = UserBackground.objects.get(name='Classic')
        instance.user_backgrounds.add(classic_background)
        instance.user_background = classic_background
        classic_color = UserColor.objects.get(name='Classic')
        instance.user_colors.add(classic_color)
        instance.user_color = classic_color
        instance.save()