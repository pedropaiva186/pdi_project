import HistogramChart from '../HistogramChart/HistogramChart.jsx'
import MetricsTable from './MetricsTable.jsx'
import styles from './AccessoryPanel.module.css'

/**
 * Dados acessórios do resultado: histogramas, imagens `aux` e métricas.
 * Cada seção só aparece quando tem conteúdo.
 */
export default function AccessoryPanel({ result, onImageClick }) {
  const histograms = result?.histograms ?? []
  const auxOutputs = (result?.outputs ?? []).filter((output) => output.role === 'aux')
  const metrics = result?.metrics ?? []
  const hasAccessories = histograms.length > 0 || auxOutputs.length > 0

  return (
    <section className={`panel ${styles.panel}`}>
      <header className="panelHeader">
        <h2 className="panelTitle">Dados / Imagens acessórias</h2>
      </header>

      <div className={styles.body}>
        {!result ? (
          <p className={styles.empty}>Os dados acessórios do processo aparecerão aqui.</p>
        ) : (
          <>
            {!hasAccessories ? (
              <p className={styles.empty}>Sem dados acessórios para este processo</p>
            ) : null}

            {histograms.length > 0 ? (
              <section>
                <h3 className={styles.sectionTitle}>Histogramas</h3>
                <div className={styles.histGrid}>
                  {histograms.map((histogram) => (
                    <figure key={histogram.id} className={styles.histCard}>
                      <figcaption className={styles.histLabel}>
                        {histogram.label}
                      </figcaption>
                      <HistogramChart
                        values={histogram.values}
                        channel={histogram.channel}
                        label={histogram.label}
                      />
                    </figure>
                  ))}
                </div>
              </section>
            ) : null}

            {auxOutputs.length > 0 ? (
              <section>
                <h3 className={styles.sectionTitle}>Imagens acessórias</h3>
                <div className={styles.auxGrid}>
                  {auxOutputs.map((output) => (
                    <figure key={output.id} className={styles.auxCard}>
                      <button
                        type="button"
                        className={`${styles.auxButton} checker`}
                        onClick={() => onImageClick(output)}
                        aria-label={`Ampliar ${output.label}`}
                      >
                        <img
                          className={styles.auxImage}
                          src={output.image}
                          alt={output.label}
                        />
                      </button>
                      <figcaption className={styles.auxLabel}>{output.label}</figcaption>
                    </figure>
                  ))}
                </div>
              </section>
            ) : null}

            {metrics.length > 0 ? (
              <section>
                <h3 className={styles.sectionTitle}>Métricas</h3>
                <MetricsTable metrics={metrics} />
              </section>
            ) : null}
          </>
        )}
      </div>
    </section>
  )
}
