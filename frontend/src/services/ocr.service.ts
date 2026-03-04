import type { OcrJob, OcrJobStatus, OcrFieldResult } from '@/types/ocr.types'

const JOBS_KEY = 'ocr:jobs'

function readList<T>(key: string): T[] {
  try {
    return JSON.parse(localStorage.getItem(key) ?? '[]') as T[]
  } catch {
    return []
  }
}

function writeList<T>(key: string, data: T[]): void {
  localStorage.setItem(key, JSON.stringify(data))
}

export function getJobs(): OcrJob[] {
  return readList<OcrJob>(JOBS_KEY)
}

export function getJob(id: string): OcrJob | undefined {
  return getJobs().find(j => j.id === id)
}

export function createJob(params: {
  templateVersionId: string
  templateName: string
  imageKey: string
  processedImageUrl?: string
}): OcrJob {
  const job: OcrJob = {
    id: crypto.randomUUID(),
    templateVersionId: params.templateVersionId,
    templateName: params.templateName,
    imageKey: params.imageKey,
    processedImageUrl: params.processedImageUrl,
    status: 'pending',
    results: [],
    createdAt: new Date().toISOString()
  }
  const jobs = getJobs()
  jobs.push(job)
  writeList(JOBS_KEY, jobs)
  return job
}

export function updateJobStatus(id: string, status: OcrJobStatus): void {
  const jobs = getJobs()
  const job = jobs.find(j => j.id === id)
  if (job) {
    job.status = status
    writeList(JOBS_KEY, jobs)
  }
}

export function updateJobResults(id: string, results: OcrFieldResult[]): void {
  const jobs = getJobs()
  const job = jobs.find(j => j.id === id)
  if (job) {
    job.results = results
    writeList(JOBS_KEY, jobs)
  }
}

export function updateFieldValue(jobId: string, fieldId: string, value: string): void {
  const jobs = getJobs()
  const job = jobs.find(j => j.id === jobId)
  if (!job) return
  const field = job.results.find(r => r.fieldId === fieldId)
  if (field) {
    field.value = value
    field.edited = true
    writeList(JOBS_KEY, jobs)
  }
}

export function deleteJob(id: string): void {
  const jobs = getJobs().filter(j => j.id !== id)
  writeList(JOBS_KEY, jobs)
}
