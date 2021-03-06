# Generated by Django 2.0.5 on 2018-06-11 02:37

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import library.fields
import library.mixins


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
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
                ('published_on', models.DateField()),
                ('added_at', models.DateTimeField(auto_now_add=True)),
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
                ('slug', library.fields.ShortUUIDField(default=library.fields.ShortUUIDField.gen, max_length=8, unique=True)),
                ('name', models.CharField(max_length=70)),
                ('color', library.fields.CssField(default='inherit', max_length=25)),
                ('priority', models.SmallIntegerField(default=0)),
                ('auto_sort', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lists', to=settings.AUTH_USER_MODEL)),
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
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='library.List')),
            ],
            options={
                'verbose_name_plural': 'entries',
            },
        ),
        migrations.CreateModel(
            name='Saga',
            fields=[
                ('slug', library.fields.ShortUUIDField(default=library.fields.ShortUUIDField.gen, max_length=8, primary_key=True, serialize=False)),
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
                'verbose_name_plural': 'entries',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Slant',
            fields=[
                ('abbr', models.CharField(help_text='This cannot be changed.', max_length=2, primary_key=True, serialize=False, unique=True, verbose_name='css class')),
                ('description', models.CharField(max_length=50)),
                ('display_order', models.PositiveSmallIntegerField()),
                ('affinity', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='library.Code', verbose_name='code affinity')),
            ],
            options={
                'ordering': ['display_order'],
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
                ('published_on', models.DateField(blank=True, null=True)),
                ('updated_on', models.DateField(blank=True, null=True)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('removed_at', models.DateTimeField(blank=True, null=True)),
                ('synopsis', models.TextField(blank=True)),
                ('authors', models.ManyToManyField(related_name='stories', to='library.Author')),
                ('codes', models.ManyToManyField(blank=True, related_name='stories', to='library.Code')),
                ('slant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='stories', to='library.Slant')),
                ('source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stories', to='library.Source')),
            ],
            options={
                'verbose_name_plural': 'stories',
                'ordering': ['sort_title', 'published_on'],
            },
            bases=(models.Model, library.mixins.AuthorsMixin, library.mixins.CodesMixin),
        ),
        migrations.CreateModel(
            name='Theme',
            fields=[
                ('slug', library.fields.ShortUUIDField(default=library.fields.ShortUUIDField.gen, max_length=8, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('css', models.TextField()),
                ('active', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('theme', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='library.Theme')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
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
            name='list',
            unique_together={('user', 'name')},
        ),
        migrations.AlterUniqueTogether(
            name='installment',
            unique_together={('story', 'ordinal', 'published_on')},
        ),
    ]
