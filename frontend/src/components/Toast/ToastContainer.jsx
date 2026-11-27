import { useEffect } from 'react'
import styles from './Toast.module.css'

const DEFAULT_DURATION = 5000

function ToastItem({ toast, onDismiss }) {
  const duration = toast.duration ?? DEFAULT_DURATION

  useEffect(() => {
    const timer = window.setTimeout(() => onDismiss(toast.id), duration)
    return () => window.clearTimeout(timer)
  }, [toast.id, duration, onDismiss])

  return (
    <div
      className={`${styles.toast} ${styles[toast.kind] ?? styles.info}`}
      role={toast.kind === 'error' ? 'alert' : 'status'}
    >
      <span className={styles.message}>{toast.message}</span>
      <button
        type="button"
        className={styles.close}
        aria-label="Fechar notificação"
        onClick={() => onDismiss(toast.id)}
      >
        ✕
      </button>
    </div>
  )
}

/** Pilha de notificações no canto inferior direito. */
export default function ToastContainer({ toasts, onDismiss }) {
  if (!toasts.length) return null

  return (
    <div className={styles.container}>
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  )
}
