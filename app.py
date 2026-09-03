from flask import Flask, request, jsonify, render_template
import analysis
import database

app = Flask(__name__)
database.init_db()


@app.route("/webhook", methods=["POST"])
def webhook():
    """Reçoit une alerte TradingView et déclenche l'analyse."""
    data = request.get_json(force=True, silent=True) or {}
    symbol = data.get("symbol", "XAUUSD").upper()
    timeframe = data.get("timeframe", "H4").upper()

    try:
        result = analysis.run_analysis(symbol, timeframe)
        database.save_signal(result)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e), "symbol": symbol}), 500


@app.route("/analyze/<symbol>", methods=["GET"])
@app.route("/analyze/<symbol>/<timeframe>", methods=["GET"])
def analyze_manual(symbol, timeframe="H4"):
    """Permet de déclencher une analyse manuellement (test, sans TradingView).
    Exemples : /analyze/XAUUSD (H4 par défaut) ou /analyze/XAUUSD/H1
    """
    try:
        result = analysis.run_analysis(symbol.upper(), timeframe.upper())
        database.save_signal(result)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e), "symbol": symbol}), 500


@app.route("/", methods=["GET"])
def dashboard():
    signals = database.get_all_signals(limit=150)
    latest_h4 = next((s for s in signals if s.get("timeframe") == "H4"), None)
    latest_h1 = next((s for s in signals if s.get("timeframe") == "H1"), None)
    return render_template(
        "dashboard.html", signals=signals, latest_h4=latest_h4, latest_h1=latest_h1
    )


@app.route("/api/signals", methods=["GET"])
def api_signals():
    return jsonify(database.get_all_signals(limit=100))


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
