from collections import Iterable
from io import BytesIO

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Min, Max, OuterRef, Subquery
from django.urls import reverse
from django.utils.functional import cached_property

from library.expressions import Concat
from library.managers import OrderedLowerManager
from library.util import get_sort_name, get_author_slug, b64md5sum, inst_path, is_css_color

DEFAULT_AUTHOR_SEP = '|'
DEFAULT_CODE_SEP = ' '


# TODO: Come up with a more specific name for this functionality. Or don't.
class List(models.Model):
    name = models.CharField(
        max_length=70,
        unique=True,
    )
    color = models.CharField(
        max_length=25,
        default='inherit',
    )
    priority = models.SmallIntegerField(
        default=0,
    )
    auto_sort = models.BooleanField(
        default=True,
    )

    @property
    def num_entries(self):
        return self.entries.count()

    def __str__(self):
        return self.name

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
    added_at = models.DateTimeField(
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
        return self.name


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
        return self.name

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
        return self.abbr

    class Meta:
        ordering = ['abbr']


class Story(models.Model):
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
    added = models.DateField(
        blank=True,
        null=True,
    )
    # TODO: generate this from chapter data?
    updated = models.DateField(
        blank=True,
        null=True,
    )
    removed = models.DateField(
        blank=True,
        null=True,
    )
    slant = models.CharField(
        max_length=2,
        blank=True,
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
    def author_dicts(self):
        dicts = self._author_dicts
        return dicts

    @author_dicts.setter
    def author_dicts(self, value):
        self._author_dicts = [
            {'name': name, 'slug': get_author_slug(name)}
            for name in value.split(DEFAULT_AUTHOR_SEP)
        ]

    @property
    def code_abbrs(self):
        return self._code_abbrs

    @code_abbrs.setter
    def code_abbrs(self, value):
        if isinstance(value, str):
            self._code_abbrs = value.split(DEFAULT_CODE_SEP)
        elif isinstance(value, Iterable):
            self._code_abbrs = value
        else:
            self._code_abbrs = []

    @property
    def num_installments(self):
        return self.current_installments.count()

    @cached_property
    def current_installments(self):
        # return [inst for inst in self.installments.all() if inst.is_current]
        return self.installments.filter(is_current=True).order_by('ordinal')

    # @cached_property
    # def installment_dates(self):
    #     return self.installments.values('ordinal').annotate(
    #         date_added=Min('added'),
    #         date_updated=Max('added'),
    #     )

    @cached_property
    def installment_dates(self):
        return {
            d['ordinal']: {
                'date_added': d['date_added'],
                'date_updated': d['date_updated'],
            }
            for d in
            self.installments.values('ordinal').order_by('ordinal').annotate(
                date_added=Min('added'),
                date_updated=Max('added'),
            )
        }

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['sort_title']
        verbose_name_plural = "stories"

    @staticmethod
    def authors_sq(separator=DEFAULT_AUTHOR_SEP):
        return Subquery(Author.objects
                        .order_by()
                        .filter(stories__pk=OuterRef('pk'))
                        .annotate(names=Concat('name', separator=separator))
                        .values_list('names', flat=True)
                        )

    @staticmethod
    def codes_sq(separator=DEFAULT_CODE_SEP):
        return Subquery(Code.objects
                        .order_by()
                        .filter(stories__pk=OuterRef('pk'))
                        .annotate(abbrs=Concat('abbr', separator=separator))
                        .values_list('abbrs', flat=True)
                        )

    def get_absolute_url(self):
        return reverse('story', args=[str(self.slug)])

    def save(self, *args, **kwargs):
        if not self.sort_title:
            self.sort_title = get_sort_name(self.title)[:self.TITLE_LEN]
        self.full_clean()
        if not self.updated:
            self.updated = self.added
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
    added = models.DateField()
    # TODO: published date?
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
            file_path = inst_path(self.story.slug, self.ordinal, self.added)
            self.file.save(file_path, buf)
            self.checksum = checksum

    @cached_property
    def versions(self):
        # NOTE: this only good if prefetching all versions of all whatevers
        installments = self.story.installments.all()
        versions = [inst for inst in installments if inst.ordinal == self.ordinal]
        # return sorted(versions, key=lambda inst: inst.added)
        return versions

        # return self.story.installments.filter(ordinal=self.ordinal)

    @property
    def date_added(self):
        dates = self.story.installment_dates[self.ordinal]
        return dates['date_added']

        # return self.versions[0].added

    @property
    def date_updated(self):
        dates = self.story.installment_dates[self.ordinal]
        added = dates['date_added']
        updated = dates['date_updated']
        return updated if updated != added else None

        # added = self.date_added
        # updated = self.versions[-1].added
        # return updated if updated != added else None

    @property
    def story_str(self):
        return '{} [{:03d}]'.format(self.story.title, self.ordinal)

    def __str__(self):
        return '{} [{:03d}] ~ {}'.format(self.story.title, self.ordinal, self.title)

    class Meta:
        unique_together = ('story', 'ordinal', 'added')

    def get_absolute_url(self):
        return reverse('installment', args=[str(self.story.slug), int(self.ordinal)])

    def save(self, *args, **kwargs):
        # TODO: fixup is_current
        super(Installment, self).save(*args, **kwargs)
