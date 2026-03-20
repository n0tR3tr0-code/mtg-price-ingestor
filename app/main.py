from flask import Flask, jsonify
import requests

app = Flask(__name__)

SCRYFALL_API = 'https://api.scryfall.com'

@app.route('/price/<card_name>', methods=['GET'])
def get_card_prices(card_name):
    search_url = f"{SCRYFALL_API}/cards/named?fuzzy={card_name}"
    response = requests.get(search_url)
    
    if response.status_code != 200:
        return jsonify({'error': 'Carta non trovata'}), 404
    
    base_data = response.json()
    prints_url = base_data.get('prints_search_uri')
    
    prints_response = requests.get(prints_url).json()
    all_prints = prints_response.get('data', [])
    
    results = []
    for p in all_prints:
        prices = p.get('prices', {})
        if any(price for price in prices.values()):
            results.append({
                "set_name": p.get('set_name'),
                "set_code": p.get('set'),
                "prices": prices,
                "released_at": p.get('released_at'),
                "uri": p.get('scryfall_uri')
            })
    
    return jsonify({
        "card_name": base_data.get('name'),
        "total_prints": len(results),
        "prints": results
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)