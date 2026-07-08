/**
 * QR code recognition overlay.
 *
 * Input data comes from GET /api/qr/latest:
 * {
 *   ok: true,
 *   qr_found: true,
 *   frame_id: 123,
 *   detect_cost_ms: 35,
 *   codes: [{ text: "https://www.seeedstudio.com" }]
 * }
 */

const found = Boolean(data && data.qr_found);
const codes = Array.isArray(data?.codes) ? data.codes : [];
const texts = codes
  .map((item) => String(item?.text || '').trim())
  .filter(Boolean);

const title = found ? 'QR code detected' : 'No QR code';
const lines = texts.length > 0
  ? texts.slice(0, 3)
  : ['Point reCamera at a clear QR code'];

const panelX = 14;
const panelY = 14;
const panelW = Math.min(canvas.width - 28, 520);
const lineH = 22;
const panelH = 58 + lines.length * lineH;
const radius = 10;

if (typeof ctx.roundRect !== 'function') {
  ctx.roundRect = function(x, y, w, h, r) {
    this.beginPath();
    this.moveTo(x + r, y);
    this.arcTo(x + w, y, x + w, y + h, r);
    this.arcTo(x + w, y + h, x, y + h, r);
    this.arcTo(x, y + h, x, y, r);
    this.arcTo(x, y, x + w, y, r);
    this.closePath();
  };
}

ctx.save();
ctx.fillStyle = found ? 'rgba(20, 83, 45, 0.88)' : 'rgba(17, 24, 39, 0.82)';
ctx.strokeStyle = found ? 'rgba(134, 239, 172, 0.95)' : 'rgba(209, 213, 219, 0.6)';
ctx.lineWidth = 1.5;
ctx.beginPath();
ctx.roundRect(panelX, panelY, panelW, panelH, radius);
ctx.fill();
ctx.stroke();

ctx.fillStyle = '#FFFFFF';
ctx.font = 'bold 18px Inter, Arial, sans-serif';
ctx.fillText(title, panelX + 16, panelY + 28);

ctx.font = '12px Inter, Arial, sans-serif';
ctx.fillStyle = found ? '#BBF7D0' : '#D1D5DB';
const meta = data?.frame_id != null
  ? `Frame ${data.frame_id}${data?.detect_cost_ms != null ? ` · ${data.detect_cost_ms} ms` : ''}`
  : 'Waiting for recognition result';
ctx.fillText(meta, panelX + 16, panelY + 48);

ctx.font = 'bold 15px Inter, Arial, sans-serif';
ctx.fillStyle = '#FFFFFF';
lines.forEach((line, idx) => {
  const y = panelY + 76 + idx * lineH;
  const maxChars = Math.max(20, Math.floor((panelW - 32) / 8));
  const text = line.length > maxChars ? `${line.slice(0, maxChars - 1)}...` : line;
  ctx.fillText(text, panelX + 16, y);
});
ctx.restore();
