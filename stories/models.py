from collections import Iterable

from django.db import models
from django.db.models import Min, Max, OuterRef, Subquery
from django.urls import reverse
from django.utils.functional import cached_property

from stories.expressions import Concat
from stories.managers import OrderedLowerManager
from stories.util import get_sort_name, get_author_slug

DEFAULT_AUTHOR_SEP = '|'
DEFAULT_TAG_SEP = ' '


class Library(models.Model):
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

    class Meta:
        verbose_name_plural = "libraries"


class Author(models.Model):
    name = models.CharField(
        max_length=150,
    )
    # TODO: verify uniqueness view Lower(slug)
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

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Author, self).save(*args, **kwargs)


class Tag(models.Model):
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
        'Library',
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
    tags = models.ManyToManyField(Tag, related_name='stories')
    synopsis = models.TextField()

    @property
    def author_list(self):
        return self.authors.all()

    @property
    def tag_list(self):
        return self.tags.all()

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
    def tag_abbrs(self):
        return self._tag_abbrs

    @tag_abbrs.setter
    def tag_abbrs(self, value):
        if isinstance(value, str):
            self._tag_abbrs = value.split(DEFAULT_TAG_SEP)
        elif isinstance(value, Iterable):
            self._tag_abbrs = value
        else:
            self._tag_abbrs = []

    @property
    def num_installments(self):
        return self.current_installments.count()

    @cached_property
    def current_installments(self):
        # return [inst for inst in self.installments.all() if inst.is_current]
        return self.installments.filter(is_current=True)

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
    def tags_sq(separator=DEFAULT_TAG_SEP):
        return Subquery(Tag.objects
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
        # see: stories.util.story_path
        # PREFIX + LETTER + 2xSLUG + ordinal + date + ext
        max_length=15 + 2 + 2*(Story.SLUG_LEN+1) + 4 + 11 + 5
    )
    checksum = models.CharField(
        max_length=64,
        blank=True,
    )

    @property
    def file_as_html(self):
        with self.file.open(mode='rb') as f:
            bytez = f.read()
        return bytez.decode('utf-8')

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

    def __str__(self):
        return '{} [{:03d}] ~ {}'.format(self.story.title, self.ordinal, self.title)

    class Meta:
        ordering = ['ordinal', 'added']
        unique_together = ('story', 'ordinal', 'added')

    def get_absolute_url(self):
        return reverse('installment', args=[str(self.story.slug), int(self.ordinal)])
