import { useRef } from 'react'
import ImagePanel from '../ImagePanel/ImagePanel.jsx'
import { dims, modeLabel } from '../../utils/format.js'
import styles from './OutputPanel.module.css'

function OutputTabs({ outputs, activeId, onSelect }) {
  const tabRefs = useRef([])

  function handleKeyDown(event) {
    if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return
    const index = outputs.findIndex((output) => output.id === activeId)
    if (index === -1) return

    event.preventDefault()
    const direction = event.key === 'ArrowRight' ? 1 : -1
    const next = (index + direction + outputs.length) % outputs.length
    onSelect(outputs[next].id)
    tabRefs.current[next]?.focus()
  }

  return (
    <div
      className={styles.tablist}
      role="tablist"
      aria-label="Saídas principais"
      onKeyDown={handleKeyDown}
    >
      {outputs.map((output, index) => {
        const selected = output.id === activeId
        return (
          <button
            key={output.id}
            ref={(node) => {
              tabRefs.current[index] = node
            }}
            type="button"
            role="tab"
            aria-selected={selected}
            tabIndex={selected ? 0 : -1}
            className={`${styles.tab} ${selected ? styles.tabActive : ''}`}
            onClick={() => onSelect(output.id)}
          >
            {output.label}
          </button>
        )
      })}
    </div>
  )
}

/**
 * Painel de saída. Exibe abas quando há mais de uma saída `main` e mantém o
 * resultado anterior visível sob a sobreposição de carregamento.
 */
export default function OutputPanel({ result, activeOutputId, onSelectOutput, status, onImageClick }) {
  const mainOutputs = (result?.outputs ?? []).filter((output) => output.role === 'main')
  const active =
    mainOutputs.find((output) => output.id === activeOutputId) ?? mainOutputs[0] ?? null

  const tabs =
    mainOutputs.length > 1 ? (
      <OutputTabs
        outputs={mainOutputs}
        activeId={active?.id}
        onSelect={onSelectOutput}
      />
    ) : null

  const badge = active
    ? `${modeLabel(active.mode)} · ${dims(active.width, active.height)}`
    : undefined

  return (
    <ImagePanel
      title="Imagem de saída"
      src={active?.image}
      alt={active?.label}
      badge={badge}
      headerExtra={tabs}
      loading={status === 'processing'}
      onImageClick={active ? onImageClick : undefined}
      emptyContent={
        <p>Selecione um processo e clique em Aplicar para ver o resultado.</p>
      }
    />
  )
}
