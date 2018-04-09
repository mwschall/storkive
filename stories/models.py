from django.db import models


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


class Tag(models.Model):
    abbr = models.CharField(
        max_length=4,
    )
    name = models.CharField(
        max_length=50,
        unique=True,
    )


class Story(models.Model):
    title = models.CharField(
        max_length=150,
    )
    sort_title = models.CharField(
        max_length=150,
    )
    slug = models.SlugField(
        max_length=70,
        allow_unicode=True,
        unique=True,
    )
    authors = models.ManyToManyField(Author)
    added = models.DateField(
        blank=True,
    )
    updated = models.DateField(
        blank=True,
    )
    removed = models.DateField(
        blank=True,
    )
    slant = models.CharField(
        max_length=2,
        blank=True,
    )
    tags = models.ManyToManyField(Tag)
    primary_tag = models.ForeignKey(
        'Tag',
        on_delete=models.PROTECT,
        related_name='+',
    )
    synopsis = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ('sort_title',)
        verbose_name_plural = "stories"


class Chapter(models.Model):
    LU_WORDS = 'w'
    LU_CHARS = 'c'
    LU_CHOICES = (
        (LU_WORDS, 'words'),
        (LU_CHARS, 'chars'),
    )
    story = models.ForeignKey(
        'Story',
        on_delete=models.CASCADE,
        related_name='chapters',
    )
    order = models.SmallIntegerField()
    # version = models.SmallIntegerField()
    title = models.CharField(
        max_length=50,
    )
    authors = models.ManyToManyField(Author)
    added = models.DateField()
    updated = models.DateField()
    length = models.IntegerField(
        default=0,
    )
    length_unit = models.CharField(
        max_length=1,
        choices=LU_CHOICES,
        default=LU_WORDS,
    )
    text = models.TextField()
