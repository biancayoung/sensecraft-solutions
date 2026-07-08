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

## Step 2: Verify the RTSP video stream {#verify_rtsp type=video_stream required=false config=devices/rtsp_preview.yaml}

Open the RTSP stream to verify that the camera video is available.

You can also verify manually from a PC:

```bash
ffplay rtsp://<device-ip>:8554/live0
```

### Troubleshooting

| Issue | Solution |
| --- | --- |
| RTSP cannot be opened | Confirm the program is running and port `8554` is reachable. |
| Wrong stream path | Use `live0` as the RTSP path. |

## Step 3: Verify the QR result API {#verify_qr_api type=http_debug required=false config=devices/qr_api.yaml}

Query the latest QR code recognition result.

Manual test command:

```bash
curl http://<device-ip>:8080/api/qr/latest
```

Example response:

```json
{
  "ok": true,
  "qr_found": true,
  "frame_id": 123,
  "detect_cost_ms": 35,
  "codes": [
    {
      "text": "https://www.seeedstudio.com"
    }
  ]
}
```

### Troubleshooting

| Issue | Solution |
| --- | --- |
| API cannot be accessed | Confirm the HTTP server is listening on port `8080`. |
| No QR code detected | Make sure the QR code is clear, large enough, and not blurred. |
