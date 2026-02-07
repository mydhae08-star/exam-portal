from django.urls import path
from . import views

urlpatterns = [
    path("test/", views.test_import, name="test_import"),
    path("choose/", views.choose_exam, name="choose_exam"),
    path("exam/<str:exam_id>/start/", views.start_exam, name="start_exam"),
    path("q/<int:q_index>/", views.question_page, name="question_page"),
    path("result/", views.exam_result, name="exam_result"),
    path("result/download/", views.download_result, name="download_result"),

]
