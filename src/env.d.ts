/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_AUTH_USER: string
  readonly VITE_AUTH_PASS: string
  readonly VITE_OCR_API_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
