# Catálogo de Processos

A fonte de verdade é [`shared/processes.json`](../../shared/processes.json). O frontend usa esse arquivo para montar a lista de processos e os formulários; o backend usa para validar os parâmetros. **Mudou um parâmetro? Altere o JSON** e os dois lados se ajustam.

## Formato do catálogo

```jsonc
{
  "version": 1,
  "categories": [{ "id": "spatial", "label": "Filtros espaciais" }],
  "processes": [{
    "id": "gaussian_blur",          // usado na rota /api/process/{id} e no registry Python
    "label": "Filtro de média gaussiana",
    "category": "spatial",          // referencia categories[].id
    "description": "…",             // texto curto mostrado na interface (tooltip/painel)
    "modes": ["gray", "rgb"],       // modos aceitos; os outros deixam o processo DESABILITADO
    "params": [ /* ParamSpec */ ],
    "constraints": [ /* opcional */ ]
  }]
}
```

**ParamSpec**

| Campo | Tipos | Descrição |
|---|---|---|
| `id` | todos | Chave enviada em `params` |
| `label` | todos | Rótulo na interface |
| `type` | — | `int` \| `float` \| `bool` \| `select` |
| `default` | todos | Valor inicial e de "Restaurar padrões" |
| `min`, `max`, `step` | `int`, `float` | Limites (inclusivos) e passo do controle |
| `odd` | `int` | `true` → só aceita ímpares (tamanhos de janela) |
| `options` | `select` | `[{ "value", "label" }]` |
| `visible_if` | todos | `{ "param", "equals" }` → só aparece (e só é enviado) quando a condição é verdadeira |
| `help` | todos | Texto de ajuda (ícone ⓘ / tooltip) |

**Constraint** (entre parâmetros): `{ "rule": "less_equal", "params": ["a", "b"], "message": "…" }`. Hoje só existe a regra `less_equal`. O frontend avisa antes de enviar e o backend valida (`422`).

## Resumo dos processos

| ID | Processo | Modos | Parâmetros | Saídas `main` | Saídas `aux` / histogramas |
|---|---|---|---|---|---|
| `rgb_split` | Decomposição RGB | rgb | — | `r`, `g`, `b` (cinza) | — |
| `hsv_split` | Decomposição HSV | rgb | — | `h`, `s`, `v` (cinza) | — |
| `threshold` | Limiarização | gray, rgb | `k` | `result` | — |
| `log_transform` | Logarítmica | gray, rgb | `c` | `result` | — |
| `power_transform` | Potência | gray, rgb | `c`, `gamma` | `result` | — |
| `histogram_equalization` | Equalização | gray | — | `equalized` | **histogramas `before` e `after`** |
| `intensity_slicing` | Fatiamento | gray, rgb | `a`, `b`, `preserve_background` | `result` | — |
| `gaussian_blur` | Média gaussiana | gray, rgb | `kernel_size`, `sigma` | `result` | — |
| `median_filter` | Mediana | gray, rgb | `kernel_size` | `result` | — |
| `min_filter` | Mínimo | gray, rgb | `kernel_size` | `result` | — |
| `max_filter` | Máximo | gray, rgb | `kernel_size` | `result` | — |
| `unsharp_mask` | Máscara de aguçamento | gray, rgb | `kernel_size`, `gain` | `result` | — |
| `laplacian_sharpen` | Realce por Laplaciano | gray, rgb | `kernel_size` | `result` | **`laplacian` (Laplaciano ajustado)** |
| `sobel` | Gradiente de Sobel | gray, rgb | `kernel_size` | `magnitude` | — |
| `adaptive_median` | Mediana adaptativa | gray, rgb | `max_window` | `result` | — |
| `gaussian_frequency_filter` | Gaussiano PB/PA | gray, rgb | `filter_type`, `cutoff` | `result` | — |
| `butterworth_filter` | Butterworth PB/PA | gray, rgb | `filter_type`, `cutoff`, `order` | `result` | — |
| `gaussian_noise` | Ruído gaussiano | gray, rgb | `intensity`, `distribution` | `result` | — |
| `salt_pepper_noise` | Sal / pimenta | gray, rgb | `noise_type`, `salt_probability`*, `pepper_probability`* | `result` | — |

\* Só aparecem quando `noise_type = salt_and_pepper`. O PDF pede parâmetro de distribuição apenas nesse caso. Para sal ou pimenta isolados, a densidade é um valor fixo definido no handler.

## Critério de aderência ao PDF

O catálogo segue **estritamente** o que está no PDF: nenhum parâmetro, saída ou restrição além do que ele pede, e nada a menos.

- **Habilitação por modo:** o PDF manda desabilitar as operações "não relevantes" e dá como exemplo a equalização de histograma em imagens coloridas. Por isso:
  - a **equalização** fica só em `gray`;
  - a **decomposição RGB/HSV** fica só em `rgb`, porque exige uma imagem colorida;
  - **todo o resto** fica habilitado nos dois modos. Em RGB, a forma de aplicar (por canal, por exemplo) fica a cargo de quem implementar.
- **Saídas:** as únicas exigências extras do PDF são os **histogramas antes e depois** (equalização), as **três imagens de canal** (RGB/HSV) e o **Laplaciano ajustado** (realce por Laplaciano). Os outros processos têm uma única saída `main`.
- **Tamanho de janela:** o PDF pede `kernel_size` em todos os filtros espaciais. No filtro adaptativo, o parâmetro do PDF é o tamanho máximo da janela (`max_window`).
- **Ruído gaussiano:** os parâmetros são exatamente "intensidade" e "distribuição", conforme o PDF. Na implementação: intensidade = σ, distribuição = μ.
- **Fatiamento:** apenas a faixa [A, B] e preservar/zerar o fundo. O valor de destaque (255) é fixo no handler.
- Faixas e valores default (`min`, `max`, `default`) são só valores iniciais dos controles e podem ser ajustados no JSON.
