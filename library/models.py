from io import BytesIO

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models, IntegrityError
from django.db.models import Min, Max, OuterRef, Subquery
from django.urls import reverse
from django.utils.functional import cached_property

from library.expressions import Concat, SQCount
from library.fields import CssField, ShortUUIDField
from library.managers import OrderedLowerManager
from library.mixins import AuthorsMixin, CodesMixin, DEFAULT_AUTHOR_SEP
from library.util import get_sort_name, get_author_slug, b64md5sum, inst_path, is_css_color


# TODO: Come up with a more specific name for this functionality. Or don't.
class List(models.Model):
    name = models.CharField(
        max_length=70,
        unique=True,
    )
    color = CssField(
        default='inherit',
    )
    priority = models.SmallIntegerField(
        default=0,
    )
    auto_sort = models.BooleanField(
        default=True,
    )

    @property
    def entry_count(self):
        return self.entries.count()

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ['-priority', 'name']

    def clean_fields(self, exclude=None):
        super(List, self).clean_fields(exclude)
        if 'color' not in exclude:
            if self.color and not is_css_color(self.color):
                raise ValidationError({'color': ['Not a valid css color.']})


class ListEntry(models.Model):
    list = models.ForeignKey(
        'List',
        related_name='entries',
        on_delete=models.CASCADE,
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    # ordinal = models.SmallIntegerField()
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('list', 'content_type', 'object_id')


class Source(models.Model):
    name = models.CharField(
        max_length=150,
    )
    abbr = models.CharField(
        max_length=15,
        blank=True,
    )
    website = models.URLField()

    def __str__(self):
        return str(self.name)


class Author(models.Model):
    name = models.CharField(
        max_length=150,
    )
    slug = models.SlugField(
        allow_unicode=True,
        max_length=70,
        unique=True,
    )
    email = models.EmailField(
        blank=True,
    )
    homepage = models.URLField(
        blank=True,
    )

    objects = OrderedLowerManager('name')

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse('author', args=[str(self.slug)])

    def _perform_unique_checks(self, unique_checks):
        errors = super(Author, self)._perform_unique_checks(unique_checks)
        try:
            slug = self.slug or get_author_slug(self.name)
            conflict = Author.objects \
                .filter(slug__iexact=slug) \
                .exclude(pk=self.pk) \
                .values_list('name', flat=True) \
                .get()
            err = self.unique_error_message(Author, ('name',))
            err.message = 'Existing author "%s" maps to the same slug.' % conflict
            errors.setdefault('name', []).append(err)
        except Author.DoesNotExist:
            pass

        return errors

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = get_author_slug(self.name)
        self.full_clean()
        super(Author, self).save(*args, **kwargs)


class Code(models.Model):
    abbr = models.CharField(
        primary_key=True,
        max_length=4,
    )
    name = models.CharField(
        max_length=50,
        blank=True,
    )

    def __str__(self):
        return str(self.abbr)

    class Meta:
        ordering = ['abbr']

    def get_absolute_url(self):
        return reverse('code', args=[str(self.abbr)])


class Slant(models.Model):
    abbr = models.CharField(
        primary_key=True,
        max_length=2,
        unique=True,
        verbose_name='css class',
        help_text='This cannot be changed.'
    )
    # TODO: cast to lowercase?
    description = models.CharField(
        max_length=50,
    )
    affinity = models.ForeignKey(
        'Code',
        verbose_name='code affinity',
        on_delete=models.PROTECT,
    )
    display_order = models.PositiveSmallIntegerField()

    def __str__(self):
        return str(self.abbr)

    class Meta:
        ordering = ['display_order']

    def get_absolute_url(self):
        return reverse('code', args=[str(self.affinity_id)])


class StoryDisplayManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset() \
            .annotate(author_dicts=Story.authors_sq(),
                      code_abbrs=Story.codes_sq(),
                      installment_count=Story.installment_count_sq(),
                      missing_count=Story.missing_count_sq())


class Story(models.Model, AuthorsMixin, CodesMixin):
    TITLE_LEN = 150
    SLUG_LEN = 70

    source = models.ForeignKey(
        'Source',
        related_name='stories',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    title = models.CharField(
        max_length=TITLE_LEN,
    )
    sort_title = models.CharField(
        max_length=TITLE_LEN,
    )
    slug = models.SlugField(
        max_length=SLUG_LEN,
        unique=True,
        # allow_unicode=True,
    )
    authors = models.ManyToManyField(Author, related_name='stories')
    published_on = models.DateField(
        blank=True,
        null=True,
    )
    updated_on = models.DateField(
        blank=True,
        null=True,
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
    )
    removed_at = models.DateTimeField(
        blank=True,
        null=True,
    )
    slant = models.ForeignKey(
        'Slant',
        related_name='stories',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    codes = models.ManyToManyField(
        Code,
        related_name='stories',
        blank=True,
    )
    synopsis = models.TextField(
        blank=True,
    )
    list_entries = GenericRelation(ListEntry, related_query_name='story')

    @cached_property
    def lists(self):
        entries = self.list_entries \
            .select_related('list') \
            .order_by('-list__priority', 'list__name') \
            .all()
        return [entry.list for entry in entries]

    @property
    def primary_list(self):
        try:
            return self.lists[0]
        except IndexError:
            return None

    @property
    def author_list(self):
        return self.authors.all()

    @property
    def code_list(self):
        return self.codes.all()

    @property
    def slant_cls(self):
        return self.slant_id

    @property
    def installment_count(self):
        if not hasattr(self, '_ic'):
            self._ic = self.current_installments.count()
        return self._ic

    @installment_count.setter
    def installment_count(self, value):
        self._ic = value

    @property
    def missing_count(self):
        return 1 if not self.installment_count else self._mc

    @missing_count.setter
    def missing_count(self, value):
        self._mc = value

    @cached_property
    def valid_installment_count(self):
        return self.current_installments.exclude(file='').count()

    @cached_property
    def current_installments(self):
        # return [inst for inst in self.installments.all() if inst.is_current]
        return self.installments.filter(is_current=True).order_by('ordinal')

    # @cached_property
    # def installment_dates(self):
    #     return self.installments.values('ordinal').annotate(
    #         date_published=Min('published_on'),
    #         date_updated=Max('published_on'),
    #     )

    @cached_property
    def installment_dates(self):
        qs = self.installments \
            .values('ordinal') \
            .order_by('ordinal') \
            .annotate(date_published=Min('published_on'),
                      date_updated=Max('published_on'))
        return {
            d['ordinal']: {
                'date_published': d['date_published'],
                'date_updated': d['date_updated'],
            }
            for d in qs
        }

    @cached_property
    def first_ordinal(self):
        try:
            return self.current_installments \
                .exclude(file='') \
                .order_by('ordinal') \
                .values_list('ordinal', flat=True)[0]
        except IndexError:
            return None

    @cached_property
    def last_ordinal(self):
        try:
            return self.current_installments \
                .exclude(file='') \
                .order_by('-ordinal') \
                .values_list('ordinal', flat=True)[0]
        except IndexError:
            return None

    objects = models.Manager()
    display_objects = StoryDisplayManager()

    def __str__(self):
        return str(self.title)

    class Meta:
        ordering = ['sort_title', 'published_on']
        verbose_name_plural = 'stories'

    @staticmethod
    def authors_sq(separator=DEFAULT_AUTHOR_SEP):
        return Subquery(Author.objects
                        .order_by()
                        .filter(stories__pk=OuterRef('pk'))
                        .annotate(names=Concat('name', separator=separator))
                        .values('names')
                        )

    @staticmethod
    def codes_sq():
        return Subquery(Code.objects
                        .order_by()
                        .filter(stories__pk=OuterRef('pk'))
                        .annotate(abbrs=Concat('abbr'))
                        .values('abbrs')
                        )

    @staticmethod
    def installment_count_sq():
        return SQCount(Installment.objects
                       .order_by()
                       .filter(story=OuterRef('pk'),
                               is_current=True)
                       )

    @staticmethod
    def missing_count_sq():
        return SQCount(Installment.objects
                       .filter(story__pk=OuterRef('pk'),
                               is_current=True,
                               file='')
                       )

    def get_absolute_url(self):
        return reverse('story', args=[str(self.slug)])

    def save(self, *args, **kwargs):
        if not self.sort_title:
            self.sort_title = get_sort_name(self.title)[:self.TITLE_LEN]
        self.full_clean()
        if not self.updated_on:
            self.updated_on = self.published_on
        super(Story, self).save(*args, **kwargs)


class Installment(models.Model):
    TITLE_LEN = 125

    LU_WORDS = 'w'
    LU_CHARS = 'c'
    LU_CHOICES = (
        (LU_WORDS, 'words'),
        (LU_CHARS, 'chars'),
    )

    FMT_HTML = 'html'
    FMT_MD = 'md'
    FMT_RST = 'rst'
    FMT_TXT = 'txt'
    FMT_CHOICES = (
        (FMT_HTML, 'HTML'),
        (FMT_MD, 'Markdown'),
        (FMT_RST, 'reStructuredText'),
        (FMT_TXT, 'Plain Text'),
    )

    story = models.ForeignKey(
        'Story',
        related_name='installments',
        on_delete=models.CASCADE,
    )
    ordinal = models.SmallIntegerField()
    is_current = models.BooleanField(
        default=True,
    )
    title = models.CharField(
        max_length=TITLE_LEN,
    )
    authors = models.ManyToManyField(Author)
    published_on = models.DateField()
    added_at = models.DateTimeField(
        auto_now_add=True,
    )
    length = models.IntegerField(
        default=0,
    )
    length_unit = models.CharField(
        max_length=1,
        choices=LU_CHOICES,
        default=LU_WORDS,
    )
    file = models.FileField(
        # see: library.util.story_path
        # PREFIX + LETTER + 2xSLUG + ordinal + date + ext
        max_length=15 + 2 + 2*(Story.SLUG_LEN+1) + 4 + 11 + 5
    )
    checksum = models.CharField(
        max_length=64,
        blank=True,
    )

    @property
    def file_as_html(self):
        if self.file:
            with self.file.open(mode='r') as f:
                html = f.read()
            return html
        else:
            return None

    @file_as_html.setter
    def file_as_html(self, value):
        assert isinstance(value, str), 'Expected a string; cannot delete here.'

        if not value:
            return

        buf = BytesIO(value.encode('utf-8'))
        checksum = b64md5sum(buf)
        if checksum != self.checksum:
            buf.seek(0)
            file_path = inst_path(self.story.slug, self.ordinal, self.published_on)
            self.file.save(file_path, buf)
            self.checksum = checksum

    @cached_property
    def versions(self):
        # NOTE: this only good if prefetching all versions of all whatevers
        installments = self.story.installments.all()
        versions = [inst for inst in installments if inst.ordinal == self.ordinal]
        # return sorted(versions, key=lambda inst: inst.published_on)
        return versions

        # return self.story.installments.filter(ordinal=self.ordinal)

    @property
    def exists(self):
        return True if self.file else False

    @property
    def date_published(self):
        dates = self.story.installment_dates[self.ordinal]
        return dates['date_published'] if dates['date_published'].year > 1 else None

        # return self.versions[0].published_on

    @property
    def date_updated(self):
        dates = self.story.installment_dates[self.ordinal]
        published_on = dates['date_published']
        updated_on = dates['date_updated']
        return updated_on if updated_on != published_on else None

        # published_on = self.date_published_on
        # updated_on = self.versions[-1].published_on
        # return updated_on if updated_on != published_on else None

    @property
    def story_str(self):
        return '{} [{:03d}]'.format(self.story.title, self.ordinal)

    def __str__(self):
        return '{} [{:03d}] ~ {}'.format(self.story.title, self.ordinal, self.title)

    class Meta:
        unique_together = ('story', 'ordinal', 'published_on')

    @staticmethod
    def _ord_seeker(forward=True):
        qs = Installment.objects \
            .filter(story__pk=OuterRef('story__pk'), is_current=True) \
            .exclude(file='') \
            .values_list('ordinal', flat=True)

        if forward:
            return qs.filter(ordinal__gt=OuterRef('ordinal')).order_by('ordinal')
        else:
            return qs.filter(ordinal__lt=OuterRef('ordinal')).order_by('-ordinal')

    @staticmethod
    def prev_sq():
        return Subquery(Installment._ord_seeker(False))

    @staticmethod
    def next_sq():
        return Subquery(Installment._ord_seeker(True))

    def get_absolute_url(self):
        return reverse('installment', args=[str(self.story.slug), int(self.ordinal)])

    def save(self, *args, **kwargs):
        # TODO: fixup is_current
        super(Installment, self).save(*args, **kwargs)


class SagaDisplayManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset() \
            .annotate(author_dicts=Saga.authors_sq(),
                      code_abbrs=Saga.codes_sq(),
                      updated_on=Saga.updated_on_sq(),
                      entry_count=Saga.entry_count_sq())


class Saga(models.Model, AuthorsMixin, CodesMixin):
    slug = ShortUUIDField(
        primary_key=True,
    )
    name = models.CharField(
        max_length=Story.TITLE_LEN,
    )
    sort_name = models.CharField(
        max_length=Story.TITLE_LEN,
    )
    synopsis = models.TextField()
    stories = models.ManyToManyField(
        'Story',
        through='SagaEntry',
        related_name='sagas',
    )

    @property
    def stories_ordered(self):
        return self.stories.order_by('sagaentry__order')

    @property
    def entry_count(self):
        if not hasattr(self, '_ec'):
            self._ec = self.stories.count()
        return self._ec

    @entry_count.setter
    def entry_count(self, value):
        self._ec = value

    @property
    def current_index(self):
        return self._ci

    @current_index.setter
    def current_index(self, value):
        self._ci = value

    @cached_property
    def prev_entry(self):
        if self.current_index and 1 < self.current_index:
            # current_index is 1-indexed
            return self.stories_ordered.all()[self.current_index-2]
        return None

    @cached_property
    def next_entry(self):
        if self.current_index and self.current_index < self.entry_count:
            # current_index is 1-indexed
            return self.stories_ordered.all()[self.current_index]
        return None

    objects = models.Manager()
    display_objects = SagaDisplayManager()

    def __str__(self):
        return '{} [{}]'.format(self.name, self.slug)

    class Meta:
        ordering = ['sort_name']

    def get_absolute_url(self):
        return reverse('saga', args=[str(self.slug)])

    def save(self, *args, **kwargs):
        if not self.sort_name:
            self.sort_name = get_sort_name(self.name)[:Story.TITLE_LEN]

        # TODO: is this safe? no, it's not...
        while True:
            try:
                super(Saga, self).save(*args, **kwargs)
                break
            except IntegrityError:
                self.slug = ShortUUIDField.gen()

    @staticmethod
    def authors_sq(separator=DEFAULT_AUTHOR_SEP):
        return Subquery(Author.objects
                        .order_by()
                        .filter(stories__sagas__pk=OuterRef('pk'))
                        .annotate(names=Concat('name', separator=separator))
                        .values('names')
                        )

    @staticmethod
    def codes_sq():
        return Subquery(Code.objects
                        .order_by()
                        .filter(stories__sagas__pk=OuterRef('pk'))
                        .annotate(abbrs=Concat('abbr', distinct=True))
                        .values('abbrs')
                        )

    @staticmethod
    def updated_on_sq():
        return Subquery(Installment.objects
                        .order_by('-published_on')
                        .filter(story__sagas__pk=OuterRef('pk'),
                                is_current=True)
                        .values('published_on')[:1]
                        )

    @staticmethod
    def entry_count_sq():
        return SQCount(Story.objects
                       .order_by()
                       .filter(sagas__pk=OuterRef('pk'))
                       )

    @staticmethod
    def current_index_sq(story):
        return Subquery(SagaEntry.objects
                        .values_list('order', flat=True)
                        .filter(story=story, saga_id=OuterRef('pk'))
                        )


class SagaEntry(models.Model):
    saga = models.ForeignKey('Saga', on_delete=models.CASCADE)
    story = models.ForeignKey('Story', on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()
    # TODO: for stories that already include a grouping in their titles?
    # short_title = models.CharField(
    #     max_length=Story.TITLE_LEN,
    #     blank=True,
    # )

    def __str__(self):
        return str(self.story.slug)

    class Meta:
        ordering = ['order']
        unique_together = ('saga', 'story')


class Theme(models.Model):
    slug = ShortUUIDField(
        primary_key=True,
    )
    name = models.CharField(
        max_length=50,
        unique=True,
    )
    css = models.TextField()
    active = models.BooleanField(
        default=False,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    objects = OrderedLowerManager('name')

    def __str__(self):
        return str(self.name)

    # TODO: atomic?
    def save(self, *args, **kwargs):
        # https://stackoverflow.com/a/44720466
        if self.active:
            qs = type(self).objects.filter(active=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            qs.update(active=False)

        super(Theme, self).save(*args, **kwargs)
