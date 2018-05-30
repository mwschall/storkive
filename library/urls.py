from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('WhatsNew.html', views.whats_new, name='whats_new'),
    path('Authors/index.html', views.author_index, name='authors'),
    path('Authors/<slug:author>.html', views.author_page, name='author'),
    path('Codes/index.html', views.code_index, name='codes'),
    path('Codes/<slug:abbr>.html', views.code_page, name='code'),
    path('Lists/index.html', views.list_index, name='lists'),
    path('Lists/<int:pk>.html', views.list_page, name='list'),
    path('Sagas/index.html', views.saga_index, name='sagas'),
    path('Sagas/<slug:saga>/index.html', views.saga_page, name='saga'),
    path('Sagas/<slug:saga>/Entries/<slug:story>/index.html', views.story_page, name='saga_story'),
    path('Sagas/<slug:saga>/Entries/<slug:story>/<int:ordinal>.html', views.installment_page, name='saga_installment'),
    path('Titles/index.html', views.letter_index, name='titles'),
    path('Titles/<slug:letter>.html', views.letter_page, name='letter'),
    path('ajax/lists/<int:pk>/entries/<slug:story>', views.list_toggle),
    path('<slug:story>/index.html', views.story_page, name='story'),
    path('<slug:story>/<int:ordinal>.html', views.installment_page, name='installment'),
]
