import os
import json
from flask import Flask, request, render_template, redirect, url_for
from portfolio_generator import generate_portfolio
from resumeparser import ats_extractor

# ---------------------- FOLDERS ----------------------
UPLOAD_PATH = "__DATA__"
os.makedirs(UPLOAD_PATH, exist_ok=True)

os.makedirs("generated_sites", exist_ok=True)

# ---------------------- FLASK APP ----------------------
app = Flask(__name__)
app.secret_key = "super-secret-key"


# ---------------------- HOME ----------------------
@app.route("/")
def index():
    return render_template(
        "index.html",
        data=None,
        data_json=None,
        ats_score=None,
        ideal_score=None,
    )


# ---------------------- PROCESS RESUME ----------------------
@app.route("/process", methods=["POST"])
def ats():
    if "pdf_doc" not in request.files:
        return "No file uploaded!"

    doc = request.files["pdf_doc"]
    file_path = os.path.join(UPLOAD_PATH, "file.pdf")
    doc.save(file_path)

    # Extract resume data (includes ats_score, ideal_score, ats_details, etc.)
    data = ats_extractor(file_path)

    # Make sure UI always gets JSON
    if not isinstance(data, dict):
        data = {"error": "Invalid response", "raw": str(data)}

    # JSON string for hidden field / JS usage
    data_json = json.dumps(data)

    return render_template(
        "index.html",
        data=data,
        data_json=data_json,
        ats_score=data.get("ats_score"),
        ideal_score=data.get("ideal_score"),
    )


# ---------------------- CREATE PORTFOLIO + REDIRECT ----------------------
@app.route("/create_portfolio", methods=["POST"])
def create_portfolio():
    parsed_data = request.form.get("parsed_json")

    if not parsed_data:
        return "No data received"

    parsed_data = json.loads(parsed_data)

    # ALWAYS use theme_modern
    uid = generate_portfolio(parsed_data, theme="theme_modern")

    return redirect(url_for("portfolio_page", pid=uid))


# ---------------------- SERVE GENERATED PORTFOLIO ----------------------
@app.route("/portfolio/<pid>")
def portfolio_page(pid):
    file_path = os.path.join("generated_sites", pid, "index.html")

    if not os.path.exists(file_path):
        return "Portfolio not found", 404

    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()

    return html


# ---------------------- RUN APP ----------------------
if __name__ == "__main__":
    app.run(port=8000, debug=True)
