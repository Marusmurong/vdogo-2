from django.urls import path
from . import views
from . import danmaku_views

app_name = 'files'

urlpatterns = [
    path('', views.index, name='home'),
    path('videos/', views.video_list, name='video_list'),
    path('category/<str:category_slug>/', views.category_view, name='category_view'),
    path('channel/<str:category_slug>/', views.channel_view, name='channel'),
    path('channel/<str:category_slug>/<str:subcategory_slug>/', views.subcategory_list, name='subcategory'),
    path('search/', views.search, name='search'),
    path('video/<int:video_id>/', views.video_detail, name='video_detail'),
    path('music/', views.music_list, name='music_list'),
    path('music/playlists/', views.playlist_list, name='playlist_list'),
    path('music/playlists/<int:playlist_id>/', views.playlist_detail, name='playlist_detail'),
    path('music/albums/', views.album_list, name='album_list'),
    path('music/albums/<int:album_id>/', views.album_detail, name='album_detail'),
    path('api/publish/content/', views.publish_content, name='publish_content'),
    path('api/publish/video/', views.publish_video, name='publish_video'),
    path('api/categories/<int:category_id>/children/', views.get_category_children, name='category_children'),
    path('api/categories/', views.get_categories, name='get_categories'),
    path('api/categories/<str:category_type>/', views.get_categories, name='get_categories_by_type'),
    
    # 弹幕相关API
    path('api/videos/<str:video_id>/danmaku/', danmaku_views.DanmakuList.as_view(), name='danmaku_list'),
    path('api/danmaku/<int:pk>/', danmaku_views.DanmakuDetail.as_view(), name='danmaku_detail'),
]
