<template>
  <Card>
    <CardHeader>
      <div class="flex items-center justify-between">
        <div>
          <span class="text-sm text-muted-foreground">Document {{ index }}</span>
          <h3 class="font-semibold">{{ job.templateName }}</h3>
        </div>
        <Badge :variant="job.status === 'done' ? 'default' : 'secondary'">
          {{ job.status }}
        </Badge>
      </div>
    </CardHeader>
    <CardContent>
      <div class="flex gap-4">
        <!-- Image thumbnail -->
        <div class="w-48 shrink-0">
          <img
            v-if="job.imageUrl"
            :src="job.imageUrl"
            :alt="job.templateName"
            class="rounded border w-full object-contain cursor-pointer hover:opacity-80 transition-opacity"
            @click="$router.push(`/ocr/${job.id}`)"
          />
          <div v-else class="h-32 rounded border bg-muted flex items-center justify-center">
            <span class="text-xs text-muted-foreground">No image</span>
          </div>
        </div>
        <!-- Results table -->
        <div class="flex-1 min-h-0 border rounded-lg overflow-hidden">
          <ResultsTable
            :results="job.results"
            :hovered-field-id="null"
            @value-change="(fieldId: string, value: string) => emit('valueChange', job.id, fieldId, value)"
          />
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import ResultsTable from '@/components/ocr/results-table.vue'
import type { OcrJob } from '@/types/ocr.types'

defineProps<{
  job: OcrJob
  index: number
}>()

const emit = defineEmits<{
  valueChange: [jobId: string, fieldId: string, value: string]
}>()
</script>
