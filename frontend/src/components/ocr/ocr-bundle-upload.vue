<template>
  <div class="space-y-5">
    <!-- Bundle selector -->
    <div class="space-y-2">
      <label class="text-sm font-medium">Select Bundle</label>
      <Select v-model="selectedBundleId">
        <SelectTrigger>
          <SelectValue placeholder="Choose a bundle..." />
        </SelectTrigger>
        <SelectContent>
          <SelectItem v-for="b in bundles" :key="b.id" :value="b.id">
            {{ b.name }} ({{ b.templateCount }} templates)
          </SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- Bundle items preview -->
    <div v-if="bundleDetail" class="space-y-2">
      <p class="text-sm font-medium">
        Templates in bundle
        <span class="text-muted-foreground font-normal">({{ bundleDetail.items.length }} items)</span>
      </p>
      <div class="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead class="w-12">#</TableHead>
              <TableHead>Template</TableHead>
              <TableHead>File</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="(item, i) in bundleDetail.items" :key="item.id">
              <TableCell class="text-muted-foreground">{{ i + 1 }}</TableCell>
              <TableCell class="font-medium">{{ item.templateName }}</TableCell>
              <TableCell>
                <span v-if="files[i]" class="text-sm text-emerald-600">{{ files[i].name }}</span>
                <span v-else class="text-sm text-muted-foreground italic">No file</span>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </div>

    <!-- File upload zone -->
    <div v-if="bundleDetail" class="space-y-2">
      <label class="text-sm font-medium">Upload Files</label>
      <div
        :class="[
          'flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center cursor-pointer transition-colors',
          isDragging ? 'border-primary bg-primary/5' : files.length
            ? 'border-emerald-400 bg-emerald-50'
            : 'border-border hover:border-primary/60 hover:bg-muted/40'
        ]"
        @click="fileInput?.click()"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="onDrop"
      >
        <input ref="fileInput" type="file" accept="image/*" multiple class="hidden" @change="onFileInput" />
        <Upload class="size-8 text-muted-foreground mb-2" />
        <p v-if="files.length" class="text-sm font-semibold text-emerald-700">
          {{ files.length }} file(s) selected
        </p>
        <p v-else class="text-sm font-semibold">
          Drop {{ bundleDetail.items.length }} document images here
        </p>
        <p class="text-xs text-muted-foreground mt-1">or click to browse</p>
      </div>
    </div>

    <!-- Validation error -->
    <Alert v-if="validationError" variant="destructive">
      <AlertTriangle class="size-4" />
      <AlertTitle>Validation Error</AlertTitle>
      <AlertDescription>{{ validationError }}</AlertDescription>
    </Alert>

    <!-- Submit button -->
    <Button class="w-full" size="lg" :disabled="!isValid" @click="onSubmit">
      <ScanText class="size-4 mr-2" />
      Start Bundle OCR
    </Button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Upload, ScanText, AlertTriangle } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { bundleService } from '@/services/bundle.service'
import type { Bundle, BundleDetail } from '@/types/bundle.types'

const emit = defineEmits<{
  submit: [payload: { bundleId: string; files: File[] }]
}>()

const bundles = ref<Bundle[]>([])
const selectedBundleId = ref<string>('')
const bundleDetail = ref<BundleDetail | null>(null)
const files = ref<File[]>([])
const isDragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const validationError = computed(() => {
  if (!bundleDetail.value || files.value.length === 0) return null
  if (files.value.length !== bundleDetail.value.items.length) {
    return `Expected ${bundleDetail.value.items.length} files, got ${files.value.length}`
  }
  const noActive = bundleDetail.value.items.find(i => !i.activeVersionId)
  if (noActive) return `Template "${noActive.templateName}" has no active version`
  return null
})

const isValid = computed(() =>
  bundleDetail.value && files.value.length > 0 && !validationError.value
)

watch(selectedBundleId, async (id) => {
  if (!id) { bundleDetail.value = null; return }
  bundleDetail.value = await bundleService.get(id)
  files.value = []
})

onMounted(async () => {
  bundles.value = await bundleService.list()
})

function applyFiles(fileList: FileList) {
  files.value = Array.from(fileList)
}

function onFileInput(e: Event) {
  const fl = (e.target as HTMLInputElement).files
  if (fl) applyFiles(fl)
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const fl = e.dataTransfer?.files
  if (fl) applyFiles(fl)
}

function onSubmit() {
  if (!selectedBundleId.value || !isValid.value) return
  emit('submit', { bundleId: selectedBundleId.value, files: files.value })
}
</script>
