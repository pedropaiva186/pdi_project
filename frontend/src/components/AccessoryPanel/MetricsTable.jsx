import { formatNumber } from '../../utils/format.js'
import styles from './AccessoryPanel.module.css'

/** Tabela de métricas (Métrica | Valor), com números em fonte mono. */
export default function MetricsTable({ metrics }) {
  return (
    <table className={styles.table}>
      <thead>
        <tr>
          <th scope="col">Métrica</th>
          <th scope="col">Valor</th>
        </tr>
      </thead>
      <tbody>
        {metrics.map((metric, index) => (
          <tr key={`${metric.label}-${index}`}>
            <td>{metric.label}</td>
            <td className={styles.metricValue}>
              {formatNumber(metric.value)}
              {metric.unit ? ` ${metric.unit}` : ''}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
