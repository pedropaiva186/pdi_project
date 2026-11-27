import { useEffect, useRef, useState } from 'react'
import styles from './FileMenu.module.css'

/**
 * Botão dividido: o clique principal salva a saída `main` ativa; a seta abre
 * o menu com todas as saídas (inclusive as `aux`).
 *
 * Teclado no menu: ao abrir, o foco vai para o primeiro item; ↑/↓ circulam,
 * Home/End vão para o início/fim; Enter/Espaço ativam o item; Esc fecha e
 * devolve o foco ao botão da seta.
 */
export default function SaveMenu({ outputs, activeOutput, onSaveActive, onSave }) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)
  const arrowRef = useRef(null)
  const itemRefs = useRef([])
  const hasOutputs = outputs.length > 0

  // Ao abrir, move o foco para o primeiro item do menu.
  useEffect(() => {
    if (open) itemRefs.current[0]?.focus()
  }, [open])

  useEffect(() => {
    if (!open) return undefined

    function handleMouseDown(event) {
      if (rootRef.current && !rootRef.current.contains(event.target)) {
        setOpen(false)
      }
    }

    function handleKeyDown(event) {
      const items = itemRefs.current.filter(Boolean)
      if (items.length === 0) return
      const currentIndex = items.indexOf(document.activeElement)

      if (event.key === 'Escape') {
        setOpen(false)
        arrowRef.current?.focus()
        return
      }

      let nextIndex = null
      if (event.key === 'ArrowDown') {
        nextIndex = (currentIndex + 1) % items.length
      } else if (event.key === 'ArrowUp') {
        nextIndex = (currentIndex - 1 + items.length) % items.length
      } else if (event.key === 'Home') {
        nextIndex = 0
      } else if (event.key === 'End') {
        nextIndex = items.length - 1
      }

      if (nextIndex !== null) {
        event.preventDefault()
        items[nextIndex].focus()
      }
    }

    document.addEventListener('mousedown', handleMouseDown)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('mousedown', handleMouseDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [open])

  function handleItem(output) {
    setOpen(false)
    onSave(output)
  }

  return (
    <div className={styles.saveGroup} ref={rootRef}>
      <button
        type="button"
        className={`btn ${styles.saveMain}`}
        onClick={onSaveActive}
        disabled={!activeOutput}
      >
        Salvar resultado
      </button>
      <button
        ref={arrowRef}
        type="button"
        className={`btn ${styles.saveArrow}`}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Mostrar todas as saídas para salvar"
        onClick={() => setOpen((value) => !value)}
        disabled={!hasOutputs}
      >
        ▾
      </button>

      {open ? (
        <div className={styles.menu} role="menu" aria-label="Saídas disponíveis">
          {outputs.map((output, index) => (
            <button
              key={output.id}
              ref={(node) => {
                itemRefs.current[index] = node
              }}
              type="button"
              role="menuitem"
              className={styles.menuItem}
              onClick={() => handleItem(output)}
            >
              <span className={styles.menuLabel}>{output.label}</span>
              <span className={styles.menuRole}>
                {output.role === 'main' ? 'principal' : 'acessória'}
              </span>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  )
}
