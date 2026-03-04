<template>
  <Badge :variant="status === 'active' ? 'default' : 'secondary'">
    {{ status }}
  </Badge>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
defineProps<{ status: 'active' | 'inactive' }>()
</script>
