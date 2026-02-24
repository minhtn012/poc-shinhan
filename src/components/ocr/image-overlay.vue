<template>
  <div ref="containerRef" class="image-overlay" />
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
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

async function initCanvas(imageUrl: string): Promise<void> {
  const container = containerRef.value
  if (!container) return

  d3.select(container).selectAll('*').remove()
  currentTransform = d3.zoomIdentity

  svg = d3.select(container)
    .append('svg')
    .attr('width', '100%')
    .attr('height', '100%')

  return new Promise(resolve => {
    const img = new Image()
    img.onload = () => {
      imgWidth = img.width
      imgHeight = img.height

      const content = svg!.append('g').attr('class', 'content')
      content.append('image')
        .attr('href', imageUrl)
        .attr('width', img.width)
        .attr('height', img.height)

      zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.05, 10])
        .wheelDelta((e: WheelEvent) => -e.deltaY * 0.001)
        .on('zoom', (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
          currentTransform = event.transform
          content.attr('transform', event.transform.toString())
          renderOverlays()
        })

      svg!.call(zoomBehavior)
      fitToContainer()
      renderOverlays()
      resolve()
    }
    img.src = imageUrl
  })
}

function fitToContainer(): void {
  const container = containerRef.value
  if (!container || !svg || !zoomBehavior || !imgWidth) return
  const rect = container.getBoundingClientRect()
  const pad = 32
  const scale = Math.min((rect.width - pad) / imgWidth, (rect.height - pad) / imgHeight, 1)
  const tx = (rect.width - imgWidth * scale) / 2
  const ty = (rect.height - imgHeight * scale) / 2
  const t = d3.zoomIdentity.translate(tx, ty).scale(scale)
  svg.call(zoomBehavior.transform, t)
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

  const t = currentTransform
  const group = content.append('g').attr('class', 'ocr-overlays')

  for (const result of props.results) {
    const px = result.bbox.x * imgWidth
    const py = result.bbox.y * imgHeight
    const pw = result.bbox.w * imgWidth
    const ph = result.bbox.h * imgHeight
    const isHovered = result.fieldId === props.hoveredFieldId
    const color = props.fieldColors[result.fieldId] ?? '#2196F3'

    group.append('rect')
      .attr('x', px)
      .attr('y', py)
      .attr('width', pw)
      .attr('height', ph)
      .attr('fill', color)
      .attr('fill-opacity', isHovered ? 0.4 : 0.15)
      .attr('stroke', color)
      .attr('stroke-width', (isHovered ? 3 : 1.5) / t.k)
      .attr('cursor', 'pointer')
      .style('transition', 'fill-opacity 0.15s')
      .on('mouseenter', () => emit('hover', result.fieldId))
      .on('mouseleave', () => emit('hover', null))
      .on('click', () => emit('select', result.fieldId))

    // Field name label above rect
    group.append('text')
      .attr('x', px + 4)
      .attr('y', py - 4)
      .attr('fill', color)
      .attr('font-size', Math.max(10, 11 / t.k))
      .attr('font-weight', 'bold')
      .style('pointer-events', 'none')
      .text(result.fieldName)
  }
}

// Re-render overlays when hover state or results change
watch(
  () => [props.hoveredFieldId, props.results] as const,
  () => renderOverlays()
)

// Reinit canvas when imageUrl changes
watch(
  () => props.imageUrl,
  async (url) => {
    if (url) await initCanvas(url)
  },
  { immediate: true }
)

onUnmounted(() => {
  zoomBehavior = null
})
</script>

<style scoped>
.image-overlay {
  width: 100%;
  height: 100%;
  background: #1a1a2e;
  overflow: hidden;
}
</style>
