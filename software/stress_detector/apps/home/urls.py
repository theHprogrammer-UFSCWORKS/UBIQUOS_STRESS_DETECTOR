# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.home import views

urlpatterns = [
    # The home page
    path('', views.index, name='home'),
    path('iniciar-analise/', views.iniciar_analise, name='iniciar-analise'),
    path('obter-dados-sensores/', views.obter_dados_sensores, name='obter_dados_sensores'),

    # Matches any html file - Esta rota deve ser a última!
    re_path(r'^.*\.*', views.pages, name='pages'),
]
