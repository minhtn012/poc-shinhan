<template>
  <div ref="containerRef" class="annotation-canvas" />
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import type { TemplateField } from '@/types/template.types'
import { useAnnotation } from '@/composables/use-annotation'

const props = defineProps<{
  imageUrl: string | null
  modelValue: TemplateField[]
  readonly?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [fields: TemplateField[]]
  'fieldSelected': [id: string | null]
}>()

const containerRef = ref<HTMLDivElement | null>(null)
const annotation = useAnnotation(containerRef, {
  initialFields: props.modelValue,
  readonly: props.readonly
})

// Keyboard delete/escape handlers (skip in readonly mode)
function handleKeydown(e: KeyboardEvent): void {
  if (props.readonly) return
  if (e.key === 'Escape') {
    annotation.selectedFieldId.value = null
    annotation.render()
    emit('fieldSelected', null)
  }
  if ((e.key === 'Delete' || e.key === 'Backspace') && annotation.selectedFieldId.value) {
    annotation.deleteField(annotation.selectedFieldId.value)
    emit('update:modelValue', annotation.fields.value)
    emit('fieldSelected', null)
  }
}

onMounted(async () => {
  window.addEventListener('keydown', handleKeydown)
  if (props.imageUrl) {
    await annotation.initCanvas(props.imageUrl)
    if (!props.readonly) emitFields()
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

watch(
  () => props.imageUrl,
  async (url) => {
    if (!url) return
    await annotation.initCanvas(url)
    if (!props.readonly) emitFields()
  }
)

// Sync incoming modelValue → internal fields (when parent resets)
watch(
  () => props.modelValue,
  (incoming) => {
    const currentIds = annotation.fields.value.map(f => f.id).join(',')
    const incomingIds = incoming.map(f => f.id).join(',')
    if (currentIds !== incomingIds) {
      annotation.fields.value = [...incoming]
      annotation.render()
    }
  }
)

// Sync internal fields → parent (skip in readonly)
watch(
  annotation.fields,
  (newFields) => {
    if (!props.readonly) emit('update:modelValue', newFields)
  }
)

watch(
  annotation.selectedFieldId,
  (id) => {
    if (!props.readonly) emit('fieldSelected', id)
  }
)

function emitFields(): void {
  emit('update:modelValue', annotation.fields.value)
}
</script>

<style scoped>
.annotation-canvas {
  width: 100%;
  height: 100%;
  min-height: 400px;
  background: #1a1a2e;
  border-radius: 4px;
  overflow: hidden;
}
</style>
