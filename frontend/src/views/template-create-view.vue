<template>
  <div class="w-full space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-semibold">
        {{ isCloning ? 'New Version from Template' : 'New Template' }}
      </h1>
      <Button variant="outline" size="sm" @click="router.push('/templates')">← Back</Button>
    </div>

    <!-- Step indicator -->
    <div class="flex items-center justify-center gap-0">
      <div v-for="(step, i) in steps" :key="i" class="flex items-center">
        <div class="flex items-center gap-2">
          <div :class="[
            'flex size-7 items-center justify-center rounded-full text-xs font-semibold transition-colors',
            activeStep > i
              ? 'bg-primary text-primary-foreground'
              : activeStep === i
                ? 'bg-primary text-primary-foreground ring-4 ring-primary/20'
                : 'bg-muted text-muted-foreground'
          ]">
            <CheckIcon v-if="activeStep > i" class="size-3.5" />
            <span v-else>{{ i + 1 }}</span>
          </div>
          <div class="hidden sm:block">
            <p :class="['text-sm font-medium', activeStep >= i ? 'text-foreground' : 'text-muted-foreground']">
              {{ step.title }}
            </p>
            <p class="text-xs text-muted-foreground">{{ step.desc }}</p>
          </div>
        </div>
        <div v-if="i < steps.length - 1" :class="[
          'mx-4 h-px flex-1 min-w-8 transition-colors',
          activeStep > i ? 'bg-primary' : 'bg-border'
        ]" />
      </div>
    </div>

    <!-- ── Step 1: Info + Image ── -->
    <Card v-if="activeStep === 0" class="max-w-xl mx-auto">
      <CardContent class="pt-6 space-y-4">
        <div class="space-y-1.5">
          <Label>Template Name <span class="text-destructive">*</span></Label>
          <Input v-model="templateName" placeholder="e.g. Invoice, Receipt" :disabled="isCloning" />
        </div>

        <div class="space-y-1.5">
          <Label>Version <span class="text-destructive">*</span></Label>
          <Input v-model="versionString" placeholder="e.g. v1" class="w-36" />
        </div>

        <div class="space-y-1.5">
          <Label>Template Image <span class="text-destructive">*</span></Label>
          <!-- Drop zone -->
          <div
            :class="[
              'relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center cursor-pointer transition-colors',
              isDragging ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/60 hover:bg-muted/40',
              (imageFile || sourceImageKey) ? 'border-emerald-400 bg-emerald-50' : ''
            ]"
            @click="fileInput?.click()"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="onDrop"
          >
            <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onFileInput" />
            <template v-if="imageFile || sourceImageKey">
              <ImageIcon class="size-8 text-emerald-500 mb-2" />
              <p class="text-sm font-medium text-emerald-700">{{ imageFile?.name ?? 'Cloned image' }}</p>
              <p class="text-xs text-muted-foreground mt-1">Click to replace</p>
            </template>
            <template v-else>
              <Upload class="size-8 text-muted-foreground mb-2" />
              <p class="text-sm font-medium">Drop image here or <span class="text-primary">click to browse</span></p>
              <p class="text-xs text-muted-foreground mt-1">JPG, PNG, WEBP, TIFF up to 10 MB</p>
            </template>
          </div>
        </div>

        <Button :disabled="!canProceedStep1" class="w-full" @click="activeStep = 1">
          Next: Annotate Fields →
        </Button>
      </CardContent>
    </Card>

    <!-- ── Step 2: Annotate ── -->
    <div v-if="activeStep === 1" class="flex flex-col gap-0 rounded-lg border overflow-hidden" style="height: calc(100vh - 280px); min-height: 480px">
      <!-- Canvas + sidebar grid -->
      <div class="flex flex-1 min-h-0">
        <div class="flex-1 min-w-0">
          <AnnotationCanvas
            :image-url="imageUrl"
            :model-value="fields"
            @update:model-value="fields = $event"
            @field-selected="selectedFieldId = $event"
          />
        </div>
        <div class="w-72 shrink-0 border-l overflow-y-auto">
          <FieldSidebar
            :fields="fields"
            :selected-field-id="selectedFieldId"
            @update:fields="fields = $event"
            @select="selectedFieldId = $event"
            @delete="deleteField"
          />
        </div>
      </div>
      <!-- Action bar -->
      <div class="flex items-center justify-between gap-3 px-4 py-3 border-t bg-muted/40 shrink-0">
        <Button variant="outline" size="sm" @click="activeStep = 0">← Back</Button>
        <p v-if="!fields.length" class="text-sm text-amber-600 font-medium">
          Draw at least one field to continue
        </p>
        <Button size="sm" :disabled="fields.length === 0" @click="activeStep = 2">
          Next: Review →
        </Button>
      </div>
    </div>

    <!-- ── Step 3: Review + Save ── -->
    <div v-if="activeStep === 2" class="space-y-4 max-w-3xl mx-auto">
      <Card class="table-card">
        <CardContent class="pt-5">
          <div class="flex items-baseline gap-2 mb-4">
            <h2 class="text-base font-semibold">{{ templateName }}</h2>
            <Badge variant="secondary">{{ versionString }}</Badge>
            <span class="text-sm text-muted-foreground ml-auto">{{ fields.length }} fields</span>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead class="w-14">Color</TableHead>
                <TableHead>Field Name</TableHead>
                <TableHead>BBox (x, y, w, h)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="field in fields" :key="field.id">
                <TableCell>
                  <span class="inline-flex size-5 rounded-md border border-black/10" :style="{ background: field.color }" />
                </TableCell>
                <TableCell class="font-medium text-sm">{{ field.name }}</TableCell>
                <TableCell class="font-mono text-xs text-muted-foreground">{{ formatBBox(field.bbox) }}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div class="flex justify-center gap-3">
        <Button variant="outline" @click="activeStep = 1">← Back</Button>
        <Button :disabled="saving" @click="saveTemplate">
          <LoaderCircle v-if="saving" class="size-4 mr-2 animate-spin" />
          Save Template
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { toast } from 'vue-sonner'
import { CheckIcon, Upload, ImageIcon, LoaderCircle } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import AnnotationCanvas from '@/components/annotation/annotation-canvas.vue'
import FieldSidebar from '@/components/annotation/field-sidebar.vue'
import type { TemplateField, NormalizedBBox } from '@/types/template.types'
import * as templateService from '@/services/template.service'
import { useImageStore } from '@/composables/use-image-store'
import { fileToBase64, blobToBase64 } from '@/lib/api-bbox-transform'

const steps = [
  { title: 'Upload Image',    desc: 'Name & image' },
  { title: 'Annotate Fields', desc: 'Draw bounding boxes' },
  { title: 'Confirm & Save',  desc: 'Review and save' },
]

const router     = useRouter()
const route      = useRoute()
const imageStore = useImageStore()

const activeStep      = ref(0)
const templateName    = ref('')
const versionString   = ref('v1')
const imageFile       = ref<File | null>(null)
const imageUrl        = ref<string | null>(null)
const sourceImageKey  = ref<string | null>(null)
const fields          = ref<TemplateField[]>([])
const selectedFieldId = ref<string | null>(null)
const saving          = ref(false)
const isDragging      = ref(false)
const fileInput       = ref<HTMLInputElement | null>(null)

const isCloning = computed(() => !!route.query.from)
const canProceedStep1 = computed(() =>
  templateName.value.trim() &&
  versionString.value.trim() &&
  (imageFile.value !== null || sourceImageKey.value !== null)
)

onMounted(async () => {
  // Populate cache before using sync getters
  await templateService.loadFromApi()

  const fromVersionId  = route.query.from as string | undefined
  const fromTemplateId = route.query.templateId as string | undefined
  if (!fromVersionId || !fromTemplateId) return

  const sourceVersion  = templateService.getVersion(fromVersionId)
  const sourceTemplate = templateService.getTemplate(fromTemplateId)
  if (!sourceVersion || !sourceTemplate) return

  templateName.value   = sourceTemplate.name
  versionString.value  = templateService.suggestNextVersion(fromTemplateId)
  fields.value         = sourceVersion.fields.map(f => ({ ...f, id: crypto.randomUUID() }))
  sourceImageKey.value = sourceVersion.imageKey

  const url = await imageStore.getImageUrl(sourceVersion.imageKey)
  if (url) imageUrl.value = url
})

function applyFile(file: File): void {
  imageFile.value = file
  imageUrl.value  = URL.createObjectURL(file)
}

function onFileInput(e: Event): void {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) applyFile(file)
}

function onDrop(e: DragEvent): void {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file && file.type.startsWith('image/')) applyFile(file)
}

function deleteField(id: string): void {
  fields.value = fields.value.filter(f => f.id !== id)
  if (selectedFieldId.value === id) selectedFieldId.value = null
}

function formatBBox(bbox: NormalizedBBox): string {
  const f = (n: number) => n.toFixed(3)
  return `${f(bbox.x)}, ${f(bbox.y)}, ${f(bbox.w)}, ${f(bbox.h)}`
}

async function saveTemplate(): Promise<void> {
  saving.value = true
  try {
    // Determine layoutId: use existing if cloning or matching name, otherwise null (new)
    const fromTemplateId = route.query.templateId as string | undefined
    let layoutId: string | null = fromTemplateId ?? null
    if (!layoutId) {
      const existing = templateService.getTemplates().find(t => t.name === templateName.value)
      if (existing) layoutId = existing.id
    }

    // Save image locally + convert to base64 for API
    let imageKey: string
    let imageBase64: string
    if (imageFile.value) {
      imageKey    = `img:${crypto.randomUUID()}`
      imageBase64 = await fileToBase64(imageFile.value)
      await imageStore.saveImage(imageKey, imageFile.value)
    } else if (sourceImageKey.value) {
      imageKey = sourceImageKey.value
      const blob = await imageStore.getImage(sourceImageKey.value)
      imageBase64 = blob ? await blobToBase64(blob) : ''
    } else {
      toast.error('No image provided')
      return
    }

    await templateService.saveVersion(layoutId, templateName.value, versionString.value, imageKey, imageBase64, fields.value)
    toast.success('Template saved successfully')
    router.push('/templates')
  } catch {
    toast.error('Failed to save template')
  } finally {
    saving.value = false
  }
}
</script>
