# Audio Merger Microservice

A simple Flask microservice that merges multiple MP3 files into a single audio file.

## Features

- Accepts a list of MP3 URLs via a REST API
- Downloads and merges audio files in order
- Returns the merged file for direct download
- Packaged as a Docker container for easy deployment

## API Usage

### Merge Audio Files

**Endpoint**: `/merge`
**Method**: `POST`
**Content-Type**: `application/json`

**Request Body**:
```json
{
  "urls": [
    "https://example.com/audio1.mp3",
    "https://example.com/audio2.mp3",
    "https://example.com/audio3.mp3"
  ]
}
```

**cURL**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"urls":["https://samplelib.com/lib/preview/mp3/sample-3s.mp3","https://samplelib.com/lib/preview/mp3/sample-6s.mp3"]}' \
  -o merged.mp3 \
  http://localhost:8080/merge
```

**Response**: The merged MP3 file as a download

## Running Locally

### Prerequisites

- Python 3.12+
- ffmpeg

### Installation

1. Clone this repository
2. Install dependencies:
   ```
   pnpm install
   ```
   or
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python app.py
   ```

## Docker Deployment

### Build the Docker Image

```bash
docker build -t audio-merger .
```

### Run the Container

```bash
docker run -p 5000:5000 audio-merger
```

The service will be available at http://localhost:5000

## Example Request

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"urls":["https://example.com/audio1.mp3","https://example.com/audio2.mp3"]}' \
  -o merged.mp3 \
  http://localhost:5000/merge
``` 