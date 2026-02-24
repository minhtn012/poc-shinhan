<template>
  <div class="max-w-4xl space-y-6">
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

    <!-- Not found -->
    <Alert v-if="!version" variant="destructive">
      <AlertTitle>Version not found</AlertTitle>
    </Alert>

    <template v-else>
      <!-- Header -->
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <h1 class="text-xl font-semibold font-mono">{{ version.version }}</h1>
          <VersionBadge :status="version.status" />
        </div>
        <div class="flex gap-2">
          <Button size="sm" @click="cloneToNew">
            <Copy class="size-3.5 mr-1.5" /> New Version
          </Button>
          <Button variant="outline" size="sm" @click="router.push('/templates/' + templateId)">
            ← Back
          </Button>
        </div>
      </div>

      <!-- Canvas -->
      <div v-if="imageUrl" class="rounded-lg border overflow-hidden">
        <AnnotationCanvas :image-url="imageUrl" :model-value="version.fields" readonly />
      </div>
      <div v-else class="space-y-2">
        <Skeleton class="h-64 w-full rounded-lg" />
      </div>

      <!-- Fields table -->
      <div class="space-y-2">
        <h2 class="text-sm font-medium text-muted-foreground uppercase tracking-wide">
          Fields ({{ version.fields.length }})
        </h2>
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead class="w-14">Color</TableHead>
                <TableHead>Field Name</TableHead>
                <TableHead>Bounding Box (x, y, w, h)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="field in version.fields" :key="field.id">
                <TableCell>
                  <span
                    class="inline-flex size-5 rounded-md border border-black/10"
                    :style="{ background: field.color }"
                  />
                </TableCell>
                <TableCell class="font-medium text-sm">{{ field.name }}</TableCell>
                <TableCell class="font-mono text-xs text-muted-foreground">
                  {{ formatBBox(field.bbox) }}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </Card>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { Copy } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
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
import type { TemplateVersion, NormalizedBBox } from '@/types/template.types'

const route       = useRoute()
const router      = useRouter()
const imageStore  = useImageStore()

const templateId   = route.params.id as string
const versionId    = route.params.vid as string
const version      = ref<TemplateVersion | undefined>()
const templateName = ref('')
const imageUrl     = ref<string | null>(null)
let objectUrl: string | null = null

function formatBBox(b: NormalizedBBox): string {
  return `${b.x.toFixed(3)}, ${b.y.toFixed(3)}, ${b.w.toFixed(3)}, ${b.h.toFixed(3)}`
}

async function load(): Promise<void> {
  version.value = templateService.getVersion(versionId)
  const tmpl = templateService.getTemplate(templateId)
  templateName.value = tmpl?.name ?? ''

  if (version.value?.imageKey) {
    const blob = await imageStore.getImage(version.value.imageKey)
    if (blob) {
      objectUrl = URL.createObjectURL(blob)
      imageUrl.value = objectUrl
    }
  }
}

function cloneToNew(): void {
  router.push(`/templates/create?from=${versionId}&templateId=${templateId}`)
}

onMounted(load)
</script>
