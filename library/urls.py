import django.contrib.auth.views as auth_views
from django.urls import path, register_converter

from library.converters import FourDigitYearConverter, ShortUUIDConverter
from . import views

register_converter(FourDigitYearConverter, 'yyyy')
register_converter(ShortUUIDConverter, 'suuid')

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('theme-<suuid:theme>.css', views.theme_css, name='theme'),
    path('WhatsNew.html', views.whats_new, name='whats_new'),
    path('WhatWasNew.html', views.what_was_new, name='what_was_new'),
    path('WhatWasNew<yyyy:year>.html', views.what_was_new, name='wwn_year'),
    path('Authors/index.html', views.author_index, name='authors'),
    path('Authors/<slug:author>.html', views.author_page, name='author'),
    path('Codes/index.html', views.code_index, name='codes'),
    path('Codes/<slug:abbr>.html', views.code_page, name='code'),
    path('Lists/index.html', views.list_index, name='lists'),
    path('Lists/<suuid:coll>/', views.list_page, name='list'),
    path('Sagas/index.html', views.saga_index, name='sagas'),
    path('Sagas/<suuid:saga>/', views.saga_page, name='saga'),
    path('Sagas/<suuid:saga>/<slug:story>/index.html', views.story_page, name='saga_story'),
    path('Sagas/<suuid:saga>/<slug:story>/<int:ordinal>.html', views.installment_page, name='saga_installment'),
    path('Titles/index.html', views.letter_index, name='titles'),
    path('Titles/<slug:letter>.html', views.letter_page, name='letter'),
    path('ajax/lists/<suuid:coll>/entries/<slug:story>', views.list_toggle),
    path('<slug:story>/index.html', views.story_page, name='story'),
    path('<slug:story>/<int:ordinal>.html', views.installment_page, name='installment'),
]
