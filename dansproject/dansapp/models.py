from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.db.models.deletion import CASCADE
import os
from django.dispatch import receiver

# Create your models here.

class User(AbstractUser):
    pass

class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=32, blank=True)
    ticker1 = models.CharField(max_length=8)
    weight1 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    
for i in range(2, 9):
    Portfolio.add_to_class(f"ticker{i}", models.CharField(max_length=8, null=True, blank=True))
    Portfolio.add_to_class(f"weight{i}", models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)], null=True, blank=True))

class RetsCSV(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=32, unique=True)
    return_series = models.FileField(validators=[FileExtensionValidator(['csv'])])

@receiver(models.signals.post_delete, sender=RetsCSV)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.return_series:
        if os.path.isfile(instance.return_series.path):
            os.remove(instance.return_series.path)

@receiver(models.signals.pre_save, sender=RetsCSV)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return False
    try:
        old_file = RetsCSV.objects.get(pk=instance.pk).return_series
    except RetsCSV.DoesNotExist:
        return False
    #new_file = instance.return_series
    #if not old_file == new_file:
    if os.path.isfile(old_file.path):
        os.remove(old_file.path)


from datetime import date
class NB(models.Model):
    #class Meta:
    #    constraints = [models.UniqueConstraint(fields=['user', 'name'], name="unique_name")]

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=32, null=False, blank=True)
    date = models.DateField(default=date.today)
    DLR_TO = models.DecimalField(decimal_places=4, max_digits=7)
    DLR_U_TO = models.DecimalField(decimal_places=4, max_digits=7)
    buy_FX = models.DecimalField(decimal_places=4, max_digits=5)
    sell_FX = models.DecimalField(decimal_places=4, max_digits=5)
    initial = models.DecimalField(decimal_places=2, max_digits=10)
    initial_fx = models.CharField(choices=(("CAD", "CAD"), ("USD", "USD"), ("TO", "DLR.TO"), ("U", "DLR-U.TO")), default="CAD", max_length=3)
    incur_buy_side_ecn = models.BooleanField()
    incur_sell_side_ecn = models.BooleanField()
    buy_side_ecn = models.DecimalField(decimal_places=4, max_digits=5)
    sell_side_ecn = models.DecimalField(decimal_places=4, max_digits=5)
    buy_side_comm = models.DecimalField(decimal_places=4, max_digits=5)
    sell_side_comm = models.DecimalField(decimal_places=4, max_digits=5)
    lower_bound = models.DecimalField(decimal_places=4, max_digits=5)
    upper_bound = models.DecimalField(decimal_places=4, max_digits=5)
    brokers_spread = models.DecimalField(decimal_places=4, max_digits=5, null=True, blank=True)
    cad_ticker = models.CharField(max_length=8, default="DLR.TO")
    usd_ticker = models.CharField(max_length=8, default="DLR-U.TO")
    closed = models.BooleanField()