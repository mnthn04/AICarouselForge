from django.urls import path
from . import views

urlpatterns = [
    # Page views
    path('', views.index, name='index'),
    path('editor/<int:project_id>/', views.editor, name='editor'),
    path('result/<int:project_id>/', views.result, name='result'),
    
    # API Endpoints
    path('api/generate-carousel/', views.generate_canva_carousel, name='generate_carousel'),
    path('api/generate-image/', views.generate_slide_image, name='generate_image'),
    path('api/generate-and-apply/', views.generate_and_apply_image, name='generate_and_apply_image'),
    path('api/regenerate-slide/', views.regenerate_slide_content, name='regenerate_slide'),
    path('api/update-slide/', views.update_slide, name='update_slide'),
    path('api/generate-all-images/', views.generate_all_images, name='generate_all_images'),
    path('api/project/<int:project_id>/slides/', views.get_project_slides, name='get_project_slides'),
    path('api/test-openai/', views.test_openai, name='test_openai'),
    path('api/debug-generate/', views.debug_generate, name='debug_generate'),
]