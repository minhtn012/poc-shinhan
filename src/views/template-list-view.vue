<template>
  <div class="w-full space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-foreground">Templates</h1>
        <p class="text-sm text-primary/50 mt-0.5">Manage your OCR document templates</p>
      </div>
      <Button @click="router.push('/templates/create')">
        <Plus class="size-4 mr-1.5" /> New Template
      </Button>
    </div>

    <!-- Skeleton -->
    <div v-if="loading" class="space-y-2">
      <Skeleton class="h-10 w-full" />
      <Skeleton v-for="i in 4" :key="i" class="h-14 w-full" />
    </div>

    <!-- Table -->
    <template v-else-if="rows.length">
      <Card class="table-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Template Name</TableHead>
              <TableHead class="w-40">Active Version</TableHead>
              <TableHead class="w-24 text-center">Fields</TableHead>
              <TableHead class="w-36">Created</TableHead>
              <TableHead class="w-12" />
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow
              v-for="row in rows"
              :key="row.id"
              class="cursor-pointer"
              @click="router.push('/templates/' + row.id)"
            >
              <TableCell class="font-medium">{{ row.name }}</TableCell>
              <TableCell>
                <div v-if="row.activeVersion" class="flex items-center gap-2">
                  <span class="text-sm">{{ row.activeVersion.version }}</span>
                  <VersionBadge status="active" />
                </div>
                <span v-else class="text-muted-foreground text-sm">—</span>
              </TableCell>
              <TableCell class="text-center text-sm">{{ row.fieldCount }}</TableCell>
              <TableCell class="text-sm text-muted-foreground">{{ formatDate(row.createdAt) }}</TableCell>
              <TableCell @click.stop>
                <DropdownMenu>
                  <DropdownMenuTrigger as-child>
                    <Button variant="ghost" size="icon" class="size-8">
                      <MoreHorizontal class="size-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" class="w-40">
                    <DropdownMenuItem @click="openEditDialog(row)">
                      <Pencil class="size-4 mr-2" /> Edit
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem class="text-destructive focus:text-destructive" @click="handleDelete(row.id)">
                      <Trash2 class="size-4 mr-2" /> Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </Card>
    </template>

    <!-- Empty state -->
    <div v-else class="flex flex-col items-center justify-center py-20 text-center">
      <div class="size-14 rounded-full bg-muted flex items-center justify-center mb-4">
        <Files class="size-7 text-muted-foreground" />
      </div>
      <h3 class="font-semibold text-base mb-1">No templates yet</h3>
      <p class="text-sm text-muted-foreground mb-4">Create your first template to get started</p>
      <Button @click="router.push('/templates/create')">
        <Plus class="size-4 mr-1.5" /> Create Template
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { Plus, MoreHorizontal, Pencil, Trash2, Files } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import VersionBadge from '@/components/common/version-badge.vue'
import * as templateService from '@/services/template.service'
import type { TemplateVersion } from '@/types/template.types'

interface TableRow {
  id: string
  name: string
  createdAt: string
  activeVersion: TemplateVersion | undefined
  fieldCount: number
}

const router = useRouter()
const loading = ref(false)
const rows = ref<TableRow[]>([])
const editDialogOpen = ref(false)
const editForm = ref({ id: '', name: '', description: '' })

function loadTemplates(): void {
  loading.value = true
  try {
    const templates = templateService.getTemplates()
    rows.value = templates.map(t => {
      const active = t.activeVersionId ? templateService.getVersion(t.activeVersionId) : undefined
      return { id: t.id, name: t.name, createdAt: t.createdAt, activeVersion: active, fieldCount: active?.fields.length ?? 0 }
    })
  } finally {
    loading.value = false
  }
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString()
}

function openEditDialog(row: TableRow): void {
  const tmpl = templateService.getTemplate(row.id)
  if (!tmpl) return
  editForm.value = { id: tmpl.id, name: tmpl.name, description: tmpl.description ?? '' }
  editDialogOpen.value = true
}

function saveEdit(): void {
  templateService.updateTemplate(editForm.value.id, {
    name: editForm.value.name.trim(),
    description: editForm.value.description.trim() || undefined
  })
  editDialogOpen.value = false
  toast.success('Template updated')
  loadTemplates()
}

function handleDelete(id: string): void {
  if (!window.confirm('Delete this template and all its versions?')) return
  templateService.deleteTemplate(id)
  toast.success('Template deleted')
  loadTemplates()
}

onMounted(loadTemplates)
</script>
