from django.urls import reverse


# noinspection PyUnusedLocal
def site_processor(request):
    url_name = request.resolver_match.url_name
    site_links = [
        {'name': 'whats_new', 'href': reverse('whats_new'), 'label': "What's New"},
        {'name': 'titles', 'href': reverse('titles'), 'label': 'Titles'},
        {'name': 'authors', 'href': reverse('authors'), 'label': 'Authors'},
        {'name': 'tags', 'href': reverse('tags'), 'label': 'Categories'},
    ]
    return {'site_links': [sl for sl in site_links if sl['name'] != url_name]}
