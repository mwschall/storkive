from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('Authors/<slug:slug>.html', views.author_page, name='author'),
    path('Authors/', views.author_index, name='authors'),
    path('Tags/<slug:abbr>.html', views.tag_page, name='tag'),
    path('Titles/', views.title_index, name='titles'),
    path('Titles/<slug:letter>.html', views.letter_index, name='letter'),
    path('<slug:slug>/', views.story_page, name='story'),
    path('<slug:slug>/<int:ordinal>.html', views.installment_page, name='installment'),
]
