<template>
  <div class="max-w-4xl space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold">OCR Jobs</h1>
        <p class="text-sm text-muted-foreground mt-0.5">Document processing history</p>
      </div>
      <Button @click="router.push('/ocr/new')">
        <Plus class="size-4 mr-1.5" /> New Job
      </Button>
    </div>

    <!-- Skeleton -->
    <div v-if="loading" class="space-y-2">
      <Skeleton class="h-10 w-full" />
      <Skeleton v-for="i in 4" :key="i" class="h-14 w-full" />
    </div>

    <!-- Table -->
    <template v-else-if="jobs.length">
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Template</TableHead>
              <TableHead class="w-36">Status</TableHead>
              <TableHead class="w-24 text-center">Fields</TableHead>
              <TableHead class="w-36">Created</TableHead>
              <TableHead class="w-12" />
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow
              v-for="job in jobs"
              :key="job.id"
              class="cursor-pointer"
              @click="router.push('/ocr/' + job.id)"
            >
              <TableCell class="font-medium">{{ job.templateName }}</TableCell>
              <TableCell>
                <Badge :variant="statusVariant(job.status)" class="capitalize">
                  <span
                    v-if="job.status === 'processing'"
                    class="size-1.5 rounded-full bg-current mr-1.5 animate-pulse inline-block"
                  />
                  {{ job.status }}
                </Badge>
              </TableCell>
              <TableCell class="text-center text-sm">{{ job.results.length }}</TableCell>
              <TableCell class="text-sm text-muted-foreground">{{ formatDate(job.createdAt) }}</TableCell>
              <TableCell @click.stop>
                <DropdownMenu>
                  <DropdownMenuTrigger as-child>
                    <Button variant="ghost" size="icon" class="size-8">
                      <MoreHorizontal class="size-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" class="w-36">
                    <DropdownMenuItem @click="router.push('/ocr/' + job.id)">
                      <Eye class="size-4 mr-2" /> View
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem class="text-destructive focus:text-destructive" @click="handleDelete(job.id)">
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
        <ScanText class="size-7 text-muted-foreground" />
      </div>
      <h3 class="font-semibold text-base mb-1">No OCR jobs yet</h3>
      <p class="text-sm text-muted-foreground mb-4">Upload a document to start processing</p>
      <Button @click="router.push('/ocr/new')">
        <Plus class="size-4 mr-1.5" /> Start First Job
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { Plus, MoreHorizontal, Eye, Trash2, ScanText } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import * as ocrService from '@/services/ocr.service'
import type { OcrJob, OcrJobStatus } from '@/types/ocr.types'

const router  = useRouter()
const loading = ref(false)
const jobs    = ref<OcrJob[]>([])

function loadJobs(): void {
  loading.value = true
  try {
    jobs.value = ocrService.getJobs().reverse()
  } finally {
    loading.value = false
  }
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString()
}

type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline'
function statusVariant(status: OcrJobStatus): BadgeVariant {
  const map: Record<OcrJobStatus, BadgeVariant> = {
    done:       'default',
    processing: 'secondary',
    error:      'destructive',
    pending:    'outline'
  }
  return map[status]
}

function handleDelete(id: string): void {
  if (!window.confirm('Delete this OCR job?')) return
  ocrService.deleteJob(id)
  toast.success('Job deleted')
  loadJobs()
}

onMounted(loadJobs)
</script>
