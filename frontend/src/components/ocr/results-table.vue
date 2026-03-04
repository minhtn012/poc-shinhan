<template>
  <div class="h-full flex flex-col overflow-hidden bg-white">
    <!-- Table header -->
    <div class="px-5 py-3.5 border-b border-black/[0.04] shrink-0">
      <h3 class="text-sm font-semibold">Extracted Fields</h3>
      <p class="text-xs text-muted-foreground mt-0.5">
        {{ results.length }} field{{ results.length !== 1 ? 's' : '' }} · click a row to highlight on image
      </p>
    </div>

    <!-- Scrollable body -->
    <div class="flex-1 overflow-y-auto">
      <table class="w-full text-sm">
        <thead class="sticky top-0 bg-primary/[0.04] backdrop-blur-sm z-10">
          <tr>
            <th class="text-left px-5 py-2.5 text-xs font-semibold uppercase tracking-wider text-primary/60 w-32">Field</th>
            <th class="text-left px-5 py-2.5 text-xs font-semibold uppercase tracking-wider text-primary/60">Value</th>
            <th class="text-center px-3 py-2.5 text-xs font-semibold uppercase tracking-wider text-primary/60 w-20">Conf.</th>
            <th class="text-center px-3 py-2.5 text-xs font-semibold uppercase tracking-wider text-primary/60 w-12">Edit</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in results"
            :key="row.fieldId"
            :class="[
              'border-b border-black/[0.04] transition-colors cursor-pointer',
              row.fieldId === hoveredFieldId
                ? 'bg-primary/8 border-primary/20'
                : 'hover:bg-muted/50 border-transparent'
            ]"
            @mouseenter="emit('hover', row.fieldId)"
            @mouseleave="emit('hover', null)"
            @click="emit('hover', row.fieldId)"
          >
            <!-- Field name with color indicator -->
            <td class="px-4 py-2.5">
              <span class="font-medium text-xs leading-tight">{{ row.fieldName }}</span>
            </td>

            <!-- Editable value -->
            <td class="px-4 py-2">
              <input
                :value="editingFieldId === row.fieldId ? editingValue : row.value"
                class="w-full text-sm bg-transparent border border-black/[0.06] outline-none focus:border-primary/30 focus:ring-2 focus:ring-primary/10 rounded-md px-2 py-1 -mx-1 transition-colors hover:bg-muted/30 cursor-text"
                @focus="onFocus(row.fieldId, row.value)"
                @input="onInput"
                @blur="onBlur(row.fieldId)"
                @click.stop
                @mousedown.stop
              />
            </td>

            <!-- Confidence badge -->
            <td class="px-3 py-2.5 text-center">
              <span :class="['inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', confidenceClass(row.confidence)]">
                {{ (row.confidence * 100).toFixed(0) }}%
              </span>
            </td>

            <!-- Edited indicator -->
            <td class="px-3 py-2.5 text-center">
              <CheckCircle2 v-if="row.edited" class="size-3.5 text-emerald-600 mx-auto" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { CheckCircle2 } from 'lucide-vue-next'
import type { OcrFieldResult } from '@/types/ocr.types'

defineProps<{
  results: OcrFieldResult[]
  hoveredFieldId: string | null
}>()

const emit = defineEmits<{
  hover: [fieldId: string | null]
  valueChange: [fieldId: string, value: string]
}>()

// Track the field being actively edited to prevent hover re-renders from resetting input
const editingFieldId = ref<string | null>(null)
const editingValue = ref('')

function onFocus(fieldId: string, currentValue: string): void {
  editingFieldId.value = fieldId
  editingValue.value = currentValue
}

function onInput(e: Event): void {
  editingValue.value = (e.target as HTMLInputElement).value
}

function onBlur(fieldId: string): void {
  if (editingFieldId.value === fieldId && editingValue.value !== '') {
    emit('valueChange', fieldId, editingValue.value)
  }
  editingFieldId.value = null
}

function confidenceClass(conf: number): string {
  if (conf >= 0.9) return 'bg-emerald-100 text-emerald-700'
  if (conf >= 0.7) return 'bg-amber-100 text-amber-700'
  return 'bg-red-100 text-red-700'
}
</script>
