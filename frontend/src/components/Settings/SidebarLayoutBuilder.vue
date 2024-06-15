<template>
  <div>
    <Draggable :list="sections" item-key="label" class="flex flex-col">
      <template #item="{ element: section }">
        <div class="border-b">
          <div class="flex items-center justify-between p-2">
            <div
              class="flex h-7 max-w-fit cursor-pointer items-center gap-2 pl-2 pr-3 text-base font-semibold leading-5"
              @click="section.opened = !section.opened"
            >
              <FeatherIcon
                name="chevron-right"
                class="h-4 text-gray-900 transition-all duration-300 ease-in-out"
                :class="{ 'rotate-90': section.opened }"
              />
              <div v-if="!section.editingLabel">
                {{ __(section.label) || __('Untitled') }}
              </div>
              <div v-else>
                <Input
                  v-model="section.label"
                  @keydown.enter="section.editingLabel = false"
                  @blur="section.editingLabel = false"
                  @click.stop
                />
              </div>
            </div>
            <div>
              <Button
                :icon="section.editingLabel ? 'check' : 'edit'"
                variant="ghost"
                @click="section.editingLabel = !section.editingLabel"
              />
              <Button
                icon="x"
                variant="ghost"
                @click="sections.splice(sections.indexOf(section), 1)"
              />
            </div>
          </div>
          <div v-show="section.opened" class="p-4 pt-0 pb-2">
            <Draggable
              :list="section.fields"
              item-key="label"
              class="flex flex-col gap-1"
              handle=".cursor-grab"
            >
              <template #item="{ element: field }">
                <div
                  class="px-1.5 py-1 border rounded text-base text-gray-800 flex items-center justify-between gap-2"
                >
                  <div class="flex items-center gap-2">
                    <DragVerticalIcon class="h-3.5 cursor-grab" />
                    <div>{{ field.label }}</div>
                  </div>
                  <div>
                    <Button
                      variant="ghost"
                      icon="x"
                      @click="
                        section.fields.splice(section.fields.indexOf(field), 1)
                      "
                    />
                  </div>
                </div>
              </template>
            </Draggable>
            <Button
              class="w-full mt-2"
              variant="outline"
              :label="__('Add Field')"
              @click="section.fields.push({ label: 'New Field' })"
            />
          </div>
        </div>
      </template>
    </Draggable>
    <div class="p-2">
      <Button
        class="w-full"
        variant="outline"
        :label="__('Add Section')"
        @click="
          sections.push({ label: 'New Section', opened: true, fields: [] })
        "
      />
    </div>
  </div>
</template>
<script setup>
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import Draggable from 'vuedraggable'
import { Input } from 'frappe-ui'

const props = defineProps({
  sections: Object,
})
</script>
