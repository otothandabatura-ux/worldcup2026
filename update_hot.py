#!/usr/bin/env python3
"""
世界杯热点频道自动更新脚本
功能：抓取最新赛果，自动生成热点看点，更新 index.html
用法：python3 update_hot.py
建议配合 cron 每天运行：0 8 * * * cd /path/to && python3 update_hot.py
"""

import json
import re
import os
import random
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

# ──────────────────────────────────────
# 配置
# ──────────────────────────────────────
HTML_FILE = "index.html"
# 免费 API：https://www.football-data.org/ （注册获取免费 key）
# 如果没有 key，使用内置的模拟数据模式
API_KEY = os.environ.get("FOOTBALL_API_KEY", "")
WORLD_CUP_ID = 2026  # 世界杯赛事 ID（需根据实际调整）

# ──────────────────────────────────────
# 球队信息（中文映射 + emoji）
# ──────────────────────────────────────
TEAMS = {
    "美国": {"flag": "🇺🇸", "en": "USA"}, "萨摩亚": {"flag": "🇼🇸", "en": "Samoa"},
    "厄瓜多尔": {"flag": "🇪🇨", "en": "Ecuador"}, "塞内加尔": {"flag": "🇸🇳", "en": "Senegal"},
    "英格兰": {"flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "en": "England"}, "伊朗": {"flag": "🇮🇷", "en": "Iran"},
    "葡萄牙": {"flag": "🇵🇹", "en": "Portugal"}, "埃及": {"flag": "🇪🇬", "en": "Egypt"},
    "日本": {"flag": "🇯🇵", "en": "Japan"}, "哥斯达黎加": {"flag": "🇨🇷", "en": "Costa Rica"},
    "法国": {"flag": "🇫🇷", "en": "France"}, "澳大利亚": {"flag": "🇦🇺", "en": "Australia"},
    "阿根廷": {"flag": "🇦🇷", "en": "Argentina"}, "克罗地亚": {"flag": "🇭🇷", "en": "Croatia"},
    "德国": {"flag": "🇩🇪", "en": "Germany"}, "荷兰": {"flag": "🇳🇱", "en": "Netherlands"},
    "西班牙": {"flag": "🇪🇸", "en": "Spain"}, "巴西": {"flag": "🇧🇷", "en": "Brazil"},
    "墨西哥": {"flag": "🇲🇽", "en": "Mexico"}, "喀麦隆": {"flag": "🇨🇲", "en": "Cameroon"},
    "瑞士": {"flag": "🇨🇭", "en": "Switzerland"}, "尼日利亚": {"flag": "🇳🇬", "en": "Nigeria"},
    "韩国": {"flag": "🇰🇷", "en": "South Korea"}, "加纳": {"flag": "🇬🇭", "en": "Ghana"},
    "丹麦": {"flag": "🇩🇰", "en": "Denmark"}, "塞尔维亚": {"flag": "🇷🇸", "en": "Serbia"},
    "比利时": {"flag": "🇧🇪", "en": "Belgium"}, "摩洛哥": {"flag": "🇲🇦", "en": "Morocco"},
    "哥伦比亚": {"flag": "🇨🇴", "en": "Colombia"}, "乌拉圭": {"flag": "🇺🇾", "en": "Uruguay"},
    "加拿大": {"flag": "🇨🇦", "en": "Canada"}, "波兰": {"flag": "🇵🇱", "en": "Poland"},
    "沙特": {"flag": "🇸🇦", "en": "Saudi Arabia"}, "突尼斯": {"flag": "🇹🇳", "en": "Tunisia"},
    "秘鲁": {"flag": "🇵🇪", "en": "Peru"}, "威尔士": {"flag": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "en": "Wales"},
}

# 热门球队（排名靠前，爆冷更有话题性）
TOP_TEAMS = {"阿根廷", "巴西", "法国", "英格兰", "西班牙", "德国", "葡萄牙", "荷兰", "比利时"}

GROUPS = "ABCDEFGHIJ"

# ──────────────────────────────────────
# 数据获取
# ──────────────────────────────────────
def fetch_api_matches():
    """从 football-data.org 获取世界杯赛果"""
    if not API_KEY:
        return None
    try:
        url = f"https://api.football-data.org/v4/competitions/{WORLD_CUP_ID}/matches?status=FINISHED"
        req = Request(url, headers={"X-Auth-Token": API_KEY})
        resp = urlopen(req, timeout=15)
        data = json.loads(resp.read())
        matches = []
        for m in data.get("matches", [])[-20:]:  # 最近20场
            matches.append({
                "home": m["homeTeam"]["name"],
                "away": m["awayTeam"]["name"],
                "home_score": m["score"]["fullTime"]["home"],
                "away_score": m["score"]["fullTime"]["away"],
                "group": m.get("group", ""),
                "matchday": m.get("matchday", 0),
                "date": m["utcDate"][:10],
            })
        return matches
    except Exception as e:
        print(f"API 获取失败: {e}")
        return None


def generate_demo_matches():
    """生成模拟赛果数据（当 API 不可用时）"""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")

    # 模拟昨天的 6 场比赛
    demo = [
        {"home": "西班牙", "away": "佛得角", "home_score": 0, "away_score": 0,
         "group": "E组", "matchday": 1, "date": date_str},
        {"home": "德国", "away": "荷兰", "home_score": 1, "away_score": 1,
         "group": "D组", "matchday": 2, "date": date_str},
        {"home": "日本", "away": "哥斯达黎加", "home_score": 4, "away_score": 0,
         "group": "C组", "matchday": 2, "date": date_str},
        {"home": "阿根廷", "away": "克罗地亚", "home_score": 0, "away_score": 1,
         "group": "D组", "matchday": 2, "date": date_str},
        {"home": "法国", "away": "澳大利亚", "home_score": 2, "away_score": 1,
         "group": "C组", "matchday": 2, "date": date_str},
        {"home": "墨西哥", "away": "喀麦隆", "home_score": 1, "away_score": 0,
         "group": "E组", "matchday": 2, "date": date_str},
    ]
    return demo


# ──────────────────────────────────────
# 热点分析引擎
# ──────────────────────────────────────
def analyze_match(match):
    """分析单场比赛，返回 (重要度分数, 标签类型, 标题模板, 描述模板)"""
    home, away = match["home"], match["away"]
    hs, as_ = match["home_score"], match["away_score"]
    group = match.get("group", "")
    matchday = match.get("matchday", 0)

    total_goals = hs + as_
    goal_diff = abs(hs - as_)
    is_draw = hs == as_
    home_win = hs > as_
    away_win = as_ > hs

    score_str = f"{hs}-{as_}"

    # 判断是否爆冷（热门球队输球或平局）
    top_home = home in TOP_TEAMS
    top_away = away in TOP_TEAMS
    upset = False
    if top_home and away_win:
        upset = True
    elif top_away and home_win:
        upset = True
    elif (top_home or top_away) and is_draw and (top_home and hs == 0) or (top_away and as_ == 0):
        upset = True

    events = []

    # 1. 爆冷
    if upset:
        if top_home and away_win:
            events.append((95, "tag-explosive", "🔥 爆冷",
                           f"{home} {score_str} {away}",
                           f"世界排名第靠前的{home}主场失利！{away}凭借顽强防守和高效反击拿下三分，这是本届世界杯最大冷门之一。"))
        elif top_away and home_win:
            events.append((95, "tag-explosive", "🔥 爆冷",
                           f"{home} {score_str} {away}",
                           f"爆出大冷门！{away}被看好但{home}以出色的战术执行力拿下胜利，让所有人刮目相看。"))
        elif is_draw:
            events.append((85, "tag-upset", "⚡ 冷平",
                           f"{home} {score_str} {away}",
                           f"被看好的{'主场' if top_home else '客场'}球队未能取胜，{away if top_home else home}顽强逼平对手，拿到宝贵一分。"))

    # 2. 大比分
    if total_goals >= 5:
        events.append((90, "tag-explosive", "💥 进球大战",
                       f"{home} {score_str} {away}",
                       f"一场进球盛宴！双方合计打入{total_goals}球，{'进攻端表现炸裂' if home_win else '客场进攻火力全开'}。"))
    elif goal_diff >= 4:
        winner = home if home_win else away
        loser = away if home_win else home
        events.append((88, "tag-explosive", "💥 大胜",
                       f"{home} {score_str} {away}",
                       f"{winner}以{goal_diff}球优势横扫{loser}，展现出绝对统治力。"))
    elif goal_diff >= 3:
        winner = home if home_win else away
        events.append((80, "tag-classic", "⚡ 悬殊",
                       f"{home} {score_str} {away}",
                       f"{winner}以{goal_diff}球优势完胜对手，攻防两端均碾压。"))

    # 3. 经典对决（平局且激烈）
    if is_draw and total_goals >= 2:
        events.append((75, "tag-classic", "⚡ 经典对决",
                       f"{home} {score_str} {away}",
                       f"双方你来我往，{total_goals}个进球让比赛精彩纷呈，最终握手言和。"))

    # 4. 零封
    if is_draw and total_goals == 0:
        events.append((70, "tag-upset", "😤 闷平",
                       f"{home} {score_str} {away}",
                       f"双方防守严密但进攻乏力，互交白卷收场。"))

    # 5. 绝杀（如果比分差距为1且不是0-0）
    if goal_diff == 1 and total_goals >= 2:
        events.append((72, "tag-classic", "🎯 险胜",
                       f"{home} {score_str} {away}",
                       f"比赛悬念保持到最后，最终{'主场' if home_win else '客场'}球队以一球优势惊险取胜。"))

    # 如果没有特别事件，生成通用战报
    if not events:
        if home_win:
            events.append((50, "tag-debut", "📋 战报",
                           f"{home} {score_str} {away}",
                           f"{home}在{group}第{matchday}轮比赛中战胜{away}，全取三分。"))
        elif away_win:
            events.append((50, "tag-debut", "📋 战报",
                           f"{home} {score_str} {away}",
                           f"{away}客场作战以{as_}-{hs}击败{home}，收获宝贵胜利。"))
        else:
            events.append((50, "tag-debut", "📋 战报",
                           f"{home} {score_str} {away}",
                           f"双方在{group}第{matchday}轮比赛中握手言和。"))

    return events


def generate_topics(matches):
    """从多场比赛中生成热点话题列表"""
    all_events = []
    for m in matches:
        events = analyze_match(m)
        for score, tag, emoji, title, desc in events:
            all_events.append({
                "score": score,
                "tag": tag,
                "emoji": emoji,
                "title": title,
                "desc": desc,
                "group": m.get("group", ""),
                "matchday": m.get("matchday", 0),
                "date": m.get("date", ""),
            })

    # 按重要度排序，取前 6 条
    all_events.sort(key=lambda x: x["score"], reverse=True)
    # 去重（同一场比赛只保留最高分的事件）
    seen_titles = set()
    unique = []
    for e in all_events:
        if e["title"] not in seen_titles:
            seen_titles.add(e["title"])
            unique.append(e)
    return unique[:6]


def generate_preview_topics():
    """生成明日看点（基于即将进行的比赛）"""
    # 这里可以接入 API 获取未来赛程，目前用模板
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%m月%d日")
    previews = [
        {
            "match": "🇵🇹 葡萄牙 vs 埃及 🇪🇬 · 00:00",
            "desc": "C罗的最后一届世界杯，首轮梅开二度状态火热。埃及方面萨拉赫同样蓄势待发，两位巨星的正面对决将是本场最大看点。葡萄牙若取胜将提前出线。",
            "key": "🔑 关键对决：C罗 vs 萨拉赫 · 两位传奇的最后之战"
        },
        {
            "match": "🇫🇷 法国 vs 丹麦 🇩🇰 · 03:00",
            "desc": "卫冕亚军法国首轮险胜，姆巴佩虽有进球但整体状态一般。丹麦是欧洲杯四强实力不容小觑，埃里克森的回归让球队中场更具创造力。",
            "key": "🔑 关键对决：姆巴佩 vs 丹麦防线 · 速度与纪律的碰撞"
        },
        {
            "match": "🇧🇷 巴西 vs 塞尔维亚 🇷🇸 · 06:00",
            "desc": "五星巴西首轮被逼平，维尼修斯和罗德里戈需要承担更多进攻责任。塞尔维亚拥有弗拉霍维奇和米特罗维奇两大高中锋，身体对抗将是巴西后防线的巨大考验。",
            "key": "🔑 关键对决：巴西技术流 vs 塞尔维亚力量流 · 风格碰撞"
        },
    ]
    return previews


# ──────────────────────────────────────
# HTML 更新
# ──────────────────────────────────────
def build_topic_html(topic, idx):
    """生成单条热点 HTML"""
    delay = idx * 0.04
    return f'''    <div class="topic fade-in" style="animation-delay:{delay}s">
      <span class="topic-tag {topic['tag']}">{topic['emoji']}</span>
      <div class="topic-title">{topic['title']}</div>
      <div class="topic-desc">{topic['desc']}</div>
      <div class="topic-time">📅 {topic.get('date', '')} · {topic.get('group', '')}第{topic.get('matchday', '')}轮</div>
    </div>'''


def build_preview_html(preview, idx):
    """生成单条看点 HTML"""
    delay = (idx + 5) * 0.04
    return f'''    <div class="preview fade-in" style="animation-delay:{delay}s">
      <div class="pv-match">{preview['match']}</div>
      <div class="pv-what">{preview['desc']}</div>
      <div class="pv-key">{preview['key']}</div>
    </div>'''


def update_html(topics, previews):
    """更新 index.html 中的热点频道内容"""
    if not os.path.exists(HTML_FILE):
        print(f"错误：找不到 {HTML_FILE}")
        return False

    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        html = f.read()

    # 构建新的热点 HTML
    topics_html = '\n'.join(build_topic_html(t, i) for i, t in enumerate(topics))
    previews_html = '\n'.join(build_preview_html(p, i) for i, p in enumerate(previews))

    # 更新热点标签页的 badge 数量
    html = re.sub(
        r'(<div class="sec"><h2>🔥 热点频道</h2><span class="badge">)\d+(\s*条</span></div>)',
        f'\\g<1>{len(topics)}\\2',
        html
    )

    # 替换热点内容（从"赛后看点"badge后到"明日看点"section前）
    pattern_topics = r'(热点频道</h2><span class="badge">.*?</span></div>)(.*?)(<div class="sec"><h2>📌 明日看点</h2>)'
    replacement_topics = f'\\1\n\n{topics_html}\n\n    \\3'
    html = re.sub(pattern_topics, replacement_topics, html, flags=re.DOTALL)

    # 替换明日看点内容（从"明日看点"badge后到 </div> 结束标签前）
    pattern_preview = r'(明日看点</h2><span class="badge">预览</span></div>)(.*?)(</div>\s*\n\s*<!-- ═══ TAB: 积分榜)'
    replacement_preview = f'\\1\n\n{previews_html}\n\n  \\3'
    html = re.sub(pattern_preview, replacement_preview, html, flags=re.DOTALL)

    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ 更新完成！热点 {len(topics)} 条，看点 {len(previews)} 条")
    return True


# ──────────────────────────────────────
# 主流程
# ──────────────────────────────────────
def main():
    print(f"🔄 开始更新热点频道... ({datetime.now().strftime('%Y-%m-%d %H:%M')})")

    # 1. 获取赛果数据
    matches = fetch_api_matches()
    if matches:
        print(f"📡 从 API 获取到 {len(matches)} 场比赛数据")
    else:
        print("📡 API 不可用，使用模拟数据")
        matches = generate_demo_matches()

    # 2. 分析生成热点
    topics = generate_topics(matches)
    print(f"📝 生成 {len(topics)} 条热点话题")
    for t in topics:
        print(f"   {t['emoji']} {t['title']}")

    # 3. 生成明日看点
    previews = generate_preview_topics()
    print(f"📝 生成 {len(previews)} 条明日看点")

    # 4. 更新 HTML
    success = update_html(topics, previews)

    if success:
        size = os.path.getsize(HTML_FILE)
        print(f"📄 文件大小: {size:,} 字节 ({size//1024} KB)")
        print("🎉 热点频道更新完成！")
    else:
        print("❌ 更新失败")


if __name__ == "__main__":
    main()
