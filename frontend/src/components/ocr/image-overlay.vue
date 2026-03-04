<template>
  <div ref="containerRef" class="image-overlay" />
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as d3 from 'd3'
import type { OcrFieldResult } from '@/types/ocr.types'

const props = defineProps<{
  imageUrl: string | null
  results: OcrFieldResult[]
  hoveredFieldId: string | null
  fieldColors: Record<string, string>
}>()

const emit = defineEmits<{
  hover: [fieldId: string | null]
  select: [fieldId: string]
}>()

const containerRef = ref<HTMLDivElement | null>(null)

let svg: d3.Selection<SVGSVGElement, unknown, null, undefined> | null = null
let currentTransform = d3.zoomIdentity
let imgWidth = 0
let imgHeight = 0
let zoomBehavior: d3.ZoomBehavior<SVGSVGElement, unknown> | null = null
let bgImgEl: HTMLImageElement | null = null

function cleanup(): void {
  d3.select(containerRef.value).selectAll('svg').remove()
  if (bgImgEl) { bgImgEl.remove(); bgImgEl = null }
  svg = null
  zoomBehavior = null
  currentTransform = d3.zoomIdentity
  imgWidth = 0
  imgHeight = 0
}

async function initCanvas(imageUrl: string): Promise<void> {
  const container = containerRef.value
  if (!container) return

  cleanup()

  // Use a real HTML <img> element — works for cross-origin display without CORS headers
  bgImgEl = document.createElement('img')
  bgImgEl.style.cssText = 'position:absolute;top:0;left:0;transform-origin:0 0;display:block;'

  await new Promise<void>((resolve, reject) => {
    bgImgEl!.onerror = () => reject(new Error(`Failed to load image: ${imageUrl}`))
    bgImgEl!.onload  = () => {
      imgWidth  = bgImgEl!.naturalWidth  || bgImgEl!.width
      imgHeight = bgImgEl!.naturalHeight || bgImgEl!.height
      resolve()
    }
    bgImgEl!.src = imageUrl
  })

  container.appendChild(bgImgEl)

  // SVG layer sits on top: captures pointer events for zoom/pan, renders bbox overlays
  svg = d3.select(container)
    .append('svg')
    .attr('width', '100%')
    .attr('height', '100%')
    .style('position', 'absolute')
    .style('top', '0')
    .style('left', '0')

  const content = svg.append('g').attr('class', 'content')

  zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.05, 10])
    .wheelDelta((e: WheelEvent) => -e.deltaY * 0.001)
    .on('zoom', (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
      currentTransform = event.transform
      content.attr('transform', event.transform.toString())
      applyImgTransform(event.transform)
      renderOverlays()
    })

  svg.call(zoomBehavior)
  fitToContainer()
  renderOverlays()
}

// Sync <img> CSS transform with D3 zoom transform
function applyImgTransform(t: d3.ZoomTransform): void {
  if (!bgImgEl) return
  bgImgEl.style.transform = `translate(${t.x}px,${t.y}px) scale(${t.k})`
}

function fitToContainer(): void {
  const container = containerRef.value
  if (!container || !svg || !zoomBehavior || !imgWidth) return
  const rect = container.getBoundingClientRect()

  // Container may not be laid out yet — retry on next animation frame
  if (!rect.width || !rect.height) {
    requestAnimationFrame(fitToContainer)
    return
  }

  const pad   = 32
  const scale = Math.min((rect.width - pad) / imgWidth, (rect.height - pad) / imgHeight, 1)
  const tx    = (rect.width  - imgWidth  * scale) / 2
  const ty    = (rect.height - imgHeight * scale) / 2
  const t     = d3.zoomIdentity.translate(tx, ty).scale(scale)
  svg.call(zoomBehavior.transform, t)
  // zoom event will call applyImgTransform(t)
}

function getContent(): d3.Selection<SVGGElement, unknown, null, undefined> | null {
  if (!svg) return null
  const c = svg.select<SVGGElement>('g.content')
  return c.empty() ? null : c
}

function renderOverlays(): void {
  const content = getContent()
  if (!content) return

  content.selectAll('.ocr-overlays').remove()
  if (!props.results.length) return

  const t     = currentTransform
  const group = content.append('g').attr('class', 'ocr-overlays')

  for (const result of props.results) {
    const px       = result.bbox.x * imgWidth
    const py       = result.bbox.y * imgHeight
    const pw       = result.bbox.w * imgWidth
    const ph       = result.bbox.h * imgHeight
    const isHovered = result.fieldId === props.hoveredFieldId
    const color    = props.fieldColors[result.fieldId] ?? '#2196F3'

    group.append('rect')
      .attr('x', px).attr('y', py).attr('width', pw).attr('height', ph)
      .attr('fill', color)
      .attr('fill-opacity', isHovered ? 0.4 : 0.15)
      .attr('stroke', color)
      .attr('stroke-width', (isHovered ? 3 : 1.5) / t.k)
      .attr('cursor', 'pointer')
      .style('transition', 'fill-opacity 0.15s')
      .on('mouseenter', () => emit('hover', result.fieldId))
      .on('mouseleave', () => emit('hover', null))
      .on('click',      () => emit('select', result.fieldId))

    group.append('text')
      .attr('x', px + 4).attr('y', py - 4)
      .attr('fill', color)
      .attr('font-size', Math.max(10, 11 / t.k))
      .attr('font-weight', 'bold')
      .style('pointer-events', 'none')
      .text(result.fieldName)
  }
}

// onMounted guarantees containerRef.value is set (unlike immediate watch which fires before child DOM is ready)
onMounted(() => {
  if (props.imageUrl) {
    initCanvas(props.imageUrl).catch(e => console.error('[ImageOverlay] failed to load:', e))
  }
})

// Watch for imageUrl changes after mount (e.g. navigating between jobs)
watch(
  () => props.imageUrl,
  async (url) => {
    if (url) {
      try {
        await initCanvas(url)
      } catch (e) {
        console.error('[ImageOverlay] failed to load:', e)
      }
    }
  }
)

watch(
  () => [props.hoveredFieldId, props.results] as const,
  () => renderOverlays()
)

onUnmounted(cleanup)
</script>

<style scoped>
.image-overlay {
  position: relative;
  width: 100%;
  height: 100%;
  background: #1a1a2e;
  overflow: hidden;
}
</style>
