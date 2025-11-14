import os
import uuid
from flask import Flask, request, send_file, jsonify, after_this_request
from pdf2image import convert_from_bytes
import pytesseract

app = Flask(__name__)

# ======================================================
# Poppler / Tesseract configuration for Linux / Render
# ======================================================

# If you set POPLER_BIN in Render env vars, we'll use it.
# Otherwise, pdf2image will rely on system PATH (pdftoppm).
POPLER_BIN = os.environ.get("POPLER_BIN", None)

# If you set TESSERACT_CMD in Render env vars, we'll use it.
# Otherwise, pytesseract will use "tesseract" from PATH.
TESSERACT_CMD = os.environ.get("TESSERACT_CMD", None)
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "PDF to Image & OCR API is running"})


# ============================================
#   PDF → IMAGE ENDPOINT
# ============================================
@app.route("/convert", methods=["POST"])
def convert_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    pdf_bytes = request.files["file"].read()

    try:
        # If POPLER_BIN is None, don't pass it (use system PATH)
        if POPLER_BIN:
            images = convert_from_bytes(pdf_bytes, poppler_path=POPLER_BIN)
        else:
            images = convert_from_bytes(pdf_bytes)

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
        print("Error in /convert:", e)
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
        print("Error in /ocr:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Render sets PORT env var; default to 5000 locally
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
