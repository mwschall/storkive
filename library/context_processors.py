from django.urls import reverse

from library.models import Slant, Theme


def site_processor(request):
    # figure out which theme to use
    try:
        current_theme = request.user.profile.theme
    except AttributeError:
        current_theme = Theme.objects.filter(active=True).first()

    # compute the nav links to show
    url_name = request.resolver_match.url_name
    site_links = [
        {'name': 'whats_new', 'href': reverse('whats_new'), 'label': "What's New"},
        {'name': 'titles', 'href': reverse('titles'), 'label': 'Titles'},
        {'name': 'sagas', 'href': reverse('sagas'), 'label': 'Sagas'},
        {'name': 'authors', 'href': reverse('authors'), 'label': 'Authors'},
        {'name': 'codes', 'href': reverse('codes'), 'label': 'Codes'},
    ]
    if request.user.is_authenticated:
        site_links.extend([
            {'name': 'lists', 'href': reverse('lists'), 'label': 'My Lists'},
            {'name': 'profile', 'href': reverse('user_profile'), 'label': 'Profile'},
        ])
    site_links = [sl for sl in site_links if sl['name'] != url_name]

    return {
        'current_theme': current_theme,
        'site_links': site_links,
        'slants': Slant.objects.all(),
    }
