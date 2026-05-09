type SoundType = 'ping' | 'alert' | 'hum';

class SoundEngine {
  private ctx: AudioContext | null = null;
  private muted: boolean;
  private humNode: OscillatorNode | null = null;
  private humGain: GainNode | null = null;

  constructor(defaultMuted = false) {
    this.muted = defaultMuted;
  }

  private ensureCtx() {
    if (!this.ctx) {
      this.ctx = new AudioContext();
    }
    return this.ctx;
  }

  toggle(): boolean {
    this.muted = !this.muted;
    if (this.muted) this.stopHum();
    return this.muted;
  }

  isMuted(): boolean {
    return this.muted;
  }

  play(type: SoundType) {
    if (this.muted) return;
    const ctx = this.ensureCtx();

    switch (type) {
      case 'ping':
        this.playTone(ctx, 880, 'sine', 0.15, 0.3);
        break;
      case 'alert':
        this.playTone(ctx, 220, 'triangle', 0.25, 0.5);
        setTimeout(() => this.playTone(ctx, 185, 'triangle', 0.2, 0.3), 200);
        break;
      case 'hum':
        this.startHum(ctx);
        break;
    }
  }

  stopHum() {
    if (this.humNode) {
      this.humGain?.gain.exponentialRampToValueAtTime(0.001, (this.humNode.context.currentTime + 0.3));
      this.humNode.stop(this.humNode.context.currentTime + 0.3);
      this.humNode = null;
      this.humGain = null;
    }
  }

  private playTone(ctx: AudioContext, freq: number, type: OscillatorType, vol: number, dur: number) {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(vol, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
    osc.connect(gain).connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + dur);
  }

  private startHum(ctx: AudioContext) {
    if (this.humNode) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.value = 80;
    gain.gain.setValueAtTime(0.001, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.06, ctx.currentTime + 0.5);
    osc.connect(gain).connect(ctx.destination);
    osc.start();
    this.humNode = osc;
    this.humGain = gain;
  }
}

export default SoundEngine;
