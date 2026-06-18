# 世界杯网站 - 自动更新说明

## 文件结构

```
├── index.html          ← 主网站（直接部署）
├── update_hot.py       ← 热点自动更新脚本
├── images/             ← 背景图片源文件
│   ├── bg1.jpg ~ bg7.jpg
├── build.sh            ← 构建脚本（重新生成整站用）
├── embed_images.py     ← 图片嵌入脚本
└── README_更新说明.md  ← 本文件
```

## 热点自动更新

### 手动运行
```bash
python3 update_hot.py
```

### 定时自动更新（cron）

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天早上 8:00 自动更新）
0 8 * * * cd /path/to/your/website && python3 update_hot.py >> /tmp/wcup_update.log 2>&1
```

### 使用真实赛事 API

脚本支持 [football-data.org](https://www.football-data.org/) 免费 API：

1. 注册并获取免费 API Key
2. 设置环境变量：
   ```bash
   export FOOTBALL_API_KEY="your_key_here"
   ```
3. 或在脚本中直接填写 `API_KEY = "your_key_here"`

没有 API Key 时会使用内置模拟数据。

## 热点内容逻辑

脚本会自动分析比赛结果，生成不同类型的热点：

| 类型 | 触发条件 | 标签 |
|------|---------|------|
| 🔥 爆冷 | 热门球队输球 | `tag-explosive` |
| ⚡ 冷平 | 热门球队被逼平 | `tag-upset` |
| 💥 进球大战 | 总进球 ≥ 5 | `tag-explosive` |
| 💥 大胜 | 净胜球 ≥ 4 | `tag-explosive` |
| ⚡ 经典对决 | 高比分平局 | `tag-classic` |
| 🎯 险胜 | 一球小胜 | `tag-classic` |
| 😤 闷平 | 0-0 平局 | `tag-upset` |
| 📋 战报 | 其他比赛 | `tag-debut` |

热点按重要度排序，最多展示 6 条。
