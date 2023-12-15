# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Analise, DadoSensor
import paho.mqtt.publish as publish
from django.http import JsonResponse


@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'index'}

    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))


@require_POST
def iniciar_analise(request):
    mac_address = request.POST.get('mac_address')
    print(f"Iniciando análise para o MAC Address: {mac_address}")  # Log para verificação
    
    try:
        publish.single('esp32/sensores/comandos', mac_address, port=1883, hostname='localhost')
        message = 'Análise iniciada para o MAC: ' + mac_address
        status = 'success'
        print("Publicação MQTT bem-sucedida.")
    except Exception as e:
        message = str(e)
        status = 'error'
        print("Erro na publicação MQTT:", e)

    # Crie uma nova análise e associe ao usuário
    nova_analise = Analise(usuario=request.user)
    nova_analise.save()
    
    return JsonResponse({'status': status, 'message': message})

def obter_dados_sensores(request):
    # Obtenha a análise mais recente
    ultima_analise = Analise.objects.latest('data_criacao')

    # Obtenha os dados mais recentes associados a essa análise
    try:
        dados = DadoSensor.objects.filter(analise=ultima_analise).latest('timestamp')
        response_data = {
            'gsr': dados.gsr_media,
            'freq_cardiaca': dados.freq_cardiaca_media,
            'temperatura': dados.temperatura_final,
            'coleta_ativa': dados.coleta_ativa,
        }
    except DadoSensor.DoesNotExist:
        # Se não houver dados, defina valores padrão
        response_data = {'gsr': 0, 'freq_cardiaca': 0, 'temperatura': 0}

    return JsonResponse(response_data)

