## Preset: Voice Grasping on Jetson {#default}

Deploy a voice-controlled grasping arm: say **"Hey Jarvis, grab the water bottle"** and the reBot B601-DM finds the object with its wrist RGB-D camera and picks it up. One compose file runs the whole stack on the Jetson — wake word, streaming ASR, Qwen3-4B LLM, object detection, grasp planning, arm control and TTS reply. Fully local, no online API.

| Device | Purpose |
|--------|---------|
| reBot B601-DM | 6-DoF arm with parallel gripper (0.088 m max jaw) — USB serial |
| Orbbec Gemini 2 | wrist-mounted RGB-D camera (eye-in-hand) — USB 3.0 |
| reComputer Super J4012 | Jetson Orin NX 16GB — runs all four containers |
| reSpeaker USB mic + speaker | far-field voice in, TTS reply out |

**What you'll get:**
- Voice-commanded grasping of boxes, cups and standing (opaque) bottles — verified on real hardware
- Open-vocabulary detection (YOLOE): the object list is a model re-export away from extending, no retraining
- Live dashboard with the wrist-camera view and arm state (`:8776`)
- Cartesian observation API (`:8775/observation`) for integration with other solutions

**Before you start (hardware checklist):**
1. Arm powered on and connected — `ls /dev/ttyACM*` shows it (usually `/dev/ttyACM0`)
2. Gemini 2 on a **USB 3.0** port (blue connector — USB 2 starves the depth stream)
3. reSpeaker mic + speaker connected; note your desktop user's uid (`id -u`, usually `1000`)
4. Docker + NVIDIA runtime (standard on JetPack 6); ~10 GB free disk
5. Internet on first boot (~4 GB: container images + LLM engine + speech models + detector)

> **China networks**: set the *HuggingFace Endpoint* input to `https://hf-mirror.com` in Step 1 — the LLM engine, speech models and grasp detector all download through it.

## Step 1: Deploy the Stack {#rebot_stack type=docker_deploy required=true config=devices/rebot_stack.yaml}

Deploy the voice, LLM, arm-control and inventory services to the Jetson.

### Services

One compose file starts four services — `rebot-arm` (the agent), `seeed-voice` (ASR/TTS), `edge-llm` (Qwen3-4B TensorRT) and `warehouse` (MCP inventory) — plus a one-shot `model-init` that downloads the grasp detector into `/opt/rebot-models/`.

### Target {#rebot_stack_remote type=remote device=jetson device_name="Jetson" config=devices/rebot_stack.yaml default=true}

Deploy to a Jetson over SSH. Enter the Jetson IP address and SSH credentials, then set the arm serial device, audio user id and HuggingFace endpoint below.

### Target {#rebot_stack_local type=local device=jetson device_name="Jetson (Local)" config=devices/rebot_stack.yaml}

Deploy directly on the current machine. Use this only when the app or CLI is running on the Jetson itself.

Fill in:
- **Arm Serial Device** — from the checklist (default `/dev/ttyACM0`)
- **Host Audio User ID** — the `id -u` result (default `1000`)
- **HuggingFace Endpoint** — default outside China; `https://hf-mirror.com` inside

First boot takes several minutes: the LLM engine (~2 GB) downloads and warms up. `edge-llm` reports healthy only after its TensorRT warm-up completes (up to ~10 min on slow links — watch `docker logs edge-llm` if curious).

## Step 2: Open the Dashboard {#verify_dashboard type=web_dashboard verify=true required=true config=devices/verify_dashboard.yaml}

Open the dashboard and confirm the camera feed and arm state are healthy.

### What to check

Enter the same Jetson IP address used in Step 1 for remote deployment, or `localhost` for local deployment. The dashboard URL is `http://<jetson>:8776`.

- Camera frames are refreshing: perception is up
- State JSON is present: the serial link is up

Then the end-to-end voice test — say near the mic:

> **"Hey Jarvis, wave"**

The arm waves and the speaker confirms. Voice + LLM + arm control all work now. Grasping needs one more step: calibration.

### If something is off

| Symptom | Cause / fix |
|---|---|
| No camera image | Gemini 2 on a USB 2 port, or another process holds the camera — replug into USB 3.0, restart the `rebot-arm` container |
| No voice response | `docker logs voice-rebot-arm \| grep -i wake`; check the audio uid input matches `id -u` |
| `edge-llm` unhealthy for long | Engine still downloading/warming — normal on first boot |

## Step 3: Hand-Eye Calibration — unlocks grasping {#handeye type=manual required=false}

Finish hand-eye calibration before using grasp commands.

### Why calibration is needed

Grasping converts camera pixels into arm coordinates through a transform that is physically unique to your unit (how the camera sits on the wrist). Until `/opt/rebot-models/hand_eye.npz` exists, grasp commands detect objects but decline to move the arm. One-time, ~30 minutes:

1. Print an ArUco GridBoard (5×7, DICT_4X4_50) and **measure the printed marker size with a ruler** — printers rescale! A 1 mm error ≈ 1 cm grasp offset; this is the #1 calibration mistake.
2. Tape the board flat on the table ~65 cm in front of the arm base.
3. Follow the collection + solve procedure in the [repository RUNBOOK §3.2](https://github.com/suharvest/openvoicestream/blob/main/agent/ovs_agent/apps/voice_rebot_arm/RUNBOOK.md) — the arm sweeps ~16 poses over the board, then solves the transform (target mean error < 5 mm).
4. Copy the resulting `hand_eye.npz` to `/opt/rebot-models/` and restart the `rebot-arm` container.

### First grasp

Place a small cardboard box (each face under 8.5 cm) about 25–30 cm in front of the arm, roughly centered, and say:

> **"Hey Jarvis, grab the box"**

The arm scans, announces what it found, grasps, lifts and carries it home. Then try a cup, then an opaque bottle (standing).

**Known-good placements**: straight ahead or moderately left/right of center. **Use opaque objects** — transparent bottles are invisible to the depth camera (stereo-depth physics, not a bug).

### Troubleshooting

| Symptom | Cause / fix |
|---|---|
| "I couldn't find the …" occasionally | Detection confidence is marginal at some angles — repeat the command; move the object toward the center |
| "The box is too big for me to grip" | Every visible face exceeds the 0.088 m jaw — expected; use a smaller object or turn a narrow face toward the arm |
| First attempt fails, retry works | Known scan-pose IK flakiness — retry is the workaround |
| Grasp lands centimeters off | Recalibrate — and re-measure the printed marker size (step 1 above) |
| Arm joints fault (`status_code=12`) | Power-cycle the arm (torque toggle is not enough) |
