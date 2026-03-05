<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-semibold">New Bundle</h1>
      <Button variant="outline" size="sm" @click="router.push('/bundles')">← Back</Button>
    </div>

    <Card>
      <CardContent class="pt-6 space-y-5">
        <!-- Name -->
        <div class="space-y-1.5">
          <Label>Bundle Name <span class="text-destructive">*</span></Label>
          <Input v-model="name" placeholder="e.g. Loan Application Documents" />
        </div>

        <!-- Description -->
        <div class="space-y-1.5">
          <Label>Description</Label>
          <Textarea v-model="description" placeholder="Optional description" :rows="2" />
        </div>

        <!-- Template selector -->
        <div class="space-y-1.5">
          <Label>Select Templates</Label>
          <div v-if="templatesLoading" class="space-y-2">
            <Skeleton class="h-10 w-full" />
          </div>
          <div v-else-if="allTemplates.length" class="border rounded-lg divide-y max-h-64 overflow-y-auto">
            <label
              v-for="tmpl in allTemplates"
              :key="tmpl.id"
              class="flex items-center gap-3 px-4 py-3 hover:bg-muted/40 cursor-pointer"
            >
              <input
                type="checkbox"
                :value="tmpl.id"
                v-model="selectedIds"
                class="rounded border-gray-300"
              />
              <span class="text-sm font-medium">{{ tmpl.name }}</span>
            </label>
          </div>
          <p v-else class="text-sm text-muted-foreground">No templates available. Create one first.</p>
          <p v-if="selectedIds.length" class="text-xs text-muted-foreground">
            {{ selectedIds.length }} template(s) selected
          </p>
        </div>

        <Button class="w-full" :disabled="!name.trim() || saving" @click="handleCreate">
          <LoaderCircle v-if="saving" class="size-4 mr-2 animate-spin" />
          Create Bundle
        </Button>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { LoaderCircle } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
import { bundleService } from '@/services/bundle.service'
import { templateService } from '@/services/template.service'
import type { Template } from '@/types/template.types'

const router = useRouter()

const name        = ref('')
const description = ref('')
const selectedIds = ref<string[]>([])
const saving      = ref(false)

const allTemplates    = ref<Template[]>([])
const templatesLoading = ref(true)

onMounted(async () => {
  try {
    allTemplates.value = await templateService.list()
  } finally {
    templatesLoading.value = false
  }
})

async function handleCreate(): Promise<void> {
  saving.value = true
  try {
    await bundleService.create({
      name: name.value.trim(),
      description: description.value.trim() || undefined,
      templateIds: selectedIds.value,
    })
    toast.success('Bundle created')
    router.push('/bundles')
  } catch (e: any) {
    toast.error(e.message ?? 'Failed to create bundle')
  } finally {
    saving.value = false
  }
}
</script>
