<template>
  <div class="brochure-root" @click="closeAllMenus">

    <!-- ═══════════════ HEADER ═══════════════ -->
    <div class="brochure-header">
      <div>
        <h5 class="brochure-header-title">{{ __('Brochures') }}</h5>
        <p class="brochure-header-sub">{{ __('Manage and preview uploaded brochures') }}</p>
      </div>
      <Button v-if="canCreate" variant="solid" :label="__('Upload Brochure')" @click.stop="openUploadModal">
        <template #prefix>
          <FeatherIcon name="upload" class="h-4 w-4" />
        </template>
      </Button>
    </div>

    <!-- ═══════════════ FILTER BAR — title + description only, no icons ═══════════════ -->
    <div class="brochure-filter-bar">
      <div class="brochure-filter-inputs">
        <input
          v-model="searchQuery"
          type="text"
          class="brochure-filter-input"
          :placeholder="__('Search by title...')"
        />
        <input
          v-model="searchDesc"
          type="text"
          class="brochure-filter-input"
          :placeholder="__('Search by description...')"
        />
      </div>
    </div>

    <!-- ═══════════════ UPLOAD / EDIT MODAL ═══════════════ -->
    <Dialog
      v-model="showUploadModal"
      :options="{ title: editingBrochure ? __('Edit Brochure') : __('Upload Brochure') }"
    >
      <template #body-content>
        <div class="flex flex-col gap-4">
          <FormControl type="text" v-model="formData.title" :label="__('Title')" :placeholder="__('Enter brochure title')" />
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Description') }}</label>
            <textarea v-model="formData.description" :placeholder="__('Enter description')" rows="3"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400" />
          </div>
          <FormControl
            type="select"
            v-model="formData.status"
            :label="__('Status')"
            :options="['Draft', 'Active', 'Under Review', 'Archived']"
          />

          <!-- Cover Image -->
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Cover Image') }}
              <span class="ml-1 text-xs text-gray-400">({{ __('Images only') }})</span>
            </label>
            <FileUploader :fileTypes="['image/*']" :validateFile="validateCoverImage" @success="(f) => onCoverImageUpload(f)">
              <template #default="{ openFileSelector, uploading, progress }">
                <div class="cover-uploader" @click="openFileSelector">
                  <img v-if="formData.cover_image" :src="formData.cover_image" class="cover-uploader-img" />
                  <div v-if="!formData.cover_image" class="cover-uploader-placeholder">
                    <FeatherIcon name="image" class="mb-1 h-7 w-7" />
                    <span v-if="uploading" class="text-xs text-blue-500">{{ __('Uploading...') }} {{ progress }}%</span>
                    <span v-else class="text-xs">{{ __('Click to upload cover image') }}</span>
                    <span class="text-xs text-gray-300">PNG, JPG, JPEG, WEBP</span>
                  </div>
                  <div v-if="formData.cover_image" class="cover-uploader-overlay">{{ __('Click to change') }}</div>
                </div>
              </template>
            </FileUploader>
          </div>

          <!-- File Upload -->
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Upload File') }}
              <span class="ml-1 text-xs text-gray-400">(PDF {{ __('or') }} image)</span>
            </label>
            <FileUploader :fileTypes="['application/pdf','image/*']" :validateFile="validateFile" @success="(f) => onFileUpload(f)">
              <template #default="{ openFileSelector, uploading, progress }">
                <div class="file-uploader" @click="openFileSelector">
                  <FeatherIcon name="upload-cloud" class="mb-1 h-6 w-6 text-gray-400" />
                  <span v-if="uploading" class="text-xs text-blue-500">{{ __('Uploading...') }} {{ progress }}%</span>
                  <span v-else-if="formData.file" class="text-xs font-medium text-green-600">✓ {{ __('File uploaded') }}</span>
                  <span v-else class="text-xs text-gray-500">{{ __('Click to upload PDF or image') }}</span>
                </div>
              </template>
            </FileUploader>
          </div>
        </div>
      </template>
      <template #actions>
        <Button
          variant="solid"
          :label="editingBrochure ? __('Update Brochure') : __('Save Brochure')"
          :disabled="!formData.title || !formData.file"
          @click="saveBrochure"
        />
      </template>
    </Dialog>

    <!-- ═══════════════ DELETE CONFIRMATION DIALOG ═══════════════ -->
    <Dialog
      v-model="showDeleteConfirm"
      :options="{ title: __('Delete brochure?'), size: 'sm' }"
    >
      <template #body-content>
        <p class="text-sm text-gray-600">
          {{ __('Are you sure you want to delete') }}
          <span class="font-semibold text-gray-900">"{{ pendingDeleteTitle }}"</span>?
          {{ __('This action cannot be undone.') }}
        </p>
      </template>
      <template #actions>
        <div style="display:flex;flex-direction:row;gap:8px;width:100%;">
          <Button style="flex:1;" variant="outline" :label="__('Cancel')" @click="showDeleteConfirm = false" />
          <Button style="flex:1;" variant="solid" theme="red" :label="__('Delete')" @click="confirmDelete" />
        </div>
      </template>
    </Dialog>

    <!-- ═══════════════ PREVIEW MODAL ═══════════════ -->
    <teleport to="body">
      <div v-if="previewBrochure" class="preview-overlay" @click.self="previewBrochure = null">
        <div class="preview-modal">

          <!-- Preview Header -->
          <div class="preview-header">
            <div class="preview-header-left">
              <span class="preview-status-dot" :class="statusDotClass(previewBrochure.status)" />
              <h6 class="preview-title">{{ previewBrochure.title }}</h6>
            </div>
            <button class="preview-close-btn" @click="previewBrochure = null">
              <FeatherIcon name="x" class="h-5 w-5" />
            </button>
          </div>

          <!-- Preview Body -->
          <div class="preview-body">

            <!-- File preview area -->
            <div class="preview-file-area">
              <!-- PDF -->
              <iframe
                v-if="previewBrochure.file && isPdf(previewBrochure.file)"
                :src="previewBrochure.file"
                class="preview-iframe"
              />
              <!-- Image -->
              <img
                v-else-if="previewBrochure.file && isImage(previewBrochure.file)"
                :src="previewBrochure.file"
                class="preview-image"
              />
              <!-- Fallback -->
              <div v-else class="preview-no-file">
                <FeatherIcon name="file-text" class="h-16 w-16 text-gray-300" />
                <p class="mt-2 text-sm text-gray-400">{{ __('Preview not available') }}</p>
              </div>
            </div>

            <!-- Side info panel -->
            <div class="preview-side">
              <div v-if="previewBrochure.custom_cover_image" class="preview-side-cover">
                <img :src="previewBrochure.custom_cover_image" class="preview-side-cover-img" />
              </div>

              <div class="preview-side-field">
                <p class="preview-side-label">{{ __('Title') }}</p>
                <p class="preview-side-value-bold">{{ previewBrochure.title }}</p>
              </div>

              <div v-if="previewBrochure.description" class="preview-side-field">
                <p class="preview-side-label">{{ __('Description') }}</p>
                <p class="preview-side-value">{{ previewBrochure.description }}</p>
              </div>

              <div class="preview-side-field">
                <p class="preview-side-label">{{ __('Status') }}</p>
                <span class="status-badge" :class="statusBadgeClass(previewBrochure.status)">
                  <span class="status-badge-dot" :class="statusDotClass(previewBrochure.status)" />
                  {{ previewBrochure.status }}
                </span>
              </div>

              <div class="preview-side-field">
                <p class="preview-side-label">{{ __('Added') }}</p>
                <p class="preview-side-value">{{ formatDate(previewBrochure.creation) }}</p>
              </div>

              <div class="preview-side-actions">
                <button v-if="canWrite" class="preview-action-btn preview-action-edit"
                  @click="openEditModal(previewBrochure); previewBrochure = null">
                  <FeatherIcon name="edit-2" class="h-4 w-4" />{{ __('Edit') }}
                </button>
                <button v-if="canDelete" class="preview-action-btn preview-action-delete"
                  @click="askDelete(previewBrochure); previewBrochure = null">
                  <FeatherIcon name="trash-2" class="h-4 w-4" />{{ __('Delete') }}
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>
    </teleport>

    <!-- ═══════════════ MAIN SCROLL CONTENT ═══════════════ -->
    <div class="brochure-content">

      <!-- Loading -->
      <div v-if="brochures.loading" class="brochure-loading">
        <LoadingIndicator class="h-8 w-8 text-gray-400" />
      </div>

      <!-- Empty state -->
      <div v-else-if="!filteredBrochures.length" class="brochure-empty">
        <FeatherIcon name="file-text" class="mb-3 h-12 w-12 text-gray-300" />
        <p class="font-medium text-gray-500">{{ __('No brochures uploaded yet') }}</p>
        <p class="mt-1 text-sm text-gray-400">{{ __('Upload your first brochure to get started') }}</p>
        <Button v-if="canCreate" class="mt-4" :label="__('Upload Brochure')" @click="openUploadModal" />
      </div>

      <!-- Card grid — 4 col → 3 → 2 → 1 responsive -->
      <div v-else class="brochure-grid">
        <div
          v-for="brochure in filteredBrochures"
          :key="brochure.name"
          class="brochure-card"
          :class="brochure.status === 'Archived' ? 'brochure-card-archived' : ''"
          @click.stop="openPreview(brochure)"
        >

          <!-- Top: dot + title + action icons (clicks don't bubble to card click) -->
          <div class="card-top" @click.stop>
            <div class="card-top-left">
              <span class="card-status-dot" :class="statusDotClass(brochure.status)" :title="brochure.status" />
              <h6 class="card-title" :class="brochure.status === 'Archived' ? 'card-title-archived' : ''">
                {{ brochure.title }}
              </h6>
            </div>
            <div class="card-actions">
              <button v-if="canRead"   class="card-action-btn"        :title="__('View')"   @click.stop="openPreview(brochure)">
                <FeatherIcon name="eye"     class="h-4 w-4" />
              </button>
              <button v-if="canWrite"  class="card-action-btn"        :title="__('Edit')"   @click.stop="openEditModal(brochure)">
                <FeatherIcon name="edit-2"  class="h-4 w-4" />
              </button>
              <button v-if="canDelete" class="card-action-btn card-action-delete" :title="__('Delete')" @click.stop="askDelete(brochure)">
                <FeatherIcon name="trash-2" class="h-4 w-4" />
              </button>
            </div>
          </div>

          <!-- Thumbnail (card click → preview) -->
          <div class="card-thumb" :class="brochure.status === 'Archived' ? 'card-thumb-archived' : ''">
            <img
              v-if="brochure.custom_cover_image"
              :src="brochure.custom_cover_image"
              class="card-thumb-img"
              :class="brochure.status === 'Archived' ? 'card-thumb-faded' : ''"
            />
            <img
              v-else-if="brochure.file && isImage(brochure.file)"
              :src="brochure.file"
              class="card-thumb-img"
              :class="brochure.status === 'Archived' ? 'card-thumb-faded' : ''"
            />
            <div v-else class="card-thumb-pdf">
              <FeatherIcon name="file-text" class="h-10 w-10 text-gray-400" />
              <span class="card-thumb-pdf-label">PDF</span>
            </div>
          </div>

          <!-- Description + date -->
          <div class="card-body">
            <p v-if="brochure.description" class="card-desc"
              :class="brochure.status === 'Archived' ? 'card-desc-archived' : ''">
              {{ brochure.description }}
            </p>
            <div class="card-footer">
              <span class="card-date">{{ formatDate(brochure.creation) }}</span>
            </div>
          </div>

        </div>
      </div>

    </div>

    <!-- ═══════════════ PAGINATION — pinned to bottom ═══════════════ -->
    <div v-if="(brochures.data || []).length" class="brochure-pagination">
      <div class="pagination-sizes">
        <button
          v-for="n in [20, 50, 100]"
          :key="n"
          class="pagination-size-btn"
          :class="pageLength === n ? 'pagination-size-active' : ''"
          @click="setPageLength(n)"
        >{{ n }}</button>
      </div>
      <span class="pagination-count">
        {{ filteredBrochures.length }} {{ __('of') }} {{ (brochures.data || []).length }}
      </span>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import {
  Button, Dialog, FormControl, FeatherIcon,
  FileUploader, LoadingIndicator,
  createListResource, createResource,
} from 'frappe-ui'

// ─── State ────────────────────────────────────────────────
const showUploadModal    = ref(false)
const editingBrochure    = ref(null)
const previewBrochure    = ref(null)
const searchQuery        = ref('')
const searchDesc         = ref('')
const pageLength         = ref(20)
const showDeleteConfirm  = ref(false)
const pendingDeleteName  = ref('')
const pendingDeleteTitle = ref('')

// ─── Permissions ─────────────────────────────────────────
const canRead   = ref(false)
const canWrite  = ref(false)
const canCreate = ref(false)
const canDelete = ref(false)

const formData = reactive({
  title: '', description: '', file: '', cover_image: '', status: 'Active',
})

onMounted(async () => {
  try {
    const res = await createResource({
      url: 'frappe.client.get_doc_permissions',
      makeParams: () => ({ doctype: 'Brochure' }),
    }).submit()
    const p = res || {}
    canRead.value   = !!(p.read)
    canWrite.value  = !!(p.write)
    canCreate.value = !!(p.create)
    canDelete.value = !!(p.delete)
  } catch {
    canRead.value = canWrite.value = canCreate.value = canDelete.value = true
  }
})

// ─── Helpers ─────────────────────────────────────────────
function closeAllMenus() {}

function resetForm() {
  formData.title = ''; formData.description = ''
  formData.file  = ''; formData.cover_image = ''
  formData.status = 'Active'
  editingBrochure.value = null
}

function openUploadModal() { resetForm(); showUploadModal.value = true }

function openEditModal(brochure) {
  editingBrochure.value = brochure
  formData.title        = brochure.title || ''
  formData.description  = brochure.description || ''
  formData.file         = brochure.file || ''
  formData.cover_image  = brochure.custom_cover_image || ''
  formData.status       = brochure.status || 'Active'
  showUploadModal.value = true
}

function openPreview(brochure) { previewBrochure.value = brochure }

// ─── Data ─────────────────────────────────────────────────
const brochures = createListResource({
  doctype:   'Brochure',
  fields:    ['name', 'title', 'description', 'file', 'custom_cover_image', 'creation', 'status'],
  orderBy:   'creation desc',
  pageLength: 100,
  auto:      true,
})

const filteredBrochures = computed(() => {
  const all = brochures.data || []
  const q   = searchQuery.value.toLowerCase()
  const d   = searchDesc.value.toLowerCase()
  return all
    .filter(b => {
      const tm = !q || b.title?.toLowerCase().includes(q)
      const dm = !d || b.description?.toLowerCase().includes(d)
      return tm && dm
    })
    .slice(0, pageLength.value)
})

function setPageLength(n) { pageLength.value = n }

// ─── Upload validators ────────────────────────────────────
function validateCoverImage(file) {
  if (!file.type.startsWith('image/')) return __('Only image files are allowed')
}
function validateFile(file) {
  const ok = ['application/pdf','image/png','image/jpeg','image/jpg','image/webp']
  if (!ok.includes(file.type)) return __('Only PDF and image files are allowed')
}
function onCoverImageUpload(f) { formData.cover_image = f.file_url }
function onFileUpload(f)       { formData.file        = f.file_url }

// ─── Save / Delete ────────────────────────────────────────
async function saveBrochure() {
  if (editingBrochure.value) {
    await createResource({
      url: 'frappe.client.set_value',
      makeParams: () => ({
        doctype: 'Brochure',
        name: editingBrochure.value.name,
        fieldname: {
          title: formData.title, description: formData.description,
          file: formData.file, custom_cover_image: formData.cover_image, status: formData.status,
        },
      }),
    }).submit()
  } else {
    await createResource({
      url: 'frappe.client.insert',
      makeParams: () => ({
        doc: {
          doctype: 'Brochure', title: formData.title, description: formData.description,
          file: formData.file, custom_cover_image: formData.cover_image, status: formData.status,
        },
      }),
    }).submit()
  }
  showUploadModal.value = false
  resetForm()
  brochures.reload()
}

// ─── Delete (with confirmation) ───────────────────────────
function askDelete(brochure) {
  pendingDeleteName.value  = brochure.name
  pendingDeleteTitle.value = brochure.title || brochure.name
  showDeleteConfirm.value  = true
}

async function confirmDelete() {
  showDeleteConfirm.value = false
  await createResource({
    url: 'frappe.client.delete',
    makeParams: () => ({ doctype: 'Brochure', name: pendingDeleteName.value }),
  }).submit()
  if (previewBrochure.value?.name === pendingDeleteName.value) previewBrochure.value = null
  pendingDeleteName.value  = ''
  pendingDeleteTitle.value = ''
  brochures.reload()
}

// ─── Status helpers ───────────────────────────────────────
function statusDotClass(status) {
  return ({ 'Active': 'dot-green', 'Draft': 'dot-yellow', 'Under Review': 'dot-blue', 'Archived': 'dot-grey' })[status] || 'dot-grey'
}
function statusBadgeClass(status) {
  return ({ 'Active': 'badge-green', 'Draft': 'badge-yellow', 'Under Review': 'badge-blue', 'Archived': 'badge-grey' })[status] || 'badge-grey'
}

// ─── File type utils ──────────────────────────────────────
function isPdf(url)   { return /\.pdf(\?.*)?$/i.test(url) || (url || '').includes('.pdf') }
function isImage(url) { return /\.(png|jpg|jpeg|webp|gif|svg)(\?.*)?$/i.test(url) }

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>

<style scoped>
/* ════════════════════════════════════
   ROOT
════════════════════════════════════ */
.brochure-root {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f9fafb;
  overflow: hidden;
}

/* ════════════════════════════════════
   HEADER
════════════════════════════════════ */
.brochure-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e5e7eb;
  background: #fff;
  padding: 12px 20px;
  flex-shrink: 0;
}
.brochure-header-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}
.brochure-header-sub {
  font-size: 0.72rem;
  color: #6b7280;
  margin: 2px 0 0;
}

/* ════════════════════════════════════
   FILTER BAR — inputs only, no icons
════════════════════════════════════ */
.brochure-filter-bar {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #e5e7eb;
  background: #fff;
  padding: 8px 16px;
  flex-shrink: 0;
}
.brochure-filter-inputs {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.brochure-filter-input {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #f3f4f6;
  padding: 7px 14px;
  font-size: 0.82rem;
  color: #374151;
  width: 220px;          /* slightly larger than before */
  outline: none;
  transition: border-color 0.15s, background 0.15s;
}
.brochure-filter-input::placeholder { color: #9ca3af; }
.brochure-filter-input:focus {
  border-color: #6366f1;
  background: #fff;
}

/* ════════════════════════════════════
   SCROLL CONTENT AREA
════════════════════════════════════ */
.brochure-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  /* ensures pagination stays at bottom */
  min-height: 0;
}
.brochure-loading,
.brochure-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  text-align: center;
}

/* ════════════════════════════════════
   RESPONSIVE GRID
   ≥1200 → 4col | ≥900 → 3col | ≥540 → 2col | <540 → 1col
════════════════════════════════════ */
.brochure-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
@media (max-width: 1199px) { .brochure-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 899px)  { .brochure-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 539px)  { .brochure-grid { grid-template-columns: 1fr; } }

/* ════════════════════════════════════
   CARD
════════════════════════════════════ */
.brochure-card {
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow 0.18s, transform 0.18s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.07);
}
.brochure-card:hover {
  box-shadow: 0 6px 20px rgba(0,0,0,0.11);
  transform: translateY(-2px);
}
/* Archived card: grey background */
.brochure-card-archived {
  background: #f3f4f6;
  border-color: #d1d5db;
}

/* Card top row */
.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 12px 8px;
  gap: 6px;
}
.card-top-left {
  display: flex;
  align-items: center;
  gap: 7px;
  min-width: 0;
  flex: 1;
}
.card-status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 0;
}
.card-title {
  font-size: 0.82rem;
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0;
  line-height: 1.3;
}
.card-title-archived { color: #9ca3af; }

/* Action icons — black, always visible */
.card-actions {
  display: flex;
  align-items: center;
  gap: 1px;
  flex-shrink: 0;
  align-self: center;
}
.card-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: #1f2937;          /* black icons */
  cursor: pointer;
  padding: 0;
  transition: background 0.15s;
}
.card-action-btn:hover            { background: #f3f4f6; }
.card-action-delete               { color: #1f2937; }
.card-action-delete:hover         { background: #fee2e2; color: #dc2626; }

/* Thumbnail */
.card-thumb {
  position: relative;
  margin: 0 12px;
  border-radius: 8px;
  overflow: hidden;
  height: 155px;
  background: #f3f4f6;
  flex-shrink: 0;
}
.card-thumb-archived { background: #e5e7eb; }
.card-thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.card-thumb-faded { opacity: 0.5; }
.card-thumb-pdf {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}
.card-thumb-pdf-label {
  font-size: 0.72rem;
  font-weight: 600;
  color: #9ca3af;
  margin-top: 4px;
}

/* Card body */
.card-body {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 10px 13px 12px;
}
.card-desc {
  font-size: 0.78rem;
  color: #1f2937;          /* dark, visible description */
  line-height: 1.55;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0 0 8px;
}
.card-desc-archived { color: #9ca3af; }
.card-footer { margin-top: auto; }
.card-date {
  font-size: 0.72rem;
  color: #4b5563;          /* visible dark-grey date */
  font-weight: 500;
}

/* ════════════════════════════════════
   PAGINATION — pinned bottom bar
════════════════════════════════════ */
.brochure-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid #e5e7eb;
  background: #fff;
  padding: 8px 20px;
  flex-shrink: 0;
}
.pagination-sizes { display: flex; gap: 4px; }
.pagination-size-btn {
  border: 1px solid #d1d5db;
  border-radius: 5px;
  background: #fff;
  color: #6b7280;
  font-size: 0.75rem;
  font-weight: 500;
  padding: 3px 10px;
  cursor: pointer;
  transition: all 0.15s;
}
.pagination-size-btn:hover { background: #f9fafb; }
.pagination-size-active { background: #1f2937 !important; border-color: #1f2937 !important; color: #fff !important; }
.pagination-count { font-size: 0.75rem; color: #6b7280; }

/* ════════════════════════════════════
   STATUS DOTS
════════════════════════════════════ */
.dot-green  { background: #22c55e; }
.dot-yellow { background: #f59e0b; }
.dot-blue   { background: #3b82f6; }
.dot-grey   { background: #9ca3af; }

/* ════════════════════════════════════
   STATUS BADGES
════════════════════════════════════ */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 0.72rem;
  font-weight: 500;
}
.status-badge-dot { width: 6px; height: 6px; border-radius: 50%; }
.badge-green  { background: #dcfce7; color: #15803d; }
.badge-yellow { background: #fef9c3; color: #a16207; }
.badge-blue   { background: #dbeafe; color: #1d4ed8; }
.badge-grey   { background: #f3f4f6; color: #6b7280; }

/* ════════════════════════════════════
   PREVIEW MODAL
════════════════════════════════════ */
.preview-overlay {
  position: fixed;
  inset: 0;
  z-index: 1050;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.72);
  padding: 16px;
}
.preview-modal {
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  width: 94vw;
  max-width: 1280px;
  height: 92vh;
  box-shadow: 0 24px 60px rgba(0,0,0,0.35);
}
.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e5e7eb;
  padding: 14px 20px;
  flex-shrink: 0;
  gap: 12px;
}
.preview-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.preview-status-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
.preview-title {
  font-size: 1rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.preview-close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
}
.preview-close-btn:hover { background: #f3f4f6; color: #111; }

/* Preview body */
.preview-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.preview-file-area {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  overflow: hidden;
}
.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}
.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
.preview-no-file {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* Side panel */
.preview-side {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border-left: 1px solid #e5e7eb;
  background: #fff;
  padding: 20px;
  overflow-y: auto;
}
.preview-side-cover { border-radius: 10px; overflow: hidden; }
.preview-side-cover-img { width: 100%; height: 130px; object-fit: cover; display: block; }
.preview-side-field {}
.preview-side-label {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #9ca3af;
  margin: 0 0 4px;
}
.preview-side-value      { font-size: 0.82rem; color: #111827; margin: 0; line-height: 1.55; }
.preview-side-value-bold { font-size: 0.85rem; font-weight: 700; color: #111827; margin: 0; }
.preview-side-actions {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-top: 1px solid #e5e7eb;
  padding-top: 16px;
}
.preview-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  width: 100%;
  padding: 8px 0;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: #fff;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  color: #374151;
  transition: background 0.15s;
}
.preview-action-edit:hover   { background: #f3f4f6; }
.preview-action-delete       { border-color: #fecaca; color: #dc2626; }
.preview-action-delete:hover { background: #fee2e2; }

/* ════════════════════════════════════
   UPLOAD WIDGETS
════════════════════════════════════ */
.cover-uploader {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  border: 2px dashed #d1d5db;
  height: 130px;
  cursor: pointer;
  background: #f9fafb;
  transition: border-color 0.15s;
}
.cover-uploader:hover { border-color: #6366f1; }
.cover-uploader-img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.cover-uploader-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #9ca3af;
}
.cover-uploader-overlay {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: rgba(0,0,0,0.45);
  text-align: center;
  color: #fff;
  font-size: 0.72rem;
  padding: 4px;
}
.file-uploader {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  border: 2px dashed #d1d5db;
  height: 85px;
  cursor: pointer;
  background: #f9fafb;
  transition: border-color 0.15s;
}
.file-uploader:hover { border-color: #6366f1; }

/* ════════════════════════════════════
   MOBILE OVERRIDES
════════════════════════════════════ */
@media (max-width: 539px) {
  .brochure-filter-input   { width: 100%; }
  .preview-body            { flex-direction: column; }
  .preview-side            { width: 100%; border-left: none; border-top: 1px solid #e5e7eb; }
  .preview-modal           { height: 96vh; }
  .brochure-header         { padding: 10px 14px; }
  .brochure-content        { padding: 12px; }
}
</style>