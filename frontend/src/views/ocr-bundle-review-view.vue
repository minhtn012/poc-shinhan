<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between gap-4">
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
              <BreadcrumbPage>Bundle Results</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <h1 class="text-xl font-semibold">
          Bundle Results{{ bundleName ? ` — ${bundleName}` : '' }}
        </h1>
      </div>
      <div class="flex gap-2 shrink-0">
        <Button variant="outline" size="sm" @click="router.push('/ocr')">← Back</Button>
        <Button size="sm" :disabled="!jobs.length" @click="exportJson">
          <Download class="size-3.5 mr-1.5" /> Export JSON
        </Button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-4">
      <Skeleton v-for="i in 3" :key="i" class="h-48 w-full rounded-lg" />
    </div>

    <!-- Empty state -->
    <Card v-else-if="!jobs.length">
      <CardContent class="pt-6 text-center text-muted-foreground">
        No documents found for this bundle.
      </CardContent>
    </Card>

    <!-- Document sections -->
    <BundleDocumentSection
      v-for="(job, i) in jobs"
      :key="job.id"
      :job="job"
      :index="i + 1"
      @value-change="onValueChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { Download } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Breadcrumb, BreadcrumbItem, BreadcrumbLink,
  BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator
} from '@/components/ui/breadcrumb'
import BundleDocumentSection from '@/components/ocr/bundle-document-section.vue'
import { ocrService } from '@/services/ocr.service'
import { bundleService } from '@/services/bundle.service'
import type { OcrJob } from '@/types/ocr.types'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const jobs = ref<OcrJob[]>([])
const bundleName = ref('')

onMounted(async () => {
  const bundleId = route.params.bundleId as string
  try {
    const [jobList, bundle] = await Promise.all([
      ocrService.listBundleJobs(bundleId),
      bundleService.get(bundleId).catch(() => null),
    ])
    jobs.value = jobList
    bundleName.value = bundle?.name ?? ''
  } catch (e: any) {
    toast.error(e.message ?? 'Failed to load bundle results')
  } finally {
    loading.value = false
  }
})

async function onValueChange(jobId: string, fieldId: string, value: string) {
  try {
    await ocrService.updateField(jobId, fieldId, value)
    const bundleId = route.params.bundleId as string
    jobs.value = await ocrService.listBundleJobs(bundleId)
    toast.success('Value updated')
  } catch (e: any) {
    toast.error(e.message ?? 'Failed to update')
  }
}

function exportJson() {
  const allResults = jobs.value.map(j => ({
    templateName: j.templateName, jobId: j.id,
    results: j.results,
  }))
  const blob = new Blob([JSON.stringify(allResults, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `bundle-${route.params.bundleId}.json`
  a.click()
  URL.revokeObjectURL(url)
  toast.success('JSON exported')
}
</script>
