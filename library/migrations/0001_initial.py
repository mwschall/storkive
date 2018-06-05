# Generated by Django 2.0.5 on 2018-06-05 06:49

import django.db.models.deletion
from django.db import migrations, models
import library.mixins
import library.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
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
        ),
        migrations.CreateModel(
            name='Code',
            fields=[
                ('abbr', models.CharField(max_length=4, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=50)),
            ],
            options={
                'ordering': ['abbr'],
            },
        ),
        migrations.CreateModel(
            name='Installment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ordinal', models.SmallIntegerField()),
                ('is_current', models.BooleanField(default=True)),
                ('title', models.CharField(max_length=125)),
                ('added_at', models.DateField()),
                ('length', models.IntegerField(default=0)),
                ('length_unit', models.CharField(choices=[('w', 'words'), ('c', 'chars')], default='w', max_length=1)),
                ('file', models.FileField(max_length=179, upload_to='')),
                ('checksum', models.CharField(blank=True, max_length=64)),
                ('authors', models.ManyToManyField(to='library.Author')),
            ],
        ),
        migrations.CreateModel(
            name='List',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=70, unique=True)),
                ('color', models.CharField(default='inherit', max_length=25)),
                ('priority', models.SmallIntegerField(default=0)),
                ('auto_sort', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['-priority', 'name'],
            },
        ),
        migrations.CreateModel(
            name='ListEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='library.List')),
            ],
        ),
        migrations.CreateModel(
            name='Saga',
            fields=[
                ('slug', models.CharField(default=library.models._slug_gen, max_length=8, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=150)),
                ('sort_name', models.CharField(max_length=150)),
                ('synopsis', models.TextField()),
            ],
            options={
                'ordering': ['sort_name'],
            },
            bases=(models.Model, library.mixins.AuthorsMixin, library.mixins.CodesMixin),
        ),
        migrations.CreateModel(
            name='SagaEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveSmallIntegerField()),
                ('saga', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='library.Saga')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('abbr', models.CharField(blank=True, max_length=15)),
                ('website', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='Story',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150)),
                ('sort_title', models.CharField(max_length=150)),
                ('slug', models.SlugField(max_length=70, unique=True)),
                ('added_at', models.DateField(blank=True, null=True)),
                ('updated_at', models.DateField(blank=True, null=True)),
                ('removed_at', models.DateField(blank=True, null=True)),
                ('slant', models.CharField(blank=True, max_length=2)),
                ('synopsis', models.TextField(blank=True)),
                ('authors', models.ManyToManyField(related_name='stories', to='library.Author')),
                ('codes', models.ManyToManyField(blank=True, related_name='stories', to='library.Code')),
                ('source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stories', to='library.Source')),
            ],
            options={
                'verbose_name_plural': 'stories',
                'ordering': ['sort_title', 'added_at'],
            },
            bases=(models.Model, library.mixins.AuthorsMixin, library.mixins.CodesMixin),
        ),
        migrations.AddField(
            model_name='sagaentry',
            name='story',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='library.Story'),
        ),
        migrations.AddField(
            model_name='saga',
            name='stories',
            field=models.ManyToManyField(related_name='sagas', through='library.SagaEntry', to='library.Story'),
        ),
        migrations.AddField(
            model_name='installment',
            name='story',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='installments', to='library.Story'),
        ),
        migrations.AlterUniqueTogether(
            name='sagaentry',
            unique_together={('saga', 'story')},
        ),
        migrations.AlterUniqueTogether(
            name='listentry',
            unique_together={('list', 'content_type', 'object_id')},
        ),
        migrations.AlterUniqueTogether(
            name='installment',
            unique_together={('story', 'ordinal', 'added_at')},
        ),
    ]
