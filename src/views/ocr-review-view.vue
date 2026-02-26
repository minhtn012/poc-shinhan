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
    <div v-if="!job" class="space-y-3">
      <Skeleton class="h-80 w-full rounded-lg" />
      <Skeleton class="h-48 w-full rounded-lg" />
    </div>

    <!-- Split panel: image | results -->
    <div v-else class="flex flex-1 min-h-0 rounded-lg border border-black/[0.06] overflow-hidden">
      <!-- Left: document image -->
      <div class="flex-[55] relative border-r border-black/[0.04]">
        <div v-if="imageLoading" class="flex items-center justify-center h-full bg-muted">
          <Loader2 class="size-8 animate-spin text-muted-foreground" />
        </div>
        <ImageOverlay
          v-else
          :image-url="imageUrl"
          :results="job.results"
          :hovered-field-id="hoveredFieldId"
          :field-colors="fieldColors"
          @hover="hoveredFieldId = $event"
          @select="hoveredFieldId = $event"
        />
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { Download, Loader2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Breadcrumb, BreadcrumbItem, BreadcrumbLink,
  BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator
} from '@/components/ui/breadcrumb'
import ImageOverlay from '@/components/ocr/image-overlay.vue'
import ResultsTable from '@/components/ocr/results-table.vue'
import * as ocrService from '@/services/ocr.service'
import * as templateService from '@/services/template.service'
import { useImageStore } from '@/composables/use-image-store'
import type { OcrJob } from '@/types/ocr.types'

const route      = useRoute()
const router     = useRouter()
const imageStore = useImageStore()

const job            = ref<OcrJob | undefined>()
const imageUrl       = ref<string | null>(null)
const imageLoading   = ref(true)
const hoveredFieldId = ref<string | null>(null)
let objectUrl: string | null = null

const fieldColors = computed<Record<string, string>>(() => {
  if (!job.value) return {}
  const version = templateService.getVersion(job.value.templateVersionId)
  if (!version) return {}
  const map: Record<string, string> = {}
  for (const f of version.fields) map[f.id] = f.color
  return map
})

async function loadJob(): Promise<void> {
  const id = route.params.id as string
  job.value = ocrService.getJob(id)
  if (!job.value) return

  imageLoading.value = true
  const url = await imageStore.getImageUrl(job.value.imageKey)
  imageUrl.value = url
  objectUrl = url
  imageLoading.value = false
}

function onValueChange(fieldId: string, value: string): void {
  if (!job.value) return
  ocrService.updateFieldValue(job.value.id, fieldId, value)
  job.value = ocrService.getJob(job.value.id)
  toast.success('Value updated')
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
onUnmounted(() => { if (objectUrl) URL.revokeObjectURL(objectUrl) })
</script>
