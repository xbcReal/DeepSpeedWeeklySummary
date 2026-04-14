#!/usr/bin/env python3
"""
DeepSpeed Weekly Summary Generator

This script generates weekly summary reports for the DeepSpeed repository
by fetching data from GitHub API.
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib import request
from urllib.error import HTTPError

# Configuration
REPO_OWNER = "microsoft"
REPO_NAME = "DeepSpeed"
GITHUB_API = "https://api.github.com"

# Badge colors for different PR types
BADGE_TYPES = {
    "feature": ("Feature", "238636"),
    "bugfix": ("Bugfix", "da3633"),
    "perf": ("Performance", "f0883e"),
    "doc": ("Documentation", "1f6feb"),
    "ci": ("CI/CD", "8957e5"),
    "test": ("Test", "d29922"),
    "refactor": ("Refactor", "e85d75"),
    "optimize": ("Optimize", "59cfd2"),
    "release": ("Release", "f778ba"),
}


def get_github_token():
    """Get GitHub token from environment."""
    return os.environ.get("GITHUB_TOKEN", "")


def make_api_request(url):
    """Make authenticated GitHub API request."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DeepSpeed-Weekly-Summary",
    }
    
    token = get_github_token()
    if token:
        headers["Authorization"] = f"token {token}"
    
    req = request.Request(url, headers=headers)
    
    try:
        with request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        print(f"API request failed: {e}")
        return None


def get_week_range(date=None):
    """Get start and end of the week for a given date."""
    if date is None:
        date = datetime.now()
    
    # Get Sunday of current week
    end = date - timedelta(days=date.weekday() + 1)
    # Get Monday of current week
    start = end - timedelta(days=6)
    
    return start, end


def classify_pr(title):
    """Classify PR type based on title keywords."""
    title_lower = title.lower()
    
    if any(kw in title_lower for kw in ["fix", "bug", "hotfix", "patch"]):
        return "bugfix"
    elif any(kw in title_lower for kw in ["perf", "performance", "speed", "optimize", "accelerate"]):
        return "perf"
    elif any(kw in title_lower for kw in ["doc", "readme", "documentation", "comment", "tutorial"]):
        return "doc"
    elif any(kw in title_lower for kw in ["test", "testing", "unittest", "pytest"]):
        return "test"
    elif any(kw in title_lower for kw in ["ci", "github action", "workflow", "build"]):
        return "ci"
    elif any(kw in title_lower for kw in ["refactor", "cleanup", "clean up", "restructure"]):
        return "refactor"
    elif any(kw in title_lower for kw in ["feature", "add", "support", "implement", "new"]):
        return "feature"
    else:
        return "feature"  # Default to feature


def fetch_prs(start_date, end_date, state="all"):
    """Fetch PRs from the repository within date range."""
    since = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    until = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/pulls?state={state}&per_page=100&sort=updated&direction=desc"
    
    data = make_api_request(url)
    if not data:
        return []
    
    # Filter by date
    filtered_prs = []
    for pr in data:
        pr_date = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
        if start_date <= pr_date <= end_date:
            filtered_prs.append(pr)
    
    return filtered_prs


def fetch_commits(start_date, end_date):
    """Fetch commits from the repository within date range."""
    since = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    until = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/commits?since={since}&until={until}&per_page=100"
    
    return make_api_request(url) or []


def generate_html_report(start_date, end_date, prs, commits, output_path):
    """Generate HTML weekly report."""
    
    # Categorize PRs
    merged_prs = [pr for pr in prs if pr["state"] == "closed" and pr.get("merged_at")]
    open_prs = [pr for pr in prs if pr["state"] == "open"]
    
    # Calculate stats
    total_prs = len(prs)
    merged_count = len(merged_prs)
    open_count = len(open_prs)
    commit_count = len(commits)
    
    # Count by type
    feature_count = sum(1 for pr in prs if classify_pr(pr["title"]) == "feature")
    
    # Format dates
    date_range_str = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
    week_num = end_date.isocalendar()[1]
    
    # Generate PR list HTML
    def pr_item_html(pr):
        pr_type = classify_pr(pr["title"])
        badge_name, badge_color = BADGE_TYPES.get(pr_type, ("Other", "8b949e"))
        
        state_badge = ""
        if pr["state"] == "closed" and pr.get("merged_at"):
            state_badge = '<span class="badge badge-ver">Merged</span>'
        elif pr["state"] == "open":
            draft = pr.get("draft", False)
            state_badge = '<span class="badge badge-draft">Draft</span>' if draft else '<span class="badge badge-approved">Open</span>'
        
        return f'''
      <li class="pr-item">
        <div class="pr-title">
          <span class="badge badge-{pr_type}">{badge_name}</span>
          {pr["title"]}
        </div>
        <div class="pr-meta">
          <span class="pr-author">@{pr["user"]["login"]}</span>
          <span class="pr-files"><a href="{pr["html_url"]}" target="_blank">#{pr["number"]}</a></span>
          {state_badge}
        </div>
      </li>'''
    
    open_prs_html = "\n".join(pr_item_html(pr) for pr in open_prs[:10])
    merged_prs_html = "\n".join(pr_item_html(pr) for pr in merged_prs[:10])
    
    # Generate commit list HTML
    commit_items_html = ""
    for commit in commits[:10]:
        sha = commit["sha"][:7]
        msg = commit["commit"]["message"].split("\n")[0][:80]
        author = commit["commit"]["author"]["name"]
        commit_items_html += f'''
      <li class="commit-item">
        <span class="commit-sha">{sha}</span>
        <span class="commit-msg">{msg}</span>
        <span class="commit-author">@{author}</span>
      </li>'''
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DeepSpeed 周报 | {date_range_str} (W{week_num})</title>
<style>
  :root {{
    --primary: #2563eb;
    --primary-dark: #1d4ed8;
    --bg: #0d1117;
    --card: #161b22;
    --border: #30363d;
    --text: #e6edf3;
    --text-muted: #8b949e;
    --link: #58a6ff;
    --badge-feature: #238636;
    --badge-bugfix: #da3633;
    --badge-ci: #8957e5;
    --badge-doc: #1f6feb;
    --badge-perf: #f0883e;
    --badge-optimize: #59cfd2;
    --badge-test: #d29922;
    --badge-refactor: #e85d75;
    --badge-release: #f778ba;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 0;
  }}
  .hero {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-bottom: 3px solid var(--primary);
    padding: 40px 0;
    text-align: center;
  }}
  .hero h1 {{
    font-size: 2.2em;
    color: var(--primary);
    margin-bottom: 8px;
    letter-spacing: -0.5px;
  }}
  .hero .subtitle {{
    color: var(--text-muted);
    font-size: 1.1em;
  }}
  .hero .date-range {{
    display: inline-block;
    background: rgba(37, 99, 235, 0.15);
    color: var(--primary);
    padding: 6px 18px;
    border-radius: 20px;
    margin-top: 12px;
    font-weight: 600;
    font-size: 0.95em;
  }}
  .container {{
    max-width: 1100px;
    margin: 0 auto;
    padding: 30px 24px;
  }}
  .stats-bar {{
    display: flex;
    gap: 16px;
    margin-bottom: 32px;
    flex-wrap: wrap;
  }}
  .stat-card {{
    flex: 1;
    min-width: 140px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
  }}
  .stat-card .num {{
    font-size: 2.4em;
    font-weight: 700;
    color: var(--primary);
  }}
  .stat-card .label {{
    color: var(--text-muted);
    font-size: 0.85em;
    margin-top: 4px;
  }}
  .stat-card.highlight {{
    border-color: var(--badge-perf);
    background: linear-gradient(135deg, #1a2518, #1a2015);
  }}
  .stat-card.highlight .num {{
    color: var(--badge-perf);
  }}
  .section {{
    margin-bottom: 36px;
  }}
  .section-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
  }}
  .section-header h2 {{
    font-size: 1.4em;
    color: var(--text);
  }}
  .section-header .icon {{
    font-size: 1.4em;
  }}
  .badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75em;
    font-weight: 600;
    color: #fff;
    margin-right: 6px;
    vertical-align: middle;
  }}
  .badge-feature {{ background: var(--badge-feature); }}
  .badge-bugfix {{ background: var(--badge-bugfix); }}
  .badge-ci {{ background: var(--badge-ci); }}
  .badge-doc {{ background: var(--badge-doc); }}
  .badge-perf {{ background: var(--badge-perf); }}
  .badge-optimize {{ background: var(--badge-optimize); color: #000; }}
  .badge-test {{ background: var(--badge-test); color: #000; }}
  .badge-refactor {{ background: var(--badge-refactor); }}
  .badge-release {{ background: var(--badge-release); color: #000; }}
  .badge-ver {{
    background: rgba(37, 99, 235, 0.2);
    color: var(--primary);
    border: 1px solid var(--primary);
  }}
  .badge-draft {{
    background: rgba(139, 148, 158, 0.2);
    color: var(--text-muted);
    border: 1px solid var(--text-muted);
  }}
  .badge-approved {{
    background: rgba(35, 134, 54, 0.2);
    color: #3fb950;
    border: 1px solid #3fb950;
  }}
  .badge-changes {{
    background: rgba(218, 54, 51, 0.2);
    color: #f85149;
    border: 1px solid #f85149;
  }}
  .pr-list {{
    list-style: none;
  }}
  .pr-item {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
    transition: border-color 0.2s, transform 0.1s;
  }}
  .pr-item:hover {{
    border-color: var(--primary);
    transform: translateX(4px);
  }}
  .pr-title {{
    font-weight: 600;
    color: var(--text);
    margin-bottom: 6px;
    line-height: 1.4;
  }}
  .pr-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
    font-size: 0.85em;
  }}
  .pr-author {{
    color: var(--text-muted);
  }}
  .pr-files {{
    color: var(--text-muted);
  }}
  .pr-files a {{
    color: var(--link);
    text-decoration: none;
  }}
  .pr-files a:hover {{
    text-decoration: underline;
  }}
  .highlight-box {{
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(37, 99, 235, 0.05));
    border: 1px solid var(--primary);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
  }}
  .highlight-box h3 {{
    color: var(--primary);
    margin-bottom: 12px;
    font-size: 1.1em;
  }}
  .highlight-box ul {{
    margin-left: 20px;
    color: var(--text);
  }}
  .highlight-box li {{
    margin-bottom: 6px;
  }}
  .commit-list {{
    list-style: none;
  }}
  .commit-item {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
  }}
  .commit-item:last-child {{
    border-bottom: none;
  }}
  .commit-sha {{
    font-family: 'SF Mono', Monaco, monospace;
    font-size: 0.85em;
    color: var(--primary);
    background: rgba(37, 99, 235, 0.1);
    padding: 2px 8px;
    border-radius: 4px;
    flex-shrink: 0;
  }}
  .commit-msg {{
    color: var(--text);
    flex: 1;
  }}
  .commit-author {{
    color: var(--text-muted);
    font-size: 0.85em;
    flex-shrink: 0;
  }}
  .footer {{
    text-align: center;
    padding: 40px 0;
    color: var(--text-muted);
    font-size: 0.9em;
    border-top: 1px solid var(--border);
    margin-top: 40px;
  }}
  .footer a {{
    color: var(--link);
    text-decoration: none;
  }}
  @media (max-width: 768px) {{
    .stats-bar {{
      flex-direction: column;
    }}
    .stat-card {{
      min-width: auto;
    }}
    .hero h1 {{
      font-size: 1.8em;
    }}
  }}
</style>
</head>
<body>

<div class="hero">
  <h1>DeepSpeed Weekly</h1>
  <div class="subtitle">GitHub Repository Weekly Tracking Report</div>
  <div class="date-range">{date_range_str} (W{week_num})</div>
</div>

<div class="container">

  <!-- 统计数据 -->
  <div class="stats-bar">
    <div class="stat-card">
      <div class="num">{total_prs}</div>
      <div class="label">新增 PR</div>
    </div>
    <div class="stat-card">
      <div class="num">{merged_count}</div>
      <div class="label">合并 PR</div>
    </div>
    <div class="stat-card">
      <div class="num">{commit_count}</div>
      <div class="label">新增 Commit</div>
    </div>
    <div class="stat-card highlight">
      <div class="num">{feature_count}</div>
      <div class="label">新特性</div>
    </div>
  </div>

  <!-- 本周亮点 -->
  <div class="section">
    <div class="section-header">
      <span class="icon">⭐</span>
      <h2>本周亮点</h2>
    </div>
    <div class="highlight-box">
      <h3>重要更新</h3>
      <ul>
        <li>本周共有 {total_prs} 个 PR 被创建，{merged_count} 个 PR 被合并</li>
        <li>新增 {commit_count} 个 commits</li>
        <li>详细数据请查看下方列表</li>
      </ul>
    </div>
  </div>

  <!-- 新增 PR -->
  <div class="section">
    <div class="section-header">
      <span class="icon">🚀</span>
      <h2>新增 PR ({open_count} 个 Open)</h2>
    </div>
    <ul class="pr-list">
{open_prs_html}
    </ul>
  </div>

  <!-- 已合并 PR -->
  <div class="section">
    <div class="section-header">
      <span class="icon">✅</span>
      <h2>已合并 PR ({merged_count} 个)</h2>
    </div>
    <ul class="pr-list">
{merged_prs_html}
    </ul>
  </div>

  <!-- 重要 Commits -->
  <div class="section">
    <div class="section-header">
      <span class="icon">📝</span>
      <h2>重要 Commits</h2>
    </div>
    <ul class="commit-list">
{commit_items_html}
    </ul>
  </div>

  <div class="footer">
    <p>Generated by AI | <a href="https://github.com/microsoft/DeepSpeed">DeepSpeed GitHub Repository</a></p>
    <p style="margin-top: 8px;">📊 <a href="../index.html">查看所有周报</a></p>
  </div>

</div>

</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Generated report: {output_path}")


def update_index_html(reports_dir):
    """Update index.html with latest report link."""
    
    # Find all report files
    reports = sorted(Path(reports_dir).glob("ds-weekly-report-*.html"))
    if not reports:
        print("No reports found")
        return
    
    latest = reports[-1]
    
    # Generate archive list
    archive_items = ""
    for report in reversed(reports[-10:]):  # Last 10 reports
        # Extract date from filename
        match = re.search(r'(\d{{4}}-\d{{2}}-\d{{2}})', report.name)
        if match:
            date_str = match.group(1)
            archive_items += f'''                <li>
                    <a href="ds-summary/{report.name}">
                        <span>📊</span>
                        <span>{date_str}</span>
                    </a>
                </li>
'''
    
    index_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepSpeed Weekly Summary</title>
    <meta http-equiv="refresh" content="0; url=ds-summary/{latest.name}">
    <style>
        :root {{
            --primary: #2563eb;
            --bg: #0d1117;
            --card: #161b22;
            --border: #30363d;
            --text: #e6edf3;
            --text-muted: #8b949e;
            --link: #58a6ff;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            text-align: center;
            padding: 40px;
        }}
        h1 {{
            font-size: 2.5em;
            color: var(--primary);
            margin-bottom: 16px;
        }}
        .subtitle {{
            color: var(--text-muted);
            font-size: 1.2em;
            margin-bottom: 24px;
        }}
        .redirect-notice {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px 32px;
            margin-top: 20px;
        }}
        .redirect-notice p {{
            color: var(--text-muted);
            margin-bottom: 12px;
        }}
        .redirect-notice a {{
            color: var(--link);
            text-decoration: none;
            font-weight: 600;
        }}
        .redirect-notice a:hover {{
            text-decoration: underline;
        }}
        .archive-section {{
            margin-top: 48px;
            text-align: left;
            max-width: 600px;
        }}
        .archive-section h2 {{
            font-size: 1.3em;
            color: var(--text);
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
        }}
        .archive-list {{
            list-style: none;
        }}
        .archive-list li {{
            margin-bottom: 8px;
        }}
        .archive-list a {{
            color: var(--link);
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 6px;
            transition: background 0.2s;
        }}
        .archive-list a:hover {{
            background: rgba(88, 166, 255, 0.1);
        }}
        .archive-list .date {{
            color: var(--text-muted);
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>DeepSpeed Weekly</h1>
        <p class="subtitle">GitHub Repository Weekly Tracking Report</p>
        
        <div class="redirect-notice">
            <p>正在跳转到最新周报...</p>
            <p>如果没有自动跳转，请 <a href="ds-summary/{latest.name}">点击这里</a></p>
        </div>

        <div class="archive-section">
            <h2>近期周报</h2>
            <ul class="archive-list">
{archive_items}            </ul>
        </div>
    </div>
</body>
</html>'''
    
    with open("index.html", 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    print(f"Updated index.html -> {latest.name}")


def main():
    """Main entry point."""
    
    # Get week range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print(f"Generating report for {start_date.date()} to {end_date.date()}")
    
    # Fetch data
    print("Fetching PRs...")
    prs = fetch_prs(start_date, end_date)
    
    print("Fetching commits...")
    commits = fetch_commits(start_date, end_date)
    
    # Generate report
    reports_dir = Path("ds-summary")
    reports_dir.mkdir(exist_ok=True)
    
    output_path = reports_dir / f"ds-weekly-report-{end_date.strftime('%Y-%m-%d')}.html"
    
    generate_html_report(start_date, end_date, prs, commits, output_path)
    
    # Update index
    print("Updating index.html...")
    update_index_html(reports_dir)
    
    print("Done!")


if __name__ == "__main__":
    main()
