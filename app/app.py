from flask import Flask, render_template_string, request, send_file, jsonify
from io import BytesIO
import time
from collections import OrderedDict
import os

app = Flask(__name__)
MAX_USERS = 4
screenshots = OrderedDict()

@app.route('/upload', methods=['POST'])
def upload():
    user_id = request.form.get('user_id')
    file = request.files['image']
    
    screenshots[user_id] = {
        'data': file.read(),
        'timestamp': time.time()
    }
    
    if len(screenshots) > MAX_USERS:
        screenshots.popitem(last=False)
    
    return 'OK'

@app.route('/get_image/<user_id>')
def get_image(user_id):
    if user_id in screenshots:
        response = send_file(
            BytesIO(screenshots[user_id]['data']),
            mimetype='image/jpeg'
        )
        response.headers['Cache-Control'] = 'no-store, max-age=0'
        return response
    return 'Not Found', 404

@app.route('/get_status')
def get_status():
    # 清理过期用户
    current_time = time.time()
    expired = [uid for uid, data in screenshots.items() 
              if current_time - data['timestamp'] > 30]
    for uid in expired:
        del screenshots[uid]
    
    return jsonify({
        'users': list(screenshots.keys()),
        'timestamp': int(time.time())
    })

@app.route('/')
def monitor():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Supervised Learning</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
            <style>
                :root {
                    --primary-color: #2c3e50;
                    --secondary-color: #3498db;
                    --background: #f8f9fa;
                    --card-bg: #ffffff;
                    --transition-duration: 0.3s;
                }

                body {
                    margin: 0;
                    padding: 20px;
                    background: var(--background);
                    font-family: 'Segoe UI', system-ui, sans-serif;
                    transition: background 0.3s ease;
                }

                .text-container {
                    max-width: 800px;
                    margin: 2rem auto;
                    padding: 20px;
                }

                .card {
                    background: var(--card-bg);
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    padding: 20px;
                    margin-top: 10px;
                    margin-bottom: 10px;
                }

                h1, h2 {
                    color: var(--primary-color);
                }

                .container {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 20px;
                    max-width: 1600px;
                    margin: 0 auto;
                }

                .user-card {
                    background: var(--card-bg);
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                    transition: transform 0.2s;
                }

                .user-card:hover {
                    transform: translateY(-3px);
                }

                .card-header {
                    padding: 15px;
                    background: var(--secondary-color);
                    color: white;
                }

                .card-header h3 {
                    margin: 0;
                    font-size: 1.2em;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .image-container {
                    position: relative;
                    width: 100%;
                    padding-top: 56.25%;
                    background: #000;
                }

                .screen-image {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                    background: #000;
                    transition: opacity 0.3s;
                }

                #floating-menu {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                }

                .menu-icon {
                    cursor: pointer;
                    font-size: 1.5em;
                    background: var(--secondary-color);
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                }
                .theme-toggle {
                    background: var(--card-bg);
                    border: 2px solid var(--secondary-color);
                    color: var(--icon-color);
                    transition: all var(--transition-duration) ease;
                }

                /* 暗黑模式变量定义 */
                [data-theme="dark"] {
                    --primary-color: #ecf0f1;
                    --secondary-color: #1abc9c;
                    --background: #2c3e50;
                    --card-bg: #34495e;
                    --icon-color: #ecf0f1;
                }
            </style>
        </head>
        <body>
            <div class="text-container">
                <div class="card">
                  <h1 style="text-align: center;">大型多智能体线上联合监督学习任务</h1>
                </div>
            </div>

            <div id="main-container"></div>

            <div id="floating-menu">
                <div class="menu-icon" onclick="window.location.href='/about'"><i class="bi bi-info"></i></div>
                <div class="menu-icon" onclick="toggleDarkMode()"><i id="themeIcon"></i></div>
            </div>

            <script>
                // 核心刷新逻辑
                function loadContent() {
                    fetch('/get_status')
                        .then(r => r.json())
                        .then(data => {
                            const container = document.getElementById('main-container');
                            container.innerHTML = `
                                <div class="container">
                                    ${data.users.map(user => `
                                        <div class="user-card" data-user="${user}">
                                            <div class="card-header">
                                                <h3><i class="fas fa-user"></i> ${user}</h3>
                                            </div>
                                            <div class="image-container">
                                                <img class="screen-image" 
                                                     src="/get_image/${user}?t=${Date.now()}" 
                                                     onload="this.style.opacity=1"
                                                     style="opacity:0">
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            `;
                        });
                }

                function initializeTheme() {
                    const savedTheme = localStorage.getItem('theme');
                    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                    
                    // 优先使用保存的主题，其次跟随系统
                    const initialTheme = savedTheme || (systemPrefersDark ? 'dark' : 'light');
                    applyTheme(initialTheme, !savedTheme);
                }

                function applyTheme(theme, isSystem = false) {
                    const root = document.documentElement;
                    root.setAttribute('data-theme', theme);
                    
                    // 更新图标
                    const icon = document.getElementById('themeIcon');
                    icon.className = theme === 'dark' 
                                ? 'bi bi-sun'
                                : 'bi bi-moon';

                    // 仅当用户手动切换时保存
                    if (!isSystem) {
                        localStorage.setItem('theme', theme);
                    }
                }

                function toggleDarkMode() {
                    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
                    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                    applyTheme(newTheme);
                }

                window.matchMedia('(prefers-color-scheme: dark)').addListener(e => {
                    if (!localStorage.getItem('theme')) {
                        applyTheme(e.matches ? 'dark' : 'light', true);
                    }
                });

                initializeTheme();

                // 初始化加载
                loadContent();
                // 每 3 秒刷新
                setInterval(loadContent, 3000);
            </script>
        </body>
        </html>
    ''')

@app.route('/about')
def about():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>About: Supervised Learning</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
            <style>
                /* 继承主界面的CSS变量 */
                :root {
                    --primary-color: #2c3e50;
                    --secondary-color: #3498db;
                    --background: #f8f9fa;
                    --card-bg: #ffffff;
                }

                /* 共用主界面样式 */
                body {
                    margin: 0;
                    padding: 20px;
                    background: var(--background);
                    font-family: 'Segoe UI', system-ui, sans-serif;
                    transition: background 0.3s ease;
                }

                .text-container {
                    max-width: 800px;
                    margin: 2rem auto;
                    padding: 20px;
                }

                .card {
                    background: var(--card-bg);
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    padding: 20px;
                    margin-top: 10px;
                    margin-bottom: 10px;
                }

                /* 复用主界面悬浮菜单 */
                #floating-menu {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                }

                .menu-icon {
                    cursor: pointer;
                    font-size: 1.5em;
                    background: var(--secondary-color);
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    color: white;
                }

                h1, h2 {
                    color: var(--primary-color);
                }

                ul {
                    padding-left: 20px;
                    color: var(--primary-color);
                }

                li {
                    margin-bottom: 10px;
                    line-height: 1.6;
                }

                .neuron {
                    width: 20px;
                    height: 20px;
                    background: var(--secondary-color);
                    border-radius: 50%;
                    margin: 10px;
                    animation: pulse 1.5s infinite;
                }

                @keyframes pulse {
                    0% { transform: scale(0.9); opacity: 0.7; }
                    50% { transform: scale(1.1); opacity: 1; }
                    100% { transform: scale(0.9); opacity: 0.7; }
                }

                /* 暗黑模式变量定义 */
                [data-theme="dark"] {
                    --primary-color: #ecf0f1;
                    --secondary-color: #1abc9c;
                    --background: #2c3e50;
                    --card-bg: #34495e;
                    --icon-color: #ecf0f1;
                }
            </style>
        </head>
        <body>
            <div class="text-container">
                <div class="card">
                    <h1><i class="bi bi-info-circle"></i> 技术说明</h1>
                    
                    <h2>系统特性：</h2>
                    <ul>
                        <li><i class="bi bi-arrow-clockwise"></i> 实时人类数据反向传播系统</li>
                        <li><i class="bi bi-robot"></i> 基于群体智慧的集成学习框架</li>
                        <li><i class="bi bi-speedometer"></i> 自适应学习率调节器 v2.3.1</li>
                        <li><i class="bi bi-graph-up"></i> 可视化梯度监控界面</li>
                    </ul>

                    <h2>使用说明：</h2>
                    <ul>
                        <li><i class="bi bi-pin-angle"></i> 每个客户端需要唯一用户ID</li>
                        <li><i class="bi bi-alarm"></i> 30秒无活动自动离线</li>
                        <li><i class="bi bi-moon"></i> 支持暗黑/明亮模式切换</li>
                        <li><i class="bi bi-robot"></i> 本项目 99% 的代码由 Deepseek-r1 生成，包括以上的笑话</li>
                    </ul>
                </div>
            </div>

            <!-- 统一悬浮菜单 -->
            <div id="floating-menu">
                <div class="menu-icon" onclick="window.location.href='/'"><i class="bi bi-house"></i></div>
                <div class="menu-icon" onclick="toggleDarkMode()"><i id="themeIcon"></i></div>
            </div>

            <script>
                // 复用主界面的暗黑模式切换
                function initializeTheme() {
                    const savedTheme = localStorage.getItem('theme');
                    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                    
                    // 优先使用保存的主题，其次跟随系统
                    const initialTheme = savedTheme || (systemPrefersDark ? 'dark' : 'light');
                    applyTheme(initialTheme, !savedTheme);
                }

                function applyTheme(theme, isSystem = false) {
                    const root = document.documentElement;
                    root.setAttribute('data-theme', theme);
                    
                    // 更新图标
                    const icon = document.getElementById('themeIcon');
                    icon.className = theme === 'dark' 
                                ? 'bi bi-sun'
                                : 'bi bi-moon';

                    // 仅当用户手动切换时保存
                    if (!isSystem) {
                        localStorage.setItem('theme', theme);
                    }
                }

                function toggleDarkMode() {
                    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
                    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                    applyTheme(newTheme);
                }

                window.matchMedia('(prefers-color-scheme: dark)').addListener(e => {
                    if (!localStorage.getItem('theme')) {
                        applyTheme(e.matches ? 'dark' : 'light', true);
                    }
                });

                initializeTheme();
            </script>
        </body>
        </html>
    ''')
