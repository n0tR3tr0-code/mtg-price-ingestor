from flask import Flask, jsonify
import requests
from sqlalchemy import create_engine, text

app = Flask(__name__)

SCRYFALL_API = 'https://api.scryfall.com'
DB_URL = "postgresql://postgres:password@db-mtg:5432/mtgdb"
engine = create_engine(DB_URL)

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

    with engine.begin() as conn:
        insert_card_query = text(
            """
            INSERT INTO cards (card_name, total_prints)
            VALUES (:card_name, :total_prints)
            ON CONFLICT (card_name) DO UPDATE SET total_prints = EXCLUDED.total_prints
            RETURNING id

            """
        )
        card_id = conn.execute(insert_card_query, {"card_name": card_name, "total_prints": len(all_prints)}).fetchone()[0]
        
        for p in all_prints:
            prices = p.get('prices', {})
            if any(price for price in prices.values()):
                insert_price_query = text(
                    """
                    INSERT INTO card_prices (card_id, set_name, set_code, price_eur, price_usd, released_at)
                    VALUES (:c_id, :s_name, :s_code, :p_eur, :p_usd, :r_at)

                    """
                )
                conn.execute(insert_price_query, {
                    "c_id": card_id,
                    "s_name": p.get('set_name'),
                    "s_code": p.get('set'),
                    "p_eur": prices.get('eur'),
                    "p_usd": prices.get('usd'),
                    "r_at": p.get('released_at')
                })
                results.append({
                    "set_name": p.get('set_name'),
                    "set_code": p.get('set'),
                    "prices": prices,
                    "released_at": p.get('released_at')
                })
    
    return jsonify({
        "card_name": base_data.get('name'),
        "database_id": card_id,
        "total_prints": len(results),
        "prints": results
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)