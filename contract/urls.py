from django.urls import path
from . import views

app_name = 'contract'

urlpatterns = [
    path('<uuid:chatroom_id>/upload/', views.upload_contract, name='upload'),
    path('<uuid:chatroom_id>/', views.get_contract, name='get_contract'),
    path('<uuid:chatroom_id>/property/', views.update_property, name='update_property'),
]
