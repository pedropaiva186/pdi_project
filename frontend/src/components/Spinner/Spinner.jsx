import styles from './Spinner.module.css'

/** Indicador de carregamento circular (SVG inline, sem dependências). */
export default function Spinner({ size = 24, label }) {
  return (
    <span className={styles.wrapper} role={label ? 'status' : undefined} aria-label={label}>
      <svg
        className={styles.spinner}
        width={size}
        height={size}
        viewBox="0 0 24 24"
        aria-hidden="true"
        focusable="false"
      >
        <circle
          cx="12"
          cy="12"
          r="9"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray="42 14"
        />
      </svg>
      {label ? <span className="srOnly">{label}</span> : null}
    </span>
  )
}
