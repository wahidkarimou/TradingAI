from flask import Flask, request, jsonify, render_template
import database
from strategy.live import get_live_signal, ASSETS
from notify import send_signal_email

app = Flask(__name__)
database.init_db()


def _process(symbol):
    previous = database.get_last_signal(symbol)
    result = get_live_signal(symbol)
    database.save_signal(result)

    is_actionable = result["signal"] in ("BULLISH", "BEARISH")
    changed = previous is None or previous.get("signal") != result["signal"]

    if is_actionable and changed:
        send_signal_email(result)

    return result


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True) or {}
    symbol = data.get("symbol", "XAUUSD").upper()
    try:
        result = _process(symbol)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e), "symbol": symbol}), 500


@app.route("/analyze/<symbol>", methods=["GET"])
def analyze_manual(symbol):
    symbol = symbol.upper()
    force = request.args.get("force", "false").lower() == "true"

    if symbol in ASSETS and not ASSETS[symbol]["enabled"] and not force:
        return jsonify({
            "symbol": symbol,
            "error": "actif desactive (validation walk-forward non passee). Ajoute ?force=true pour forcer."
        }), 403

    try:
        result = _process(symbol)
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
        assets=ASSETS
    )


@app.route("/api/signals", methods=["GET"])
def api_signals():
    return jsonify(database.get_all_signals(limit=100))


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)