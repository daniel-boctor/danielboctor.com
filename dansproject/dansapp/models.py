from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.deletion import CASCADE

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