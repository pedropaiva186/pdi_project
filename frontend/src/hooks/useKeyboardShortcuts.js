import { useEffect } from 'react'

/**
 * Registra os atalhos globais da aplicação.
 *
 * @param {object} options
 * @param {() => void} options.onApply
 * @param {() => void} options.onOpen
 * @param {() => void} options.onSave
 * @param {() => void} options.onEscape
 * @param {boolean} options.canApply
 * @param {boolean} options.hasResult
 */
export function useKeyboardShortcuts({ onApply, onOpen, onSave, onEscape, canApply, hasResult }) {
  useEffect(() => {
    function handleKeyDown(event) {
      const modifier = event.metaKey || event.ctrlKey

      if (modifier && event.key === 'Enter') {
        if (canApply) {
          event.preventDefault()
          onApply()
        }
        return
      }

      if (modifier && (event.key === 'o' || event.key === 'O')) {
        event.preventDefault()
        onOpen()
        return
      }

      if (modifier && (event.key === 's' || event.key === 'S')) {
        if (hasResult) {
          event.preventDefault()
          onSave()
        }
        return
      }

      if (event.key === 'Escape') {
        onEscape()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onApply, onOpen, onSave, onEscape, canApply, hasResult])
}
