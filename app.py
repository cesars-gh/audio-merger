import os
import uuid
import tempfile
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import requests
from pydub import AudioSegment

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint for container orchestration systems"""
    return jsonify({"status": "healthy", "service": "audio-merger"}), 200


@app.route("/merge", methods=["POST"])
def merge_audio():
    # Check if request has JSON data
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    # Get list of URLs from request
    data = request.get_json()
    if (
        "urls" not in data
        or not isinstance(data["urls"], list)
        or len(data["urls"]) < 1
    ):
        return jsonify({"error": "Request must contain a non-empty list of URLs"}), 400

    urls = data["urls"]

    # Create temp directory for downloads
    temp_dir = tempfile.mkdtemp()
    audio_files = []

    try:
        # Download each audio file from URL
        for i, url in enumerate(urls):
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                return jsonify({"error": f"Failed to download file from {url}"}), 400

            # Save the downloaded file
            file_path = os.path.join(temp_dir, f"audio_{i}.mp3")
            with open(file_path, "wb") as f:
                f.write(response.content)
            audio_files.append(file_path)

        # Merge audio files
        if not audio_files:
            return jsonify({"error": "No valid audio files were found"}), 400

        merged = AudioSegment.from_mp3(audio_files[0])
        for file_path in audio_files[1:]:
            sound = AudioSegment.from_mp3(file_path)
            merged += sound

        # Save the merged file
        output_filename = f"merged_{uuid.uuid4().hex}.mp3"
        output_path = os.path.join(temp_dir, output_filename)
        merged.export(output_path, format="mp3")

        # Send the file as response for download
        return send_file(
            output_path,
            as_attachment=True,
            download_name="merged.mp3",
            mimetype="audio/mpeg",
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Clean up downloaded files
        for file_path in audio_files:
            if os.path.exists(file_path):
                os.remove(file_path)

        # Clean up output file - it will be removed after the response is sent
        # as the OS will clean up the temp directory


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
