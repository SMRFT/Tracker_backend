from django.urls import path
from .views import RegisterView,BoardsView,LoginView,upload_content,CardCreateView,update_card,get_file,save_description,get_files,delete_file,save_comment,get_comments
from django.conf import settings
from django.conf.urls.static import static
from .views import GetBoardsView,get_all_employees,add_member_to_card,get_dynamic_notifications,delete_comment,update_card_dates,edit_comment
urlpatterns = [
    path('register/', RegisterView, name='register'),
    path('login/', LoginView, name='login'),
    path('upload-content/', upload_content, name='upload_content'),
    path('cards/', CardCreateView, name='card-list'),  # For creating/listing cards
    path('cards/<str:card_id>/', CardCreateView, name='card-detail'),  # For retrieving/deleting specific cards by cardId
    path('cards/<str:card_id>/', update_card, name='update_card'),
    path('boards/', BoardsView, name='boards-list'),  # For GET and POST requests
    path('boards/<int:boardId>/', BoardsView, name='board-detail'),  # For PUT and DELETE requests
    path('get-file/<str:board_id>/<str:card_id>/', get_file, name='get_file'),
    path('save-description/', save_description, name='save_description'),
    path('get-files/', get_files, name='get_files'),
    path('delete-file/<str:board_id>/<str:card_id>/<str:filename>/', delete_file, name='delete_file'),
    path('save_comment/', save_comment, name='save_comment'),
    path('get_comments/', get_comments, name='get_comments'),
    path('get-boards/', GetBoardsView, name='boards-list'),  # For GET 
    path('boards/<int:boardId>/', BoardsView, name='board-detail'),  # For PUT and DELETE requests
    path('get-employees/', get_all_employees, name='get_all_employees'),
    path('add_member_to_card/', add_member_to_card, name='add_member_to_card'),
    path('notifications/', get_dynamic_notifications, name='get_notifications'),
    path('delete_comment/', delete_comment, name='delete_comment'),
    path('cards/<str:card_id>/', update_card_dates, name='update-card-dates'),
    path('edit_comment/', edit_comment, name='edit_comment'),

  
]
