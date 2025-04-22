import os
import uuid
import tempfile
import logging
from datetime import datetime
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import requests
from pydub import AudioSegment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint for container orchestration systems"""
    return jsonify({"status": "healthy", "service": "audio-merger"}), 200


@app.route("/merge", methods=["POST"])
def merge_audio():
    request_id = uuid.uuid4().hex[:8]  # Generate short request ID for tracking
    logger.info(f"[{request_id}] New merge request received")

    # Check if request has JSON data
    if not request.is_json:
        logger.warning(f"[{request_id}] Request without JSON data rejected")
        return jsonify({"error": "Request must be JSON"}), 400

    # Get list of URLs from request
    data = request.get_json()
    if (
        "urls" not in data
        or not isinstance(data["urls"], list)
        or len(data["urls"]) < 1
    ):
        logger.warning(f"[{request_id}] Request with invalid or empty URLs rejected")
        return jsonify({"error": "Request must contain a non-empty list of URLs"}), 400

    urls = data["urls"]
    logger.info(f"[{request_id}] Processing {len(urls)} audio files")

    # Create temp directory for downloads
    temp_dir = tempfile.mkdtemp()
    logger.info(f"[{request_id}] Created temporary directory: {temp_dir}")
    audio_files = []

    try:
        # Download each audio file from URL
        for i, url in enumerate(urls):
            logger.info(
                f"[{request_id}] Downloading file {i+1}/{len(urls)} from: {url}"
            )
            start_time = datetime.now()

            response = requests.get(url, stream=True)
            if response.status_code != 200:
                logger.error(
                    f"[{request_id}] Failed to download file from {url}: Status code {response.status_code}"
                )
                return jsonify({"error": f"Failed to download file from {url}"}), 400

            # Save the downloaded file
            file_path = os.path.join(temp_dir, f"audio_{i}.mp3")
            with open(file_path, "wb") as f:
                f.write(response.content)

            download_time = (datetime.now() - start_time).total_seconds()
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            logger.info(
                f"[{request_id}] Downloaded file {i+1}: {file_size:.2f} MB in {download_time:.2f} seconds"
            )

            audio_files.append(file_path)

        # Merge audio files
        if not audio_files:
            logger.error(f"[{request_id}] No valid audio files were found")
            return jsonify({"error": "No valid audio files were found"}), 400

        logger.info(f"[{request_id}] Starting audio merge of {len(audio_files)} files")
        merge_start_time = datetime.now()

        merged = AudioSegment.from_mp3(audio_files[0])
        logger.info(
            f"[{request_id}] Loaded first file: {os.path.basename(audio_files[0])}, duration: {len(merged)/1000:.2f}s"
        )

        for i, file_path in enumerate(audio_files[1:], 1):
            logger.info(
                f"[{request_id}] Merging file {i+1}/{len(audio_files)}: {os.path.basename(file_path)}"
            )
            sound = AudioSegment.from_mp3(file_path)
            logger.info(f"[{request_id}] File {i+1} duration: {len(sound)/1000:.2f}s")
            merged += sound

        # Save the merged file
        output_filename = f"merged_{uuid.uuid4().hex}.mp3"
        output_path = os.path.join(temp_dir, output_filename)
        logger.info(f"[{request_id}] Exporting merged file to: {output_path}")

        export_start_time = datetime.now()
        merged.export(output_path, format="mp3")
        export_time = (datetime.now() - export_start_time).total_seconds()

        total_merge_time = (datetime.now() - merge_start_time).total_seconds()
        merged_size = os.path.getsize(output_path) / (1024 * 1024)  # Size in MB
        logger.info(
            f"[{request_id}] Merge completed: {merged_size:.2f} MB, duration: {len(merged)/1000:.2f}s, processing time: {total_merge_time:.2f}s"
        )

        # Send the file as response for download
        logger.info(f"[{request_id}] Sending merged file to client")
        return send_file(
            output_path,
            as_attachment=True,
            download_name="merged.mp3",
            mimetype="audio/mpeg",
        )

    except Exception as e:
        logger.error(
            f"[{request_id}] Error during audio merge: {str(e)}", exc_info=True
        )
        return jsonify({"error": str(e)}), 500

    finally:
        # Clean up downloaded files
        logger.info(f"[{request_id}] Cleaning up temporary files")
        for file_path in audio_files:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"[{request_id}] Removed file: {file_path}")

        # Clean up output file - it will be removed after the response is sent
        # as the OS will clean up the temp directory


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
