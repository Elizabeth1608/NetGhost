from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime

app = Flask(__name__)

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def log_action(ip, action, detail):
    log_file = os.path.join(LOG_DIR, f"{ip}.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {action} | {detail}\n")

def search_anime(query):
    url = f"https://api.jikan.moe/v4/anime?q={query}&limit=5"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("data", [])
        return []
    except Exception as e:
        print(f"API error: {e}")
        return []

def get_top_season():
    url = "https://api.jikan.moe/v4/seasons/now"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("data", [])[:10]
        return []
    except Exception as e:
        print(f"API error: {e}")
        return []

def get_random_anime():
    url = "https://api.jikan.moe/v4/random/anime"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("data")
        return None
    except Exception as e:
        print(f"API error: {e}")
        return None

def scrape_description(title):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    search_url = f"https://animego.org/search/anime?q={title.replace(' ', '+')}"
    
    try:
        resp = requests.get(search_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, "html.parser")
        link_tag = soup.find("a", href=re.compile(r"/anime/.*-\d+"))
        if not link_tag:
            return None
        
        anime_url = "https://animego.org" + link_tag["href"]
        resp = requests.get(anime_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, "html.parser")
        desc_block = soup.find("div", class_="description")
        
        if desc_block:
            description = desc_block.get_text(strip=True)
            description = description.replace("Развернуть", "").strip()
            if len(description) > 800:
                description = description[:800] + "..."
            return description
        
        return None
    except Exception as e:
        print(f"Scraping error: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    ip = request.remote_addr
    log_action(ip, "SEARCH", f"query={query}")
    if not query:
        return jsonify({"error": "Empty query"}), 400
    results = search_anime(query)
    return jsonify({"success": True, "data": results})

@app.route('/api/top')
def api_top():
    ip = request.remote_addr
    log_action(ip, "TOP_SEASON", "loaded")
    results = get_top_season()
    return jsonify({"success": True, "data": results})

@app.route('/api/random')
def api_random():
    ip = request.remote_addr
    log_action(ip, "RANDOM", "loaded")
    result = get_random_anime()
    return jsonify({"success": True, "data": result})

@app.route('/api/description')
def api_description():
    title = request.args.get('title', '')
    ip = request.remote_addr
    log_action(ip, "SCRAPE", f"title={title}")
    if not title:
        return jsonify({"error": "No title"}), 400
    description = scrape_description(title)
    if description:
        return jsonify({"success": True, "description": description})
    else:
        return jsonify({"success": False, "description": "Описание не найдено"})

@app.route('/logs/<ip>.log')
def serve_log(ip):
    log_file = os.path.join(LOG_DIR, f"{ip}.log")
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
        return f"<pre style='background:#0A0A0F; color:#00FFC3; padding:20px; font-family:monospace;'>{content}</pre>"
    else:
        return "Лог-файл пока не создан", 404

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)