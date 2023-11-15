from django.urls import path
from . import views

urlpatterns = [
  path('login/', views.loginuser, name='login'),
  path('logout/', views.logoutuser, name='logout'),

  path("", views.home, name="home"),
  path('home/', views.home, name='home'),

  path('sign-up/', views.role, name='role'),
  path('sign-up/<str:role>', views.sign_up, name='sign_up'),
  path('irregular', views.irreg_sign_up, name='irreg_sign_up'),
  path('irregular/<str:sections>', views.irreg_sign_up_subjects, name='irreg_sign_up_subjects'),
  path('profile/update', views.update_profile, name='update_profile'),

  path('evaluation/', views.evaluation_select, name='evaluation_select'),
  path('evaluation/<int:evaluated>', views.questionnaire, name='questionnaire'),

  path('evaluation/edit_students_questionnaire', views.edit_students_questionnaire, name='edit_students_questionnaire'),
  path('evaluation/edit_instructors_questionnaire', views.edit_instructors_questionnaire, name='edit_instructors_questionnaire'),
  path('evaluation/edit_students_questionnaire/<int:id>', views.update_students_questionnaire, name='update_students_questionnaire'),
  path('evaluation/edit_instructors_questionnaire/<int:id>', views.update_instructors_questionnaire, name='update_instructors_questionnaire'),
  path('evaluation/edit_students_questionnaire/add_<str:category>', views.add_students_questionnaire, name='add_students_questionnaire'),
  path('evaluation/edit_instructors_questionnaire/add_<str:category>', views.add_instructors_questionnaire, name='add_instructors_questionnaire'),
  path('evaluation/edit_students_questionnaire/delete_<int:id>', views.delete_students_questionnaire, name='delete_students_questionnaire'),
  path('evaluation/edit_instructors_questionnaire/delete_<int:id>', views.delete_instructors_questionnaire, name='delete_instructors_questionnaire'),

  path('evaluation/view', views.view_responses, name='view_responses'),
  path('evaluation/view/completion-chart', views.view_completion_chart, name='view_completion_chart'),
  path('evaluation/view/instructor-chart', views.view_instructor_chart, name='view_instructor_chart'),
  path('evaluation/view/instructor-chart/student-evaluation', views.view_instructor_chart_student, name='view_instructor_chart_student'),
  path('evaluation/view/instructor-chart/instructor-evaluation', views.view_instructor_chart_instructor, name='view_instructor_chart_instructor'),
  path('evaluation/view/instructor-chart/student-evaluation/<int:id>', views.view_instructor_chart_id_student, name='view_instructor_chart_id_student'),
  path('evaluation/view/instructor-chart/instructor-evaluation/<int:id>', views.view_instructor_chart_id_instructor, name='view_instructor_chart_id_instructor'),

  path('evaluation/view-subjects', views.view_subjects, name='view_subjects'),
  path('evaluation/view-subjects/edit/<int:id>', views.edit_subjects, name='edit_subjects'),
  path('evaluation/view-subjects/delete/<int:id>', views.delete_subjects, name='delete_subjects'),
  path('evaluation/view-subjects/add', views.add_subjects_pick, name='add_subjects_pick'),
  path('evaluation/view-subjects/add/single', views.add_subjects_single, name='add_subjects_single'),
  path('evaluation/view-subjects/add/bulk', views.add_subjects_bulk, name='add_subjects_bulk'),

  path('evaluation/edit-choice', views.edit_choice, name='edit_choice'),
  path('evaluation/edit-choice/bulk', views.add_bulk_instructor_per_section, name='add_bulk_instructor_per_section'),
  path('evaluation/edit-choice/edit-instructor', views.edit_instructor, name='edit_instructor'),
  path('evaluation/edit-choice/edit-instructor/<str:section>', views.edit_instructor_per_section, name='edit_instructor_per_section'),
  path('evaluation/edit-choice/edit-instructor/<str:section>/<int:id>', views.edit_instructor_per_id, name='edit_instructor_per_id'),
  path('evaluation/edit-choice/edit-instructor/<str:section>/<int:id>/delete', views.delete_instructor_per_id, name='delete_instructor'),
  path('evaluation/edit-choice/edit-instructor/<str:section>/add', views.add_instructor, name='add_instructor'),

  path('evaluation/dean', views.evaluation_select_dean, name='dean_evaluation_select'),
  path('evaluation/dean/<int:id>', views.questionnaire, name='dean_questionnaire'),
  
  path('settings', views.settings, name='settings'),
  path('settings/evaluation_sched', views.evalsched, name='evalsched'),
  path('settings/evaluation_sched/delete', views.delete_evalsched, name='delete_evalsched'),
]