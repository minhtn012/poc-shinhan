<template>
  <router-view />
  <Toaster position="bottom-right" :duration="3000" rich-colors />
</template>

<script setup lang="ts">
import { Toaster } from '@/components/ui/sonner'
</script>
