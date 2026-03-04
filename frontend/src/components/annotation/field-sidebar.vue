<template>
  <div class="flex flex-col h-full bg-background">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b shrink-0">
      <span class="text-sm font-semibold">Fields ({{ fields.length }})</span>
      <span class="text-xs text-muted-foreground">Draw on image to add</span>
    </div>

    <!-- List -->
    <div class="flex-1 overflow-y-auto p-2 space-y-1">
      <div
        v-for="field in fields"
        :key="field.id"
        :class="[
          'flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer transition-colors',
          field.id === selectedFieldId
            ? 'bg-primary/10 ring-1 ring-primary/30'
            : 'hover:bg-muted/60'
        ]"
        @click="emit('select', field.id)"
      >
        <span
          class="size-3 rounded-sm shrink-0 border border-black/10"
          :style="{ background: field.color }"
        />
        <input
          :value="field.name"
          class="flex-1 min-w-0 bg-transparent text-sm outline-none focus:ring-1 focus:ring-ring rounded px-1 -mx-1"
          @change="(e) => onNameChange(field.id, (e.target as HTMLInputElement).value)"
          @click.stop
        />
        <button
          class="size-6 flex items-center justify-center rounded text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors shrink-0"
          title="Delete field"
          @click.stop="emit('delete', field.id)"
        >
          <Trash2 class="size-3.5" />
        </button>
      </div>

      <!-- Empty state -->
      <div v-if="!fields.length" class="flex flex-col items-center justify-center py-10 text-center px-4">
        <MousePointer2 class="size-8 text-muted-foreground mb-2" />
        <p class="text-xs text-muted-foreground leading-relaxed">
          Draw rectangles on the image to define fields
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Trash2, MousePointer2 } from 'lucide-vue-next'
import type { TemplateField } from '@/types/template.types'

const props = defineProps<{
  fields: TemplateField[]
  selectedFieldId: string | null
}>()

const emit = defineEmits<{
  'update:fields': [fields: TemplateField[]]
  'select': [id: string]
  'delete': [id: string]
}>()

function onNameChange(id: string, name: string): void {
  emit('update:fields', props.fields.map(f => f.id === id ? { ...f, name } : f))
}
</script>
