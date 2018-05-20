from django.db import IntegrityError
from django.db.models import F, Count, OuterRef, Min, Exists
from django.db.models.functions import Substr, Upper
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_safe, require_http_methods

from library.expressions import SQCount
from library.models import Author, Installment, List, Story, Code

ONE_DAY = 24 * 60 * 60


@require_safe
def index(request):
    return render(request, 'index.html')


@require_safe
@cache_page(ONE_DAY)
def whats_new(request):
    last_two = Story.objects.values_list('updated_at', flat=True).order_by('-updated_at').distinct()[:2]

    def fetch_updates(date):
        new_insts_exist = Installment.objects \
            .order_by() \
            .filter(story=OuterRef('pk'), added_at=date)

        new_insts = Installment.objects \
            .order_by() \
            .filter(story_id=OuterRef('pk')) \
            .values('ordinal') \
            .annotate(ord_min=Min('added_at')) \
            .filter(ord_min=date)

        return Story.objects \
            .annotate(inst_on_date=Exists(new_insts_exist)) \
            .filter(inst_on_date=True) \
            .annotate(up_cnt=SQCount(new_insts)) \
            .annotate(author_dicts=Story.authors_sq(),
                      code_abbrs=Story.codes_sq()) \
            .iterator()

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
        .annotate(story_count=Count('id', distinct=True)) \
        .order_by('letter') \
        .iterator()
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
                  code_abbrs=Story.codes_sq()) \
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
        .annotate(story_count=Count('stories')) \
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
        .only('slug', 'title', 'slant', 'added_at', 'updated_at') \
        .annotate(code_abbrs=Story.codes_sq())
    context = {
        'page_title': author.name,
        'author': author,
        'stories': stories,
        'has_updated': False,
    }
    # TODO: updated col
    return render(request, 'author.html', context)


@require_safe
def code_index(request):
    codes = Code.objects.annotate(story_count=Count('stories'))
    context = {
        'page_title': 'Codes',
        'codes': codes,
    }
    return render(request, 'codes.html', context)


@require_safe
@cache_page(ONE_DAY, key_prefix='code')
def code_page(request, abbr):
    code = get_object_or_404(Code, abbr=abbr)
    stories = Story.objects.filter(codes__abbr=abbr) \
        .only('slug', 'title', 'slant') \
        .annotate(code_abbrs=Story.codes_sq()) \
        .iterator()
    context = {
        'page_title': 'Codes; '+abbr,
        'code': code,
        'stories': stories,
    }
    return render(request, 'code.html', context)


@require_safe
def story_page(request, slug):
    qs = Story.objects.annotate(author_dicts=Story.authors_sq(),
                                code_abbrs=Story.codes_sq())
    story = get_object_or_404(qs, slug=slug)
    installments = story.current_installments
    context = {
        'page_title': story.title,
        'story': story,
        'ordinal': 0,
        'next': 1,
        'installment_count': story.installment_count,
        'lists': List.objects.all(),
        'story_lists': [l.pk for l in story.lists],
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
    installment_count = story.installment_count
    title = inst.story_title
    if installment_count > 1:
        title = title + ' ({:d} of {:d})'.format(ordinal, installment_count)

    context = {
        'page_title': title,
        'story': story,
        'inst': inst,
        'authors': inst.authors.all(),
        'ordinal': ordinal,
        'prev': ordinal-1,
        'next': ordinal+1 if ordinal < installment_count else 0,
        'installment_count': installment_count,
    }
    return render(request, 'installment.html', context)


@require_safe
def list_index(request):
    context = {
        'page_title': 'Lists',
        'lists': List.objects.all(),
    }
    return render(request, 'lists.html', context)


@require_safe
def list_page(request, pk):
    user_list = get_object_or_404(List, pk=pk)
    # TODO: put this Story link + codes query somewhere central
    stories = Story.objects.filter(list_entries__list=user_list) \
        .only('slug', 'title', 'slant') \
        .annotate(code_abbrs=Story.codes_sq()) \
        .iterator()
    context = {
        'page_title': 'Lists',
        'list': user_list,
        'stories': stories,
    }
    return render(request, 'list.html', context)


@require_http_methods(['PUT', 'DELETE'])
def list_toggle(request, pk, slug):
    try:
        user_list = List.objects.get(pk=pk)
        story = Story.objects.filter(slug=slug).only('pk').get()
        if request.method == 'PUT':
            story.list_entries.create(list=user_list)
        else:
            story.list_entries.filter(list=user_list).delete()
        return HttpResponse(status=204)
    except (List.DoesNotExist, Story.DoesNotExist, IntegrityError):
        return HttpResponse(status=304)