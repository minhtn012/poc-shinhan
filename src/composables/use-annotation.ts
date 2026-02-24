/**
 * useAnnotation composable
 * Combines D3 canvas management (from use-d3-canvas reference) with
 * rectangle drawing, selection, move, resize, and NormalizedBBox conversion.
 */
import { ref, shallowRef, onUnmounted, type Ref } from 'vue'
import * as d3 from 'd3'
import type { TemplateField, NormalizedBBox } from '@/types/template.types'
import { renderFields } from '@/lib/render-fields'

const MIN_RECT_PX = 8

const FIELD_COLORS = [
  '#2196F3', '#4CAF50', '#FF9800', '#E91E63',
  '#9C27B0', '#00BCD4', '#FF5722', '#607D8B'
]

function nextColor(existingCount: number): string {
  return FIELD_COLORS[existingCount % FIELD_COLORS.length] ?? '#2196F3'
}

export function useAnnotation(
  containerRef: Ref<HTMLDivElement | null>,
  options: { initialFields?: TemplateField[]; readonly?: boolean } = {}
) {
  // ---- D3 state ----
  const svg = shallowRef<d3.Selection<SVGSVGElement, unknown, null, undefined> | null>(null)
  const currentTransform = ref<d3.ZoomTransform>(d3.zoomIdentity)
  const imgWidth = ref(0)
  const imgHeight = ref(0)
  let zoomBehavior: d3.ZoomBehavior<SVGSVGElement, unknown> | null = null

  // ---- Drawing state ----
  const isDrawing = ref(false)
  const drawStart = ref<{ x: number; y: number } | null>(null)
  const drawCurrent = ref<{ x: number; y: number } | null>(null)

  // ---- Field data ----
  const fields = ref<TemplateField[]>(options.initialFields ? [...options.initialFields] : [])
  const selectedFieldId = ref<string | null>(null)

  // ---- Canvas init (adapted from use-d3-canvas) ----
  async function initCanvas(imageUrl: string): Promise<void> {
    const container = containerRef.value
    if (!container) return

    d3.select(container).selectAll('*').remove()
    currentTransform.value = d3.zoomIdentity

    svg.value = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .style('cursor', 'crosshair')

    return new Promise(resolve => {
      const img = new Image()
      img.onload = () => {
        imgWidth.value = img.width
        imgHeight.value = img.height

        const content = svg.value!.append('g').attr('class', 'content')
        content.append('image')
          .attr('href', imageUrl)
          .attr('width', img.width)
          .attr('height', img.height)

        zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
          .filter((event: Event) => {
            // Scroll wheel = zoom; middle-mouse drag = pan; left-click reserved for drawing
            if ((event as WheelEvent).type === 'wheel') return true
            return (event as MouseEvent).button === 1
          })
          .scaleExtent([0.05, 10])
          .wheelDelta((event: WheelEvent) => -event.deltaY * 0.001)
          .on('zoom', (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
            currentTransform.value = event.transform
            content.attr('transform', event.transform.toString())
          })

        svg.value!.call(zoomBehavior)
        fitToContainer()
        if (!options.readonly) {
          wireSvgEvents()
        } else {
          svg.value!.style('cursor', 'default')
        }
        render()
        resolve()
      }
      img.src = imageUrl
    })
  }

  function fitToContainer(): void {
    const container = containerRef.value
    if (!container || !svg.value || !zoomBehavior || !imgWidth.value) return
    const rect = container.getBoundingClientRect()
    const padding = 40
    const scaleX = (rect.width - padding) / imgWidth.value
    const scaleY = (rect.height - padding) / imgHeight.value
    const scale = Math.min(scaleX, scaleY, 1)
    const tx = (rect.width - imgWidth.value * scale) / 2
    const ty = (rect.height - imgHeight.value * scale) / 2
    const t = d3.zoomIdentity.translate(tx, ty).scale(scale)
    svg.value.call(zoomBehavior.transform, t)
  }

  function getContent(): d3.Selection<SVGGElement, unknown, null, undefined> | null {
    if (!svg.value) return null
    const c = svg.value.select<SVGGElement>('g.content')
    return c.empty() ? null : c
  }

  // ---- Render ----
  function render(): void {
    const content = getContent()
    if (!content) return

    // Clear previous overlays only
    content.selectAll('.field-overlay').remove()

    const preview = buildDrawPreview()

    renderFields(
      {
        content,
        transform: currentTransform.value,
        imgWidth: imgWidth.value,
        imgHeight: imgHeight.value
      },
      fields.value,
      selectedFieldId.value,
      preview,
      {
        onSelect: selectField,
        onMove: moveField,
        onResize: resizeField
      },
      svg.value?.node() ?? null
    )
  }

  function buildDrawPreview(): { x: number; y: number; w: number; h: number } | null {
    if (!isDrawing.value || !drawStart.value || !drawCurrent.value) return null
    const s = drawStart.value
    const c = drawCurrent.value
    return {
      x: Math.min(s.x, c.x),
      y: Math.min(s.y, c.y),
      w: Math.abs(c.x - s.x),
      h: Math.abs(c.y - s.y)
    }
  }

  // ---- SVG event wiring ----
  function wireSvgEvents(): void {
    if (!svg.value) return

    svg.value
      .on('mousedown.draw', (event: MouseEvent) => {
        // Only start drawing when clicking on background (not on a field rect)
        const target = event.target as SVGElement
        const isFieldEl = target.closest?.('[data-field-id]') || target.getAttribute('data-field-id')
        if (isFieldEl) return
        if (event.button !== 0) return

        const [sx, sy] = d3.pointer(event)
        const [ix, iy] = currentTransform.value.invert([sx, sy])
        startDraw(ix, iy)
      })
      .on('mousemove.draw', (event: MouseEvent) => {
        if (!isDrawing.value) return
        const [sx, sy] = d3.pointer(event)
        const [ix, iy] = currentTransform.value.invert([sx, sy])
        updateDraw(ix, iy)
        render()
      })
      .on('mouseup.draw', () => {
        if (isDrawing.value) finishDraw()
      })
      .on('click.deselect', (event: MouseEvent) => {
        // Deselect when clicking on bare SVG/image
        const target = event.target as SVGElement
        const isFieldEl = target.closest?.('[data-field-id]') || target.getAttribute('data-field-id')
        if (!isFieldEl) {
          selectedFieldId.value = null
          render()
        }
      })
  }

  // ---- Draw state machine ----
  function startDraw(x: number, y: number): void {
    isDrawing.value = true
    drawStart.value = { x, y }
    drawCurrent.value = { x, y }
  }

  function updateDraw(x: number, y: number): void {
    if (!isDrawing.value) return
    drawCurrent.value = { x, y }
  }

  function finishDraw(): TemplateField | null {
    if (!isDrawing.value || !drawStart.value || !drawCurrent.value) {
      cancelDraw()
      return null
    }

    const s = drawStart.value
    const c = drawCurrent.value
    const w = Math.abs(c.x - s.x)
    const h = Math.abs(c.y - s.y)

    if (w < MIN_RECT_PX || h < MIN_RECT_PX) {
      cancelDraw()
      return null
    }

    const bbox: NormalizedBBox = {
      x: Math.min(s.x, c.x) / imgWidth.value,
      y: Math.min(s.y, c.y) / imgHeight.value,
      w: w / imgWidth.value,
      h: h / imgHeight.value
    }

    const field: TemplateField = {
      id: crypto.randomUUID(),
      name: `Field ${fields.value.length + 1}`,
      color: nextColor(fields.value.length),
      bbox
    }

    fields.value = [...fields.value, field]
    selectedFieldId.value = field.id
    cancelDraw()
    render()
    return field
  }

  function cancelDraw(): void {
    isDrawing.value = false
    drawStart.value = null
    drawCurrent.value = null
  }

  // ---- Field operations ----
  function selectField(id: string): void {
    selectedFieldId.value = id
    render()
  }

  function deleteField(id: string): void {
    fields.value = fields.value.filter(f => f.id !== id)
    if (selectedFieldId.value === id) selectedFieldId.value = null
    render()
  }

  function updateFieldName(id: string, name: string): void {
    fields.value = fields.value.map(f => f.id === id ? { ...f, name } : f)
    render()
  }

  function moveField(id: string, dx: number, dy: number): void {
    fields.value = fields.value.map(f => {
      if (f.id !== id) return f
      const newX = Math.max(0, Math.min(1 - f.bbox.w, f.bbox.x + dx / imgWidth.value))
      const newY = Math.max(0, Math.min(1 - f.bbox.h, f.bbox.y + dy / imgHeight.value))
      return { ...f, bbox: { ...f.bbox, x: newX, y: newY } }
    })
    render()
  }

  function resizeField(id: string, handleIndex: number, imgX: number, imgY: number): void {
    fields.value = fields.value.map(f => {
      if (f.id !== id) return f
      const px = f.bbox.x * imgWidth.value
      const py = f.bbox.y * imgHeight.value
      const pr = px + f.bbox.w * imgWidth.value
      const pb = py + f.bbox.h * imgHeight.value

      let [l, t, r, b] = [px, py, pr, pb]

      // 0:TL, 1:TR, 2:BR, 3:BL, 4:top, 5:right, 6:bottom, 7:left
      switch (handleIndex) {
        case 0: l = imgX; t = imgY; break
        case 1: r = imgX; t = imgY; break
        case 2: r = imgX; b = imgY; break
        case 3: l = imgX; b = imgY; break
        case 4: t = imgY; break
        case 5: r = imgX; break
        case 6: b = imgY; break
        case 7: l = imgX; break
      }

      const newL = Math.max(0, Math.min(l, r))
      const newT = Math.max(0, Math.min(t, b))
      const newR = Math.min(imgWidth.value, Math.max(l, r))
      const newB = Math.min(imgHeight.value, Math.max(t, b))

      if (newR - newL < MIN_RECT_PX || newB - newT < MIN_RECT_PX) return f

      return {
        ...f,
        bbox: {
          x: newL / imgWidth.value,
          y: newT / imgHeight.value,
          w: (newR - newL) / imgWidth.value,
          h: (newB - newT) / imgHeight.value
        }
      }
    })
    render()
  }

  function getSvgNode(): SVGSVGElement | null {
    return svg.value?.node() ?? null
  }

  function destroy(): void {
    if (svg.value) {
      svg.value.on('mousedown.draw', null)
      svg.value.on('mousemove.draw', null)
      svg.value.on('mouseup.draw', null)
      svg.value.on('click.deselect', null)
    }
    zoomBehavior = null
  }

  onUnmounted(destroy)

  return {
    fields,
    selectedFieldId,
    isDrawing,
    imgWidth,
    imgHeight,
    initCanvas,
    fitToContainer,
    getSvgNode,
    render,
    selectField,
    deleteField,
    updateFieldName,
    moveField,
    resizeField
  }
}

export type AnnotationReturn = ReturnType<typeof useAnnotation>
