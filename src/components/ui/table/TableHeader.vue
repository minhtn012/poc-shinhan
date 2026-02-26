<script setup lang="ts">
import type { HTMLAttributes } from "vue"
import { cn } from "@/lib/utils"

const props = defineProps<{
  class?: HTMLAttributes["class"]
}>()
</script>

<template>
  <thead
    data-slot="table-header"
    :class="cn('bg-primary/[0.04] [&_tr]:border-b [&_tr]:border-primary/8', props.class)"
  >
    <slot />
  </thead>
</template>
