from django.urls import path

from . import views

app_name = "catalog"
urlpatterns = [
    path("candidates/<slug:family_slug>/", views.candidate_queue, name="candidate-queue"),
    path(
        "candidates/<slug:family_slug>/<int:candidate_id>/approve/",
        views.candidate_approve,
        name="candidate-approve",
    ),
    path(
        "candidates/<slug:family_slug>/<int:candidate_id>/reject/",
        views.candidate_reject,
        name="candidate-reject",
    ),
    path(
        "candidates/<slug:family_slug>/<int:candidate_id>/revalidate/",
        views.candidate_revalidate,
        name="candidate-revalidate",
    ),
    path(
        "candidates/<slug:family_slug>/<int:candidate_id>/move/",
        views.candidate_move,
        name="candidate-move",
    ),
]
