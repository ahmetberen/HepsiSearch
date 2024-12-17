from flask import Flask, request, jsonify
import requests  # HTTP istekleri için kütüphane
from bs4 import BeautifulSoup  # HTML parsing için kütüphane
from flask_cors import CORS  # CORS import edilir
import re
import time

app = Flask(__name__)

CORS(app)

def scrape(product_query, max_pages):
    product_query_url = product_query.replace(" ", "+")

    if max_pages > 6:
        max_pages = 6

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    base_url = f"https://www.hepsiburada.com/ara?q={product_query_url}"

    product_names = []
    product_prices = []
    product_links = []
    reviewScores = []

    for page in range(1, max_pages + 1):
        url = f"{base_url}&sayfa={page}"
        with requests.Session() as session:
            response = session.get(url, headers=headers)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            product_containers = soup.findAll('li', attrs={'class': 'productListContent-zAP0Y5msy8OHn5z7T_K_'})

            for product in product_containers:
                try:
                    name_tag = product.find('h3', attrs={'data-test-id': 'product-card-name'})
                    name = name_tag.text.strip() if name_tag else "Bilinmeyen Ürün"
                    name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
                    name = ' '.join(name.split())
                    product_names.append(name)

                    price_tag = product.find('div', attrs={'data-test-id': 'price-current-price'})
                    price = price_tag.text.strip() if price_tag else "Fiyat Bilinmiyor"
                    product_prices.append(price)

                    link_tag = product.find('a')
                    link = 'https://www.hepsiburada.com' + link_tag.get('href') if link_tag else "Bağlantı Yok"
                    product_links.append(link)


                    with requests.Session() as session:
                        response = session.get(link, headers=headers)
                        if response.status_code != 200:
                            continue
                        soup = BeautifulSoup(response.content, 'html.parser')
                        reviewDiv = soup.find("div",attrs={'data-test-id': 'has-review'})
                        reviewScore = reviewDiv.find("span").text
                        reviewScores.append(reviewScore)

                except Exception as e:
                    continue

        time.sleep(2)

    data = []
    for name, price, link, reviewScore in zip(product_names, product_prices, product_links, reviewScores):
        data.append({"name": name, "price": price, "link": link, "reviewScore": reviewScore})

    return data

@app.route('/scrape', methods=['GET'])
def scrape_endpoint():
    product_query = request.args.get('query')
    max_pages = int(request.args.get('page_number', 1))

    if not product_query:
        return jsonify({"error": "'query' parametresi gerekli."}), 400

    try:
        result = scrape(product_query, max_pages)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2000)
