<template>
  <Dialog
    v-model="show"
    :options="{
      size: 'xl',
      actions: [
        {
          label: editMode ? __('Update') : __('Create'),
          variant: 'solid',
          onClick: () => updateNote(),
        },
      ],
    }"
  >
    <template #body-title>
      <div class="flex items-center gap-3">
        <h3 class="text-2xl font-semibold leading-6 text-gray-900">
          {{ editMode ? __('Edit Note') : __('Create Note') }}
        </h3>
        <Button
          v-if="_note?.reference_docname"
          variant="outline"
          size="sm"
          :label="
            _note.reference_doctype == 'CRM Deal'
              ? __('Open Deal')
              : __('Open Lead')
          "
          @click="redirect()"
        >
          <template #suffix>
            <ArrowUpRightIcon class="h-4 w-4" />
          </template>
        </Button>
      </div>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <div class="mb-1.5 text-sm text-gray-600">{{ __('Title') }}</div>
          <TextInput
            ref="title"
            variant="outline"
            v-model="_note.title"
            :placeholder="__('Call with John Doe')"
          />
        </div>
        <div>
          <div class="mb-1.5 text-sm text-gray-600">{{ __('Content') }}</div>
          <TextEditor
            variant="outline"
            ref="content"
            editor-class="!prose-sm overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded border border-gray-300 bg-white hover:border-gray-400 hover:shadow-sm focus:bg-white focus:border-gray-500 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-gray-400 text-gray-800 transition-colors"
            :bubbleMenu="true"
            :content="_note.content"
            @change="(val) => (_note.content = val)"
            :placeholder="
              __('Took a call with John Doe and discussed the new project.')
            "
          />
        </div>
        <div>
          <FileUploader
              @success="(file) => addAttachment(file)"
            >
            <template #default="{ openFileSelector }">
              <Button @click="openFileSelector()">Attach File</Button>
            </template>
          </FileUploader>
           </div>

           <!-- <template>
              <div>
                <h3>Attach Files to Note</h3>
                <input type="file" multiple @change="handleFileUpload" />
                <button @click="uploadFiles">Upload</button>
                <div v-if="uploadedFiles.length">
                  <h4>Uploaded Files</h4>
                  <ul>
                    <li v-for="file in uploadedFiles" :key="file.name">{{ file.name }}</li>
                  </ul>
                </div>
              </div>
            </template> -->
          <div class="flex flex-wrap gap-2 sm:px-10 px-4">
            <AttachmentItem
              v-for="a in attachments"
              :key="a.file_name"
              :label="a.file_name"
               :url="a.file_name"
            >
              <template #suffix>
                <FeatherIcon
                  class="h-3.5"
                  name="x"
                  @click.stop="removeAttachment(a)"
                />
              </template>
            </AttachmentItem>
          </div>




      </div>
    </template>
  </Dialog>
</template>

<script setup>
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import { capture } from '@/telemetry'
import { TextEditor, call, FileUploader, createResource } from 'frappe-ui'
import { ref, nextTick, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import AttachmentItem from '@/components/AttachmentItem.vue'

const props = defineProps({
  note: {
    type: Object,
    default: {},
  },
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
  doc: {
    type: String,
    default: '',
  },
})

const show = defineModel()
const notes = defineModel('reloadNotes')
const attachments = ref([]);

const emit = defineEmits(['after'])

const router = useRouter()

const title = ref(null)
const editMode = ref(false)
let _note = ref({})

async function updateNote() {

  if (_note.value.name) {
    let d = await call('frappe.client.set_value', {
      doctype: 'FCRM Note',
      name: _note.value.name,
      fieldname: _note.value,
    })
    if (d.name) {
      mapped_attachments_on_note(d, attachments.value)
      notes.value?.reload()
      emit('after', d)
    }
  } else {
    let d = await call('frappe.client.insert', {
      doc: {
        doctype: 'FCRM Note',
        title: _note.value.title,
        content: _note.value.content,
        reference_doctype: props.doctype,
        reference_docname: props.doc || '',
      },
    })
    if (d.name) {
      mapped_attachments_on_note(d, attachments.value)
      capture('note_created')
      notes.value?.reload()
      emit('after', d, true)
    }
  }
  show.value = false
  notes.value?.reload()

}

function redirect() {
  if (!props.note?.reference_docname) return
  let name = props.note.reference_doctype == 'CRM Deal' ? 'Deal' : 'Lead'
  let params = { leadId: props.note.reference_docname }
  if (name == 'Deal') {
    params = { dealId: props.note.reference_docname }
  }
  router.push({ name: name, params: params })
}

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
    nextTick(() => {
      attachments.value = [];
      if(props.note.name){
        get_attachments_from_note(props.note.name)

      }
      title.value.el.focus()
      _note.value = { ...props.note }
      if (_note.value.title || _note.value.content) {
        editMode.value = true
      }
    })
  }
)

function addAttachment(file) {
  if (!_note.attachments) {
    _note.attachments = [];
  }
  _note.attachments.push(file);
  attachments.value.push(file);

}

function removeAttachment(attachment) {
  attachments.value = attachments.value.filter(a => a !== attachment);
}

function mapped_attachments_on_note(note, attachments){
  createResource({
    params: {
      note: note,
      attachments: attachments,
    },
    auto: true,
    url: 'crm.fcrm.doctype.fcrm_note.api.add_attachments_on_note',
    transform: (data) => {
      notes.value?.reload()

    },
  });

}

function get_attachments_from_note(note_name){
  attachments.value = [];
  createResource({
    params: {
      note_name: note_name,
    },
    auto: true,
    url: 'crm.fcrm.doctype.fcrm_note.api.get_attachments_from_note',
    transform: (data) => {
    data.forEach((item) => {
      attachments.value.push(item);
    });
    },
  });
}

</script>