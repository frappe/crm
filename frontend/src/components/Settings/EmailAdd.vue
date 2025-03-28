<template>
  <div class="flex flex-col h-full gap-4">
    <!-- title and desc -->
    <div role="heading" aria-level="1" class="flex flex-col gap-1">
      <h5 class="text-xl font-semibold">Setup Email</h5>
      <p class="text-sm text-gray-600">
        Choose the email service provider you want to configure.
      </p>
    </div>
    <!-- email service provider selection -->
    <div class="flex flex-wrap items-center">
      <div v-for="s in services" :key="s.name" class="flex flex-col items-center gap-1 mt-4 w-[70px]"
        @click="handleSelect(s)">
        <EmailProviderIcon :service-name="s.name" :logo="s.icon" :selected="selectedService?.name === s?.name" />
      </div>
    </div>
    <div v-if="selectedService" class="flex flex-col gap-4">
      <!-- email service provider info -->
      <div class="flex items-center gap-2 p-2 rounded-md ring-1 ring-gray-200">
        <CircleAlert class="w-5 h-6 text-blue-500 w-min-5 w-max-5 min-h-5 max-w-5" />
        <div class="text-xs text-gray-700 text-wrap">
          {{ selectedService.info }}
          <a :href="selectedService.link" target="_blank" class="text-blue-500 underline">here</a>.
        </div>
      </div>
      <!-- service provider fields -->
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-1 gap-4">
          <div v-for="field in fields" :key="field.name" class="flex flex-col gap-1">
            <FormControl v-model="state[field.name]" :label="field.label" :name="field.name" :type="field.type"
              :placeholder="field.placeholder" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div v-for="field in incomingOutgoingFields" :key="field.name" class="flex flex-col gap-1">
            <FormControl v-model="state[field.name]" :label="field.label" :name="field.name" :type="field.type" />
            <p class="text-gray-500 text-p-sm">{{ field.description }}</p>
          </div>
        </div>
        <ErrorMessage v-if="error" class="ml-1" :message="error" />
      </div>
    </div>
    <!-- action button -->
    <div v-if="selectedService" class="flex justify-between mt-auto">
      <Button label="Back" theme="gray" variant="outline" :disabled="addEmailRes.loading"
        @click="emit('update:step', 'email-list')" />
      <Button label="Create" variant="solid" :loading="addEmailRes.loading" @click="createEmailAccount" />
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { createResource } from "frappe-ui";
import CircleAlert from "~icons/lucide/circle-alert";
import { createToast } from "@/utils";
import {
  customProviderFields,
  popularProviderFields,
  services,
  validateInputs,
  incomingOutgoingFields,
} from "./emailConfig";
import EmailProviderIcon from "./EmailProviderIcon.vue";

const emit = defineEmits();

const state = reactive({
  service: "",
  email_account_name: "",
  email_id: "",
  password: "",
  api_key: "",
  api_secret: "",
  frappe_mail_site: "",
  enable_incoming: false,
  enable_outgoing: false,
  default_incoming: false,
  default_outgoing: false,
});

const selectedService = ref(null);
const fields = computed(() =>
  selectedService.value.custom ? customProviderFields : popularProviderFields
);

function handleSelect(service) {
  selectedService.value = service;
  state.service = service.name;
}

const addEmailRes = createResource({
  url: "crm.api.settings.create_email_account",
  makeParams: (val) => {
    return {
      ...val,
    };
  },
  onSuccess: () => {
    createToast({
      title: "Email account created successfully",
      icon: "check",
      iconClasses: "text-green-600",
    });
    emit("update:step", "email-list");
  },
  onError: () => {
    error.value = "Failed to create email account, Invalid credentials";
  },
});

const error = ref();
function createEmailAccount() {
  error.value = validateInputs(state, selectedService.value.custom);
  if (error.value) return;

  addEmailRes.submit({ data: state });
}
</script>

<style scoped></style>
