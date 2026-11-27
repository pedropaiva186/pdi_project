import { useState } from 'react'
import ProcessItem from './ProcessItem.jsx'
import styles from './ProcessSidebar.module.css'

/** Barra lateral com categorias recolhíveis (todas abertas por padrão). */
export default function ProcessSidebar({ catalog, input, selectedProcessId, onSelect }) {
  const [collapsed, setCollapsed] = useState({})

  function toggleCategory(id) {
    setCollapsed((previous) => ({ ...previous, [id]: !previous[id] }))
  }

  const categories = catalog?.categories ?? []
  const processes = catalog?.processes ?? []

  return (
    <nav className={styles.sidebar} aria-label="Processos">
      <h2 className={styles.title}>Processos</h2>
      <div className={styles.list}>
        {categories.map((category) => {
          const open = !collapsed[category.id]
          const categoryProcesses = processes.filter(
            (process) => process.category === category.id,
          )
          return (
            <section key={category.id} className={styles.category}>
              <button
                type="button"
                className={styles.categoryButton}
                aria-expanded={open}
                aria-controls={`category-${category.id}`}
                onClick={() => toggleCategory(category.id)}
              >
                <span className={styles.chevron} aria-hidden="true">
                  {open ? '▾' : '▸'}
                </span>
                {category.label}
              </button>
              {open ? (
                <div id={`category-${category.id}`} className={styles.items}>
                  {categoryProcesses.map((process) => (
                    <ProcessItem
                      key={process.id}
                      process={process}
                      input={input}
                      selected={process.id === selectedProcessId}
                      onSelect={onSelect}
                    />
                  ))}
                </div>
              ) : null}
            </section>
          )
        })}
      </div>
    </nav>
  )
}
