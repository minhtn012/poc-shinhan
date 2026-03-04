<template>
  <div class="w-full space-y-4">
    <!-- Header -->
    <div class="flex items-start justify-between">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">Templates</h1>
        <p class="text-muted-foreground">Manage your OCR document templates</p>
      </div>
    </div>

    <!-- Toolbar -->
    <div class="flex items-center justify-between gap-4">
      <div class="flex items-center gap-2 flex-1">
        <!-- Search -->
        <div class="relative max-w-sm">
          <Input
            v-model="searchQuery"
            placeholder="Filter templates..."
            class="h-8 w-[200px] lg:w-[280px]"
          />
        </div>
        <!-- Status filter -->
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button variant="outline" size="sm" class="h-8 border-dashed">
              <PlusCircle class="mr-2 size-4" />
              Status
              <Badge v-if="statusFilter" variant="secondary" class="ml-2 rounded-sm px-1 font-normal">
                {{ statusFilter }}
              </Badge>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" class="w-[150px]">
            <DropdownMenuItem @click="statusFilter = null">
              <span>All</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem @click="statusFilter = 'active'">
              <CheckCircle2 class="mr-2 size-4 text-emerald-500" />
              <span>Active</span>
            </DropdownMenuItem>
            <DropdownMenuItem @click="statusFilter = 'draft'">
              <Circle class="mr-2 size-4 text-muted-foreground" />
              <span>Draft</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <!-- Clear filters -->
        <Button
          v-if="searchQuery || statusFilter"
          variant="ghost"
          size="sm"
          class="h-8 px-2 lg:px-3"
          @click="searchQuery = ''; statusFilter = null"
        >
          Reset
          <X class="ml-2 size-4" />
        </Button>
      </div>

      <div class="flex items-center gap-2">
        <Button @click="router.push('/templates/create')">
          <Plus class="mr-2 size-4" /> Add Template
        </Button>
      </div>
    </div>

    <!-- Skeleton -->
    <div v-if="loading" class="rounded-md border">
      <div class="p-4 space-y-3">
        <Skeleton class="h-8 w-full" />
        <Skeleton v-for="i in 5" :key="i" class="h-12 w-full" />
      </div>
    </div>

    <!-- Table -->
    <div v-else-if="rows.length" class="rounded-md border border-black/[0.06]">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead class="w-12">
              <Checkbox
                :checked="selectAllChecked"
                @update:checked="onSelectAllClick"
              />
            </TableHead>
            <TableHead class="w-[100px]">
              <div class="flex items-center gap-1">
                Template
                <ArrowUpDown class="size-3" />
              </div>
            </TableHead>
            <TableHead>
              <div class="flex items-center gap-1">
                Title
                <ArrowUpDown class="size-3" />
              </div>
            </TableHead>
            <TableHead class="w-[120px]">
              <div class="flex items-center gap-1">
                Status
                <ArrowUpDown class="size-3" />
              </div>
            </TableHead>
            <TableHead class="w-[100px]">
              <div class="flex items-center gap-1">
                Fields
                <ArrowUpDown class="size-3" />
              </div>
            </TableHead>
            <TableHead class="w-12" />
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow
            v-for="row in filteredRows"
            :key="row.id"
            class="cursor-pointer"
            :data-state="isRowSelected(row.id) ? 'selected' : undefined"
            @click="router.push('/templates/' + row.id)"
          >
            <!-- Checkbox -->
            <TableCell @click.stop>
              <Checkbox
                :checked="isRowSelected(row.id)"
                @update:checked="toggleRow(row.id)"
              />
            </TableCell>

            <!-- Template ID -->
            <TableCell class="font-medium">
              <span class="text-muted-foreground">TPL-{{ row.id.slice(0, 4).toUpperCase() }}</span>
            </TableCell>

            <!-- Title with version badge -->
            <TableCell>
              <div class="flex items-center gap-2">
                <Badge
                  :variant="row.activeVersion ? 'default' : 'outline'"
                  class="rounded-md font-medium"
                  :class="row.activeVersion ? 'bg-blue-500/10 text-blue-700 hover:bg-blue-500/20 border-0' : ''"
                >
                  {{ row.activeVersion ? `v${row.activeVersion.version}` : 'Draft' }}
                </Badge>
                <span class="truncate max-w-[400px]">{{ row.name }}</span>
              </div>
            </TableCell>

            <!-- Status -->
            <TableCell>
              <div class="flex items-center gap-2">
                <component
                  :is="getStatusIcon(row)"
                  class="size-4"
                  :class="getStatusColor(row)"
                />
                <span>{{ getStatusLabel(row) }}</span>
              </div>
            </TableCell>

            <!-- Fields -->
            <TableCell>
              <div class="flex items-center gap-1">
                <ArrowRight class="size-3.5 text-muted-foreground" />
                <span>{{ row.fieldCount }} fields</span>
              </div>
            </TableCell>

            <!-- Actions -->
            <TableCell @click.stop>
              <div class="flex items-center gap-0.5">
                <Button variant="ghost" size="icon" class="size-7 text-muted-foreground hover:text-foreground" @click="router.push('/templates/' + row.id)">
                  <ExternalLink class="size-3.5" />
                  <span class="sr-only">View details</span>
                </Button>
                <Button variant="ghost" size="icon" class="size-7 text-muted-foreground hover:text-foreground" @click="openEditDialog(row)">
                  <SquarePen class="size-3.5" />
                  <span class="sr-only">Edit</span>
                </Button>
                <Button variant="ghost" size="icon" class="size-7 text-muted-foreground hover:text-red-500" @click="handleDelete(row.id)">
                  <Trash2 class="size-3.5" />
                  <span class="sr-only">Delete</span>
                </Button>
              </div>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>

      <!-- Footer -->
      <div class="flex items-center justify-between px-4 py-2 border-t border-black/[0.04]">
        <div class="text-sm text-muted-foreground">
          {{ selectedIds.length }} of {{ filteredRows.length }} row(s) selected.
        </div>
        <div v-if="selectedIds.length > 0" class="flex items-center gap-2">
          <Button variant="outline" size="sm" @click="selectedIds = []">
            Clear selection
          </Button>
          <Button variant="destructive" size="sm" @click="handleBulkDelete">
            <Trash2 class="mr-2 size-3.5" /> Delete selected
          </Button>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="flex flex-col items-center justify-center py-16 text-center">
      <div class="size-12 rounded-full bg-muted flex items-center justify-center mb-4">
        <FileText class="size-6 text-muted-foreground" />
      </div>
      <h3 class="font-semibold text-lg mb-1">No templates</h3>
      <p class="text-sm text-muted-foreground mb-4 max-w-sm">
        Get started by creating your first OCR template.
      </p>
      <Button @click="router.push('/templates/create')">
        <Plus class="mr-2 size-4" /> Add Template
      </Button>
    </div>

    <!-- Edit dialog -->
    <Dialog v-model:open="editDialogOpen">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Template</DialogTitle>
        </DialogHeader>
        <div class="space-y-4 py-2">
          <div class="space-y-1.5">
            <Label>Name <span class="text-destructive">*</span></Label>
            <Input v-model="editForm.name" placeholder="Template name" />
          </div>
          <div class="space-y-1.5">
            <Label>Description</Label>
            <Textarea v-model="editForm.description" placeholder="Optional description" :rows="3" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="editDialogOpen = false">Cancel</Button>
          <Button :disabled="!editForm.name.trim()" @click="saveEdit">Save changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import {
  Plus, SquarePen, Trash2, X, ExternalLink, FileText,
  PlusCircle, Circle, CheckCircle2, ArrowUpDown, ArrowRight
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import * as templateService from '@/services/template.service'
import type { TemplateVersion } from '@/types/template.types'

interface TableRowData {
  id: string
  name: string
  createdAt: string
  activeVersion: TemplateVersion | undefined
  fieldCount: number
}

const router = useRouter()
const loading = ref(false)
const rows = ref<TableRowData[]>([])
const editDialogOpen = ref(false)
const editForm = ref({ id: '', name: '', description: '' })
const searchQuery = ref('')
const statusFilter = ref<'active' | 'draft' | null>(null)

// ── Filtered rows ───────────────────────────────────────────────────────────
const filteredRows = computed(() => {
  let result = rows.value
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(r => r.name.toLowerCase().includes(q))
  }
  if (statusFilter.value === 'active') {
    result = result.filter(r => r.activeVersion)
  } else if (statusFilter.value === 'draft') {
    result = result.filter(r => !r.activeVersion)
  }
  return result
})

// ── Status helpers ──────────────────────────────────────────────────────────
function getStatusIcon(row: TableRowData) {
  if (row.activeVersion) return CheckCircle2
  return Circle
}

function getStatusColor(row: TableRowData): string {
  if (row.activeVersion) return 'text-emerald-500'
  return 'text-muted-foreground'
}

function getStatusLabel(row: TableRowData): string {
  if (row.activeVersion) return 'Active'
  return 'Draft'
}

// ── Bulk selection ─────────────────────────────────────────────────────────────
// Use a plain array for Vue reactivity (Set mutations are not tracked by ref)

const selectedIds = ref<string[]>([])

const allSelected = computed(
  () => rows.value.length > 0 && selectedIds.value.length === rows.value.length
)
const someSelected = computed(
  () => selectedIds.value.length > 0 && selectedIds.value.length < rows.value.length
)

/** Value passed to the "select all" checkbox — reka-ui uses 'indeterminate' string */
const selectAllChecked = computed<boolean | 'indeterminate'>(() => {
  if (allSelected.value) return true
  if (someSelected.value) return 'indeterminate'
  return false
})

/** Click handler for the select-all div — toggles between all/none */
function onSelectAllClick(): void {
  selectedIds.value = selectedIds.value.length > 0 ? [] : rows.value.map(r => r.id)
}

function toggleRow(id: string): void {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

function isRowSelected(id: string): boolean {
  return selectedIds.value.includes(id)
}

async function handleBulkDelete(): Promise<void> {
  const count = selectedIds.value.length
  if (!window.confirm(`Delete ${count} template${count > 1 ? 's' : ''}?`)) return
  for (const id of selectedIds.value) {
    await templateService.deleteTemplate(id)
  }
  selectedIds.value = []
  toast.info('Delete not supported by the API yet')
  await loadTemplates()
}

// ── Data loading ───────────────────────────────────────────────────────────────

async function loadTemplates(): Promise<void> {
  loading.value = true
  try {
    await templateService.loadFromApi()
    const templates = templateService.getTemplates()
    rows.value = templates.map(t => {
      const active = t.activeVersionId ? templateService.getVersion(t.activeVersionId) : undefined
      return { id: t.id, name: t.name, createdAt: t.createdAt, activeVersion: active, fieldCount: active?.fields.length ?? 0 }
    })
  } finally {
    loading.value = false
  }
}

// ── Row actions ────────────────────────────────────────────────────────────────

function openEditDialog(row: TableRowData): void {
  const tmpl = templateService.getTemplate(row.id)
  if (!tmpl) return
  editForm.value = { id: tmpl.id, name: tmpl.name, description: tmpl.description ?? '' }
  editDialogOpen.value = true
}

async function saveEdit(): Promise<void> {
  await templateService.updateTemplate(editForm.value.id, {
    name: editForm.value.name.trim(),
    description: editForm.value.description.trim() || undefined,
  })
  editDialogOpen.value = false
  toast.success('Template updated')
  await loadTemplates()
}

async function handleDelete(id: string): Promise<void> {
  if (!window.confirm('Delete this template and all its versions?')) return
  await templateService.deleteTemplate(id)
  toast.info('Delete not supported by the API yet')
  await loadTemplates()
}

onMounted(() => loadTemplates())
</script>

<style scoped>
/* Selected row highlight */
tr[data-state="selected"] {
  background-color: oklch(0.97 0.01 250);
}
</style>
