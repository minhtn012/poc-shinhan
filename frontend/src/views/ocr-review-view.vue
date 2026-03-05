<template>
  <div class="h-full flex flex-col gap-4">
    <!-- Breadcrumb + header -->
    <div class="flex items-center justify-between gap-4 shrink-0">
      <div class="space-y-1">
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink as-child>
                <RouterLink to="/ocr">OCR Jobs</RouterLink>
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>{{ job?.templateName ?? 'Review' }}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <h1 class="text-xl font-semibold">{{ job?.templateName }}</h1>
      </div>

      <div class="flex gap-2 shrink-0">
        <Button variant="outline" size="sm" @click="router.push('/ocr')">← Back</Button>
        <Button size="sm" @click="exportJson">
          <Download class="size-3.5 mr-1.5" /> Export JSON
        </Button>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="space-y-3">
      <Skeleton class="h-80 w-full rounded-lg" />
      <Skeleton class="h-48 w-full rounded-lg" />
    </div>

    <!-- Split panel: image | results -->
    <div v-else-if="job" class="flex flex-1 min-h-0 rounded-lg border border-black/[0.06] overflow-hidden">
      <!-- Left: document image -->
      <div class="flex-[55] relative border-r border-black/[0.04]">
        <ImageOverlay
          v-if="fullImageUrl"
          :image-url="fullImageUrl"
          :results="job.results"
          :hovered-field-id="hoveredFieldId"
          :field-colors="fieldColors"
          @hover="hoveredFieldId = $event"
          @select="hoveredFieldId = $event"
        />
        <div v-else class="flex items-center justify-center h-full bg-muted">
          <p class="text-sm text-muted-foreground">No image</p>
        </div>
      </div>

      <!-- Right: results table -->
      <div class="flex-[45] min-h-0">
        <ResultsTable
          :results="job.results"
          :hovered-field-id="hoveredFieldId"
          @hover="hoveredFieldId = $event"
          @value-change="onValueChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { Download } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Breadcrumb, BreadcrumbItem, BreadcrumbLink,
  BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator
} from '@/components/ui/breadcrumb'
import ImageOverlay from '@/components/ocr/image-overlay.vue'
import ResultsTable from '@/components/ocr/results-table.vue'
import { ocrService } from '@/services/ocr.service'
import { templateService } from '@/services/template.service'
import type { OcrJob } from '@/types/ocr.types'

const API_BASE = ''

const route  = useRoute()
const router = useRouter()

const loading        = ref(true)
const job            = ref<OcrJob | null>(null)
const fullImageUrl   = ref<string | null>(null)
const hoveredFieldId = ref<string | null>(null)

const fieldColors = computed<Record<string, string>>(() => {
  // Will be populated after loading template version fields
  return _fieldColors.value
})
const _fieldColors = ref<Record<string, string>>({})

async function loadJob(): Promise<void> {
  loading.value = true
  try {
    const id = route.params.id as string
    job.value = await ocrService.get(id)

    if (job.value.imageUrl) {
      fullImageUrl.value = API_BASE + job.value.imageUrl
    }

    // Fetch field colors from template version
    try {
      const templates = await templateService.list()
      for (const t of templates) {
        const detail = await templateService.get(t.id)
        const ver = detail.versions.find(v => v.id === job.value!.templateVersionId)
        if (ver) {
          const map: Record<string, string> = {}
          for (const f of ver.fields) map[f.id] = f.color
          _fieldColors.value = map
          break
        }
      }
    } catch {
      // Field colors are optional enhancement
    }
  } catch (e: any) {
    toast.error(e.message ?? 'Failed to load job')
  } finally {
    loading.value = false
  }
}

async function onValueChange(fieldId: string, value: string): Promise<void> {
  if (!job.value) return
  try {
    await ocrService.updateField(job.value.id, fieldId, value)
    job.value = await ocrService.get(job.value.id)
    toast.success('Value updated')
  } catch (e: any) {
    toast.error(e.message ?? 'Failed to update')
  }
}

function exportJson(): void {
  if (!job.value) return
  const blob = new Blob([JSON.stringify(job.value.results, null, 2)], { type: 'application/json' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url
  a.download = `ocr-${job.value.id}.json`
  a.click()
  URL.revokeObjectURL(url)
  toast.success('JSON exported')
}

onMounted(loadJob)
</script>
