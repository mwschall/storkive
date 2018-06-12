import datetime as dt
from itertools import groupby

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import F, Count, OuterRef, Min, Exists
from django.db.models.functions import Substr, Upper, ExtractYear, ExtractWeek
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_safe, require_http_methods, condition

from library.expressions import SQCount, ChillSubquery
from library.models import Author, Installment, List, Story, Code, Saga, Theme

ONE_DAY = 24 * 60 * 60


@require_safe
def index(request):
    return render(request, 'index.html')


@require_safe
# @cache_page(ONE_DAY)
def whats_new(request):
    last_two = Story.objects.values_list('updated_on', flat=True).order_by('-updated_on').distinct()[:2]

    def fetch_updates(date):
        new_insts_exist = Installment.objects \
            .order_by() \
            .filter(story=OuterRef('pk'), published_on=date)

        new_insts = Installment.objects \
            .order_by() \
            .filter(story_id=OuterRef('pk')) \
            .values('ordinal') \
            .annotate(ord_min=Min('published_on')) \
            .filter(ord_min=date)

        next_inst = Installment.objects \
            .order_by('ordinal') \
            .filter(story_id=OuterRef('pk')) \
            .values('ordinal') \
            .annotate(ord_min=Min('published_on')) \
            .filter(ord_min=date) \
            .values('ordinal')

        return Story.display_objects \
            .annotate(inst_on_date=Exists(new_insts_exist)) \
            .filter(inst_on_date=True) \
            .annotate(up_count=SQCount(new_insts),
                      next_inst=ChillSubquery(next_inst[:1])) \
            .iterator()

    days = [{'date': date, 'updates': fetch_updates(date)} for date in last_two]

    context = {
        'page_title': 'Recent Additions',
        'days': days,
    }
    return render(request, 'whats-new.html', context)


@require_safe
def what_was_new(request, year=None):
    this_year = dt.date.today().year
    if not year:
        year = this_year

    prev_year = Installment.objects \
        .annotate(year=ExtractYear('published_on')) \
        .filter(year__lt=year) \
        .order_by('-year') \
        .values_list('year', flat=True) \
        .first()

    prev_versions_sq = Installment.objects \
        .order_by() \
        .filter(story_id=OuterRef('story_id'),
                ordinal=OuterRef('ordinal'),
                published_on__lt=OuterRef('published_on')) \
        .values('pk')

    prev_insts_sq = Installment.objects \
        .order_by() \
        .annotate(year=ExtractYear('published_on'),
                  week=ExtractWeek('published_on')) \
        .filter(story_id=OuterRef('story_id'),
                published_on__lt=OuterRef('published_on')) \
        .exclude(year=OuterRef('year'), week=OuterRef('week')) \
        .values('pk')

    updates = Installment.objects \
        .order_by() \
        .values('story_id') \
        .annotate(year=ExtractYear('published_on'),
                  week=ExtractWeek('published_on'),
                  is_revision=Exists(prev_versions_sq),
                  is_update=Exists(prev_insts_sq),
                  up_count=Count('story_id')) \
        .filter(year=year, is_revision=False) \
        .order_by('-week', 'is_update', 'story__sort_title') \
        .values('story__title',
                'story__slug',
                'story__slant_id',
                'week',
                'is_update',
                'up_count',
                )

    def map_story(story):
        return {
            'title': story['story__title'],
            'slug': story['story__slug'],
            'slant_cls': story['story__slant_id'],
            'up_count': story['up_count'],
        }

    def make_week(number, stories):
        week = {
            'updated' if u else 'added': [map_story(s) for s in sl]
            for u, sl in groupby(stories, lambda s: s['is_update'])
        }
        week['number'] = number
        return week

    weeks = [make_week(n, s) for n, s in groupby(updates, lambda u: u['week'])]
    if not len(weeks):
        raise Http404('No updates in {:d}.'.format(year))

    context = {
        'page_title': 'Previously Recent' if year == this_year else
                      'What Was New in {:d}'.format(year),
        'year': year,
        'weeks': weeks,
        # TODO: fix this when allowing Installments with NULL published_on
        'prev_year': prev_year if prev_year and prev_year > 1 else None,
    }

    # TODO: missing_count
    return render(request, 'what-was-new.html', context)


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
# @cache_page(ONE_DAY, key_prefix='letter')
def letter_page(request, letter):
    stories = Story.display_objects \
        .filter(sort_title__istartswith=letter) \
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
def author_page(request, author):
    author = get_object_or_404(Author, slug=author)
    stories = author.stories \
        .only('slug', 'title', 'slant_id', 'published_on', 'updated_on') \
        .annotate(code_abbrs=Story.codes_sq(),
                  installment_count=Story.installment_count_sq(),
                  missing_count=Story.missing_count_sq())
    sagas = Saga.objects.filter(stories__authors__in=[author]).distinct()
    context = {
        'page_title': author.name,
        'author': author,
        'sagas': sagas,
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
# @cache_page(ONE_DAY, key_prefix='code')
def code_page(request, abbr):
    code = get_object_or_404(Code, abbr=abbr)
    stories = Story.display_objects \
        .filter(codes__abbr=abbr) \
        .only('slug', 'title', 'slant_id') \
        .iterator()
    context = {
        'page_title': 'Codes; '+abbr,
        'code': code,
        'stories': stories,
    }
    return render(request, 'code.html', context)


@require_safe
def saga_index(request):
    context = {
        'page_title': 'Sagas',
        'sagas': Saga.display_objects.all(),
    }
    return render(request, 'sagas.html', context)


@require_safe
def saga_page(request, saga):
    saga = get_object_or_404(Saga.display_objects, slug=saga)
    stories = saga.stories_ordered.all()
    context = {
        'page_title': saga.name,
        'saga': saga,
        'stories': stories,
    }
    return render(request, 'saga.html', context)


@require_safe
def story_page(request, story, saga=None):
    story = get_object_or_404(Story.display_objects, slug=story)
    installments = story.current_installments
    sagas = None

    if saga:
        qs = Saga.display_objects \
            .annotate(current_index=Saga.current_index_sq(story))
        saga = get_object_or_404(qs, slug=saga)
    else:
        sagas = story.sagas.only('slug', 'name').all()

    context = {
        'page_title': story.title,
        'saga': saga,
        'sagas': sagas,
        'story': story,
        'next': story.first_ordinal,
        'installment_count': story.installment_count,
    }

    if story.installment_count == 1:
        context['chapter'] = installments[0]
    elif not story.installment_count:
        context['chapter'] = {'title': story.title, 'exists': False}
    else:
        context['headers'] = [
            {'cls': 'wc', 'name': 'Length'},
            {'cls': 'cdate', 'name': 'Published'},
        ]
        # TODO: authors
        if next(filter(lambda inst: inst.date_updated, installments), None):
            context['headers'].append({'cls': 'mdate', 'name': 'Updated'})
        context['installments'] = installments

    try:
        context.update({
            'user_lists': request.user.lists.all(),
            'story_lists': story.user_lists(request.user),
        })
    except AttributeError:
        pass

    return render(request, 'title.html', context)


@require_safe
@login_required
def installment_page(request, story, ordinal, saga=None):
    qs = Story.objects.only('slug', 'title')
    story = get_object_or_404(qs, slug=story)
    inst = story.current_installments \
        .filter(ordinal=ordinal) \
        .annotate(story_title=F('story__title'),
                  prev=Installment.prev_sq(),
                  next=Installment.next_sq()) \
        .prefetch_related('authors') \
        .get()
    installment_count = story.installment_count
    title = inst.story_title
    if installment_count > 1:
        title = title + ' ({:d} of {:d})'.format(ordinal, installment_count)

    if saga:
        qs = Saga.display_objects \
            .annotate(current_index=Saga.current_index_sq(story))
        saga = get_object_or_404(qs, slug=saga)

    context = {
        'page_title': title,
        'saga': saga,
        'story': story,
        'inst': inst,
        'authors': inst.authors.all(),
        'ordinal': ordinal,
        'prev': inst.prev,
        'next': inst.next,
        'installment_count': installment_count,
    }
    return render(request, 'installment.html', context)


@require_safe
@login_required
def list_index(request):
    context = {
        'page_title': 'Lists',
        'lists': request.user.lists.all(),
    }
    return render(request, 'lists.html', context)


@require_safe
@login_required
def list_page(request, coll):
    user_list = get_object_or_404(List, slug=coll, user=request.user)
    stories = Story.display_objects \
        .filter(list_entries__list=user_list) \
        .only('slug', 'title', 'slant_id') \
        .iterator()
    context = {
        'page_title': user_list.name,
        'list': user_list,
        'stories': stories,
    }
    return render(request, 'list.html', context)


@require_http_methods(['PUT', 'DELETE'])
@login_required
def list_toggle(request, coll, story):
    try:
        user_list = List.objects.get(slug=coll, user=request.user)
        story = Story.objects.filter(slug=story).only('pk').get()
        if request.method == 'PUT':
            story.list_entries.create(list=user_list)
        else:
            story.list_entries.filter(list=user_list).delete()
        return HttpResponse(status=204)
    except (List.DoesNotExist, Story.DoesNotExist, IntegrityError):
        return HttpResponse(status=304)


def theme_last_modified(request, theme):
    try:
        return Theme.objects.values_list('updated_at', flat=True).get(slug=theme)
    except Theme.DoesNotExist:
        return None


@require_safe
@condition(last_modified_func=theme_last_modified)
def theme_css(request, theme):
    theme = get_object_or_404(Theme, slug=theme)
    return HttpResponse(theme.css, content_type='text/css')
