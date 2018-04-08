# Generated by Django 2.0.4 on 2018-04-08 02:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('slug', models.SlugField(allow_unicode=True, max_length=70, unique=True)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('homepage', models.URLField(blank=True)),
            ],
            options={
                'ordering': ('slug',),
            },
        ),
        migrations.CreateModel(
            name='Chapter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.SmallIntegerField()),
                ('title', models.CharField(max_length=50)),
                ('added', models.DateField()),
                ('updated', models.DateField()),
                ('authors', models.ManyToManyField(to='stories.Author')),
            ],
        ),
        migrations.CreateModel(
            name='Story',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150)),
                ('sort_title', models.CharField(max_length=150)),
                ('slug', models.SlugField(allow_unicode=True, max_length=70, unique=True)),
                ('added', models.DateField()),
                ('updated', models.DateField()),
                ('removed', models.DateField(blank=True)),
                ('synopsis', models.TextField(blank=True)),
                ('authors', models.ManyToManyField(to='stories.Author')),
            ],
            options={
                'verbose_name_plural': 'stories',
                'ordering': ('sort_title',),
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abbr', models.CharField(max_length=4)),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='story',
            name='primary_tag',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='stories.Tag'),
        ),
        migrations.AddField(
            model_name='story',
            name='tags',
            field=models.ManyToManyField(to='stories.Tag'),
        ),
        migrations.AddField(
            model_name='chapter',
            name='story',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stories.Story'),
        ),
    ]
