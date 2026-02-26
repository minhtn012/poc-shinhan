<template>
  <SidebarProvider>
    <Sidebar collapsible="icon">
      <!-- Logo -->
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" class="pointer-events-none select-none">
              <div class="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shrink-0">
                <ScanText class="size-4" />
              </div>
              <div class="flex flex-col gap-0.5 leading-none">
                <span class="font-semibold text-sm">OCR System</span>
                <span class="text-xs text-sidebar-foreground/60">Document AI</span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <!-- Navigation -->
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem v-for="item in navItems" :key="item.to">
                <SidebarMenuButton
                  as-child
                  :is-active="isActive(item.to)"
                  :tooltip="item.label"
                >
                  <RouterLink :to="item.to">
                    <component :is="item.icon" />
                    <span>{{ item.label }}</span>
                  </RouterLink>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <!-- Footer: logout -->
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton :tooltip="'Logout'" @click="handleLogout">
              <LogOut />
              <span>Logout</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>

    <!-- Main content -->
    <SidebarInset class="h-screen overflow-hidden">
      <!-- Top bar with trigger -->
      <header class="flex h-14 shrink-0 items-center gap-2 border-b border-primary/10 px-6 bg-white/80 backdrop-blur-sm">
        <SidebarTrigger class="-ml-1 text-primary/60 hover:text-primary transition-colors" />
        <Separator orientation="vertical" class="h-4 bg-primary/15" />
      </header>

      <div class="flex-1 overflow-y-auto content-area p-6">
        <router-view />
      </div>
    </SidebarInset>
  </SidebarProvider>
</template>

<script setup lang="ts">
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { Files, ScanText, LogOut } from 'lucide-vue-next'
import {
  Sidebar, SidebarContent, SidebarFooter, SidebarGroup,
  SidebarGroupContent, SidebarGroupLabel, SidebarHeader,
  SidebarInset, SidebarMenu, SidebarMenuButton, SidebarMenuItem,
  SidebarProvider, SidebarRail, SidebarTrigger,
} from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import { useAuthStore } from '@/stores/auth.store'

const navItems = [
  { to: '/templates', label: 'Templates', icon: Files },
  { to: '/ocr',       label: 'OCR Jobs',  icon: ScanText },
]

const route     = useRoute()
const router    = useRouter()
const authStore = useAuthStore()

function isActive(path: string): boolean {
  return route.path.startsWith(path)
}

function handleLogout(): void {
  authStore.logout()
  router.push('/login')
}
</script>
