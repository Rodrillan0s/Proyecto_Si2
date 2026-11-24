import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { ChartSpec } from '../../services/reportes.service';

interface ChartDatum {
  label: string;
  value: number;
  color: string;
  percent: number;
}

const PALETTE = ['#d97706', '#2563eb', '#059669', '#7c3aed', '#e11d48', '#0891b2', '#ea580c', '#4f46e5'];

@Component({
  selector: 'app-chart-spec-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div *ngIf="shouldRender" class="chart-card" [class.compact]="compact">
      <div class="chart-header">
        <span class="chart-eyebrow">VISUALIZACIÓN</span>
        <h4>{{ spec?.titulo || 'Resumen gráfico' }}</h4>
      </div>

      <!-- KPI -->
      <div *ngIf="spec?.tipo === 'kpi'" class="kpi-grid">
        <div *ngFor="let item of kpiItems" class="kpi-tile">
          <span class="kpi-label">{{ item.label }}</span>
          <strong class="kpi-value">{{ item.value }}</strong>
        </div>
      </div>

      <!-- BAR / STACKED_BAR -->
      <div *ngIf="spec?.tipo === 'bar' || spec?.tipo === 'stacked_bar'" class="bar-list">
        <div *ngFor="let item of dataPoints" class="bar-row">
          <div class="bar-meta">
            <span class="bar-label" [title]="item.label">{{ item.label }}</span>
            <strong class="bar-val">{{ formatNumber(item.value) }}</strong>
          </div>
          <div class="bar-track">
            <div class="bar-fill" [style.width.%]="item.percent" [style.background]="item.color"></div>
          </div>
        </div>
        <p *ngIf="extraCount > 0" class="chart-note">Mostrando los primeros {{ dataPoints.length }} registros (+{{ extraCount }} adicionales en tabla).</p>
      </div>

      <!-- LINE -->
      <div *ngIf="spec?.tipo === 'line' && linePoints.length >= 2" class="line-wrap">
        <svg viewBox="0 0 360 140" class="line-svg" role="img" [attr.aria-label]="spec?.titulo || 'Gráfico de tendencia'">
          <line x1="24" y1="20" x2="344" y2="20" class="grid-line" />
          <line x1="24" y1="70" x2="344" y2="70" class="grid-line" />
          <line x1="24" y1="120" x2="344" y2="120" class="grid-line" />
          <polyline [attr.points]="linePolyline" fill="none" stroke="#d97706" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" />
          <circle *ngFor="let pt of linePoints" [attr.cx]="pt.x" [attr.cy]="pt.y" r="3.5" fill="#d97706">
            <title>{{ pt.label }}: {{ formatNumber(pt.value) }}</title>
          </circle>
        </svg>
        <div class="line-axis">
          <span>{{ linePoints[0].label }}</span>
          <span>Máx: {{ formatNumber(maxValue) }}</span>
          <span>{{ linePoints[linePoints.length - 1].label }}</span>
        </div>
      </div>

      <!-- PIE / DONUT -->
      <div *ngIf="spec?.tipo === 'pie' && dataPoints.length" class="pie-wrap">
        <svg viewBox="0 0 120 120" class="pie-svg" role="img" [attr.aria-label]="spec?.titulo || 'Distribución'">
          <circle cx="60" cy="60" r="44" fill="none" stroke="rgba(148,163,184,0.2)" stroke-width="18" />
          <circle
            *ngFor="let seg of pieSegments"
            cx="60"
            cy="60"
            r="44"
            fill="none"
            [attr.stroke]="seg.color"
            stroke-width="18"
            [attr.stroke-dasharray]="seg.dashArray"
            [attr.stroke-dashoffset]="seg.dashOffset"
            transform="rotate(-90 60 60)"
          >
            <title>{{ seg.label }}: {{ formatNumber(seg.value) }} ({{ seg.share }}%)</title>
          </circle>
        </svg>
        <div class="pie-legend">
          <div *ngFor="let seg of pieSegments" class="legend-item">
            <span class="legend-dot" [style.background]="seg.color"></span>
            <span class="legend-label">{{ seg.label }}</span>
            <strong class="legend-val">{{ seg.share }}%</strong>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .chart-card {
      margin: 12px 0;
      padding: 14px 16px;
      border-radius: 12px;
      border: 1px solid var(--ob-border, #e2e8f0);
      background: var(--ob-surface, #ffffff);
    }
    .chart-card.compact {
      margin: 8px 0;
      padding: 10px 12px;
    }
    .chart-header {
      margin-bottom: 10px;
    }
    .chart-eyebrow {
      display: block;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.08em;
      color: var(--ob-primary, #d97706);
    }
    .chart-header h4 {
      margin: 2px 0 0;
      font-size: 13.5px;
      font-weight: 700;
      color: var(--ob-text, #0f172a);
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
      gap: 8px;
    }
    .kpi-tile {
      padding: 8px 10px;
      border-radius: 8px;
      background: var(--ob-surface-2, #f8fafc);
      border: 1px solid var(--ob-border, #e2e8f0);
    }
    .kpi-label {
      display: block;
      font-size: 10.5px;
      text-transform: uppercase;
      color: var(--ob-muted, #64748b);
    }
    .kpi-value {
      font-size: 14px;
      color: var(--ob-text, #0f172a);
    }
    .bar-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .bar-meta {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      font-size: 12px;
      margin-bottom: 3px;
    }
    .bar-label {
      color: var(--ob-text, #0f172a);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .bar-val {
      color: var(--ob-text, #0f172a);
      white-space: nowrap;
    }
    .bar-track {
      height: 8px;
      border-radius: 999px;
      background: rgba(148, 163, 184, 0.22);
      overflow: hidden;
    }
    .bar-fill {
      height: 100%;
      border-radius: 999px;
      min-width: 4px;
      transition: width 0.25s ease;
    }
    .chart-note {
      margin: 4px 0 0;
      font-size: 11px;
      color: var(--ob-muted, #64748b);
    }
    .line-svg {
      width: 100%;
      height: 120px;
      display: block;
    }
    .grid-line {
      stroke: rgba(148, 163, 184, 0.28);
      stroke-dasharray: 3 3;
      stroke-width: 1;
    }
    .line-axis {
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: var(--ob-muted, #64748b);
      margin-top: 4px;
    }
    .pie-wrap {
      display: flex;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
    }
    .pie-svg {
      width: 108px;
      height: 108px;
      flex-shrink: 0;
    }
    .pie-legend {
      flex: 1;
      min-width: 140px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .legend-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
    }
    .legend-dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    .legend-label {
      flex: 1;
      color: var(--ob-text, #0f172a);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .legend-val {
      color: var(--ob-text, #0f172a);
    }
  `],
})
export class ChartSpecCardComponent {
  @Input() spec?: ChartSpec | null;
  @Input() rows: Record<string, unknown>[] = [];
  @Input() resumen?: Record<string, unknown> | null;
  @Input() compact = false;

  get shouldRender(): boolean {
    if (!this.spec || !this.spec.tipo || this.spec.tipo === 'none') return false;
    if (this.spec.tipo === 'kpi') return this.kpiItems.length > 0;
    if (this.spec.tipo === 'line') return this.linePoints.length >= 2;
    return this.dataPoints.length > 0;
  }

  get extraCount(): number {
    return Math.max(0, (this.rows?.length || 0) - 10);
  }

  get kpiItems(): { label: string; value: string }[] {
    const source = this.resumen && Object.keys(this.resumen).length
      ? this.resumen
      : (this.rows?.[0] || {});
    return Object.entries(source)
      .slice(0, 6)
      .map(([k, v]) => ({
        label: k.replaceAll('_', ' '),
        value: typeof v === 'number' ? this.formatNumber(v) : String(v ?? '—'),
      }));
  }

  private resolveMetricField(): string | null {
    const firstSeries = this.spec?.series?.[0];
    if (firstSeries?.campo) return firstSeries.campo;
    if (firstSeries?.field) return firstSeries.field;
    const sample = this.rows?.[0];
    if (!sample) return null;
    for (const [k, v] of Object.entries(sample)) {
      if (k === this.spec?.eje_x) continue;
      if (typeof v === 'number' || (typeof v === 'string' && v.trim() !== '' && !Number.isNaN(Number(v)))) {
        return k;
      }
    }
    return null;
  }

  private resolveLabelField(): string | null {
    if (this.spec?.eje_x) return this.spec.eje_x;
    const sample = this.rows?.[0];
    return sample ? Object.keys(sample)[0] ?? null : null;
  }

  get dataPoints(): ChartDatum[] {
    const labelKey = this.resolveLabelField();
    const metricKey = this.resolveMetricField();
    if (!labelKey || !metricKey || !this.rows?.length) return [];
    const sliced = this.rows.slice(0, 10).map((row, idx) => {
      const raw = row[metricKey];
      const num = typeof raw === 'number' ? raw : Number(raw ?? 0);
      return {
        label: String(row[labelKey] ?? `#${idx + 1}`),
        value: Number.isFinite(num) ? num : 0,
        color: PALETTE[idx % PALETTE.length],
      };
    });
    const maxAbs = Math.max(...sliced.map((d) => Math.abs(d.value)), 1);
    return sliced.map((d) => ({
      ...d,
      percent: Math.min(100, Math.max(2, (Math.abs(d.value) / maxAbs) * 100)),
    }));
  }

  get maxValue(): number {
    const vals = this.dataPoints.map((d) => d.value);
    return vals.length ? Math.max(...vals) : 0;
  }

  get linePoints(): { x: number; y: number; label: string; value: number }[] {
    const pts = this.dataPoints;
    if (pts.length < 2) return [];
    const min = Math.min(...pts.map((p) => p.value));
    const max = Math.max(...pts.map((p) => p.value));
    const span = max - min || 1;
    const stepX = 320 / (pts.length - 1);
    return pts.map((p, i) => ({
      x: Math.round(24 + i * stepX),
      y: Math.round(118 - ((p.value - min) / span) * 96),
      label: p.label,
      value: p.value,
    }));
  }

  get linePolyline(): string {
    return this.linePoints.map((p) => `${p.x},${p.y}`).join(' ');
  }

  get pieSegments(): { label: string; value: number; color: string; share: string; dashArray: string; dashOffset: number }[] {
    const pts = this.dataPoints.filter((d) => d.value > 0);
    const total = pts.reduce((acc, d) => acc + d.value, 0);
    if (!total) return [];
    const circ = 2 * Math.PI * 44;
    let offset = 0;
    return pts.map((d) => {
      const ratio = d.value / total;
      const len = ratio * circ;
      const seg = {
        label: d.label,
        value: d.value,
        color: d.color,
        share: (ratio * 100).toFixed(1),
        dashArray: `${len.toFixed(2)} ${(circ - len).toFixed(2)}`,
        dashOffset: -offset,
      };
      offset += len;
      return seg;
    });
  }

  formatNumber(val: number): string {
    return new Intl.NumberFormat('es-BO', { maximumFractionDigits: 2 }).format(val);
  }
}
