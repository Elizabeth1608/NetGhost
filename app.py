from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Функция 1: Поиск аниме
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

# Функция 2: Топ сезона
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "Empty query"}), 400
    results = search_anime(query)
    return jsonify({"success": True, "data": results})

@app.route('/api/top')
def api_top():
    results = get_top_season()
    return jsonify({"success": True, "data": results})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)