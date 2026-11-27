import { useEffect, useState } from 'react'
import Toggle from './Toggle.jsx'
import SegmentedControl from './SegmentedControl.jsx'
import { decimalsOf, normalizeValue } from '../../utils/params.js'
import styles from './ParamField.module.css'

function formatValue(param, value) {
  if (param.type === 'float') {
    return Number(value).toFixed(decimalsOf(param.step))
  }
  return String(value)
}

/**
 * Campo de parâmetro:
 * - `int`/`float`: slider + campo numérico sincronizados (commit no blur/Enter);
 * - `bool`: switch "Sim/Não";
 * - `select`: botões segmentados (≤ 3 opções) ou `<select>`.
 */
export default function ParamField({ processId, param, value, onChange }) {
  const id = `param-${processId}-${param.id}`
  const labelId = `${id}-label`
  const [text, setText] = useState(() => formatValue(param, value))
  const [helpOpen, setHelpOpen] = useState(false)

  useEffect(() => {
    setText(formatValue(param, value))
  }, [param, value])

  function commit() {
    const raw = text.trim()
    const parsed = Number(raw)
    if (raw === '' || Number.isNaN(parsed)) {
      setText(formatValue(param, value))
      return
    }
    const next = normalizeValue(param, parsed)
    onChange(next)
    setText(formatValue(param, next))
  }

  const options = param.options ?? []
  const useSegmented = param.type === 'select' && options.length <= 3

  let label
  if (useSegmented) {
    label = (
      <span id={labelId} className={styles.label}>
        {param.label}
      </span>
    )
  } else {
    label = (
      <label htmlFor={id} className={styles.label}>
        {param.label}
      </label>
    )
  }

  let control
  if (param.type === 'bool') {
    control = <Toggle id={id} checked={Boolean(value)} onChange={onChange} />
  } else if (param.type === 'select') {
    control = useSegmented ? (
      <SegmentedControl
        id={id}
        labelledBy={labelId}
        options={options}
        value={value}
        onChange={(next) => onChange(normalizeValue(param, next))}
      />
    ) : (
      <select
        id={id}
        className={styles.select}
        value={value}
        onChange={(event) => onChange(normalizeValue(param, event.target.value))}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    )
  } else {
    control = (
      <div className={styles.sliderRow}>
        <input
          type="range"
          id={`${id}-range`}
          className={styles.range}
          aria-label={param.label}
          min={param.min}
          max={param.max}
          step={param.step}
          value={Number(value)}
          onChange={(event) => onChange(normalizeValue(param, event.target.value))}
        />
        <input
          type="number"
          id={id}
          className={styles.numberInput}
          inputMode={param.type === 'float' ? 'decimal' : 'numeric'}
          min={param.min}
          max={param.max}
          step={param.step}
          value={text}
          onChange={(event) => setText(event.target.value)}
          onBlur={commit}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault()
              commit()
            }
          }}
        />
      </div>
    )
  }

  return (
    <div className={styles.field}>
      <div className={styles.labelRow}>
        {label}
        {param.help ? (
          <span
            className={styles.helpWrap}
            onMouseEnter={() => setHelpOpen(true)}
            onMouseLeave={() => setHelpOpen(false)}
          >
            <button
              type="button"
              className={styles.helpButton}
              title={param.help}
              aria-label={`Ajuda: ${param.help}`}
              onFocus={() => setHelpOpen(true)}
              onBlur={() => setHelpOpen(false)}
              onClick={() => setHelpOpen((open) => !open)}
            >
              ⓘ
            </button>
            {helpOpen ? (
              <span role="tooltip" className={styles.popover}>
                {param.help}
              </span>
            ) : null}
          </span>
        ) : null}
      </div>

      {control}

      {param.type === 'int' || param.type === 'float' ? (
        <div className={styles.bounds} aria-hidden="true">
          <span>{param.min}</span>
          <span>{param.max}</span>
        </div>
      ) : null}
    </div>
  )
}
