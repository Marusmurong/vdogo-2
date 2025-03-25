from django.db import models
from django.utils import timezone
from django.conf import settings
from users.models import UserGroup
import os
import logging

VIDEO_TYPES = [
    ('single', '单集视频'),
    ('series', '剧集视频'),
    ('short', '小视频')
]

VIDEO_STATUS = [
    ('draft', '草稿'),
    ('processing', '处理中'),
    ('published', '已发布'),
    ('blocked', '已封禁')
]

QUALITY_LEVELS = [
    ('240p', '流畅'),
    ('480p', '清晰'),
    ('720p', '高清'),
    ('1080p', '超清')
]

logger = logging.getLogger(__name__)


class Category(models.Model):
    """分类"""
    MEDIA_TYPE_CHOICES = [
        ('video', '视频'),
        ('article', '文章'),
        ('image', '图片'),
        ('music', '音乐')
    ]
    
    CATEGORY_TYPE_CHOICES = [
        ('movie', '电影'),
        ('tv', '电视剧'),
        ('variety', '综艺'),
        ('anime', '动漫'),
        ('documentary', '纪录片'),
        ('actor', '演员'),
        ('director', '导演'),
        ('other', '其他')
    ]
    
    name = models.CharField('名称', max_length=100)
    slug = models.SlugField('别名', max_length=50, unique=True)
    description = models.TextField('描述')
    parent = models.ForeignKey('self', verbose_name='父分类', null=True, blank=True,
                              on_delete=models.SET_NULL, related_name='children')
    media_type = models.CharField('媒体类型', max_length=20, choices=MEDIA_TYPE_CHOICES)
    category_type = models.CharField('分类类型', max_length=20, null=True, blank=True)
    is_root = models.BooleanField('是否根分类', default=False)
    show_in_menu = models.BooleanField('显示在菜单', default=True)
    order = models.IntegerField('排序', default=0)
    icon = models.CharField('图标', max_length=50, null=True, blank=True)
    template = models.CharField('模板', max_length=100, null=True, blank=True, default='')
    keywords = models.TextField('关键词', null=True, blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    objects = models.Manager()

    class Meta:
        verbose_name = '分类'
        verbose_name_plural = '分类管理'
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class TagCategory(models.Model):
    """标签分类"""
    name = models.CharField(max_length=100, verbose_name='名称')
    slug = models.SlugField(unique=True, verbose_name='别名', null=True, blank=True)
    order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '标签分类'
        verbose_name_plural = '标签分类'
        ordering = ['order']

    def __str__(self):
        return self.name


class Tag(models.Model):
    """标签"""
    name = models.CharField(max_length=100, verbose_name='名称')
    slug = models.SlugField(unique=True, verbose_name='别名', default='default-slug')
    description = models.TextField(blank=True, verbose_name='描述')
    category = models.ForeignKey(TagCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='标签分类')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签管理'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name




class VideoMedia(models.Model):
    """视频媒体文件"""
    file_path = models.FileField(upload_to='videos/%Y/%m/%d/', verbose_name='文件路径', null=True, blank=True)
    file_size = models.BigIntegerField(default=0, verbose_name='文件大小')
    duration = models.IntegerField(default=0, verbose_name='时长')
    width = models.IntegerField(default=0, verbose_name='宽度')
    height = models.IntegerField(default=0, verbose_name='高度')
    media_type = models.CharField(max_length=20, default='mp4', verbose_name='媒体类型')
    quality = models.CharField(max_length=20, choices=QUALITY_LEVELS, default='720p', verbose_name='清晰度')
    api_request_url = models.URLField(blank=True, null=True, verbose_name='API请求URL')
    cdn_url = models.URLField(blank=True, null=True, verbose_name='CDN地址')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')
    episode_index = models.IntegerField(default=0, verbose_name='集数索引')
    episode_title = models.CharField(max_length=200, blank=True, null=True, verbose_name='集数标题')
    source_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='来源名称')
    source_index = models.IntegerField(default=0, verbose_name='来源索引')
    extra_info = models.JSONField(default=dict, blank=True, verbose_name='额外信息')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def save(self, *args, **kwargs):
        if not self.file_path:
            self.file_path = 'videos/default.mp4'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = '视频媒体'
        verbose_name_plural = '视频媒体'
        ordering = ['-created_at']
        app_label = 'files'

    def __str__(self):
        return f"{self.file_path}"

class Video(models.Model):
    """视频"""
    title = models.CharField('标题', max_length=200)
    description = models.TextField('描述', default='暂无描述')
    video_type = models.CharField('视频类型', choices=VIDEO_TYPES, max_length=10, default='single')
    categories = models.ManyToManyField('Category', verbose_name='分类', related_name='videos', through='VideoCategory')
    tags = models.ManyToManyField('Tag', verbose_name='标签', related_name='videos')
    status = models.CharField('状态', choices=VIDEO_STATUS, max_length=20, default='draft')
    quality_versions = models.JSONField('清晰度版本', default=dict)
    media_files = models.ManyToManyField('VideoMedia', verbose_name='媒体文件', related_name='videos')
    thumbnail = models.URLField('缩略图', blank=True, null=True)
    duration = models.IntegerField('时长', default=0)
    views = models.IntegerField('播放次数', default=0)
    play_count = models.IntegerField('播放次数', default=0)
    like_count = models.IntegerField('点赞数', default=0)
    comment_count = models.IntegerField('评论数', default=0)
    actors = models.ManyToManyField('Actor', verbose_name='演员', related_name='videos', through='VideoActor')
    directors = models.ManyToManyField('Director', verbose_name='导演', related_name='videos', through='VideoDirector')
    year = models.CharField('年份', max_length=20, blank=True, null=True)
    area = models.CharField('地区', max_length=100, blank=True, null=True)
    language = models.CharField('语言', max_length=50, blank=True, null=True)
    total_episodes = models.IntegerField('总集数', default=1)
    current_episodes = models.IntegerField('当前集数', default=1)
    update_status = models.CharField('更新状态', max_length=20, default='completed', 
                                   choices=[('ongoing', '更新中'), ('completed', '已完结')])
    third_party_id = models.CharField('第三方ID', max_length=100, blank=True, null=True)
    extra_info = models.JSONField('额外信息', default=dict, blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    objects = models.Manager()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='创建者', on_delete=models.CASCADE, default=1)

    class Meta:
        verbose_name = '视频'
        verbose_name_plural = '视频管理'
        ordering = ['-created_at']

    def __str__(self):
        return self.title



class VideoCategory(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'files_video_categories'
        app_label = 'files'

class VideoTag(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'files_video_tags'

    class Meta:
        verbose_name = '视频'
        verbose_name_plural = '视频管理'
        ordering = ['-created_at']

    def __str__(self):
        return self.title



class SeriesVideo(models.Model):
    video = models.ForeignKey(Video, verbose_name='视频', on_delete=models.CASCADE)
    series_title = models.CharField('剧集标题', max_length=200)
    episode_number = models.IntegerField('集数')
    total_episodes = models.IntegerField('总集数')
    update_status = models.CharField('更新状态', max_length=50, choices=[
        ('ongoing', '连载中'),
        ('completed', '已完结')
    ])
    next_update = models.DateTimeField('下次更新时间', null=True, blank=True)

    class Meta:
        verbose_name = '剧集视频'
        verbose_name_plural = '剧集视频'
        ordering = ['episode_number']
        app_label = 'files'

    def __str__(self):
        return f'{self.series_title} - 第{self.episode_number}集'

    def is_token_valid(self):
        if not self.token or not self.token_expires_at:
            return False
        return timezone.now() < self.token_expires_at

    def is_m3u8_expired(self):
        """检查m3u8链接是否过期"""
        if not self.m3u8_url:
            return True
        # m3u8链接48小时过期
        return (timezone.now() - self.updated_at).total_seconds() > 48 * 3600

    def should_download(self):
        """检查是否应该下载到本地"""
        return (not self.is_downloaded and 
                self.play_count >= self.download_threshold and 
                self.m3u8_url)

    def get_local_m3u8_path(self):
        """获取本地m3u8文件路径"""
        if self.is_downloaded and self.local_path:
            return os.path.join('media_files', str(self.id), 'index.m3u8')
        return None







class EncodeProfile(models.Model):
    """视频编码配置"""
    name = models.CharField('名称', max_length=100)
    extension = models.CharField('扩展名', max_length=10, default='mp4')
    resolution = models.IntegerField('分辨率', default=720)
    bitrate = models.IntegerField('码率(kbps)', default=1000)
    audio_bitrate = models.IntegerField('音频码率(kbps)', default=128)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    
    class Meta:
        verbose_name = '编码配置'
        verbose_name_plural = verbose_name
        ordering = ['resolution']
        
    def __str__(self):
        return f"{self.name} ({self.resolution}p)"

class Encoding(models.Model):
    """视频编码任务"""
    STATUS_CHOICES = (
        ('pending', '等待处理'),
        ('running', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败')
    )
    
    media = models.ForeignKey(VideoMedia, on_delete=models.CASCADE, verbose_name='媒体文件')
    profile = models.ForeignKey(EncodeProfile, on_delete=models.CASCADE, verbose_name='编码配置')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField('进度', default=0)
    output_url = models.URLField('输出URL', blank=True)
    error_message = models.TextField('错误信息', blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    started_at = models.DateTimeField('开始时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    
    class Meta:
        verbose_name = '编码任务'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.media} - {self.profile}"

class Rating(models.Model):
    """视频评分"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='ratings', verbose_name='视频')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    score = models.IntegerField('评分', default=0)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    
    class Meta:
        verbose_name = '视频评分'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        unique_together = ['video', 'user']
        
    def __str__(self):
        return f"{self.video} - {self.user} - {self.score}"

class VideoCache(models.Model):
    """视频缓存"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='caches', verbose_name='视频')
    quality = models.CharField('画质', max_length=20)
    file_path = models.CharField('文件路径', max_length=255)
    file_size = models.BigIntegerField('文件大小', default=0)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    
    class Meta:
        verbose_name = '视频缓存'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        unique_together = ['video', 'quality']
        
    def __str__(self):
        return f"{self.video} - {self.quality}"

class HotSearch(models.Model):
    keyword = models.CharField(max_length=100, verbose_name='搜索关键词')
    count = models.IntegerField(default=0, verbose_name='搜索次数')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '热门搜索'
        verbose_name_plural = verbose_name
        ordering = ['order', '-count']

    def __str__(self):
        return self.keyword

class Actor(models.Model):
    """演员模型"""
    name = models.CharField(max_length=100, verbose_name='姓名')
    description = models.TextField(blank=True, verbose_name='描述')
    avatar = models.URLField(blank=True, verbose_name='头像')
    status = models.CharField(max_length=20, default='active', verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '演员'
        verbose_name_plural = '演员管理'
        ordering = ['name']

    def __str__(self):
        return self.name

class Director(models.Model):
    """导演模型"""
    name = models.CharField(max_length=100, verbose_name='姓名')
    description = models.TextField(blank=True, verbose_name='描述')
    avatar = models.URLField(blank=True, verbose_name='头像')
    status = models.CharField(max_length=20, default='active', verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '导演'
        verbose_name_plural = '导演管理'
        ordering = ['name']

    def __str__(self):
        return self.name

class Music(models.Model):
    """音乐"""
    title = models.CharField('标题', max_length=200)
    artist = models.CharField('艺术家', max_length=200)
    album = models.ForeignKey('Album', on_delete=models.SET_NULL, null=True, blank=True, related_name='musics')
    playlists = models.ManyToManyField('Playlist', through='PlaylistMusic', related_name='musics')
    file_path = models.FileField('音乐文件', upload_to='music/%Y/%m/%d/')
    duration = models.IntegerField('时长', default=0)
    cover = models.ImageField('封面', upload_to='music/covers/%Y/%m/%d/', null=True, blank=True)
    play_count = models.IntegerField('播放次数', default=0)
    like_count = models.IntegerField('点赞数', default=0)
    comment_count = models.IntegerField('评论数', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '音乐'
        verbose_name_plural = '音乐管理'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.artist}"

class Album(models.Model):
    """专辑"""
    title = models.CharField('标题', max_length=200)
    artist = models.CharField('艺术家', max_length=200)
    description = models.TextField('描述', blank=True)
    cover = models.ImageField('封面', upload_to='music/albums/%Y/%m/%d/', null=True, blank=True)
    release_date = models.DateField('发行日期', null=True, blank=True)
    play_count = models.IntegerField('播放次数', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '专辑'
        verbose_name_plural = '专辑管理'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.artist}"

class Playlist(models.Model):
    """歌单"""
    title = models.CharField('标题', max_length=200)
    description = models.TextField('描述', blank=True)
    cover = models.ImageField('封面', upload_to='music/playlists/%Y/%m/%d/', null=True, blank=True)
    play_count = models.IntegerField('播放次数', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '歌单'
        verbose_name_plural = '歌单管理'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class PlaylistMusic(models.Model):
    """歌单音乐关联"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    music = models.ForeignKey(Music, on_delete=models.CASCADE)
    order = models.IntegerField('排序', default=0)
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        verbose_name = '歌单音乐'
        verbose_name_plural = '歌单音乐管理'
        ordering = ['order']
        unique_together = ['playlist', 'music']

    def __str__(self):
        return f"{self.playlist.title} - {self.music.title}"

class ImageResource(models.Model):
    """图片资源"""
    IMAGE_TYPES = [
        ('cover', '封面图'),
        ('screenshot', '截图'),
        ('poster', '海报'),
        ('banner', '横幅'),
        ('avatar', '头像'),
        ('other', '其他')
    ]
    
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='images', null=True, blank=True, verbose_name='关联视频')
    image_type = models.CharField('图片类型', max_length=20, choices=IMAGE_TYPES, default='other')
    url = models.URLField('图片URL')
    local_path = models.FileField('本地路径', upload_to='images/%Y/%m/%d/', null=True, blank=True)
    cdn_url = models.URLField('CDN地址', blank=True, null=True)
    width = models.IntegerField('宽度', default=0)
    height = models.IntegerField('高度', default=0)
    file_size = models.IntegerField('文件大小', default=0)
    is_main = models.BooleanField('是否主图', default=False)
    order = models.IntegerField('排序', default=0)
    status = models.CharField('状态', max_length=20, default='active')
    extra_info = models.JSONField('额外信息', default=dict, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '图片资源'
        verbose_name_plural = '图片资源管理'
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.image_type}: {self.url}"

class ThirdPartySource(models.Model):
    """第三方来源"""
    SOURCE_TYPES = [
        ('api', 'API接口'),
        ('scrape', '网页抓取'),
        ('import', '数据导入'),
        ('other', '其他')
    ]
    
    name = models.CharField('来源名称', max_length=100)
    source_type = models.CharField('来源类型', max_length=20, choices=SOURCE_TYPES, default='other')
    base_url = models.URLField('基础URL', blank=True, null=True)
    api_key = models.CharField('API密钥', max_length=255, blank=True, null=True)
    auth_token = models.CharField('认证令牌', max_length=255, blank=True, null=True)
    headers = models.JSONField('请求头', default=dict, blank=True)
    params = models.JSONField('请求参数', default=dict, blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    extra_info = models.JSONField('额外信息', default=dict, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '第三方来源'
        verbose_name_plural = '第三方来源管理'
        ordering = ['name']

    def __str__(self):
        return self.name

class VideoActor(models.Model):
    """视频演员关联"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, verbose_name='视频')
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE, verbose_name='演员')
    role = models.CharField('角色', max_length=100, blank=True, null=True)
    is_main = models.BooleanField('是否主演', default=False)
    order = models.IntegerField('排序', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '视频演员关联'
        verbose_name_plural = '视频演员关联'
        ordering = ['order']
        unique_together = ['video', 'actor']

    def __str__(self):
        return f"{self.video.title} - {self.actor.name}"

class VideoDirector(models.Model):
    """视频导演关联"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, verbose_name='视频')
    director = models.ForeignKey(Director, on_delete=models.CASCADE, verbose_name='导演')
    is_main = models.BooleanField('是否主导演', default=True)
    order = models.IntegerField('排序', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '视频导演关联'
        verbose_name_plural = '视频导演关联'
        ordering = ['order']
        unique_together = ['video', 'director']

    def __str__(self):
        return f"{self.video.title} - {self.director.name}"

class Comment(models.Model):
    """视频评论"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments', verbose_name='视频')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户')
    text = models.TextField('评论内容')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', verbose_name='父评论')
    is_approved = models.BooleanField('是否审核通过', default=True)
    add_date = models.DateTimeField('添加时间', default=timezone.now)
    uid = models.CharField('唯一ID', max_length=50, unique=True, blank=True)
    media_url = models.URLField('媒体URL', blank=True, null=True)
    
    class Meta:
        verbose_name = '视频评论'
        verbose_name_plural = '视频评论'
        ordering = ['-add_date']
    
    def __str__(self):
        return f"{self.user.username}对{self.video.title}的评论"
    
    def save(self, *args, **kwargs):
        # 生成唯一ID
        if not self.uid:
            import uuid
            self.uid = str(uuid.uuid4())
        super().save(*args, **kwargs)
        
        # 更新视频评论数
        self.video.comment_count = Comment.objects.filter(video=self.video).count()
        self.video.save(update_fields=['comment_count'])

class Danmaku(models.Model):
    """弹幕"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='danmakus', verbose_name='视频')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户')
    text = models.CharField('弹幕内容', max_length=100)
    time = models.FloatField('时间点(秒)')
    color = models.CharField('颜色', max_length=10, default='#ffffff')
    type = models.CharField('类型', max_length=20, default='right')
    font_size = models.IntegerField('字体大小', default=25)
    is_approved = models.BooleanField('是否审核通过', default=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    
    class Meta:
        verbose_name = '弹幕'
        verbose_name_plural = '弹幕'
        ordering = ['time']
    
    def __str__(self):
        return f"{self.user.username}在{self.video.title}的弹幕"
