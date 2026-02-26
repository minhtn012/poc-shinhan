<template>
  <div class="h-full flex flex-col gap-4">
    <!-- Breadcrumb + header -->
    <div class="flex items-center justify-between gap-4 shrink-0">
      <div class="space-y-1">
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink as-child>
                <RouterLink to="/templates">Templates</RouterLink>
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbLink as-child>
                <RouterLink :to="'/templates/' + templateId">{{ templateName }}</RouterLink>
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>{{ version?.version }}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <div class="flex items-center gap-3">
          <h1 class="text-xl font-bold text-foreground font-mono">{{ version?.version }}</h1>
          <VersionBadge v-if="version" :status="version.status" />
        </div>
      </div>

      <div class="flex gap-2 shrink-0">
        <Button size="sm" @click="cloneToNew">
          <Copy class="size-3.5 mr-1.5" /> New Version
        </Button>
        <Button variant="outline" size="sm" @click="router.push('/templates/' + templateId)">
          ← Back
        </Button>
      </div>
    </div>

    <!-- Not found -->
    <Alert v-if="notFound" variant="destructive">
      <AlertTitle>Version not found</AlertTitle>
    </Alert>

    <!-- Loading skeleton -->
    <div v-else-if="!version" class="flex flex-1 min-h-0 gap-4">
      <Skeleton class="flex-[55] rounded-lg" />
      <Skeleton class="flex-[45] rounded-lg" />
    </div>

    <!-- Split panel: image | fields -->
    <div v-else class="flex flex-1 min-h-0 rounded-lg border border-black/[0.06] overflow-hidden">
      <!-- Left: image with annotation overlay -->
      <div class="flex-[55] relative border-r border-black/[0.04]">
        <div v-if="imageLoading" class="flex items-center justify-center h-full bg-muted/30">
          <Loader2 class="size-8 animate-spin text-primary/40" />
        </div>
        <AnnotationCanvas
          v-else-if="imageUrl"
          :image-url="imageUrl"
          :model-value="editableFields"
          readonly
        />
        <div v-else class="flex items-center justify-center h-full bg-muted/30">
          <p class="text-sm text-muted-foreground">No image available</p>
        </div>
      </div>

      <!-- Right: editable fields panel -->
      <div class="flex-[45] flex flex-col min-h-0 bg-white">
        <!-- Panel header -->
        <div class="flex items-center justify-between px-5 py-3.5 border-b border-black/[0.04] shrink-0">
          <div>
            <h2 class="text-sm font-bold text-foreground">Fields</h2>
            <p class="text-xs text-primary/50 mt-0.5">{{ editableFields.length }} fields · click to edit</p>
          </div>
          <Button v-if="hasChanges" size="sm" @click="saveFields">
            <Save class="size-3.5 mr-1.5" /> Save Changes
          </Button>
        </div>

        <!-- Scrollable field list -->
        <div class="flex-1 overflow-y-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead class="w-12">Color</TableHead>
                <TableHead>Field Name</TableHead>
                <TableHead class="w-48">Bounding Box</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow
                v-for="(field, idx) in editableFields"
                :key="field.id"
                :class="editingIdx === idx ? 'bg-primary/[0.03]' : ''"
              >
                <TableCell>
                  <label class="cursor-pointer">
                    <input
                      type="color"
                      :value="field.color"
                      class="sr-only"
                      @input="updateFieldColor(idx, ($event.target as HTMLInputElement).value)"
                    />
                    <span
                      class="inline-flex size-6 rounded-md border border-black/[0.06] cursor-pointer hover:ring-2 hover:ring-primary/20 transition-shadow"
                      :style="{ background: field.color }"
                    />
                  </label>
                </TableCell>
                <TableCell>
                  <div v-if="editingIdx === idx" class="flex items-center gap-2">
                    <Input
                      v-model="editingName"
                      class="h-8 text-sm"
                      @keyup.enter="commitEdit"
                      @keyup.escape="cancelEdit"
                    />
                    <Button variant="ghost" size="icon" class="size-7 shrink-0" @click="commitEdit">
                      <Check class="size-3.5 text-primary" />
                    </Button>
                    <Button variant="ghost" size="icon" class="size-7 shrink-0" @click="cancelEdit">
                      <X class="size-3.5" />
                    </Button>
                  </div>
                  <span
                    v-else
                    class="font-medium text-sm cursor-pointer hover:text-primary transition-colors"
                    @click="startEdit(idx)"
                  >
                    {{ field.name }}
                  </span>
                </TableCell>
                <TableCell class="font-mono text-xs text-muted-foreground">
                  {{ formatBBox(field.bbox) }}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { Copy, Loader2, Save, Check, X } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertTitle } from '@/components/ui/alert'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import {
  Breadcrumb, BreadcrumbItem, BreadcrumbLink,
  BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator
} from '@/components/ui/breadcrumb'
import VersionBadge from '@/components/common/version-badge.vue'
import AnnotationCanvas from '@/components/annotation/annotation-canvas.vue'
import * as templateService from '@/services/template.service'
import { useImageStore } from '@/composables/use-image-store'
import type { TemplateField, NormalizedBBox } from '@/types/template.types'

const route      = useRoute()
const router     = useRouter()
const imageStore = useImageStore()

const templateId   = route.params.id as string
const versionId    = route.params.vid as string
const version      = ref<ReturnType<typeof templateService.getVersion>>()
const templateName = ref('')
const imageUrl     = ref<string | null>(null)
const imageLoading = ref(true)
const notFound     = ref(false)
let objectUrl: string | null = null

// Editable fields (cloned from version)
const editableFields = ref<TemplateField[]>([])
const originalFields = ref<string>('')  // JSON snapshot for dirty check

// Inline edit state
const editingIdx  = ref<number | null>(null)
const editingName = ref('')

const hasChanges = computed(() =>
  JSON.stringify(editableFields.value) !== originalFields.value
)

function formatBBox(b: NormalizedBBox): string {
  return `${b.x.toFixed(3)}, ${b.y.toFixed(3)}, ${b.w.toFixed(3)}, ${b.h.toFixed(3)}`
}

async function load(): Promise<void> {
  version.value = templateService.getVersion(versionId)
  const tmpl = templateService.getTemplate(templateId)
  templateName.value = tmpl?.name ?? ''

  if (!version.value) {
    notFound.value = true
    imageLoading.value = false
    return
  }

  // Clone fields for editing
  editableFields.value = version.value.fields.map(f => ({ ...f, bbox: { ...f.bbox } }))
  originalFields.value = JSON.stringify(editableFields.value)

  // Load image
  if (version.value.imageKey) {
    const blob = await imageStore.getImage(version.value.imageKey)
    if (blob) {
      objectUrl = URL.createObjectURL(blob)
      imageUrl.value = objectUrl
    }
  }
  imageLoading.value = false
}

function startEdit(idx: number): void {
  editingIdx.value = idx
  editingName.value = editableFields.value[idx].name
}

function commitEdit(): void {
  if (editingIdx.value === null) return
  const trimmed = editingName.value.trim()
  if (trimmed) {
    editableFields.value[editingIdx.value].name = trimmed
  }
  editingIdx.value = null
}

function cancelEdit(): void {
  editingIdx.value = null
}

function updateFieldColor(idx: number, color: string): void {
  editableFields.value[idx].color = color
}

function saveFields(): void {
  templateService.updateVersionFields(versionId, editableFields.value)
  originalFields.value = JSON.stringify(editableFields.value)
  // Refresh version from storage
  version.value = templateService.getVersion(versionId)
  toast.success('Fields updated')
}

function cloneToNew(): void {
  router.push(`/templates/create?from=${versionId}&templateId=${templateId}`)
}

onMounted(load)
onUnmounted(() => { if (objectUrl) URL.revokeObjectURL(objectUrl) })
</script>
