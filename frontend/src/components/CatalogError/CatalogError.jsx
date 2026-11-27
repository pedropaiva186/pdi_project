import styles from './CatalogError.module.css'

/** Tela cheia exibida quando o catálogo não pôde ser carregado. */
export default function CatalogError({ message, onRetry }) {
  return (
    <div className={styles.screen}>
      <div className={styles.card}>
        <h1 className={styles.title}>Não foi possível carregar o catálogo</h1>
        <p className={styles.message}>
          {message || 'Verifique se o backend está rodando e tente novamente.'}
        </p>
        <button type="button" className="btn btnPrimary" onClick={onRetry}>
          Tentar novamente
        </button>
      </div>
    </div>
  )
}
