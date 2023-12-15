# Generated by Django 3.2.16 on 2023-12-12 20:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Analise',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DadoSensor',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('gsr_media', models.FloatField()),
                ('freq_cardiaca_media', models.FloatField()),
                ('temperatura_final', models.FloatField()),
                ('coleta_ativa', models.CharField(max_length=5)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('analise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dados', to='home.analise')),
            ],
        ),
    ]
