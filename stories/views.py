from django.db.models import F, Count, OuterRef, Min, Exists
from django.db.models.functions import Substr, Upper
from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_safe

from stories.expressions import SQCount
from stories.models import Story, Author, Tag, Installment

ONE_DAY = 24 * 60 * 60


@require_safe
def index(request):
    return render(request, 'index.html')


@require_safe
@cache_page(ONE_DAY)
def whats_new(request):
    last_two = Story.objects.values_list('updated', flat=True).order_by('-updated').distinct()[:2]

    def fetch_updates(date):
        new_insts_exist = Installment.objects \
            .order_by() \
            .filter(story=OuterRef('pk'), added=date)

        new_insts = Installment.objects \
            .order_by() \
            .filter(story_id=OuterRef('pk')) \
            .values('ordinal') \
            .annotate(ord_min=Min('added')) \
            .filter(ord_min=date)

        return Story.objects \
            .annotate(inst_on_date=Exists(new_insts_exist)) \
            .filter(inst_on_date=True) \
            .annotate(up_cnt=SQCount(new_insts)) \
            .annotate(author_dicts=Story.authors_sq(),
                      tag_abbrs=Story.tags_sq()) \
            .all()

    days = [{'date': date, 'updates': fetch_updates(date)} for date in last_two]

    context = {
        'page_title': 'Recent Additions',
        'days': days,
    }
    return render(request, 'whats-new.html', context)


@require_safe
def letter_index(request):
    letters = Story.objects \
        .annotate(letter=Upper(Substr('sort_title', 1, 1))) \
        .values('letter') \
        .annotate(num_stories=Count('id', distinct=True)) \
        .order_by('letter') \
        .all()
    context = {
        'page_title': 'Titles',
        'letters': letters,
    }
    return render(request, 'titles.html', context)


@require_safe
@cache_page(ONE_DAY, key_prefix='letter')
def letter_page(request, letter):
    stories = Story.objects \
        .filter(sort_title__istartswith=letter) \
        .annotate(author_dicts=Story.authors_sq(),
                  tag_abbrs=Story.tags_sq()) \
        .iterator()
    context = {
        'page_title': 'Stories: ' + letter,
        'stories': stories,
    }
    return render(request, 'letter.html', context)


@require_safe
def author_index(request):
    authors = Author.objects \
        .only('slug', 'name') \
        .annotate(num_stories=Count('stories')) \
        .iterator()
    context = {
        'page_title': 'Authors',
        'authors': authors,
    }
    return render(request, 'authors.html', context)


@require_safe
def author_page(request, slug):
    author = get_object_or_404(Author, slug=slug)
    stories = author.stories \
        .only('slug', 'title', 'slant', 'added', 'updated') \
        .annotate(tag_abbrs=Story.tags_sq())
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
    stories = Story.objects.filter(tags__abbr=abbr) \
        .only('slug', 'title', 'slant') \
        .annotate(tag_abbrs=Story.tags_sq()) \
        .all()
    context = {
        'page_title': 'Categories; '+abbr,
        'tag': tag,
        'stories': stories,
    }
    return render(request, 'tag.html', context)


@require_safe
def story_page(request, slug):
    qs = Story.objects.annotate(author_dicts=Story.authors_sq(),
                                tag_abbrs=Story.tags_sq())
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
    inst = story.current_installments \
        .filter(ordinal=ordinal) \
        .annotate(story_title=F('story__title')) \
        .prefetch_related('authors') \
        .get()
    num_installments = story.num_installments
    title = inst.story_title
    if num_installments > 1:
        title = title + ' ({:d} of {:d})'.format(ordinal, num_installments)

    context = {
        'page_title': title,
        'story': story,
        'inst': inst,
        'authors': inst.authors.all(),
        'ordinal': ordinal,
        'prev': ordinal-1,
        'next': ordinal+1 if ordinal < num_installments else 0,
        'num_installments': num_installments,
    }
    return render(request, 'installment.html', context)
