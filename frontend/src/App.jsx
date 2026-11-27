import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from 'react'
import {
  DISMISS_TOAST,
  PUSH_TOAST,
  RESET_PARAMS,
  RESTORE_ORIGINAL,
  SELECT_PROCESS,
  SET_ACTIVE_OUTPUT,
  SET_PARAM,
} from './state/actions.js'
import { appReducer, initialState } from './state/appReducer.js'
import { useCatalog } from './hooks/useCatalog.js'
import { useImageLoader } from './hooks/useImageLoader.js'
import { useProcessRunner } from './hooks/useProcessRunner.js'
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts.js'
import { checkConstraints, getDefaults } from './utils/params.js'
import { outputFilename } from './utils/format.js'
import { dataUrlToFile } from './utils/dataUrl.js'
import { downloadDataUrl } from './utils/download.js'
import FileMenu from './components/FileMenu/FileMenu.jsx'
import ProcessSidebar from './components/ProcessSidebar/ProcessSidebar.jsx'
import InputPanel from './components/InputPanel/InputPanel.jsx'
import OutputPanel from './components/OutputPanel/OutputPanel.jsx'
import ParamsPanel from './components/ParamsPanel/ParamsPanel.jsx'
import AccessoryPanel from './components/AccessoryPanel/AccessoryPanel.jsx'
import ImageModal from './components/ImageModal/ImageModal.jsx'
import ToastContainer from './components/Toast/ToastContainer.jsx'
import Spinner from './components/Spinner/Spinner.jsx'
import CatalogError from './components/CatalogError/CatalogError.jsx'
import styles from './App.module.css'

export default function App() {
  const [state, dispatch] = useReducer(appReducer, initialState)
  const { retry } = useCatalog(dispatch)
  const openFile = useImageLoader(dispatch)

  const [modalImage, setModalImage] = useState(null)
  const fileInputRef = useRef(null)
  const referencedUrls = useRef(new Set())

  const selectedProcess = useMemo(() => {
    if (!state.catalog || !state.selectedProcessId) return null
    return (
      state.catalog.processes.find(
        (process) => process.id === state.selectedProcessId,
      ) ?? null
    )
  }, [state.catalog, state.selectedProcessId])

  const paramValues = useMemo(() => {
    if (!selectedProcess) return {}
    return state.paramsByProcess[selectedProcess.id] ?? getDefaults(selectedProcess)
  }, [selectedProcess, state.paramsByProcess])

  const constraints = useMemo(
    () => (selectedProcess ? checkConstraints(selectedProcess, paramValues) : []),
    [selectedProcess, paramValues],
  )

  const modeAllowed = Boolean(
    selectedProcess &&
      state.input &&
      selectedProcess.modes.includes(state.input.mode),
  )
  const canApply = Boolean(
    state.input &&
      selectedProcess &&
      modeAllowed &&
      state.status === 'idle' &&
      constraints.length === 0,
  )

  const run = useProcessRunner({
    state,
    dispatch,
    process: selectedProcess,
    canApply,
  })

  const outputs = useMemo(() => state.result?.outputs ?? [], [state.result])
  const mainOutputs = useMemo(
    () => outputs.filter((output) => output.role === 'main'),
    [outputs],
  )
  const activeMainOutput = useMemo(
    () =>
      mainOutputs.find((output) => output.id === state.activeOutputId) ??
      mainOutputs[0] ??
      null,
    [mainOutputs, state.activeOutputId],
  )

  // Revoga object URLs que deixaram de ser referenciados por input/original.
  useEffect(() => {
    const current = new Set()
    if (state.input?.url) current.add(state.input.url)
    if (state.original?.url) current.add(state.original.url)

    for (const url of referencedUrls.current) {
      if (!current.has(url) && url.startsWith('blob:')) {
        URL.revokeObjectURL(url)
      }
    }
    referencedUrls.current = current
  }, [state.input, state.original])

  // Soltar um arquivo fora do painel de entrada não deve fazer o navegador
  // abri-lo (o que descartaria o estado). Só o InputPanel aceita o drop.
  useEffect(() => {
    function preventNavigation(event) {
      event.preventDefault()
    }

    window.addEventListener('dragover', preventNavigation)
    window.addEventListener('drop', preventNavigation)
    return () => {
      window.removeEventListener('dragover', preventNavigation)
      window.removeEventListener('drop', preventNavigation)
    }
  }, [])

  const handleSelectProcess = useCallback(
    (id) => dispatch({ type: SELECT_PROCESS, id }),
    [dispatch],
  )

  const handleParamChange = useCallback(
    (processId, paramId, value) =>
      dispatch({ type: SET_PARAM, processId, paramId, value }),
    [dispatch],
  )

  const handleResetParams = useCallback(() => {
    if (state.selectedProcessId) {
      dispatch({ type: RESET_PARAMS, processId: state.selectedProcessId })
    }
  }, [dispatch, state.selectedProcessId])

  const handleSelectOutput = useCallback(
    (id) => dispatch({ type: SET_ACTIVE_OUTPUT, id }),
    [dispatch],
  )

  const handleRestoreOriginal = useCallback(
    () => dispatch({ type: RESTORE_ORIGINAL }),
    [dispatch],
  )

  const handleDismissToast = useCallback(
    (id) => dispatch({ type: DISMISS_TOAST, id }),
    [dispatch],
  )

  const handleSaveOutput = useCallback(
    (output) => {
      if (!state.result || !output) return
      const filename = outputFilename(
        state.result.inputName,
        state.result.process_id,
        output.id,
      )
      downloadDataUrl(output.image, filename)
      dispatch({
        type: PUSH_TOAST,
        toast: { kind: 'success', message: `Imagem salva: ${filename}` },
      })
    },
    [state.result, dispatch],
  )

  const handleSaveActive = useCallback(() => {
    if (activeMainOutput) handleSaveOutput(activeMainOutput)
  }, [activeMainOutput, handleSaveOutput])

  const handleUseAsInput = useCallback(() => {
    if (!state.result || !activeMainOutput) return
    const filename = outputFilename(
      state.result.inputName,
      state.result.process_id,
      activeMainOutput.id,
    )
    const file = dataUrlToFile(activeMainOutput.image, filename)
    openFile(file, { asOriginal: false })
  }, [state.result, activeMainOutput, openFile])

  const openFilePicker = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileInputChange = useCallback(
    (event) => {
      const file = event.target.files?.[0]
      event.target.value = ''
      if (file) openFile(file, { asOriginal: true })
    },
    [openFile],
  )

  const handleDropFile = useCallback(
    (file) => openFile(file, { asOriginal: true }),
    [openFile],
  )

  const handleOpenInputModal = useCallback(() => {
    if (!state.input) return
    setModalImage({
      src: state.input.url,
      title: 'Imagem de entrada',
      width: state.input.width,
      height: state.input.height,
    })
  }, [state.input])

  const handleOpenOutputModal = useCallback(() => {
    if (!activeMainOutput) return
    setModalImage({
      src: activeMainOutput.image,
      title: activeMainOutput.label,
      width: activeMainOutput.width,
      height: activeMainOutput.height,
    })
  }, [activeMainOutput])

  const handleOpenAuxModal = useCallback((output) => {
    setModalImage({
      src: output.image,
      title: output.label,
      width: output.width,
      height: output.height,
    })
  }, [])

  const handleCloseModal = useCallback(() => setModalImage(null), [])

  useKeyboardShortcuts({
    onApply: run,
    onOpen: openFilePicker,
    onSave: handleSaveActive,
    onEscape: handleCloseModal,
    canApply,
    hasResult: Boolean(state.result),
  })

  if (state.catalogStatus === 'loading') {
    return (
      <div className="fullscreen">
        <Spinner size={40} label="Carregando catálogo" />
        <p className="muted">Carregando catálogo…</p>
      </div>
    )
  }

  if (state.catalogStatus === 'error') {
    return <CatalogError message={state.catalogError} onRetry={retry} />
  }

  return (
    <div className={styles.app}>
      <div className={styles.topbar}>
        <FileMenu
          input={state.input}
          original={state.original}
          result={state.result}
          outputs={outputs}
          activeOutput={activeMainOutput}
          onOpen={openFilePicker}
          onSaveActive={handleSaveActive}
          onSaveOutput={handleSaveOutput}
          onUseAsInput={handleUseAsInput}
          onRestoreOriginal={handleRestoreOriginal}
        />
      </div>

      <aside className={styles.sidebar}>
        <ProcessSidebar
          catalog={state.catalog}
          input={state.input}
          selectedProcessId={state.selectedProcessId}
          onSelect={handleSelectProcess}
        />
      </aside>

      <main className={styles.main}>
        <div className={styles.workspace}>
          <div className={styles.inputArea}>
            <InputPanel
              input={state.input}
              status={state.status}
              onOpen={openFilePicker}
              onFile={handleDropFile}
              onImageClick={handleOpenInputModal}
            />
          </div>

          <div className={styles.outputArea}>
            <OutputPanel
              result={state.result}
              activeOutputId={state.activeOutputId}
              onSelectOutput={handleSelectOutput}
              status={state.status}
              onImageClick={handleOpenOutputModal}
            />
          </div>

          <div className={styles.paramsArea}>
            <ParamsPanel
              process={selectedProcess}
              values={paramValues}
              constraints={constraints}
              canApply={canApply}
              onParamChange={handleParamChange}
              onReset={handleResetParams}
              onApply={run}
            />
          </div>

          <div className={styles.accessoryArea}>
            <AccessoryPanel result={state.result} onImageClick={handleOpenAuxModal} />
          </div>
        </div>
      </main>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,.png"
        hidden
        onChange={handleFileInputChange}
      />

      {modalImage ? <ImageModal image={modalImage} onClose={handleCloseModal} /> : null}

      <ToastContainer toasts={state.toasts} onDismiss={handleDismissToast} />
    </div>
  )
}
