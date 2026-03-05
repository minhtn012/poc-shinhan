import type { NormalizedBBox } from '@/types/template.types'
import type { YoloBBox } from '@/types/ocr.types'

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v))
}

/** YOLO [cx, cy, w, h] → NormalizedBBox {x, y, w, h} (top-left origin) */
export function yoloToNormalized([cx, cy, w, h]: YoloBBox): NormalizedBBox {
  return {
    x: clamp01(cx - w / 2),
    y: clamp01(cy - h / 2),
    w: clamp01(w),
    h: clamp01(h),
  }
}

/** NormalizedBBox {x, y, w, h} (top-left origin) → YOLO [cx, cy, w, h] */
export function normalizedToYolo({ x, y, w, h }: NormalizedBBox): YoloBBox {
  return [
    clamp01(x + w / 2),
    clamp01(y + h / 2),
    clamp01(w),
    clamp01(h),
  ]
}
