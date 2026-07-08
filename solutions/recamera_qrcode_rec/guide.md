## Preset: Native Binary Deployment {#default}

Deploy a prebuilt `qrcode_rec` executable to reCamera. Users do not need to compile source code on the device.

| Device | Purpose |
| --- | --- |
| reCamera | Captures video, streams RTSP, and runs QR recognition |

**What you'll get:**

- RTSP video stream: `rtsp://<device-ip>:8554/live0`
- Latest QR result API: `http://<device-ip>:8080/api/qr/latest`
- Health check API: `http://<device-ip>:8080/api/health`

**Requirements:**

- reCamera 2002 Series
- SSH access to reCamera
- Internet access from the machine running deployment, so the prebuilt executable can be downloaded from Seeed solution assets

## Step 1: Deploy the binary to reCamera {#deploy_binary type=recamera_cpp required=true config=devices/recamera.yaml}

Download the prebuilt `qrcode_rec` executable, copy it to reCamera, stop default camera services, grant execute permission, and start the QR recognition program.

### Deployment Complete

When the program starts successfully, the device log should show:

```text
reCamera QR scanner is running
RTSP      : rtsp://<device-ip>:8554/live0
QR latest : http://<device-ip>:8080/api/qr/latest
Health    : http://<device-ip>:8080/api/health
[http] listening on 0.0.0.0:8080
```

### Troubleshooting

| Issue | Solution |
| --- | --- |
| SSH connection failed | Check the IP address, network connection, and SSH password. |
| Camera resource is busy | Stop Node-RED and sscma-node services, then run the program again. |
| Program exits immediately | Run `cat /tmp/qrcode_rec.log` on reCamera to inspect the runtime log. |

## Step 2: Preview QR recognition {#verify_rtsp type=video_stream required=true config=devices/rtsp_preview.yaml}

Open the preview in this app. Point the reCamera at a clear QR code; the live video should appear in the preview window, and the decoded text should be overlaid directly on the video.

Use this preview as the deployment check. No external player is required.

### Troubleshooting

| Issue | Solution |
| --- | --- |
| RTSP cannot be opened | Confirm the program is running and port `8554` is reachable. |
| Wrong stream path | Use `live0` as the RTSP path. |
| API cannot be accessed | Confirm the HTTP server is listening on port `8080`. |
| No QR code detected | Make sure the QR code is clear, large enough, and not blurred. |
