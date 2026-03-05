<template>
  <div class="w-full space-y-6">
    <!-- Breadcrumb -->
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink as-child>
            <RouterLink to="/bundles">Bundles</RouterLink>
          </BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          <BreadcrumbPage>{{ bundle?.name ?? 'Loading…' }}</BreadcrumbPage>
        </BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>

    <!-- Loading -->
    <div v-if="loading" class="space-y-2">
      <Skeleton class="h-10 w-64" />
      <Skeleton class="h-48 w-full" />
    </div>

    <!-- Not found -->
    <div v-else-if="!bundle" class="flex flex-col items-center justify-center py-20 text-center">
      <p class="text-muted-foreground mb-4">Bundle not found</p>
      <Button variant="outline" @click="router.push('/bundles')">← Back</Button>
    </div>

    <template v-else>
      <!-- Header -->
      <div class="flex items-start justify-between gap-4">
        <div>
          <h1 class="text-xl font-bold text-foreground">{{ bundle.name }}</h1>
          <p v-if="bundle.description" class="text-sm text-muted-foreground mt-0.5">
            {{ bundle.description }}
          </p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <Button size="sm" variant="outline" @click="openEditDialog">
            <Pencil class="size-3.5 mr-1.5" /> Edit
          </Button>
          <Button variant="outline" size="sm" @click="router.push('/bundles')">← Back</Button>
        </div>
      </div>

      <!-- Templates in bundle -->
      <div class="space-y-2">
        <h2 class="text-sm font-medium text-muted-foreground uppercase tracking-wide">
          Templates ({{ bundle.items.length }})
        </h2>
        <Card v-if="bundle.items.length" class="table-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead class="w-12">#</TableHead>
                <TableHead>Template Name</TableHead>
                <TableHead class="w-32">Active Version</TableHead>
                <TableHead class="w-20 text-center">View</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="item in bundle.items" :key="item.id">
                <TableCell class="text-muted-foreground text-sm">{{ item.sortOrder + 1 }}</TableCell>
                <TableCell class="font-medium">{{ item.templateName }}</TableCell>
                <TableCell class="text-sm text-muted-foreground">
                  {{ item.activeVersionId ? '✓' : '—' }}
                </TableCell>
                <TableCell class="text-center">
                  <Button variant="ghost" size="icon" class="size-8" @click="router.push('/templates/' + item.templateId)">
                    <Eye class="size-4" />
                  </Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </Card>
        <div v-else class="py-8 text-center text-sm text-muted-foreground">
          No templates in this bundle
        </div>
      </div>
    </template>

    <!-- Edit dialog -->
    <Dialog v-model:open="editDialogOpen">
      <DialogContent class="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Edit Bundle</DialogTitle>
        </DialogHeader>
        <div class="space-y-4 py-2">
          <div class="space-y-1.5">
            <Label>Name <span class="text-destructive">*</span></Label>
            <Input v-model="editForm.name" placeholder="Bundle name" />
          </div>
          <div class="space-y-1.5">
            <Label>Description</Label>
            <Textarea v-model="editForm.description" placeholder="Optional" :rows="2" />
          </div>
          <div class="space-y-1.5">
            <Label>Templates</Label>
            <div v-if="allTemplates.length" class="border rounded-lg divide-y max-h-48 overflow-y-auto">
              <label
                v-for="tmpl in allTemplates"
                :key="tmpl.id"
                class="flex items-center gap-3 px-4 py-2.5 hover:bg-muted/40 cursor-pointer"
              >
                <input type="checkbox" :value="tmpl.id" v-model="editForm.templateIds" class="rounded" />
                <span class="text-sm">{{ tmpl.name }}</span>
              </label>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="editDialogOpen = false">Cancel</Button>
          <Button :disabled="!editForm.name.trim()" @click="saveEdit">Save</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { Pencil, Eye } from 'lucide-vue-next'
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
import { bundleService } from '@/services/bundle.service'
import { templateService } from '@/services/template.service'
import type { BundleDetail } from '@/types/bundle.types'
import type { Template } from '@/types/template.types'

const route  = useRoute()
const router = useRouter()

const loading        = ref(true)
const bundle         = ref<BundleDetail | null>(null)
const allTemplates   = ref<Template[]>([])
const editDialogOpen = ref(false)
const editForm       = ref({ name: '', description: '', templateIds: [] as string[] })

async function load(): Promise<void> {
  loading.value = true
  try {
    const id = route.params.id as string
    bundle.value = await bundleService.get(id)
  } catch {
    bundle.value = null
  } finally {
    loading.value = false
  }
}

function openEditDialog(): void {
  if (!bundle.value) return
  editForm.value = {
    name: bundle.value.name,
    description: bundle.value.description ?? '',
    templateIds: bundle.value.items.map(i => i.templateId),
  }
  editDialogOpen.value = true
}

async function saveEdit(): Promise<void> {
  if (!bundle.value) return
  try {
    await bundleService.update(bundle.value.id, {
      name: editForm.value.name.trim(),
      description: editForm.value.description.trim() || undefined,
      templateIds: editForm.value.templateIds,
    })
    editDialogOpen.value = false
    toast.success('Bundle updated')
    await load()
  } catch (e: any) {
    toast.error(e.message ?? 'Failed to update')
  }
}

onMounted(async () => {
  await load()
  try {
    allTemplates.value = await templateService.list()
  } catch {
    // Optional
  }
})
</script>
