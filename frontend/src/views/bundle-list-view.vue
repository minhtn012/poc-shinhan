<template>
  <div class="w-full space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-foreground">Bundles</h1>
        <p class="text-sm text-primary/50 mt-0.5">Manage document template bundles</p>
      </div>
      <Button @click="router.push('/bundles/create')">
        <Plus class="size-4 mr-1.5" /> New Bundle
      </Button>
    </div>

    <!-- Skeleton -->
    <div v-if="loading" class="space-y-2">
      <Skeleton class="h-10 w-full" />
      <Skeleton v-for="i in 3" :key="i" class="h-14 w-full" />
    </div>

    <!-- Table -->
    <template v-else-if="bundles.length">
      <Card class="table-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Bundle Name</TableHead>
              <TableHead class="w-40">Templates</TableHead>
              <TableHead class="w-36">Created</TableHead>
              <TableHead class="w-12" />
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow
              v-for="bundle in bundles"
              :key="bundle.id"
              class="cursor-pointer"
              @click="router.push('/bundles/' + bundle.id)"
            >
              <TableCell>
                <div>
                  <p class="font-medium">{{ bundle.name }}</p>
                  <p v-if="bundle.description" class="text-xs text-muted-foreground">{{ bundle.description }}</p>
                </div>
              </TableCell>
              <TableCell class="text-sm">{{ bundle.templateCount }} templates</TableCell>
              <TableCell class="text-sm text-muted-foreground">{{ formatDate(bundle.createdAt) }}</TableCell>
              <TableCell @click.stop>
                <DropdownMenu>
                  <DropdownMenuTrigger as-child>
                    <Button variant="ghost" size="icon" class="size-8">
                      <MoreHorizontal class="size-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" class="w-36">
                    <DropdownMenuItem class="text-destructive focus:text-destructive" @click="handleDelete(bundle.id)">
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
        <FolderOpen class="size-7 text-muted-foreground" />
      </div>
      <h3 class="font-semibold text-base mb-1">No bundles yet</h3>
      <p class="text-sm text-muted-foreground mb-4">Create a bundle to group related templates</p>
      <Button @click="router.push('/bundles/create')">
        <Plus class="size-4 mr-1.5" /> Create Bundle
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { Plus, MoreHorizontal, Trash2, FolderOpen } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { bundleService } from '@/services/bundle.service'
import type { Bundle } from '@/types/bundle.types'

const router  = useRouter()
const loading = ref(false)
const bundles = ref<Bundle[]>([])

async function loadBundles(): Promise<void> {
  loading.value = true
  try {
    bundles.value = await bundleService.list()
  } catch (e: any) {
    toast.error(e.message ?? 'Failed to load bundles')
  } finally {
    loading.value = false
  }
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString()
}

async function handleDelete(id: string): Promise<void> {
  if (!window.confirm('Delete this bundle? Templates will NOT be deleted.')) return
  try {
    await bundleService.delete(id)
    toast.success('Bundle deleted')
    await loadBundles()
  } catch (e: any) {
    toast.error(e.message ?? 'Failed to delete')
  }
}

onMounted(loadBundles)
</script>
