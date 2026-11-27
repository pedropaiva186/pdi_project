import styles from './SegmentedControl.module.css'

/** Grupo de botões com semântica de `radiogroup` (para selects curtos). */
export default function SegmentedControl({ id, labelledBy, options, value, onChange }) {
  return (
    <div id={id} className={styles.group} role="radiogroup" aria-labelledby={labelledBy}>
      {options.map((option) => {
        const checked = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={checked}
            className={`${styles.option} ${checked ? styles.checked : ''}`}
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
