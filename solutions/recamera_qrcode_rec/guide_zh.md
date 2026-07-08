## 套餐: 原生可执行文件部署 {#default}

将已经编译好的 `qrcode_rec` 可执行文件部署到 reCamera。用户不需要在设备上编译源码。

| 设备 | 用途 |
| --- | --- |
| reCamera | 采集视频、输出 RTSP，并运行二维码识别 |

**部署完成后可以获得：**

- RTSP 视频流：`rtsp://<device-ip>:8554/live0`
- 最新二维码结果 API：`http://<device-ip>:8080/api/qr/latest`
- 健康检查 API：`http://<device-ip>:8080/api/health`

**准备条件：**

- reCamera 2002 系列
- 可以通过 SSH 访问 reCamera
- 已编译好的可执行文件：`assets/qrcode_rec`

## 步骤 1: 部署可执行文件到 reCamera {#deploy_binary type=recamera_cpp required=true config=devices/recamera.yaml}

将已经编译好的 `qrcode_rec` 可执行文件复制到 reCamera，停止默认摄像头服务，添加可执行权限，并启动二维码识别程序。

### 前置条件

部署前请确认可执行文件已经放在方案目录中：

```text
solutions/recamera_qrcode_rec/assets/qrcode_rec
```

### 部署完成

程序启动成功后，设备日志会显示类似内容：

```text
reCamera QR scanner is running
RTSP      : rtsp://<device-ip>:8554/live0
QR latest : http://<device-ip>:8080/api/qr/latest
Health    : http://<device-ip>:8080/api/health
[http] listening on 0.0.0.0:8080
```

### 故障排查

| 问题 | 解决方法 |
| --- | --- |
| SSH 连接失败 | 检查 IP 地址、网络连接和 SSH 密码。 |
| 摄像头资源被占用 | 停止 Node-RED 和 sscma-node 服务后重新运行。 |
| 程序立即退出 | 在 reCamera 上运行 `cat /tmp/qrcode_rec.log` 查看日志。 |

## 步骤 2: 验证 RTSP 视频流 {#verify_rtsp type=video_stream required=false config=devices/rtsp_preview.yaml}

打开 RTSP 视频流，确认摄像头画面可以正常显示。

也可以在 PC 上手动验证：

```bash
ffplay rtsp://<device-ip>:8554/live0
```

### 故障排查

| 问题 | 解决方法 |
| --- | --- |
| RTSP 无法打开 | 确认程序正在运行，并且 `8554` 端口可以访问。 |
| 视频路径错误 | RTSP 路径使用 `live0`。 |

## 步骤 3: 验证二维码结果 API {#verify_qr_api type=http_debug required=false config=devices/qr_api.yaml}

查询最新一次二维码识别结果。

手动测试命令：

```bash
curl http://<device-ip>:8080/api/qr/latest
```

示例返回：

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

### 故障排查

| 问题 | 解决方法 |
| --- | --- |
| API 无法访问 | 确认 HTTP 服务正在监听 `8080` 端口。 |
| 未识别到二维码 | 确认二维码清晰、足够大，并且没有明显模糊。 |
