import { USE_MOCK } from '../../api/index.js'
import { dims, modeLabel } from '../../utils/format.js'
import SaveMenu from './SaveMenu.jsx'
import styles from './FileMenu.module.css'

/** Barra superior: ações de arquivo e informações da imagem atual. */
export default function FileMenu({
  input,
  original,
  result,
  outputs,
  activeOutput,
  onOpen,
  onSaveActive,
  onSaveOutput,
  onUseAsInput,
  onRestoreOriginal,
}) {
  const restoreDisabled = !original || input === original

  return (
    <header className={styles.bar}>
      <div className={styles.actions}>
        <button type="button" className="btn" onClick={onOpen}>
          Abrir PNG
        </button>

        <SaveMenu
          outputs={outputs}
          activeOutput={activeOutput}
          onSaveActive={onSaveActive}
          onSave={onSaveOutput}
        />

        <button
          type="button"
          className="btn"
          onClick={onUseAsInput}
          disabled={!result}
        >
          Usar como entrada
        </button>

        <button
          type="button"
          className="btn"
          onClick={onRestoreOriginal}
          disabled={restoreDisabled}
        >
          Restaurar original
        </button>
      </div>

      <div className={styles.info}>
        {input ? (
          <span className={styles.imageInfo} title={input.filename}>
            <strong className={styles.filename}>{input.filename}</strong>
            <span aria-hidden="true"> · </span>
            {modeLabel(input.mode)}
            <span aria-hidden="true"> · </span>
            {dims(input.width, input.height)}
          </span>
        ) : (
          <span className={styles.imageInfo}>Nenhuma imagem carregada</span>
        )}
        {USE_MOCK ? <span className="badge badgeAccent">Modo simulado</span> : null}
      </div>
    </header>
  )
}
