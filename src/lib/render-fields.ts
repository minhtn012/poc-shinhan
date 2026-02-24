/**
 * D3 renderer for template field rectangles.
 * Adapted from render-rectangles.ts — simplified for OCR use case:
 * no rotation, no erase mode, uses NormalizedBBox instead of polygon points.
 */
import * as d3 from 'd3'
import type { NormalizedBBox } from '@/types/template.types'

export interface FieldRect {
  id: string
  name: string
  color: string
  bbox: NormalizedBBox // 0-1 normalized
}

export interface RenderContext {
  content: d3.Selection<SVGGElement, unknown, null, undefined>
  transform: d3.ZoomTransform
  imgWidth: number
  imgHeight: number
}

export interface FieldCallbacks {
  onSelect: (id: string) => void
  onMove: (id: string, dx: number, dy: number) => void
  onResize: (id: string, handleIndex: number, x: number, y: number) => void
}

export interface DrawPreview {
  x: number
  y: number
  w: number
  h: number
}

export function renderFields(
  ctx: RenderContext,
  fields: FieldRect[],
  selectedId: string | null,
  drawPreview: DrawPreview | null,
  callbacks: FieldCallbacks,
  svgNode: SVGSVGElement | null
): void {
  const { content, transform, imgWidth, imgHeight } = ctx
  const group = content.append('g').attr('class', 'field-overlay')

  for (const field of fields) {
    // Denormalize bbox to pixel coords
    const px = field.bbox.x * imgWidth
    const py = field.bbox.y * imgHeight
    const pw = field.bbox.w * imgWidth
    const ph = field.bbox.h * imgHeight
    const cx = px + pw / 2
    const cy = py + ph / 2

    const isSelected = field.id === selectedId
    const color = field.color

    const fieldGroup = group.append('g')
      .attr('class', 'field-rect')
      .attr('data-field-id', field.id)

    // Rectangle body
    const rect = fieldGroup.append('rect')
      .attr('x', px)
      .attr('y', py)
      .attr('width', pw)
      .attr('height', ph)
      .attr('fill', color)
      .attr('fill-opacity', 0.18)
      .attr('stroke', isSelected ? '#fff' : color)
      .attr('stroke-width', (isSelected ? 3 : 2) / transform.k)
      .attr('cursor', 'move')
      .on('click', (event: MouseEvent) => {
        event.stopPropagation()
        callbacks.onSelect(field.id)
      })

    if (isSelected) {
      rect
        .attr('stroke-dasharray', `${6 / transform.k},${3 / transform.k}`)
    }

    // Label at center
    const label = field.name || field.id.slice(0, 6)
    const tw = Math.max(40, label.length * 6 + 12)
    fieldGroup.append('rect')
      .attr('x', cx - tw / 2)
      .attr('y', cy - 9)
      .attr('width', tw)
      .attr('height', 18)
      .attr('rx', 3)
      .attr('fill', color)
      .attr('fill-opacity', 0.85)
      .style('pointer-events', 'none')

    fieldGroup.append('text')
      .attr('x', cx)
      .attr('y', cy + 5)
      .attr('fill', '#fff')
      .attr('font-size', Math.max(10, 11 / transform.k))
      .attr('text-anchor', 'middle')
      .style('pointer-events', 'none')
      .style('user-select', 'none')
      .text(label)

    // Drag-to-move on selected rect body.
    // Container = svgNode (stable, not moving) so event.dx/dy stays in SVG viewport coords.
    // Updating fieldGroup's translate mid-drag would shift parentNode's coordinate space,
    // causing D3's delta calc to drift → jitter if we used the default parentNode container.
    if (isSelected && svgNode) {
      let totalDx = 0
      let totalDy = 0
      const dragMove = d3.drag<SVGRectElement, unknown>()
        .container(() => svgNode)
        .on('start', () => { totalDx = 0; totalDy = 0 })
        .on('drag', (event: d3.D3DragEvent<SVGRectElement, unknown, unknown>) => {
          // event.dx/dy in SVG viewport (screen) coords → divide by k for image coords
          totalDx += event.dx / transform.k
          totalDy += event.dy / transform.k
          fieldGroup.attr('transform', `translate(${totalDx},${totalDy})`)
        })
        .on('end', () => {
          fieldGroup.attr('transform', null)
          callbacks.onMove(field.id, totalDx, totalDy)
        })
      fieldGroup.select<SVGRectElement>('rect').call(dragMove)
    }

    // Resize handles for selected rect
    if (isSelected && svgNode) {
      // 8 handles: 4 corners (0-3) + 4 edge midpoints (4-7)
      const handles = [
        { x: px, y: py },           // 0: TL corner
        { x: px + pw, y: py },      // 1: TR corner
        { x: px + pw, y: py + ph }, // 2: BR corner
        { x: px, y: py + ph },      // 3: BL corner
        { x: cx, y: py },           // 4: top edge
        { x: px + pw, y: cy },      // 5: right edge
        { x: cx, y: py + ph },      // 6: bottom edge
        { x: px, y: cy }            // 7: left edge
      ]

      const cursors = [
        'nw-resize', 'ne-resize', 'se-resize', 'sw-resize',
        'n-resize', 'e-resize', 's-resize', 'w-resize'
      ]

      handles.forEach((h, idx) => {
        const handle = fieldGroup.append('rect')
          .attr('x', h.x - 4 / transform.k)
          .attr('y', h.y - 4 / transform.k)
          .attr('width', 8 / transform.k)
          .attr('height', 8 / transform.k)
          .attr('fill', '#fff')
          .attr('stroke', color)
          .attr('stroke-width', 1.5 / transform.k)
          .attr('cursor', cursors[idx] ?? 'pointer')

        const dragResize = d3.drag<SVGRectElement, unknown>()
          .on('drag', (event: d3.D3DragEvent<SVGRectElement, unknown, unknown>) => {
            // Use d3.pointer relative to SVG root (not offsetX/Y which is relative to event target)
            const [svgX, svgY] = d3.pointer(event.sourceEvent, svgNode)
            const [imgX, imgY] = transform.invert([svgX, svgY])
            callbacks.onResize(field.id, idx, imgX, imgY)
          })
        handle.call(dragResize)
      })
    }
  }

  // Draw preview rectangle during creation
  if (drawPreview) {
    group.append('rect')
      .attr('x', drawPreview.x)
      .attr('y', drawPreview.y)
      .attr('width', drawPreview.w)
      .attr('height', drawPreview.h)
      .attr('fill', 'none')
      .attr('stroke', '#2196F3')
      .attr('stroke-width', 2 / transform.k)
      .attr('stroke-dasharray', `${6 / transform.k},${4 / transform.k}`)
      .attr('pointer-events', 'none')
  }
}
