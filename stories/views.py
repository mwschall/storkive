import os.path

from django.db.models import F, Count
from django.db.models.functions import Substr, Upper
from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_safe

from stories.models import Story, Author, Tag
from stories.util import get_story_path, char_range
from storkive import settings

ONE_DAY = 24 * 60 * 60


@require_safe
def index(request):
    return render(request, 'index.html')


@require_safe
def letter_index(request):
    letters = Story.objects\
        .annotate(letter=Upper(Substr('sort_title', 1, 1)))\
        .values('letter')\
        .annotate(num_stories=Count('id', distinct=True))\
        .order_by('letter')
    context = {
        'page_title': 'Titles',
        #          TODO: temporary until sort_title is fixed
        'letters': [l for l in letters if l['letter'] in list(char_range('A', 'Z'))]
    }
    return render(request, 'titles.html', context)


@require_safe
@cache_page(ONE_DAY, key_prefix='letter')
def letter_page(request, letter):
    qs = Story.objects.filter(sort_title__istartswith=letter).prefetch_related('authors', 'tags')
    context = {
        'page_title': 'Stories: ' + letter,
        'stories': qs.all(),
    }
    return render(request, 'letter.html', context)


@require_safe
def author_index(request):
    authors = Author.objects\
        .only('slug', 'name')\
        .annotate(num_stories=Count('stories'))\
        .iterator()
    context = {
        'page_title': 'Authors',
        'authors': authors,
    }
    return render(request, 'authors.html', context)


@require_safe
def author_page(request, slug):
    author = get_object_or_404(Author, slug=slug)
    stories = author.stories\
        .only('slug', 'title', 'slant', 'added', 'updated')\
        .prefetch_related('tags')
    context = {
        'page_title': author.name,
        'author': author,
        'stories': stories,
        'has_updated': False,
    }
    # TODO: updated col
    return render(request, 'author.html', context)


@require_safe
def tag_index(request):
    tags = Tag.objects.annotate(num_stories=Count('stories'))
    context = {
        'page_title': 'Categories',
        'tags': tags,
    }
    return render(request, 'tags.html', context)


@require_safe
@cache_page(ONE_DAY, key_prefix='tag')
def tag_page(request, abbr):
    tag = get_object_or_404(Tag, abbr=abbr)
    stories = Story.objects.filter(tags__abbr=abbr)\
        .only('slug', 'title', 'slant')\
        .prefetch_related('tags')
    context = {
        'page_title': 'Categories; '+abbr,
        'tag': tag,
        'stories': stories.all(),
    }
    return render(request, 'tag.html', context)


@require_safe
def story_page(request, slug):
    # inst_choices = Installment.objects.filter(is_current=True).order_by('ordinal')
    # inst_prefetch = Prefetch('installments', queryset=inst_choices)
    # qs = Story.objects.prefetch_related('authors', inst_prefetch, 'tags')

    # qs = Story.objects.prefetch_related('authors', 'installments', 'tags')

    qs = Story.objects.prefetch_related('authors', 'tags')
    story = get_object_or_404(qs, slug=slug)
    installments = story.current_installments
    context = {
        'page_title': story.title,
        'story': story,
        'ordinal': 0,
        'next': 1,
        'num_installments': story.num_installments,
    }
    if len(installments) == 1:
        context['chapter'] = installments[0]
    else:
        context['headers'] = [
            {'cls': 'wc', 'name': 'Length'},
            {'cls': 'cdate', 'name': 'Added'},
        ]
        # TODO: authors
        if next(filter(lambda inst: inst.date_updated, installments), None):
            context['headers'].append({'cls': 'mdate', 'name': 'Updated'})
        context['installments'] = installments

    return render(request, 'title.html', context)


@require_safe
def installment_page(request, slug, ordinal):
    qs = Story.objects.only('slug', 'title')
    story = get_object_or_404(qs, slug=slug)
    inst = story.current_installments\
        .filter(ordinal=ordinal)\
        .annotate(story_title=F('story__title'))\
        .prefetch_related('authors')\
        .get()
    num_installments = story.num_installments
    title = inst.story_title
    if num_installments > 1:
        title = title + ' ({:d} of {:d})'.format(ordinal, num_installments)

    file_path = os.path.join(settings.DATA_DIR, get_story_path(story), inst.file_name)
    with open(file_path, 'r', encoding='utf-8') as f:
        body = f.read()

    context = {
        'page_title': title,
        'story': story,
        'authors': inst.authors.all(),
        'ordinal': ordinal,
        'prev': ordinal-1,
        'next': ordinal+1 if ordinal < num_installments else 0,
        'num_installments': num_installments,
        'body': body,
    }
    return render(request, 'installment.html', context)
