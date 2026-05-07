"""测试报告生成器 - 生成独立 HTML 报告（支持分组统计和搜索过滤）"""
import json
import math
from datetime import datetime
from pathlib import Path
from collections import defaultdict


def _calculate_pie_svg(passed: int, failed: int) -> str:
    """
    计算饼图 SVG 路径
    
    Args:
        passed: 通过数量
        failed: 失败数量
        
    Returns:
        str: SVG 字符串
    """
    total = passed + failed
    if total == 0:
        return '<svg width="120" height="120"><circle cx="60" cy="60" r="50" fill="#e8e8e8"/></svg>'
    elif failed == 0:
        return '<svg width="120" height="120"><circle cx="60" cy="60" r="50" fill="#52c41a"/></svg>'
    elif passed == 0:
        return '<svg width="120" height="120"><circle cx="60" cy="60" r="50" fill="#ff4d4f"/></svg>'
    
    # 计算通过比例对应的角度（从 12 点钟方向顺时针）
    passed_ratio = passed / total
    start_angle = -90  # 12 点钟方向
    end_angle = start_angle + 360 * passed_ratio
    
    # 转换为弧度
    start_rad = math.radians(start_angle)
    end_rad = math.radians(end_angle)
    
    # 计算终点坐标（圆心 50,50，半径 40）
    x = 50 + 40 * math.cos(end_rad)
    y = 50 + 40 * math.sin(end_rad)
    
    # 大弧标志
    large_arc = 1 if passed_ratio > 0.5 else 0
    
    # 生成 SVG 路径
    # 绿色扇形（通过部分）：
    #   M50,50: 从圆心开始
    #   L50,10: 画线到 12 点钟方向 (起点，角度 -90°)
    #   A40,40 0 {large_arc},1: 顺时针绘制圆弧到终点
    #   {x},{y}: 圆弧终点坐标
    #   Z: 闭合路径回到圆心
    #
    # 红色扇形（失败部分）：
    #   M50,50: 从圆心开始
    #   L{x},{y}: 画线到绿色扇形的终点
    #   A40,40 0 {1-large_arc},1: 继续顺时针绘制剩余圆弧回到 12 点钟方向
    #   50,10: 回到起点
    #   Z: 闭合路径回到圆心
    return f'''<svg width="120" height="120" viewBox="0 0 100 100">
        <path d="M50,50 L50,10 A40,40 0 {large_arc},1 {x:.2f},{y:.2f} Z" fill="#52c41a"/>
        <path d="M50,50 L{x:.2f},{y:.2f} A40,40 0 {1-large_arc},1 50,10 Z" fill="#ff4d4f"/>
    </svg>'''


def generate_html_report(results: list, output_path: str, title: str = "接口自动化测试报告", script_duration: float = 0):
    """
    生成 HTML 报告
    
    Args:
        results: 测试结果列表，每项包含 name, success, duration, status_code, request, response, assertion, group
        output_path: 输出文件路径
        title: 报告标题
        script_duration: 脚本总执行时长（秒），用于在报告中显示
    """
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0
    total_duration_ms = sum(r["duration"] for r in results)  # 毫秒
    total_duration_s = total_duration_ms / 1000  # 转换为秒
    
    # 按组统计
    groups = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0})
    for r in results:
        group = r.get("group", "未分组")
        groups[group]["total"] += 1
        if r["success"]:
            groups[group]["passed"] += 1
        else:
            groups[group]["failed"] += 1
    
    # 生成饼图
    pie_svg = _calculate_pie_svg(passed, failed)
    
    # 生成分组统计 HTML
    groups_html = ""
    if len(groups) > 1:
        groups_html = '<div class="groups-section"><h2 style="margin-bottom:15px">📊 分组统计</h2><div class="groups-grid">'
        for gname, stats in groups.items():
            g_pass_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            groups_html += f'''
            <div class="group-card">
                <div class="group-name">{gname}</div>
                <div class="group-stats">
                    <span>总计：{stats["total"]}</span>
                    <span style="color:#52c41a">✅ {stats["passed"]}</span>
                    <span style="color:#ff4d4f">❌ {stats["failed"]}</span>
                </div>
                <div class="group-progress"><div class="group-bar" style="width:{g_pass_rate}%"></div></div>
                <div class="group-rate">{g_pass_rate:.1f}%</div>
            </div>'''
        groups_html += '</div></div>'
    
    # 生成详情
    details_html = ""
    for i, r in enumerate(results):
        status_class = "passed" if r["success"] else "failed"
        status_text = "✅ 通过" if r["success"] else "❌ 失败"
        group_tag = f'<span class="test-group">{r.get("group", "")}</span>' if r.get("group") else ""
        details_html += f'''
        <div class="test-item" data-group="{r.get('group', '').lower()}" data-status="{'pass' if r['success'] else 'fail'}">
            <div class="test-header {status_class}" onclick="toggleDetails(this)">
                <span class="arrow">▶</span>
                <span class="test-name">{i+1}. {r.get('api_name', r.get('name', '未知接口'))}</span>
                {group_tag}
                <span class="test-status {status_class}">{status_text}</span>
                <span class="test-duration">⏱ {r['duration'] / 1000:.2f}s</span>
            </div>
            <div class="test-details">
                <div class="detail-row"><div class="detail-label">接口地址:</div><div class="detail-content url">{r.get('url', 'N/A')}</div></div>
                <div class="detail-row"><div class="detail-label">状态码:</div><div class="detail-content">{r.get('status_code', 'N/A')}</div></div>
                <div class="detail-row"><div class="detail-label">请求参数:</div><div class="detail-content json">{json.dumps(r.get('request_params') or r.get('request', {}), ensure_ascii=False, indent=2)}</div></div>
                <div class="detail-row"><div class="detail-label">请求体:</div><div class="detail-content json">{json.dumps(r.get('request_body') or r.get('request', {}), ensure_ascii=False, indent=2)}</div></div>
                <div class="detail-row"><div class="detail-label">响应数据:</div><div class="detail-content json">{json.dumps(r.get('response_data') or r.get('response', {}), ensure_ascii=False, indent=2)}</div></div>
                <div class="detail-row"><div class="detail-label">断言:</div><div class="detail-content">{r.get('assertion', 'N/A')}</div></div>
            </div>
        </div>'''
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:#f5f6f7;color:#333;line-height:1.6}}
        .container{{max-width:1200px;margin:0 auto;padding:20px}}
        .header{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:30px;border-radius:10px;margin-bottom:20px}}
        .header h1{{font-size:28px;margin-bottom:10px}}
        .header .meta{{font-size:14px;opacity:0.9}}
        .header .meta span{{margin-right:20px}}
        .stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:15px;margin-bottom:20px}}
        .stat-card{{background:white;padding:20px;border-radius:8px;text-align:center}}
        .stat-card .value{{font-size:36px;font-weight:bold;margin-bottom:5px}}
        .stat-card .label{{font-size:14px;color:#666}}
        .stat-card.passed .value{{color:#52c41a}}
        .stat-card.failed .value{{color:#ff4d4f}}
        .stat-card.total .value{{color:#1890ff}}
        .stat-card.duration .value{{color:#faad14}}
        .stat-card.script-duration .value{{color:#722ed1}}
        .progress-section{{background:white;padding:20px;border-radius:8px;margin-bottom:20px}}
        .progress-bar{{height:24px;background:#f0f0f0;border-radius:12px;overflow:hidden;margin-top:10px}}
        .progress-fill{{height:100%;background:linear-gradient(90deg,#52c41a,#73d13d);display:flex;align-items:center;justify-content:center;color:white;font-size:12px;font-weight:bold}}
        .chart-section{{background:white;padding:20px;border-radius:8px;margin-bottom:20px}}
        .chart-container{{display:flex;justify-content:center;align-items:center;gap:30px;flex-wrap:wrap}}
        .legend{{display:flex;flex-direction:column;gap:10px}}
        .legend-item{{display:flex;align-items:center;gap:8px}}
        .legend-color{{width:16px;height:16px;border-radius:3px}}
        .legend-color.passed{{background:#52c41a}}
        .legend-color.failed{{background:#ff4d4f}}
        .groups-section{{background:white;padding:20px;border-radius:8px;margin-bottom:20px}}
        .groups-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px}}
        .group-card{{background:#fafafa;padding:15px;border-radius:6px;border:1px solid #e8e8e8}}
        .group-name{{font-weight:600;font-size:16px;margin-bottom:10px;color:#667eea}}
        .group-stats{{display:flex;gap:10px;font-size:13px;margin-bottom:8px}}
        .group-progress{{height:8px;background:#e8e8e8;border-radius:4px;overflow:hidden}}
        .group-bar{{height:100%;background:linear-gradient(90deg,#52c41a,#73d13d)}}
        .group-rate{{text-align:right;font-size:12px;color:#666;margin-top:5px}}
        .filter-section{{background:white;padding:20px;border-radius:8px;margin-bottom:20px}}
        .filter-row{{display:flex;gap:15px;flex-wrap:wrap;align-items:center}}
        .filter-group{{display:flex;flex-direction:column;gap:5px}}
        .filter-group label{{font-size:12px;color:#666;font-weight:600}}
        .filter-input{{padding:8px 12px;border:1px solid #d9d9d9;border-radius:4px;font-size:14px}}
        .filter-select{{padding:8px 12px;border:1px solid #d9d9d9;border-radius:4px;font-size:14px;background:white}}
        .filter-btn{{padding:8px 16px;background:#667eea;color:white;border:none;border-radius:4px;cursor:pointer;font-size:14px}}
        .filter-btn:hover{{background:#5568d3}}
        .details-section{{background:white;padding:20px;border-radius:8px}}
        .details-section h2{{font-size:20px;margin-bottom:15px;padding-bottom:10px;border-bottom:2px solid #f0f0f0}}
        .test-item{{border:1px solid #e8e8e8;border-radius:6px;margin-bottom:10px;overflow:hidden}}
        .test-header{{padding:12px 15px;display:flex;align-items:center;cursor:pointer;gap:10px}}
        .test-header:hover{{background:#f5f5f5}}
        .test-header.passed{{background:#f6ffed;border-left:4px solid #52c41a}}
        .test-header.failed{{background:#fff1f0;border-left:4px solid #ff4d4f}}
        .test-name{{font-weight:500;flex:1}}
        .test-group{{padding:2px 8px;background:#f0f0f0;border-radius:10px;font-size:11px;color:#666}}
        .test-status{{padding:4px 12px;border-radius:12px;font-size:12px;font-weight:bold;color:white}}
        .test-status.passed{{background:#52c41a}}
        .test-status.failed{{background:#ff4d4f}}
        .test-duration{{margin-left:15px;font-size:13px;color:#666}}
        .arrow{{font-size:12px;color:#999}}
        .test-details{{padding:15px;background:#fafafa;display:none;border-top:1px solid #e8e8e8}}
        .test-details.show{{display:block}}
        .detail-row{{margin-bottom:10px}}
        .detail-label{{font-weight:600;color:#555;margin-bottom:5px}}
        .detail-content{{background:white;padding:10px;border-radius:4px;border:1px solid #e8e8e8;font-family:Consolas,monospace;font-size:13px;overflow-x:auto;white-space:pre-wrap}}
        .detail-content.url{{background:#e6f7ff;border-color:#91d5ff;color:#1890ff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;word-break:break-all}}
        .footer{{text-align:center;padding:20px;color:#999;font-size:13px}}
        .no-results{{text-align:center;padding:40px;color:#999}}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {title}</h1>
            <div class="meta">
                <span>🕐 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                <span>👤 测试人员：测试AI团队</span>
            </div>
        </div>
        <div class="stats">
            <div class="stat-card total"><div class="value">{total}</div><div class="label">总用例数</div></div>
            <div class="stat-card passed"><div class="value">{passed}</div><div class="label">✅ 通过</div></div>
            <div class="stat-card failed"><div class="value">{failed}</div><div class="label">❌ 失败</div></div>
            <div class="stat-card duration"><div class="value">{total_duration_s:.2f}s</div><div class="label">接口请求耗时</div></div>
            {f'<div class="stat-card script-duration"><div class="value">{script_duration:.2f}s</div><div class="label">脚本执行时长</div></div>' if script_duration > 0 else ''}
        </div>
        <div class="progress-section">
            <div style="display:flex;justify-content:space-between;margin-bottom:10px">
                <strong>通过率</strong>
                <span style="font-weight:bold;color:{'#52c41a' if pass_rate>=90 else '#faad14' if pass_rate>=70 else '#ff4d4f'}">{pass_rate:.1f}%</span>
            </div>
            <div class="progress-bar"><div class="progress-fill" style="width:{pass_rate}%">{passed}/{total}</div></div>
        </div>
        <div class="chart-section">
            <h2 style="margin-bottom:15px">📈 结果分布</h2>
            <div class="chart-container">
                {pie_svg}
                <div class="legend">
                    <div class="legend-item"><div class="legend-color passed"></div><span>通过：{passed} ({passed/total*100:.1f}%)</span></div>
                    <div class="legend-item"><div class="legend-color failed"></div><span>失败：{failed} ({failed/total*100:.1f}%)</span></div>
                </div>
            </div>
        </div>
        {groups_html}
        <div class="filter-section">
            <h2 style="margin-bottom:15px">🔍 搜索过滤</h2>
            <div class="filter-row">
                <div class="filter-group">
                    <label>关键字搜索</label>
                    <input type="text" id="searchInput" class="filter-input" placeholder="输入接口名称..." onkeyup="filterTests()">
                </div>
                <div class="filter-group">
                    <label>按分组筛选</label>
                    <select id="groupFilter" class="filter-select" onchange="filterTests()">
                        <option value="">全部分组</option>
                        {''.join([f'<option value="{g.lower()}">{g}</option>' for g in groups.keys()])}
                    </select>
                </div>
                <div class="filter-group">
                    <label>按状态筛选</label>
                    <select id="statusFilter" class="filter-select" onchange="filterTests()">
                        <option value="">全部状态</option>
                        <option value="pass">✅ 通过</option>
                        <option value="fail">❌ 失败</option>
                    </select>
                </div>
                <div class="filter-group" style="justify-content:flex-end">
                    <label>&nbsp;</label>
                    <button class="filter-btn" onclick="resetFilters()">重置筛选</button>
                </div>
            </div>
            <div style="margin-top:10px;font-size:13px;color:#666">
                显示 <span id="showCount">{total}</span> / {total} 个测试用例
            </div>
        </div>
        <div class="details-section">
            <h2>📋 测试详情</h2>
            <div id="testList">{details_html}</div>
            <div id="noResults" class="no-results" style="display:none">😕 没有找到匹配的测试用例</div>
        </div>
        <div class="footer"><p>Generated by Test Report Generator | © 2026 我的 AI 团队</p></div>
    </div>
    <script>
        function toggleDetails(header) {{
            const details = header.nextElementSibling;
            details.classList.toggle('show');
            header.querySelector('.arrow').textContent = details.classList.contains('show') ? '▼' : '▶';
        }}
        function filterTests() {{
            const search = document.getElementById('searchInput').value.toLowerCase();
            const group = document.getElementById('groupFilter').value;
            const status = document.getElementById('statusFilter').value;
            let count = 0;
            document.querySelectorAll('.test-item').forEach(item => {{
                const name = item.querySelector('.test-name').textContent.toLowerCase();
                const itemGroup = item.dataset.group;
                const itemStatus = item.dataset.status;
                const matchSearch = !search || name.includes(search);
                const matchGroup = !group || itemGroup === group;
                const matchStatus = !status || itemStatus === status;
                if (matchSearch && matchGroup && matchStatus) {{
                    item.style.display = '';
                    count++;
                }} else {{
                    item.style.display = 'none';
                }}
            }});
            document.getElementById('showCount').textContent = count;
            document.getElementById('noResults').style.display = count === 0 ? 'block' : 'none';
            document.getElementById('testList').style.display = count === 0 ? 'none' : 'block';
        }}
        function resetFilters() {{
            document.getElementById('searchInput').value = '';
            document.getElementById('groupFilter').value = '';
            document.getElementById('statusFilter').value = '';
            filterTests();
        }}
    </script>
</body>
</html>'''
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html, encoding='utf-8')
    print(f"✅ 报告已生成：{output_path}")
    return output_path


if __name__ == "__main__":
    demo_data = [
        {"name": "用户登录接口", "success": True, "duration": 0.52, "status_code": 200, "group": "platform", "request": {"method": "POST", "url": "/api/login"}, "response": {"code": 200}, "assertion": "状态码=200"},
        {"name": "获取用户信息", "success": True, "duration": 0.38, "status_code": 200, "group": "platform", "request": {"method": "GET", "url": "/api/user"}, "response": {"code": 200}, "assertion": "状态码=200"},
        {"name": "创建订单", "success": False, "duration": 1.25, "status_code": 500, "group": "merchant", "request": {"method": "POST", "url": "/api/order"}, "response": {"code": 500}, "assertion": "状态码=200 ❌"},
        {"name": "查询商品列表", "success": True, "duration": 0.67, "status_code": 200, "group": "merchant", "request": {"method": "GET", "url": "/api/products"}, "response": {"code": 200}, "assertion": "状态码=200"},
        {"name": "提交评价", "success": True, "duration": 0.89, "status_code": 200, "group": "merchant", "request": {"method": "POST", "url": "/api/review"}, "response": {"code": 200}, "assertion": "状态码=200"},
        {"name": "删除购物车", "success": False, "duration": 0.45, "status_code": 404, "group": "merchant", "request": {"method": "DELETE", "url": "/api/cart"}, "response": {"code": 404}, "assertion": "状态码=200 ❌"},
        {"name": "修改地址", "success": True, "duration": 0.73, "status_code": 200, "group": "platform", "request": {"method": "PUT", "url": "/api/address"}, "response": {"code": 200}, "assertion": "状态码=200"},
    ]
    generate_html_report(demo_data, "reports/demo_report.html", "🧪 接口自动化测试 Demo 报告")
