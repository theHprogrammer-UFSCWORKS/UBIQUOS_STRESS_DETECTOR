# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.db import models
from django.contrib.auth.models import User

class Analise(models.Model):
    # id com autoincremento
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)

class DadoSensor(models.Model):
    id = models.AutoField(primary_key=True)
    analise = models.ForeignKey(Analise, related_name='dados', on_delete=models.CASCADE)
    gsr_media = models.FloatField()
    freq_cardiaca_media = models.FloatField()
    temperatura_final = models.FloatField()
    coleta_ativa = models.CharField(max_length=5)
    timestamp = models.DateTimeField(auto_now_add=True)
