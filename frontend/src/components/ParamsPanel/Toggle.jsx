import styles from './Toggle.module.css'

/** Interruptor acessível (`role="switch"`) com o estado em texto. */
export default function Toggle({ id, checked, onChange }) {
  return (
    <button
      type="button"
      id={id}
      role="switch"
      aria-checked={checked}
      className={`${styles.toggle} ${checked ? styles.on : ''}`}
      onClick={() => onChange(!checked)}
    >
      <span className={styles.track} aria-hidden="true">
        <span className={styles.knob} />
      </span>
      <span className={styles.text}>{checked ? 'Sim' : 'Não'}</span>
    </button>
  )
}
