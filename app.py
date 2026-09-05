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
    selected_symbol = request.args.get("symbol", "XAUUSD").upper()
    all_signals = database.get_all_signals(limit=300)
    signals = [s for s in all_signals if s["symbol"] == selected_symbol]
    latest = signals[0] if signals else None
    return render_template(
        "dashboard.html",
        signals=signals[:100],
        latest=latest,
        selected_symbol=selected_symbol,
    )


@app.route("/api/signals", methods=["GET"])
def api_signals():
    return jsonify(database.get_all_signals(limit=100))


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
