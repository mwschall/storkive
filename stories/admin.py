from django.contrib import admin

from stories.models import Author, Installment, Story, Tag, Library


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('abbr', 'name')
    search_fields = ['abbr']


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    search_fields = ['abbr']

    autocomplete_fields = ['authors']


class InstallmentInline(admin.TabularInline):
    model = Installment
    classes = ['collapse']
    extra = 0

    fields = (
        'ordinal',
        'added',
        'title',
        'length',
    )
    readonly_fields = (
        'ordinal',
        'added',
        'title',
        'length',
    )
    show_change_link = True

    # def get_queryset(self, request):
    #     qs = super(InstallmentInline, self).get_queryset(request)
    #     return qs.filter(is_current=True)


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slant', 'added')
    list_filter = ('added', )
    search_fields = ['slug', 'title']

    autocomplete_fields = ['authors', 'tags']
    inlines = [
        InstallmentInline,
    ]
