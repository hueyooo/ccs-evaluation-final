# Generated by Django 4.2.5 on 2023-11-09 08:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_instructorquestionnaire'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstructorQuestionnaireScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField()),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('evaluated', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.instructor')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.questionnaire')),
            ],
        ),
    ]
