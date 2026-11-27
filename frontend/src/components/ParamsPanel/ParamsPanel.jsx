import { useMemo } from 'react'
import ParamField from './ParamField.jsx'
import { isVisible } from '../../utils/params.js'
import styles from './ParamsPanel.module.css'

function isMacPlatform() {
  if (typeof navigator === 'undefined') return false
  return /Mac|iPhone|iPad|iPod/.test(navigator.userAgent)
}

/** Formulário dinâmico do processo selecionado + Aplicar/Restaurar padrões. */
export default function ParamsPanel({
  process,
  values,
  constraints,
  canApply,
  onParamChange,
  onReset,
  onApply,
}) {
  const shortcut = useMemo(() => (isMacPlatform() ? '⌘+Enter' : 'Ctrl+Enter'), [])

  if (!process) {
    return (
      <section className={`panel ${styles.panel}`}>
        <header className="panelHeader">
          <h2 className="panelTitle">Parâmetros do processo</h2>
        </header>
        <div className={styles.empty}>Selecione um processo na barra lateral.</div>
      </section>
    )
  }

  const visibleFields = (process.params ?? []).filter((param) =>
    isVisible(param, values),
  )

  return (
    <section className={`panel ${styles.panel}`}>
      <header className={styles.header}>
        <div className={styles.heading}>
          <span className={styles.kicker}>Parâmetros do processo</span>
          <h2 className={styles.name}>
            {process.label}
            {process.implemented === false ? (
              <span className="badge badgeWarning">não implementado</span>
            ) : null}
          </h2>
          <p className={styles.description}>{process.description}</p>
        </div>
        <div className={styles.actions}>
          <button type="button" className="btn" onClick={onReset}>
            Restaurar padrões
          </button>
          <button
            type="button"
            className="btn btnPrimary"
            onClick={onApply}
            disabled={!canApply}
          >
            Aplicar ▶ <span className={styles.shortcut}>{shortcut}</span>
          </button>
        </div>
      </header>

      <div className={styles.body}>
        {visibleFields.length === 0 ? (
          <p className={styles.noParams}>Este processo não possui parâmetros.</p>
        ) : (
          <div className={styles.fields}>
            {visibleFields.map((param) => (
              <ParamField
                key={param.id}
                processId={process.id}
                param={param}
                value={values[param.id]}
                onChange={(value) => onParamChange(process.id, param.id, value)}
              />
            ))}
          </div>
        )}

        {constraints.length > 0 ? (
          <div className={styles.constraints} role="alert">
            {constraints.map((message) => (
              <p key={message}>{message}</p>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  )
}
