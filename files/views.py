from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from .models import Category, VideoMedia, Video, HotSearch, Actor, Director, Playlist, Album, Music
from cloud_music.models import Song, Album as CloudMusicAlbum, Playlist as CloudMusicPlaylist, Artist
from cms.models import Slide
from django.db.models import Q
import logging
import openai
from django.conf import settings
import json

logger = logging.getLogger(__name__)

def get_nav_context():
    """获取导航栏需要的上下文数据"""
    return {
        'main_categories': Category.objects.filter(
            parent__isnull=True,  # 一级类目
            is_active=True,
            show_in_menu=True
        ).order_by('order')
    }

def index(request):
    """首页视图"""
    # 获取幻灯片
    slides = Slide.objects.filter(
        position='home',
        is_active=True
    ).order_by('order')
    
    # 获取一级分类(用于热门分类展示)
    categories = Category.objects.filter(
        parent__isnull=True,
        is_active=True,
        show_in_menu=True
    ).prefetch_related('children').order_by('order')
    
    # 获取热门视频
    hot_videos = Video.objects.filter(
        is_active=True
    ).order_by('-play_count')[:12]
    
    context = {
        'slides': slides,
        'categories': categories,
        'hot_videos': hot_videos,
        **get_nav_context()  # 添加导航栏数据
    }
    
    return render(request, 'pages/home/index.html', context)

def category_view(request, category_slug):
    """分类视图"""
    # 获取分类
    category = get_object_or_404(Category, slug=category_slug)
    
    # 获取该分类下的视频
    videos = Video.objects.filter(
        categories=category,
        is_active=True
    ).order_by('-created_at')
    
    # 分页
    page = request.GET.get('page', 1)
    paginator = Paginator(videos, 20)  # 每页20个视频
    videos_page = paginator.get_page(page)
    
    context = {
        'category': category,
        'videos': videos_page,
        'is_channel_page': True,
        'current_category': category,
        **get_nav_context()  # 添加导航栏数据
    }
    
    return render(request, 'pages/category/detail.html', context)

def channel_view(request, category_slug):
    """频道页视图"""
    # 获取一级类目
    category = get_object_or_404(Category, slug=category_slug, is_root=True)
    
    # 发现频道使用独立模板和数据结构
    if category_slug == 'discover':
        # 获取分类参数
        subcategory_slug = request.GET.get('subcategory', None)
        
        # 获取发现页面的幻灯片
        slides = Slide.objects.filter(
            position='discover',
            is_active=True
        ).order_by('order')
        
        # 获取子分类及其视频数量
        subcategories = category.children.filter(is_active=True).order_by('order')
        
        # 基础查询 - 热门视频
        videos_query = Video.objects.filter(is_active=True)
        
        # 如果指定了子分类，筛选对应子分类的内容
        selected_subcategory = None
        if subcategory_slug:
            try:
                selected_subcategory = Category.objects.get(
                    slug=subcategory_slug,
                    parent=category,
                    is_active=True
                )
                videos_query = videos_query.filter(categories=selected_subcategory)
            except Category.DoesNotExist:
                pass
        
        # 获取热门视频
        hot_videos = videos_query.order_by('-play_count')[:20]

        context = {
            'slides': slides,
            'hot_videos': hot_videos,
            'is_channel_page': True,
            'current_category': category,
            'selected_subcategory': selected_subcategory,
            'subcategories': subcategories,
            **get_nav_context()  # 添加导航栏数据
        }
        return render(request, 'pages/discover.html', context)
    
    # 其他频道的处理逻辑
    # 获取该类目的幻灯片
    slides = Slide.objects.filter(
        position=category_slug,
        is_active=True
    ).order_by('order')
    
    # 如果没有找到该类目的幻灯片，使用首页幻灯片
    if not slides.exists():
        slides = Slide.objects.filter(
            position='home',
            is_active=True
        ).order_by('order')
    
    # 获取二级类目
    subcategories = Category.objects.filter(
        parent=category,
        is_active=True,
        show_in_menu=True
    ).order_by('order')
    
    # 获取该类目下的最新视频，确保只获取有效的视频对象
    latest_videos = Video.objects.filter(
        categories=category,
        is_active=True,
        id__isnull=False  # 确保有 ID
    ).order_by('-created_at')[:12]
    
    # 获取该类目下的热门视频，确保只获取有效的视频对象
    hot_videos = Video.objects.filter(
        categories=category,
        is_active=True,
        id__isnull=False  # 确保有 ID
    ).order_by('-play_count')[:12]
    
    # 检查幻灯片中的视频对象
    valid_slides = []
    for slide in slides:
        if hasattr(slide, 'video') and slide.video and slide.video.id:
            valid_slides.append(slide)
    
    context = {
        'category': category,
        'slides': valid_slides,
        'subcategories': subcategories,
        'latest_videos': latest_videos,
        'hot_videos': hot_videos,
        'is_channel_page': True,
        'current_category': category,
        **get_nav_context()  # 添加导航栏数据
    }
    
    return render(request, 'pages/channel/index.html', context)

def subcategory_list(request, category_slug, subcategory_slug):
    """二级类目列表页"""
    # 获取一级类目
    parent_category = get_object_or_404(Category, slug=category_slug, is_root=True)
    
    # 获取二级类目
    subcategory = get_object_or_404(Category, 
        slug=subcategory_slug, 
        parent=parent_category,
        show_in_menu=True
    )
    
    # 获取同级的其他二级类目
    sibling_categories = Category.objects.filter(
        parent=parent_category,
        show_in_menu=True
    ).exclude(id=subcategory.id).order_by('order')
    
    # 获取该二级类目下的视频
    videos = Video.objects.filter(
        categories=subcategory,
        is_active=True
    )
    
    # 获取筛选条件
    order_by = request.GET.get('order', '-created_at')  # 默认按创建时间倒序
    if order_by == 'play_count':
        videos = videos.order_by('-play_count')
    elif order_by == 'created_at':
        videos = videos.order_by('-created_at')
    
    # 分页
    page = request.GET.get('page', 1)
    paginator = Paginator(videos, 20)  # 每页20个视频
    videos_page = paginator.get_page(page)
    
    context = {
        'parent_category': parent_category,
        'category': subcategory,
        'sibling_categories': sibling_categories,
        'videos': videos_page,
        'current_order': order_by,
        'is_channel_page': True,
        'current_category': parent_category,
        **get_nav_context()  # 添加导航栏数据
    }
    
    return render(request, 'pages/channel/detail.html', context)

def search(request):
    """搜索视图"""
    query = request.GET.get('q', '')
    
    if query:
        # 搜索视频标题和描述
        videos = Video.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query),
            is_active=True
        ).order_by('-created_at')
        
        # 分页
        paginator = Paginator(videos, 20)  # 每页20个视频
        page = request.GET.get('page')
        videos = paginator.get_page(page)
    else:
        videos = []
    
    context = {
        'query': query,
        'videos': videos,
        **get_nav_context()  # 添加导航栏数据
    }
    
    return render(request, 'pages/search/index.html', context)

def video_detail(request, video_id):
    """视频详情页视图"""
    video = get_object_or_404(Video, id=video_id, is_active=True)
    
    context = {
        'video': video,
        **get_nav_context()
    }
    
    return render(request, 'pages/play/index.html', context)

@require_http_methods(['POST'])
def publish_content(request):
    """处理发布内容"""
    try:
        # 获取表单数据
        content = request.POST.get('content', '')
        category_id = request.POST.get('category')
        files = request.FILES.getlist('files[]')
        
        # 验证数据
        if not content or not files:
            return JsonResponse({
                'success': False,
                'message': '内容和文件不能为空'
            }, status=400)
            
        # 获取分类
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': '分类不存在'
            }, status=400)
            
        # 创建视频记录
        video = Video.objects.create(
            title=content[:50],  # 截取前50个字符作为标题
            description=content,
            user=request.user,
            is_active=True
        )
        
        # 添加分类
        video.categories.add(category)
        
        # 处理上传文件
        for file in files:
            # 验证文件类型和大小
            if file.size > 100 * 1024 * 1024:  # 100MB
                return JsonResponse({
                    'success': False,
                    'message': '文件大小不能超过100MB'
                }, status=400)
                
            if not file.content_type.startswith(('image/', 'video/')):
                return JsonResponse({
                    'success': False,
                    'message': '仅支持图片和视频文件'
                }, status=400)
                
            # 保存文件
            media = VideoMedia.objects.create(
                video=video,
                file=file,
                media_type='image' if file.content_type.startswith('image/') else 'video'
            )
            
        return JsonResponse({
            'success': True,
            'message': '发布成功',
            'video_id': video.id
        })
        
    except Exception as e:
        logger.error(f'发布失败: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': '发布失败，请稍后重试'
        }, status=500)

@require_http_methods(['POST'])
def publish_video(request):
    """处理视频发布"""
    try:
        # 获取表单数据
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        category_id = request.POST.get('category')
        video_file = request.FILES.get('video')
        
        # 验证数据
        if not title or not video_file:
            return JsonResponse({
                'success': False,
                'message': '标题和视频文件不能为空'
            }, status=400)
            
        # 获取分类
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': '分类不存在'
            }, status=400)
            
        # 验证文件类型和大小
        if video_file.size > 500 * 1024 * 1024:  # 500MB
            return JsonResponse({
                'success': False,
                'message': '视频大小不能超过500MB'
            }, status=400)
            
        if not video_file.content_type.startswith('video/'):
            return JsonResponse({
                'success': False,
                'message': '仅支持视频文件'
            }, status=400)
            
        # 创建视频记录
        video = Video.objects.create(
            title=title,
            description=description,
            user=request.user,
            is_active=True,
            video_type='short'  # 标记为短视频类型
        )
        
        # 添加分类
        video.categories.add(category)
        
        # 保存视频文件
        media = VideoMedia.objects.create(
            video=video,
            file=video_file,
            media_type='video'
        )
            
        return JsonResponse({
            'success': True,
            'message': '发布成功',
            'video_id': video.id
        })
        
    except Exception as e:
        logger.error(f'视频发布失败: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': '发布失败，请稍后重试'
        }, status=500)

def get_ai_description(name, role):
    """使用AI生成演员或导演的描述"""
    try:
        # 设置 OpenAI API
        openai.api_key = settings.OPENAI_API_KEY
        
        # 根据角色构建不同的提示
        if role == 'actor':
            prompt = f"请用100字简要介绍演员{name}的主要成就和代表作品。"
        else:  # director
            prompt = f"请用100字简要介绍导演{name}的导演风格和代表作品。"
        
        # 调用 OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的影视资料编辑。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI生成描述失败: {str(e)}")
        return f"{name}是一位知名{role=='actor' and '演员' or '导演'}。"

def process_cast(names, role_type):
    """处理演员或导演名单"""
    result = []
    for name in names.split('，'):  # 使用中文逗号分隔
        name = name.strip()
        if not name:
            continue
            
        if role_type == 'actor':
            person, created = Actor.objects.get_or_create(
                name=name,
                defaults={
                    'description': get_ai_description(name, 'actor'),
                    'status': 'active'
                }
            )
        else:  # director
            person, created = Director.objects.get_or_create(
                name=name,
                defaults={
                    'description': get_ai_description(name, 'director'),
                    'status': 'active'
                }
            )
        result.append(person)
    return result

@require_http_methods(["POST"])
def publish_movie(request):
    """发布影视内容"""
    try:
        data = json.loads(request.body)
        
        # 处理演员和导演
        actors = process_cast(data.get('actors', ''), 'actor')
        directors = process_cast(data.get('directors', ''), 'director')
        
        # 创建影视记录
        movie = Movie.objects.create(
            title=data['title'],
            description=data['description'],
            category_id=data['category_id'],
            region=data['region'],
            language=data['language'],
            year=data['year'],
            status=data['status'],
            update_cycle=data.get('update_cycle'),
            cover_image=data['cover_image']
        )
        
        # 添加关联
        movie.actors.set(actors)
        movie.directors.set(directors)
        
        # 处理视频文件...
        
        return JsonResponse({'status': 'success', 'message': '发布成功'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def get_categories(request, category_type=None):
    """获取分类列表"""
    try:
        # 根据类型过滤分类
        categories = Category.objects.filter(is_active=True)
        if category_type:
            categories = categories.filter(category_type=category_type)
        
        # 获取一级分类
        root_categories = categories.filter(parent__isnull=True).order_by('order')
        
        # 构建分类树
        result = []
        for category in root_categories:
            children = category.children.filter(is_active=True).order_by('order')
            result.append({
                'id': category.id,
                'name': category.name,
                'children': [{'id': child.id, 'name': child.name} for child in children]
            })
        
        return JsonResponse(result, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_category_children(request, category_id):
    """获取分类的子分类"""
    try:
        category = Category.objects.get(id=category_id)
        children = category.children.filter(is_active=True).order_by('order')
        subcategories = [{'id': child.id, 'name': child.name} for child in children]
        return JsonResponse(subcategories, safe=False)
    except Category.DoesNotExist:
        return JsonResponse([], safe=False)

def video_list(request):
    """视频列表页视图"""
    # 获取筛选条件
    category_id = request.GET.get('category')
    tag_id = request.GET.get('tag')
    sort = request.GET.get('sort', '-created_at')  # 默认按创建时间倒序
    
    # 构建查询
    videos = Video.objects.filter(is_active=True)
    
    # 分类筛选
    if category_id:
        videos = videos.filter(categories__id=category_id)
    
    # 标签筛选
    if tag_id:
        videos = videos.filter(tags__id=tag_id)
    
    # 排序
    if sort == 'popular':
        videos = videos.order_by('-play_count')
    elif sort == 'newest':
        videos = videos.order_by('-created_at')
    else:
        videos = videos.order_by('-created_at')
    
    # 分页
    page = request.GET.get('page', 1)
    paginator = Paginator(videos, 20)  # 每页20个视频
    videos_page = paginator.get_page(page)
    
    context = {
        'videos': videos_page,
        'categories': Category.objects.filter(is_active=True),
        'tags': Tag.objects.filter(is_active=True),
        'selected_category': category_id,
        'selected_tag': tag_id,
        'current_sort': sort,
        **get_nav_context()
    }
    
    return render(request, 'pages/video/list.html', context)

def music_list(request):
    """音乐列表页面"""
    # 获取所有音乐
    songs = Song.objects.all().order_by('-created_at')
    
    # 分页
    page = request.GET.get('page', 1)
    paginator = Paginator(songs, 20)
    songs_page = paginator.get_page(page)
    
    context = {
        'songs': songs_page,
        **get_nav_context()
    }
    return render(request, 'pages/music/list.html', context)

def playlist_list(request):
    """歌单列表页面"""
    # 获取所有歌单
    playlists = CloudMusicPlaylist.objects.filter(is_active=True).order_by('-created_at')
    
    # 分页
    page = request.GET.get('page', 1)
    paginator = Paginator(playlists, 20)
    playlists_page = paginator.get_page(page)
    
    context = {
        'playlists': playlists_page,
        **get_nav_context()
    }
    return render(request, 'pages/music/playlist_list.html', context)

def playlist_detail(request, playlist_id):
    """歌单详情页面"""
    playlist = get_object_or_404(CloudMusicPlaylist, id=playlist_id, is_active=True)
    
    # 获取歌单内的歌曲
    songs = playlist.songs.all().order_by('order')
    
    context = {
        'playlist': playlist,
        'songs': songs,
        **get_nav_context()
    }
    return render(request, 'pages/music/playlist_detail.html', context)

def album_list(request):
    """专辑列表页面"""
    # 获取所有专辑
    albums = Album.objects.filter(is_active=True).order_by('-created_at')
    
    # 分页
    page = request.GET.get('page', 1)
    paginator = Paginator(albums, 20)
    albums_page = paginator.get_page(page)
    
    context = {
        'albums': albums_page,
        **get_nav_context()
    }
    return render(request, 'pages/music/album_list.html', context)

def album_detail(request, album_id):
    """专辑详情页面"""
    album = get_object_or_404(Album, id=album_id, is_active=True)
    
    # 获取专辑内的歌曲
    songs = album.songs.all().order_by('order')
    
    context = {
        'album': album,
        'songs': songs,
        **get_nav_context()
    }
    return render(request, 'pages/music/album_detail.html', context)
