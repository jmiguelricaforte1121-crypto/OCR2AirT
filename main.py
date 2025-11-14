from flask import Flask, request, send_file, jsonify, after_this_request
from pdf2image import convert_from_bytes
import pytesseract
import uuid
import os

app = Flask(__name__)

# Your Poppler path (Windows)
POPLER_BIN = r"C:\Users\Administrator\Documents\Release-25.07.0-0\poppler-25.07.0\Library\bin"

# Your Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "PDF to Image API is running"})


# ============================================
#   PDF → IMAGE ENDPOINT
# ============================================
@app.route("/convert", methods=["POST"])
def convert_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    pdf_bytes = request.files["file"].read()

    try:
        images = convert_from_bytes(pdf_bytes, poppler_path=POPLER_BIN)

        img_name = f"{uuid.uuid4()}.png"
        images[0].save(img_name, "PNG")

        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(img_name):
                    os.remove(img_name)
            except Exception as e:
                print("Cleanup error:", e)
            return response

        return send_file(img_name, mimetype="image/png")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================
#   OCR ENDPOINT (IMAGE → TEXT)
# ============================================
@app.route("/ocr", methods=["POST"])
def extract_text():
    if "file" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["file"]

    try:
        # Save the image temporarily
        img_name = f"{uuid.uuid4()}.png"
        file.save(img_name)

        # Run OCR
        text = pytesseract.image_to_string(img_name)

        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(img_name):
                    os.remove(img_name)
            except Exception as e:
                print("Cleanup error:", e)
            return response

        return jsonify({"text": text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000)
