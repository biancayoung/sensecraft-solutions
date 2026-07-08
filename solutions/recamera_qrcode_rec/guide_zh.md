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
- 运行部署的电脑可以访问网络，用于从 Seeed solution assets 下载预编译可执行文件

## 步骤 1: 部署可执行文件到 reCamera {#deploy_binary type=recamera_cpp required=true config=devices/recamera.yaml}

下载已经编译好的 `qrcode_rec` 可执行文件，将它复制到 reCamera，停止默认摄像头服务，添加可执行权限，并启动二维码识别程序。

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

## 步骤 2: 预览二维码识别效果 {#verify_rtsp type=video_stream required=true config=devices/rtsp_preview.yaml}

在软件里打开预览窗口。把 reCamera 对准清晰二维码后，预览窗口应能直接显示实时画面，并把解码文本直接叠加在画面上。

这个预览就是部署验证，不需要再打开外部播放器。

### 故障排查

| 问题 | 解决方法 |
| --- | --- |
| RTSP 无法打开 | 确认程序正在运行，并且 `8554` 端口可以访问。 |
| 视频路径错误 | RTSP 路径使用 `live0`。 |
| API 无法访问 | 确认 HTTP 服务正在监听 `8080` 端口。 |
| 未识别到二维码 | 确认二维码清晰、足够大，并且没有明显模糊。 |
