<template>
  <div class="min-h-screen flex items-center justify-center bg-muted/40 px-4">
    <div class="w-full max-w-sm">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center size-12 rounded-xl bg-primary text-primary-foreground mb-4">
          <ScanText class="size-6" />
        </div>
        <h1 class="text-2xl font-bold tracking-tight">OCR System</h1>
        <p class="text-muted-foreground text-sm mt-1">Sign in to your account</p>
      </div>

      <!-- Card -->
      <Card>
        <CardContent class="pt-6">
          <form class="space-y-4" @submit.prevent="handleLogin">
            <div class="space-y-1.5">
              <Label for="username">Username</Label>
              <Input
                id="username"
                v-model="form.username"
                placeholder="Enter username"
                autocomplete="username"
                :class="errors.username ? 'border-destructive focus-visible:ring-destructive' : ''"
              />
              <p v-if="errors.username" class="text-xs text-destructive">{{ errors.username }}</p>
            </div>

            <div class="space-y-1.5">
              <Label for="password">Password</Label>
              <div class="relative">
                <Input
                  id="password"
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="Enter password"
                  autocomplete="current-password"
                  class="pr-10"
                  :class="errors.password ? 'border-destructive focus-visible:ring-destructive' : ''"
                  @keyup.enter="handleLogin"
                />
                <button
                  type="button"
                  tabindex="-1"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  @click="showPassword = !showPassword"
                >
                  <Eye v-if="!showPassword" class="size-4" />
                  <EyeOff v-else class="size-4" />
                </button>
              </div>
              <p v-if="errors.password" class="text-xs text-destructive">{{ errors.password }}</p>
            </div>

            <p v-if="loginError" class="text-sm text-destructive text-center font-medium">
              {{ loginError }}
            </p>

            <Button type="submit" class="w-full" :disabled="loading">
              <LoaderCircle v-if="loading" class="size-4 animate-spin mr-2" />
              Sign In
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ScanText, Eye, EyeOff, LoaderCircle } from 'lucide-vue-next'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/auth.store'

const router    = useRouter()
const authStore = useAuthStore()

const loading      = ref(false)
const showPassword = ref(false)
const loginError   = ref('')
const form         = reactive({ username: '', password: '' })
const errors       = reactive({ username: '', password: '' })

function validate(): boolean {
  errors.username = form.username.trim() ? '' : 'Username is required'
  errors.password = form.password       ? '' : 'Password is required'
  return !errors.username && !errors.password
}

async function handleLogin(): Promise<void> {
  loginError.value = ''
  if (!validate()) return

  loading.value = true
  try {
    const ok = authStore.login(form.username, form.password)
    if (ok) {
      router.push('/templates')
    } else {
      loginError.value = 'Invalid username or password'
    }
  } finally {
    loading.value = false
  }
}
</script>
