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
        allow_unicode=True,
        max_length=70,
        unique=True,
    )
    authors = models.ManyToManyField(Author)
    added = models.DateField()
    updated = models.DateField()
    removed = models.DateField(
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
    story = models.ForeignKey(
        'Story',
        on_delete=models.CASCADE,
    )
    order = models.SmallIntegerField()
    # version = models.SmallIntegerField()
    title = models.CharField(
        max_length=50,
    )
    authors = models.ManyToManyField(Author)
    added = models.DateField()
    updated = models.DateField()


