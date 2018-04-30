from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('Authors/index.html', views.author_index, name='authors'),
    path('Authors/<slug:slug>.html', views.author_page, name='author'),
    path('Tags/index.html', views.tag_index, name='tags'),
    path('Tags/<slug:abbr>.html', views.tag_page, name='tag'),
    path('Titles/index.html', views.letter_index, name='titles'),
    path('Titles/<slug:letter>.html', views.letter_page, name='letter'),
    path('<slug:slug>/index.html', views.story_page, name='story'),
    path('<slug:slug>/<int:ordinal>.html', views.installment_page, name='installment'),
]
