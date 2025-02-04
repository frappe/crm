<template>
    <div class="flex flex-col h-screen overflow-hidden">
        <ContactHeader :contact="contact?.data" />
        <div class="flex flex-1 min-h-0">
            <Resizer 
                v-if="contact?.data" 
                :parent="$refs.parentRef" 
                ref="parentRef"
                class="flex-shrink-0 w-80 border-r flex flex-col"
            >
                <div class="flex-shrink-0">
                    <ContactProfile 
                        :contact="contact?.data" 
                        @update="contact?.reload" 
                    />
                </div>
                <div v-if="sections?.data" class="flex-shrink-0">
                    <SidePanelLayout 
                        v-model="contact.data" 
                        :sections="sections.data" 
                        doctype="Contact"
                        @update="updateField" 
                        @reload="sections?.reload" 
                    />
                </div>
                <div class="flex-shrink-0 border-t px-4 py-4">
                    <EmailDropZone 
                        :contact-name="contactId" 
                        @upload-complete="timeline?.reload()" 
                    />
                </div>
            </Resizer>

            <div class="flex-1 flex flex-col min-w-0">
                <ContactTabs 
                    v-model="tabIndex"
                    :timeline="timeline?.data || []"
                    :deals="deals?.data || []"
                    :contact="contact?.data"
                    :rows="rows || []"
                    :columns="columns || []"
                    @comment-added="refreshTimeline"
                />
            </div>
        </div>
        <AddressModal v-model="showAddressModal" v-model:address="_address" />
    </div>
</template>

<script setup>
import Resizer from '@/components/Resizer.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import AddressModal from '@/components/Modals/AddressModal.vue'
import { formatDate, timeAgo, createToast } from '@/utils'
import { getView } from '@/utils/view'
import { getSettings } from '@/stores/settings'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global.js'
import { usersStore } from '@/stores/users.js'
import { organizationsStore } from '@/stores/organizations.js'
import { statusesStore } from '@/stores/statuses'
import {
    call,
    createResource,
    usePageMeta,
} from 'frappe-ui'
import { ref, computed, h, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import EmailDropZone from '@/components/EmailDropZone.vue'
import ContactHeader from '@/components/Contact/ContactHeader.vue'
import ContactProfile from '@/components/Contact/ContactProfile.vue'
import ContactTabs from '@/components/Contact/ContactTabs.vue'

const { brand } = getSettings()
const { $dialog, makeCall } = globalStore()

const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()

const props = defineProps({
    contactId: {
        type: String,
        required: true,
    },
})

const route = useRoute()
const router = useRouter()

const showAddressModal = ref(false)
const _contact = ref({})
const _address = ref({})
const tabIndex = ref(0)

const contact = createResource({
    url: 'crm.api.contact.get_contact',
    cache: ['contact', props.contactId],
    params: { name: props.contactId },
    auto: true,
    transform: (data) => {
        return {
            ...data,
            actual_mobile_no: data.mobile_no,
            mobile_no: data.mobile_no,
        }
    },
})

const breadcrumbs = computed(() => {
    let items = [{ label: __('Contacts'), route: { name: 'Contacts' } }]

    if (route.query.view || route.query.viewType) {
        let view = getView(route.query.view, route.query.viewType, 'Contact')
        if (view) {
            items.push({
                label: __(view.label),
                icon: view.icon,
                route: {
                    name: 'Contacts',
                    params: { viewType: route.query.viewType },
                    query: { view: route.query.view },
                },
            })
        }
    }

    items.push({
        label: contact.data?.full_name,
        route: { name: 'Contact', params: { contactId: props.contactId } },
    })
    return items
})

usePageMeta(() => {
    return {
        title: contact.data?.full_name || contact.data?.name,
        icon: brand.favicon,
    }
})

function validateFile(file) {
    let extn = file.name.split('.').pop().toLowerCase()
    if (!['png', 'jpg', 'jpeg'].includes(extn)) {
        return __('Only PNG and JPG images are allowed')
    }
}

async function changeContactImage(file) {
    await call('frappe.client.set_value', {
        doctype: 'Contact',
        name: props.contactId,
        fieldname: 'image',
        value: file?.file_url || '',
    })
    contact.reload()
}

async function deleteContact() {
    $dialog({
        title: __('Delete contact'),
        message: __('Are you sure you want to delete this contact?'),
        actions: [
            {
                label: __('Delete'),
                theme: 'red',
                variant: 'solid',
                async onClick(close) {
                    await call('frappe.client.delete', {
                        doctype: 'Contact',
                        name: props.contactId,
                    })
                    close()
                    router.push({ name: 'Contacts' })
                },
            },
        ],
    })
}

const tabs = [
    {
        label: 'Timeline',
        icon: h(CalendarIcon, { class: 'h-4 w-4' }),
        count: computed(() => timeline.data?.length || 0),
    },
    {
        label: 'Deals',
        icon: h(DealsIcon, { class: 'h-4 w-4' }),
        count: computed(() => deals.data?.length || 0),
    },
]

const deals = createResource({
    url: 'crm.api.contact.get_linked_deals',
    cache: ['deals', props.contactId],
    params: {
        contact: props.contactId,
    },
    auto: true,
})

const rows = computed(() => {
    if (!deals.data || deals.data == []) return []

    return deals.data.map((row) => getDealRowObject(row))
})

const sections = createResource({
    url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
    cache: ['sidePanelSections', 'Contact'],
    params: { doctype: 'Contact' },
    auto: true,
    transform: (data) => computed(() => getParsedSections(data)),
})

function getParsedSections(_sections) {
    return _sections.map((section) => {
        section.columns = section.columns.map((column) => {
            column.fields = column.fields.map((field) => {
                if (field.fieldname === 'email_id') {
                    return {
                        ...field,
                        read_only: false,
                        fieldtype: 'Dropdown',
                        options:
                            contact.data?.email_ids?.map((email) => {
                                return {
                                    name: email.name,
                                    value: email.email_id,
                                    selected: email.email_id === contact.data.email_id,
                                    placeholder: 'john@doe.com',
                                    onClick: () => {
                                        _contact.value.email_id = email.email_id
                                        setAsPrimary('email', email.email_id)
                                    },
                                    onSave: (option, isNew) => {
                                        if (isNew) {
                                            createNew('email', option.value)
                                            if (contact.data.email_ids.length === 1) {
                                                _contact.value.email_id = option.value
                                            }
                                        } else {
                                            editOption(
                                                'Contact Email',
                                                option.name,
                                                'email_id',
                                                option.value,
                                            )
                                        }
                                    },
                                    onDelete: async (option, isNew) => {
                                        contact.data.email_ids = contact.data.email_ids.filter(
                                            (email) => email.name !== option.name,
                                        )
                                        !isNew && (await deleteOption('Contact Email', option.name))
                                        if (_contact.value.email_id === option.value) {
                                            if (contact.data.email_ids.length === 0) {
                                                _contact.value.email_id = ''
                                            } else {
                                                _contact.value.email_id = contact.data.email_ids.find(
                                                    (email) => email.is_primary,
                                                )?.email_id
                                            }
                                        }
                                    },
                                }
                            }) || [],
                        create: () => {
                            contact.data?.email_ids?.push({
                                name: 'new-1',
                                value: '',
                                selected: false,
                                isNew: true,
                            })
                        },
                    }
                } else if (field.fieldname === 'mobile_no') {
                    return {
                        ...field,
                        read_only: false,
                        fieldtype: 'Dropdown',
                        options:
                            contact.data?.phone_nos?.map((phone) => {
                                return {
                                    name: phone.name,
                                    value: phone.phone,
                                    selected: phone.phone === contact.data.actual_mobile_no,
                                    onClick: () => {
                                        _contact.value.actual_mobile_no = phone.phone
                                        _contact.value.mobile_no = phone.phone
                                        setAsPrimary('mobile_no', phone.phone)
                                    },
                                    onSave: (option, isNew) => {
                                        if (isNew) {
                                            createNew('phone', option.value)
                                            if (contact.data.phone_nos.length === 1) {
                                                _contact.value.actual_mobile_no = option.value
                                            }
                                        } else {
                                            editOption(
                                                'Contact Phone',
                                                option.name,
                                                'phone',
                                                option.value,
                                            )
                                        }
                                    },
                                    onDelete: async (option, isNew) => {
                                        contact.data.phone_nos = contact.data.phone_nos.filter(
                                            (phone) => phone.name !== option.name,
                                        )
                                        !isNew && (await deleteOption('Contact Phone', option.name))
                                        if (_contact.value.actual_mobile_no === option.value) {
                                            if (contact.data.phone_nos.length === 0) {
                                                _contact.value.actual_mobile_no = ''
                                            } else {
                                                _contact.value.actual_mobile_no =
                                                    contact.data.phone_nos.find(
                                                        (phone) => phone.is_primary_mobile_no,
                                                    )?.phone
                                            }
                                        }
                                    },
                                }
                            }) || [],
                        create: () => {
                            contact.data?.phone_nos?.push({
                                name: 'new-1',
                                value: '',
                                selected: false,
                                isNew: true,
                            })
                        },
                    }
                } else if (field.fieldname === 'address') {
                    return {
                        ...field,
                        create: (value, close) => {
                            _contact.value.address = value
                            _address.value = {}
                            showAddressModal.value = true
                            close()
                        },
                        edit: async (addr) => {
                            _address.value = await call('frappe.client.get', {
                                doctype: 'Address',
                                name: addr,
                            })
                            showAddressModal.value = true
                        },
                    }
                } else {
                    return field
                }
            })
            return column
        })
        return section
    })
}

async function setAsPrimary(field, value) {
    let d = await call('crm.api.contact.set_as_primary', {
        contact: contact.data.name,
        field,
        value,
    })
    if (d) {
        contact.reload()
        createToast({
            title: 'Contact updated',
            icon: 'check',
            iconClasses: 'text-ink-green-3',
        })
    }
}

async function createNew(field, value) {
    if (!value) return
    let d = await call('crm.api.contact.create_new', {
        contact: contact.data.name,
        field,
        value,
    })
    if (d) {
        contact.reload()
        createToast({
            title: 'Contact updated',
            icon: 'check',
            iconClasses: 'text-ink-green-3',
        })
    }
}

async function editOption(doctype, name, fieldname, value) {
    let d = await call('frappe.client.set_value', {
        doctype,
        name,
        fieldname,
        value,
    })
    if (d) {
        contact.reload()
        createToast({
            title: 'Contact updated',
            icon: 'check',
            iconClasses: 'text-ink-green-3',
        })
    }
}

async function deleteOption(doctype, name) {
    await call('frappe.client.delete', {
        doctype,
        name,
    })
    await contact.reload()
    createToast({
        title: 'Contact updated',
        icon: 'check',
        iconClasses: 'text-ink-green-3',
    })
}

async function updateField(fieldname, value) {
    await call('frappe.client.set_value', {
        doctype: 'Contact',
        name: props.contactId,
        fieldname,
        value,
    })
    createToast({
        title: 'Contact updated',
        icon: 'check',
        iconClasses: 'text-ink-green-3',
    })

    contact.reload()
}

const { getFormattedCurrency } = getMeta('CRM Deal')

const columns = computed(() => dealColumns)

function getDealRowObject(deal) {
    return {
        name: deal.name,
        organization: {
            label: deal.organization,
            logo: getOrganization(deal.organization)?.organization_logo,
        },
        annual_revenue: getFormattedCurrency('annual_revenue', deal),
        status: {
            label: deal.status,
            color: getDealStatus(deal.status)?.color,
        },
        email: deal.email,
        mobile_no: deal.mobile_no,
        deal_owner: {
            label: deal.deal_owner && getUser(deal.deal_owner).full_name,
            ...(deal.deal_owner && getUser(deal.deal_owner)),
        },
        modified: {
            label: formatDate(deal.modified),
            timeAgo: __(timeAgo(deal.modified)),
        },
    }
}

const dealColumns = [
    {
        label: __('Organization'),
        key: 'organization',
        width: '11rem',
    },
    {
        label: __('Amount'),
        key: 'annual_revenue',
        align: 'right',
        width: '9rem',
    },
    {
        label: __('Status'),
        key: 'status',
        width: '10rem',
    },
    {
        label: __('Email'),
        key: 'email',
        width: '12rem',
    },
    {
        label: __('Mobile no'),
        key: 'mobile_no',
        width: '11rem',
    },
    {
        label: __('Deal owner'),
        key: 'deal_owner',
        width: '10rem',
    },
    {
        label: __('Last modified'),
        key: 'modified',
        width: '8rem',
    },
]

const timeline = createResource({
    url: 'crm.api.doc.get_timeline',
    cache: ['timeline', props.contactId],
    params: {
        doctype: 'Contact',
        name: props.contactId,
        for_contact: true,
    },
    auto: true,
})

const refreshTimeline = async () => {
    try {
        if (timeline?.reload) {
            await timeline.reload()
        }
    } catch (error) {
        console.error('Error refreshing timeline:', error)
    }
}

</script>

<style>
.drop-zone {
    border: 2px dashed #ccc;
    padding: 20px;
    text-align: center;
    margin: 20px 0;
    border-radius: 5px;
    background-color: rgba(255, 0, 0, 0.1);
    z-index: 1000;
    position: relative;
}

.drag-over {
    border-color: #000;
    background-color: #f0f0f0;
}
</style>
