# Real-Time QR Code Recognition on reCamera

This solution runs QR code recognition directly on reCamera.

The device streams live camera video through RTSP and exposes the latest QR code result through an HTTP API. SenseCraft Solution shows the live stream in the preview window and overlays the decoded QR content, detection time, and bounding box directly on the video.

## Key Features

- RTSP live video stream from reCamera
- Local QR code detection on reCamera
- Separate QR detection thread that does not block video streaming
- Latest-frame queue with length 1 to avoid detection backlog
- HTTP API for the latest QR result
- In-app preview with QR recognition overlay

## Data Links

| Data Type | Protocol | Address | Purpose |
| --- | --- | --- | --- |
| Video Stream | RTSP | `rtsp://<device-ip>:8554/live0` | Display live camera video |
| QR Result | HTTP API | `http://<device-ip>:8080/api/qr/latest` | Get the latest QR code recognition result |
| Health Check | HTTP API | `http://<device-ip>:8080/api/health` | Check service status |

## How It Works

The application uses two video channels on reCamera. One channel is encoded as H.264 and streamed through RTSP. The other channel provides low-resolution NV21 frames for QR code detection.

The QR detection thread reads from a latest-frame queue with length 1. If detection is slower than the camera frame rate, old frames are overwritten by new frames. This keeps video smooth and prevents detection latency from continuously increasing.
