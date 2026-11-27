import { useRef, useState } from 'react'
import ImagePanel from '../ImagePanel/ImagePanel.jsx'
import { dims, modeLabel } from '../../utils/format.js'
import styles from './InputPanel.module.css'

function EmptyState({ onOpen }) {
  return (
    <div className={styles.empty}>
      <svg
        className={styles.icon}
        width="48"
        height="48"
        viewBox="0 0 48 48"
        fill="none"
        aria-hidden="true"
        focusable="false"
      >
        <rect x="6" y="9" width="36" height="30" rx="3" stroke="currentColor" strokeWidth="2" />
        <circle cx="17" cy="20" r="4" stroke="currentColor" strokeWidth="2" />
        <path d="M9 35l10-10 7 7 5-5 8 8" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      </svg>
      <p>Arraste um PNG aqui ou</p>
      <button type="button" className="btn" onClick={onOpen}>
        Abrir PNG
      </button>
    </div>
  )
}

/**
 * Painel de entrada com arrastar e soltar. A validação do PNG acontece no
 * `useImageLoader` antes de qualquer chamada à API.
 */
export default function InputPanel({ input, status, onOpen, onFile, onImageClick }) {
  const [dragging, setDragging] = useState(false)
  const dragDepth = useRef(0)

  function handleDragEnter(event) {
    event.preventDefault()
    dragDepth.current += 1
    setDragging(true)
  }

  function handleDragOver(event) {
    event.preventDefault()
    if (event.dataTransfer) event.dataTransfer.dropEffect = 'copy'
    setDragging(true)
  }

  function handleDragLeave(event) {
    event.preventDefault()
    dragDepth.current -= 1
    if (dragDepth.current <= 0) {
      dragDepth.current = 0
      setDragging(false)
    }
  }

  function handleDrop(event) {
    event.preventDefault()
    dragDepth.current = 0
    setDragging(false)
    const file = event.dataTransfer?.files?.[0]
    if (file) onFile(file)
  }

  const badge = input ? `${modeLabel(input.mode)} · ${dims(input.width, input.height)}` : undefined

  return (
    <div
      className={`${styles.wrapper} ${dragging ? styles.dragging : ''}`}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <ImagePanel
        title="Imagem de entrada"
        src={input?.url}
        alt={input?.filename}
        badge={badge}
        emptyContent={<EmptyState onOpen={onOpen} />}
        loading={status === 'inspecting'}
        onImageClick={input ? onImageClick : undefined}
      />
      {dragging ? (
        <div className={styles.dropOverlay} aria-hidden="true">
          Solte o PNG aqui
        </div>
      ) : null}
    </div>
  )
}
