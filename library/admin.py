from adminsortable2.admin import SortableInlineAdminMixin, SortableAdminMixin
from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count

from library.forms import TextField
from library.models import Author, Installment, Story, Code, Source, List, Saga, SagaEntry, Slant, Theme, UserProfile


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    search_fields = ['name', 'slug']
    exclude = ['slug']


@admin.register(Code)
class CodeAdmin(admin.ModelAdmin):
    list_display = ('abbr', 'name')
    search_fields = ['abbr']


@admin.register(Slant)
class SlantAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('abbr', 'description')
    search_fields = ['abbr', 'description']

    autocomplete_fields = ['affinity']
    fields = (
        'abbr',
        'description',
        'affinity',
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['abbr']
        else:
            return []


class InstallmentAdminForm(forms.ModelForm):
    file_as_html = TextField(
        widget=forms.Textarea(attrs={'rows': 40, 'cols': 80}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        # only populate if editing and not saving
        # called from django.contrib.admin.ModelAdmin._changeform_view()
        if instance and not len(args):
            if not kwargs.get('initial'):
                kwargs['initial'] = {}
            kwargs['initial'].update({'file_as_html': instance.file_as_html})
        super().__init__(*args, **kwargs)

    class Meta:
        model = Installment
        fields = (
            'story',
            'ordinal',
            'title',
            'authors',
            'published_on',
            'file_as_html',
        )


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    list_display = ('story_str', 'published_on', 'title')
    ordering = ('story', 'ordinal', 'published_on')
    search_fields = ['story__slug', 'published_on']
    form = InstallmentAdminForm
    autocomplete_fields = ['story', 'authors']

    def get_queryset(self, request):
        return super().get_queryset(request) \
            .select_related('story')

    def save_model(self, request, obj, form, change):
        obj.file_as_html = form.cleaned_data['file_as_html']
        # raise NotImplementedError
        super().save_model(request, obj, form, change)


class InstallmentInline(admin.TabularInline):
    model = Installment
    classes = ['collapse']
    extra = 0

    fields = (
        'ordinal',
        'published_on',
        'title',
        'length',
    )
    readonly_fields = (
        'ordinal',
        'published_on',
        'title',
        'length',
    )
    show_change_link = True


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slant', 'published_on')
    list_filter = ('published_on', )
    search_fields = ['slug', 'title']

    autocomplete_fields = ['authors', 'codes', 'slant']
    exclude = ['sort_title']
    inlines = [
        InstallmentInline,
    ]


@admin.register(List)
class ListAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'priority', 'entry_count')
    ordering = ('user__username', '-priority', 'name')

    def get_queryset(self, request):
        return super().get_queryset(request) \
            .annotate(entry_count=Count('entries'))

    fields = (
        'slug',
        'user',
        'name',
        'color',
        'priority',
        'auto_sort',
    )
    readonly_fields = ['slug']


class SagaEntryInline(SortableInlineAdminMixin, admin.TabularInline):
    model = SagaEntry
    extra = 0

    autocomplete_fields = ['story']


@admin.register(Saga)
class SagaAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'entry_count')

    exclude = ['sort_name']
    fields = (
        'slug',
        'name',
        'synopsis',
    )
    readonly_fields = ['slug']
    inlines = [
        SagaEntryInline,
    ]


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'active')
    fields = (
        'name',
        'active',
        'css',
    )


class ProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'


class UserAdmin(BaseUserAdmin):
    inlines = [
        ProfileInline,
    ]


admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), UserAdmin)
