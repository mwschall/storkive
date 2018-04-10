import re

from django.db import models


def get_sort_name(name):
    name = name.strip().lower()
    name = re.sub(r'\s+', ' ', name)
    return re.match(r'^(?:the |a |an )?(.*)$', name).group(1)


class Library(models.Model):
    name = models.CharField(
        max_length=150,
    )
    website = models.URLField()


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

    class Meta:
        ordering = ('slug',)

    def __str__(self):
        return self.name

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
        unique=True,
        blank=True,
    )


class Story(models.Model):
    source = models.ForeignKey(
        'Library',
        related_name='stories',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    title = models.CharField(
        max_length=150,
    )
    sort_title = models.CharField(
        max_length=150,
    )
    slug = models.SlugField(
        max_length=70,
        unique=True,
        # allow_unicode=True,
    )
    authors = models.ManyToManyField(Author)
    added = models.DateField(
        blank=True,
        null=True,
    )
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
    tags = models.ManyToManyField(Tag)
    synopsis = models.TextField()

    class Meta:
        ordering = ('sort_title',)
        verbose_name_plural = "stories"

    def save(self, *args, **kwargs):
        if not self.sort_title:
            self.sort_title = get_sort_name(self.title)
        self.full_clean()
        super(Story, self).save(*args, **kwargs)


class Chapter(models.Model):
    story = models.ForeignKey(
        'Story',
        related_name='chapters',
        on_delete=models.CASCADE,
    )
    title = models.CharField(
        max_length=200,
    )
    ordinal = models.SmallIntegerField()
    span = models.SmallIntegerField(
        default=1,
    )
    # NOTE: these could be generated, or have meaning beyond what's in the DB
    # added = models.DateField()
    # updated = models.DateField()


class ChapterVersion(models.Model):
    LU_WORDS = 'w'
    LU_CHARS = 'c'
    LU_CHOICES = (
        (LU_WORDS, 'words'),
        (LU_CHARS, 'chars'),
    )

    FMT_HTML = 'html'
    FMT_MD = 'md'
    FMT_RST = 'rst'
    FMT_CHOICES = (
        (FMT_HTML, 'HTML'),
        (FMT_MD, 'Markdown'),
        (FMT_RST, 'reStructuredText'),
    )

    chapter = models.ForeignKey(
        'Chapter',
        related_name='versions',
        on_delete=models.CASCADE,
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
    text = models.TextField()
    text_fmt = models.CharField(
        max_length=4,
        choices=FMT_CHOICES,
        default=FMT_HTML,
    )
