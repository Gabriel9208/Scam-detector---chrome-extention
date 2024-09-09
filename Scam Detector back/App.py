from Data.whoisInfo import searchWhois
from Data.TLS_check import fetchTlsCert
from Data.findbiz import findbiz
from Data.scraper import scraper

from flask import Flask, request, jsonify
from flask_cors import CORS
import ssl
import socket

app = Flask(__name__)
CORS(app)

def get_cert_info(hostname, port=443):
    context = ssl.create_default_context()
    with socket.create_connection((hostname, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as secure_sock:
            cert = secure_sock.getpeercert()
    
    return {
        "subject": dict(x[0] for x in cert['subject']),
        "issuer": dict(x[0] for x in cert['issuer']),
        "version": cert['version'],
        "serialNumber": cert['serialNumber'],
        "notBefore": cert['notBefore'],
        "notAfter": cert['notAfter']
    }

@app.route('/get-tls-info')
def get_tls_cert():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400
    
    try:
        hostname = url.split("://")[-1].split("/")[0]
        cert_info = get_cert_info(hostname)
        return jsonify(cert_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/get-whois-info')
def get_whois():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400
    
    try:
        whois_info = searchWhois(url)
        return jsonify(whois_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/get-business-info')
def get_biz():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400
    
    try:
        biz_info = findbiz(url)
        return jsonify(biz_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@app.route('/get-page-info')
def get_scraper():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400
    
    try:
        scraper_info = scraper(url)
        return jsonify(scraper_info)
    except Exception as e: 
        return jsonify({"error": str(e)}), 500



# if __name__ == '__main__':
#     app.run(debug=True, port=5000, threaded=True)