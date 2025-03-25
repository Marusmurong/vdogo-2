# VDOGO 影视模块核心代码

本仓库包含VDOGO影视网站的核心代码，包括模型定义、视图函数、URL配置和模板文件。前端开发人员可以参考这些文件来实现与后端的交互。

## 目录结构

```
├── files/                  # 核心后端代码
│   ├── models.py           # 数据模型定义
│   ├── views.py            # 视图函数
│   └── urls.py             # URL配置
├── templates/              # 模板文件
│   ├── components/         # 可复用组件
│   │   ├── player.html     # 音乐播放器组件
│   │   ├── video-card.html # 视频卡片组件
│   │   └── video-grid.html # 视频网格组件
│   ├── pages/              # 页面模板
│   │   └── video/
│   │       └── list.html   # 视频列表页面
│   ├── video/              # 视频相关模板
│   │   └── player.html     # 视频播放器模板
│   └── cms/                # 内容管理系统模板
│       └── video_detail.html # 视频详情页模板
```

## 数据模型

### Video 模型

主要视频模型，存储视频的基本信息。

主要字段：
- `title`: 视频标题
- `description`: 视频描述
- `video_type`: 视频类型（单集/系列）
- `categories`: 视频分类（多对多关系）
- `tags`: 视频标签（多对多关系）
- `actors`: 演员（多对多关系）
- `directors`: 导演（多对多关系）
- `media_files`: 媒体文件（一对多关系）
- `thumbnail`: 缩略图URL
- `total_episodes`: 总集数
- `current_episodes`: 当前集数
- `year`: 年份
- `area`: 地区
- `language`: 语言
- `status`: 状态（已发布/草稿/已阻止）
- `is_active`: 是否激活
- `play_count`: 播放次数
- `like_count`: 点赞次数
- `extra_info`: 额外信息（JSON字段）

### VideoMedia 模型

存储视频媒体文件信息。

主要字段：
- `episode_index`: 集数索引
- `episode_title`: 集数标题
- `source_name`: 来源名称
- `source_index`: 来源索引
- `api_request_url`: API请求URL
- `file_path`: 文件路径
- `file_size`: 文件大小
- `duration`: 时长
- `width`: 宽度
- `height`: 高度
- `media_type`: 媒体类型
- `quality`: 质量
- `is_default`: 是否默认
- `extra_info`: 额外信息（JSON字段）

### Category 模型

视频分类模型。

主要字段：
- `name`: 分类名称
- `slug`: URL友好的名称
- `parent`: 父分类（自关联）
- `level`: 层级
- `order`: 排序
- `is_active`: 是否激活
- `show_in_menu`: 是否在菜单中显示

### Tag 模型

标签模型，用于给视频添加标签。

主要字段：
- `name`: 标签名称
- `slug`: URL友好的名称
- `category`: 标签分类

## 视图函数

### 主要视图

- `index`: 首页视图，显示幻灯片、分类和热门视频
- `video_list`: 视频列表视图，支持分类和标签筛选
- `video_detail`: 视频详情视图，显示视频信息和播放器
- `category_view`: 分类视图，显示特定分类下的视频
- `search`: 搜索视图，根据关键词搜索视频
- `channel_view`: 频道视图，显示特定频道的视频

## URL配置

主要URL路径：

- `/`: 首页
- `/videos/`: 视频列表页
- `/videos/<id>/`: 视频详情页
- `/category/<slug>/`: 分类页
- `/search/`: 搜索页
- `/channel/<slug>/`: 频道页

## 模板文件

### 视频播放器 (templates/video/player.html)

视频播放器模板，用于播放视频。支持多种播放源和清晰度选择。

### 视频列表页 (templates/pages/video/list.html)

视频列表页模板，显示视频列表，支持分页和筛选。

### 视频卡片组件 (templates/components/video-card.html)

可复用的视频卡片组件，用于在列表中显示单个视频的信息。

### 视频网格组件 (templates/components/video-grid.html)

可复用的视频网格组件，用于以网格形式显示多个视频。

### 音乐播放器组件 (templates/components/player.html)

可复用的音乐播放器组件，用于播放音频文件。

### 视频详情页 (templates/cms/video_detail.html)

视频详情页模板，显示视频的详细信息、播放器和评论。

## 数据导入

本项目包含从mac_vod.sql文件导入数据的脚本（import_from_sql.py）。该脚本实现了从原始数据到新数据库结构的映射，主要映射关系如下：

- vod_name → title
- vod_content → description
- vod_pic → cover + original_cover_url
- vod_actor → actors
- vod_director → directors
- vod_remarks → remarks
- vod_total → episodes_count
- vod_serial → current_episode
- vod_area → area
- vod_lang → language
- vod_year → year

其他字段被映射到extra_info JSON字段中。

## 前端开发指南

1. **视频列表页**：使用video-grid.html和video-card.html组件来显示视频列表。
2. **视频详情页**：使用video_detail.html模板作为参考，实现视频详情页面。
3. **视频播放器**：使用player.html模板来实现视频播放功能。
4. **API交互**：参考views.py中的视图函数，了解前端需要与哪些API交互。

## 注意事项

1. 所有模板都使用Bootstrap 5进行样式设计，确保引入相应的CSS和JavaScript文件。
2. 视频播放功能需要处理多种播放源和清晰度选择。
3. 视频列表页需要实现分页和筛选功能。
4. 视频详情页需要实现评论、点赞和收藏功能。
