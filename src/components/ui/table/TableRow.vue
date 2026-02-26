<script setup lang="ts">
import type { HTMLAttributes } from "vue"
import { cn } from "@/lib/utils"

const props = defineProps<{
  class?: HTMLAttributes["class"]
}>()
</script>

<template>
  <tr
    data-slot="table-row"
    :class="cn('hover:bg-primary/[0.03] data-[state=selected]:bg-primary/[0.06] border-b border-black/[0.04] transition-colors duration-150', props.class)"
  >
    <slot />
  </tr>
</template>
