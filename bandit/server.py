"""Flask HTTP service for bandit recommendations."""
from flask import Flask, jsonify


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    return app


if __name__ == "__main__":
    create_app().run(port=5000, debug=True)
