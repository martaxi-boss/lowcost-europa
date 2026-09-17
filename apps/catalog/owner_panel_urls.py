from django.urls import path

from . import owner_panel_views as views

app_name = "owner-panel"
urlpatterns = [
    path("entrar/", views.owner_login, name="login"),
    path("sair/", views.owner_logout, name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("familias/<slug:family_slug>/", views.family_manage, name="family"),
    path(
        "familias/<slug:family_slug>/candidatos/<int:candidate_id>/aprovar/",
        views.candidate_approve,
        name="candidate-approve",
    ),
    path(
        "familias/<slug:family_slug>/candidatos/<int:candidate_id>/rejeitar/",
        views.candidate_reject,
        name="candidate-reject",
    ),
    path(
        "familias/<slug:family_slug>/candidatos/<int:candidate_id>/mover/",
        views.candidate_move,
        name="candidate-move",
    ),
    path(
        "familias/<slug:family_slug>/candidatos/<int:candidate_id>/revalidar/",
        views.candidate_revalidate,
        name="candidate-revalidate",
    ),
    path(
        "familias/<slug:family_slug>/ofertas/<int:offer_id>/retirar/",
        views.offer_hide,
        name="offer-hide",
    ),
    path(
        "familias/<slug:family_slug>/ofertas/<int:offer_id>/publicar/",
        views.offer_publish,
        name="offer-publish",
    ),
]
