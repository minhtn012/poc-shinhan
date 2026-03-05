<template>
  <div class="w-full space-y-6">
    <!-- Breadcrumb -->
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink as-child>
            <RouterLink to="/templates">Templates</RouterLink>
          </BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          <BreadcrumbPage>{{ detail?.name ?? 'Loading…' }}</BreadcrumbPage>
        </BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>

    <!-- Loading -->
    <div v-if="loading" class="space-y-2">
      <Skeleton class="h-10 w-64" />
      <Skeleton class="h-48 w-full" />
    </div>

    <!-- Not found -->
    <div v-else-if="!detail" class="flex flex-col items-center justify-center py-20 text-center">
      <p class="text-muted-foreground mb-4">Template not found</p>
      <Button variant="outline" @click="router.push('/templates')">← Back to Templates</Button>
    </div>

    <template v-else>
      <!-- Header -->
      <div class="flex items-start justify-between gap-4">
        <div>
          <h1 class="text-xl font-bold text-foreground">{{ detail.name }}</h1>
          <p v-if="detail.description" class="text-sm text-muted-foreground mt-0.5">
            {{ detail.description }}
          </p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <Button size="sm" :disabled="!detail.versions.length" @click="updateVersion">
            Update Version
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger as-child>
              <Button variant="ghost" size="icon" class="size-8">
                <MoreHorizontal class="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" class="w-44">
              <DropdownMenuItem @click="openEditDialog">
                <Pencil class="size-4 mr-2" /> Edit Template
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <Button variant="outline" size="sm" @click="router.push('/templates')">
            ← Back
          </Button>
        </div>
      </div>

      <!-- Versions table -->
      <div class="space-y-2">
        <h2 class="text-sm font-medium text-muted-foreground uppercase tracking-wide">Versions</h2>
        <Card v-if="detail.versions.length" class="table-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Version</TableHead>
                <TableHead class="w-24">Status</TableHead>
                <TableHead class="w-20 text-center">Fields</TableHead>
                <TableHead class="w-32">Created</TableHead>
                <TableHead class="w-20 text-center">View</TableHead>
                <TableHead class="w-28 text-center">Active</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="ver in detail.versions" :key="ver.id">
                <TableCell class="font-mono text-sm font-medium">{{ ver.version }}</TableCell>
                <TableCell><VersionBadge :status="ver.status" /></TableCell>
                <TableCell class="text-center text-sm">{{ ver.fields.length }}</TableCell>
                <TableCell class="text-sm text-muted-foreground">{{ formatDate(ver.createdAt) }}</TableCell>
                <TableCell class="text-center">
                  <Button variant="ghost" size="icon" class="size-8" @click="viewVersion(ver.id)">
                    <Eye class="size-4" />
                  </Button>
                </TableCell>
                <TableCell class="text-center">
                  <Button
                    variant="ghost"
                    size="sm"
                    :disabled="ver.status === 'active'"
                    class="text-xs gap-1.5"
                    @click="handleActivate(ver.id)"
                  >
                    <CheckCircle2 class="size-3.5" />
                    {{ ver.status === 'active' ? 'Active ✓' : 'Set Active' }}
                  </Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </Card>

        <div v-else class="flex flex-col items-center justify-center py-12 text-center">
          <p class="text-sm text-muted-foreground">No versions yet</p>
        </div>
      </div>
    </template>

    <!-- Edit template metadata dialog -->
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
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { Pencil, MoreHorizontal, Eye, CheckCircle2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Breadcrumb, BreadcrumbItem, BreadcrumbLink,
  BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator
} from '@/components/ui/breadcrumb'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import VersionBadge from '@/components/common/version-badge.vue'
import { templateService } from '@/services/template.service'
import type { TemplateVersion } from '@/types/template.types'

interface TemplateDetail {
  id: string
  name: string
  description?: string | null
  activeVersionId: string | null
  versions: TemplateVersion[]
  createdAt: string
}

const route  = useRoute()
const router = useRouter()

const loading        = ref(true)
const detail         = ref<TemplateDetail | null>(null)
const editDialogOpen = ref(false)
const editForm       = ref({ name: '', description: '' })

async function load(): Promise<void> {
  loading.value = true
  try {
    const id = route.params.id as string
    detail.value = await templateService.get(id)
  } catch {
    detail.value = null
  } finally {
    loading.value = false
  }
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString()
}

function updateVersion(): void {
  if (!detail.value) return
  const baseId = detail.value.activeVersionId ?? detail.value.versions[0]?.id
  if (!baseId) return
  router.push(`/templates/create?from=${baseId}&templateId=${route.params.id}`)
}

function openEditDialog(): void {
  if (!detail.value) return
  editForm.value = { name: detail.value.name, description: detail.value.description ?? '' }
  editDialogOpen.value = true
}

async function saveEdit(): Promise<void> {
  if (!detail.value) return
  try {
    await templateService.update(detail.value.id, {
      name: editForm.value.name.trim(),
      description: editForm.value.description.trim() || undefined
    })
    editDialogOpen.value = false
    toast.success('Template updated')
    await load()
  } catch (e: any) {
    toast.error(e.message ?? 'Failed to update')
  }
}

async function handleActivate(versionId: string): Promise<void> {
  try {
    await templateService.activateVersion(versionId)
    toast.success('Version activated')
    await load()
  } catch (e: any) {
    toast.error(e.message ?? 'Failed to activate')
  }
}

function viewVersion(versionId: string): void {
  router.push(`/templates/${route.params.id}/versions/${versionId}`)
}

onMounted(load)
</script>
