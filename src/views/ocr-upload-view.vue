<template>
  <div class="max-w-3xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold">New OCR Job</h1>
        <p class="text-sm text-muted-foreground mt-0.5">Upload a document to extract data</p>
      </div>
      <Button variant="outline" size="sm" @click="router.push('/ocr')">← Back</Button>
    </div>

    <!-- No active template warning -->
    <Alert v-if="!hasTemplates" variant="destructive">
      <AlertTriangle class="size-4" />
      <AlertTitle>No active templates found</AlertTitle>
      <AlertDescription class="mt-1">
        Create and activate a template before running OCR.
        <Button variant="link" class="h-auto p-0 ml-1 text-destructive underline" @click="router.push('/templates/create')">
          Create Template
        </Button>
      </AlertDescription>
    </Alert>

    <!-- ── Upload stage ── -->
    <Card v-if="stage === 'upload'">
      <CardContent class="pt-6 space-y-5">
        <!-- Drop zone -->
        <div
          :class="[
            'flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 text-center cursor-pointer transition-colors',
            !hasTemplates ? 'pointer-events-none opacity-50' : '',
            isDragging
              ? 'border-primary bg-primary/5'
              : file
                ? 'border-emerald-400 bg-emerald-50'
                : 'border-border hover:border-primary/60 hover:bg-muted/40'
          ]"
          @click="fileInput?.click()"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="onDrop"
        >
          <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onFileInput" />
          <template v-if="file">
            <ImageIcon class="size-10 text-emerald-500 mb-3" />
            <p class="text-sm font-semibold text-emerald-700">{{ file.name }}</p>
            <p class="text-xs text-muted-foreground mt-1">Click to replace</p>
          </template>
          <template v-else>
            <Upload class="size-10 text-muted-foreground mb-3" />
            <p class="text-sm font-semibold">Drop document image here</p>
            <p class="text-sm text-muted-foreground">or <span class="text-primary">click to browse</span></p>
            <p class="text-xs text-muted-foreground mt-2">JPG, PNG, WEBP, TIFF supported</p>
          </template>
        </div>

        <Button
          class="w-full"
          size="lg"
          :disabled="!file || !hasTemplates"
          @click="startProcessing"
        >
          <ScanText class="size-4 mr-2" />
          Start OCR Processing
        </Button>
      </CardContent>
    </Card>

    <!-- ── Processing stage ── -->
    <Card v-if="stage === 'processing'">
      <CardContent class="pt-6 space-y-8">
        <!-- Step progress -->
        <div class="space-y-3">
          <div v-for="(step, i) in processingSteps" :key="i" class="flex items-center gap-3">
            <div :class="[
              'flex size-7 items-center justify-center rounded-full shrink-0 transition-colors',
              processingStep > i
                ? 'bg-primary text-primary-foreground'
                : processingStep === i
                  ? 'bg-primary/10 text-primary ring-2 ring-primary/30'
                  : 'bg-muted text-muted-foreground'
            ]">
              <CheckIcon v-if="processingStep > i" class="size-3.5" />
              <LoaderCircle v-else-if="processingStep === i" class="size-3.5 animate-spin" />
              <span v-else class="text-xs font-medium">{{ i + 1 }}</span>
            </div>
            <div class="flex-1 min-w-0">
              <p :class="['text-sm font-medium', processingStep >= i ? 'text-foreground' : 'text-muted-foreground']">
                {{ step.label }}
              </p>
              <p class="text-xs text-muted-foreground truncate">{{ step.desc }}</p>
            </div>
          </div>
        </div>

        <!-- Current status -->
        <div class="flex items-center gap-3 rounded-lg bg-muted/40 p-4">
          <LoaderCircle class="size-5 animate-spin text-primary shrink-0" />
          <p class="text-sm text-muted-foreground">{{ processingMessage }}</p>
        </div>
      </CardContent>
    </Card>

    <!-- ── Error stage ── -->
    <Card v-if="stage === 'error'">
      <CardContent class="pt-6">
        <div class="flex flex-col items-center text-center py-4 gap-4">
          <div class="size-14 rounded-full bg-destructive/10 flex items-center justify-center">
            <XCircle class="size-7 text-destructive" />
          </div>
          <div>
            <h3 class="font-semibold text-base mb-1">Processing Failed</h3>
            <p class="text-sm text-muted-foreground max-w-sm">{{ errorMessage }}</p>
          </div>
          <div class="flex gap-2">
            <Button @click="reset">Try Again</Button>
            <Button variant="outline" @click="router.push('/ocr')">Back to Jobs</Button>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { Upload, ImageIcon, ScanText, CheckIcon, LoaderCircle, XCircle, AlertTriangle } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { mockPreprocess, mockOcr } from '@/services/mock-api'
import * as templateService from '@/services/template.service'
import * as ocrService from '@/services/ocr.service'
import { useImageStore } from '@/composables/use-image-store'

type Stage = 'upload' | 'processing' | 'error'

const router     = useRouter()
const imageStore = useImageStore()

const stage           = ref<Stage>('upload')
const file            = ref<File | null>(null)
const isDragging      = ref(false)
const fileInput       = ref<HTMLInputElement | null>(null)
const processingStep  = ref(0)
const processingMessage = ref('Analyzing document...')
const errorMessage    = ref('')
const hasTemplates    = ref(false)

const processingSteps = [
  { label: 'Preprocessing',    desc: 'Detecting template...' },
  { label: 'Template Matching', desc: '' },
  { label: 'OCR Extraction',   desc: 'Reading fields...' },
]

onMounted(() => {
  hasTemplates.value = templateService.getTemplates().some(t => t.activeVersionId)
})

function applyFile(f: File): void {
  file.value = f
}

function onFileInput(e: Event): void {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f) applyFile(f)
}

function onDrop(e: DragEvent): void {
  isDragging.value = false
  const f = e.dataTransfer?.files?.[0]
  if (f && f.type.startsWith('image/')) applyFile(f)
}

function reset(): void {
  stage.value = 'upload'
  file.value  = null
  processingStep.value = 0
  processingMessage.value = 'Analyzing document...'
  errorMessage.value = ''
}

async function startProcessing(): Promise<void> {
  if (!file.value) return
  stage.value = 'processing'
  processingStep.value = 0
  processingMessage.value = 'Preprocessing document image…'

  try {
    const match = await mockPreprocess(file.value)
    if (!match) {
      errorMessage.value = 'No matching template found. Please create a template first.'
      stage.value = 'error'
      return
    }
    processingStep.value = 1

    const version = templateService.getActiveVersion(match.templateId)
    if (!version) {
      errorMessage.value = 'Matched template has no active version.'
      stage.value = 'error'
      return
    }

    const tpl = templateService.getTemplate(match.templateId)
    const matchStep = processingSteps[1]
    if (matchStep) matchStep.desc = `Matched: ${tpl?.name ?? 'Unknown'} (${(match.confidence * 100).toFixed(0)}%)`
    processingMessage.value = `Template matched: ${tpl?.name}. Running OCR…`
    processingStep.value = 2

    const results = await mockOcr(file.value, version)
    processingStep.value = 3

    const imageKey = `img:${crypto.randomUUID()}`
    await imageStore.saveImage(imageKey, file.value)

    const job = ocrService.createJob({ templateVersionId: version.id, templateName: tpl?.name ?? 'Unknown', imageKey })
    ocrService.updateJobStatus(job.id, 'done')
    ocrService.updateJobResults(job.id, results)

    toast.success('OCR processing complete')
    router.push(`/ocr/${job.id}`)
  } catch {
    errorMessage.value = 'An unexpected error occurred during processing.'
    stage.value = 'error'
  }
}
</script>
