import Spinner from '../Spinner/Spinner.jsx'
import styles from './ImagePanel.module.css'

/**
 * Painel genérico de imagem: título, selo, conteúdo vazio, imagem clicável e
 * sobreposição de carregamento.
 */
export default function ImagePanel({
  title,
  src,
  alt,
  badge,
  emptyContent,
  loading,
  onImageClick,
  headerExtra,
}) {
  let content
  if (src) {
    const image = <img className={styles.image} src={src} alt={alt || title} />
    content = onImageClick ? (
      <button
        type="button"
        className={styles.imageButton}
        onClick={onImageClick}
        aria-label={`Ampliar ${alt || title}`}
      >
        {image}
      </button>
    ) : (
      image
    )
  } else {
    content = <div className={styles.empty}>{emptyContent}</div>
  }

  return (
    <section className={`panel ${styles.panel}`}>
      <header className="panelHeader">
        <div className={styles.headerLeft}>
          <h2 className="panelTitle">{title}</h2>
          {headerExtra}
        </div>
        {badge ? <span className="badge">{badge}</span> : null}
      </header>
      <div className={`${styles.body} checker`}>
        {content}
        {loading ? (
          <div className={styles.overlay}>
            <Spinner size={28} />
            <span>Processando…</span>
          </div>
        ) : null}
      </div>
    </section>
  )
}
