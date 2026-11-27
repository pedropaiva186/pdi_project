import styles from './ProcessSidebar.module.css'

/** Motivo pelo qual um processo está desabilitado, ou `null` se habilitado. */
function disabledReason(process, input) {
  if (!input) return 'Abra uma imagem'
  if (process.modes.includes(input.mode)) return null
  if (process.modes.length === 1 && process.modes[0] === 'gray') {
    return 'Disponível apenas para imagens em escala de cinza'
  }
  if (process.modes.length === 1 && process.modes[0] === 'rgb') {
    return 'Disponível apenas para imagens coloridas (RGB)'
  }
  return 'Indisponível para o tipo da imagem atual'
}

/** Item de processo: `<button>` para funcionar também com teclado. */
export default function ProcessItem({ process, input, selected, onSelect }) {
  const reason = disabledReason(process, input)
  const disabled = Boolean(reason)

  const className = [
    styles.item,
    selected ? styles.selected : '',
    disabled ? styles.disabled : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <button
      type="button"
      className={className}
      aria-current={selected ? 'true' : undefined}
      aria-disabled={disabled ? 'true' : undefined}
      title={reason || undefined}
      onClick={() => {
        if (!disabled) onSelect(process.id)
      }}
    >
      <span className={styles.label}>{process.label}</span>
      {process.implemented === false ? (
        <span className={styles.notImplemented}>não implementado</span>
      ) : null}
    </button>
  )
}
