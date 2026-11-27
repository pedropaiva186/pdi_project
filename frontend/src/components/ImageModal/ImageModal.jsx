import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { dims } from '../../utils/format.js'
import styles from './ImageModal.module.css'

const FOCUSABLE_SELECTOR =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

/**
 * Visualização em tamanho real (padrão) com rolagem nos dois eixos e
 * alternância para "Ajustar à tela". Renderizado em portal no `body`.
 * O foco fica preso dentro do diálogo enquanto ele estiver aberto.
 */
export default function ImageModal({ image, onClose }) {
  const [fit, setFit] = useState(false)
  const closeRef = useRef(null)
  const dialogRef = useRef(null)

  function handleDialogKeyDown(event) {
    if (event.key !== 'Tab' || !dialogRef.current) return

    const focusable = Array.from(dialogRef.current.querySelectorAll(FOCUSABLE_SELECTOR))
    if (focusable.length === 0) {
      event.preventDefault()
      return
    }

    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    const active = document.activeElement
    const outside = !dialogRef.current.contains(active)

    if (event.shiftKey) {
      if (active === first || outside) {
        event.preventDefault()
        last.focus()
      }
    } else if (active === last || outside) {
      event.preventDefault()
      first.focus()
    }
  }

  useEffect(() => {
    const previous = document.activeElement
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    closeRef.current?.focus()

    return () => {
      document.body.style.overflow = previousOverflow
      if (previous instanceof HTMLElement) previous.focus()
    }
  }, [])

  if (!image) return null

  return createPortal(
    <div
      className={styles.overlay}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <div
        ref={dialogRef}
        className={styles.dialog}
        role="dialog"
        aria-modal="true"
        aria-label={image.title}
        onClick={(event) => event.stopPropagation()}
        onKeyDown={handleDialogKeyDown}
      >
        <header className={styles.header}>
          <div className={styles.heading}>
            <h2 className={styles.title}>{image.title}</h2>
            <span className={styles.dims}>{dims(image.width, image.height)}</span>
          </div>
          <div className={styles.actions}>
            <button type="button" className="btn" onClick={() => setFit((value) => !value)}>
              {fit ? 'Tamanho real' : 'Ajustar à tela'}
            </button>
            <button ref={closeRef} type="button" className="btn" onClick={onClose}>
              Fechar ✕
            </button>
          </div>
        </header>

        <div className={`${styles.body} ${fit ? styles.fit : styles.actual} checker`}>
          <img
            className={fit ? styles.fitImage : styles.actualImage}
            src={image.src}
            alt={image.title}
          />
        </div>
      </div>
    </div>,
    document.body,
  )
}
