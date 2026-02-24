import localforage from 'localforage'

const store = localforage.createInstance({ name: 'ocr-images' })

export function useImageStore() {
  async function saveImage(key: string, blob: Blob): Promise<void> {
    await store.setItem(key, blob)
  }

  async function getImage(key: string): Promise<Blob | null> {
    return store.getItem<Blob>(key)
  }

  async function getImageUrl(key: string): Promise<string | null> {
    const blob = await getImage(key)
    if (!blob) return null
    return URL.createObjectURL(blob)
  }

  async function removeImage(key: string): Promise<void> {
    await store.removeItem(key)
  }

  return { saveImage, getImage, getImageUrl, removeImage }
}
