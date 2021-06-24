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