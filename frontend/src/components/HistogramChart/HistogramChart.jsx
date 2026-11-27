import { memo, useMemo, useState } from 'react'
import styles from './HistogramChart.module.css'

const WIDTH = 560
const HEIGHT = 220
const MARGIN = { top: 12, right: 12, bottom: 28, left: 44 }
const PLOT_WIDTH = WIDTH - MARGIN.left - MARGIN.right
const PLOT_HEIGHT = HEIGHT - MARGIN.top - MARGIN.bottom
const BAR_WIDTH = PLOT_WIDTH / 256
const X_TICKS = [0, 64, 128, 192, 255]

const CHANNEL_COLORS = {
  gray: 'var(--hist-gray)',
  r: 'var(--hist-r)',
  g: 'var(--hist-g)',
  b: 'var(--hist-b)',
}

const compactFormatter = new Intl.NumberFormat('pt-BR', { notation: 'compact' })
const plainFormatter = new Intl.NumberFormat('pt-BR')

function HistogramChart({ values, channel = 'gray', label }) {
  const [hovered, setHovered] = useState(null)

  const max = useMemo(
    () => values.reduce((acc, value) => Math.max(acc, Number(value) || 0), 0),
    [values],
  )

  const color = CHANNEL_COLORS[channel] ?? CHANNEL_COLORS.gray
  const plotBottom = MARGIN.top + PLOT_HEIGHT
  const hoveredValue = hovered == null ? 0 : Number(values[hovered]) || 0

  let tooltip = null
  if (hovered != null) {
    const centerX = MARGIN.left + hovered * BAR_WIDTH + BAR_WIDTH / 2
    const tooltipWidth = 160
    const x = Math.min(
      Math.max(centerX, MARGIN.left + tooltipWidth / 2),
      MARGIN.left + PLOT_WIDTH - tooltipWidth / 2,
    )
    tooltip = (
      <g pointerEvents="none">
        <rect
          x={x - tooltipWidth / 2}
          y={MARGIN.top + 2}
          width={tooltipWidth}
          height={22}
          rx={4}
          fill="var(--text)"
          opacity="0.92"
        />
        <text
          x={x}
          y={MARGIN.top + 17}
          textAnchor="middle"
          fontSize="11"
          fill="#ffffff"
        >
          Intensidade {hovered}: {plainFormatter.format(hoveredValue)} pixels
        </text>
      </g>
    )
  }

  return (
    <svg
      className={styles.chart}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      width="100%"
      role="img"
      aria-label={label ?? 'Histograma'}
    >
      <line
        x1={MARGIN.left}
        y1={MARGIN.top}
        x2={MARGIN.left + PLOT_WIDTH}
        y2={MARGIN.top}
        stroke="var(--border)"
        strokeDasharray="2 3"
      />
      <line
        x1={MARGIN.left}
        y1={plotBottom}
        x2={MARGIN.left + PLOT_WIDTH}
        y2={plotBottom}
        stroke="var(--border)"
      />
      <line
        x1={MARGIN.left}
        y1={MARGIN.top}
        x2={MARGIN.left}
        y2={plotBottom}
        stroke="var(--border)"
      />

      {values.map((value, index) => {
        const numeric = Number(value) || 0
        const height = max > 0 ? (numeric / max) * PLOT_HEIGHT : 0
        return (
          <rect
            key={`bar-${index}`}
            x={MARGIN.left + index * BAR_WIDTH}
            y={plotBottom - height}
            width={BAR_WIDTH}
            height={height}
            style={{ fill: color }}
          />
        )
      })}

      {values.map((_, index) => (
        <rect
          key={`hover-${index}`}
          x={MARGIN.left + index * BAR_WIDTH}
          y={MARGIN.top}
          width={BAR_WIDTH}
          height={PLOT_HEIGHT}
          fill="transparent"
          onMouseEnter={() => setHovered(index)}
          onMouseLeave={() => setHovered(null)}
        />
      ))}

      {hovered != null && max > 0 ? (
        <rect
          x={MARGIN.left + hovered * BAR_WIDTH}
          y={plotBottom - (hoveredValue / max) * PLOT_HEIGHT}
          width={BAR_WIDTH}
          height={(hoveredValue / max) * PLOT_HEIGHT}
          fill="none"
          stroke="var(--text)"
          strokeWidth="1"
          pointerEvents="none"
        />
      ) : null}

      {X_TICKS.map((tick) => {
        const x = MARGIN.left + (tick / 255) * PLOT_WIDTH
        const anchor = tick === 0 ? 'start' : tick === 255 ? 'end' : 'middle'
        return (
          <g key={tick}>
            <line
              x1={x}
              y1={plotBottom}
              x2={x}
              y2={plotBottom + 4}
              stroke="var(--border)"
            />
            <text
              x={x}
              y={plotBottom + 16}
              textAnchor={anchor}
              fontSize="10"
              fill="var(--text-2)"
            >
              {tick}
            </text>
          </g>
        )
      })}

      <text
        x={MARGIN.left - 6}
        y={plotBottom}
        textAnchor="end"
        dominantBaseline="middle"
        fontSize="10"
        fill="var(--text-2)"
      >
        0
      </text>
      <text
        x={MARGIN.left - 6}
        y={MARGIN.top}
        textAnchor="end"
        dominantBaseline="middle"
        fontSize="10"
        fill="var(--text-2)"
      >
        {compactFormatter.format(max)}
      </text>

      {tooltip}
    </svg>
  )
}

export default memo(HistogramChart)
