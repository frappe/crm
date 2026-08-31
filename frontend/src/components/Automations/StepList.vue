<template>
  <div class="flex w-full flex-col items-center">
    <template v-for="(step, i) in steps" :key="i">
      <div class="h-4 w-px bg-outline-gray-3" />

      <!-- if_else -->
      <div
        v-if="step.type == 'if_else'"
        class="group w-full rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3"
      >
        <div class="flex items-center justify-between">
          <Badge :label="__('If / Else')" theme="orange" />
          <div class="flex shrink-0 items-center gap-1" @click.stop>
            <Button
              variant="ghost"
              icon="lucide-arrow-up"
              :disabled="i == 0"
              @click="editor.moveStep(steps, i, -1)"
            />
            <Button
              variant="ghost"
              icon="lucide-arrow-down"
              :disabled="i == steps.length - 1"
              @click="editor.moveStep(steps, i, 1)"
            />
            <Button variant="ghost" icon="lucide-trash-2" @click="steps.splice(i, 1)" />
          </div>
        </div>
        <div class="mt-3 grid gap-3" :class="gridClass((step.branches?.length || 0) + 1)">
          <div
            v-for="(branch, bi) in step.branches"
            :key="bi"
            class="rounded-md border border-outline-gray-2 bg-surface-base p-2"
          >
            <div class="flex items-center justify-between gap-2">
              <span class="truncate text-sm font-medium text-ink-gray-8">
                {{ branch.label || __('Branch') + ' ' + (bi + 1) }}
              </span>
              <div class="flex items-center gap-1">
                <Button
                  variant="ghost"
                  icon="lucide-settings-2"
                  @click="editor.editBranch(step, bi)"
                />
                <Button
                  v-if="step.branches.length > 1"
                  variant="ghost"
                  icon="lucide-trash-2"
                  @click="step.branches.splice(bi, 1)"
                />
              </div>
            </div>
            <div class="truncate text-xs text-ink-gray-5">
              {{ editor.groupsSummary(branch.condition_groups) }}
            </div>
            <StepList :steps="branch.steps" :meta="meta" />
          </div>
          <div class="rounded-md border border-dashed border-outline-gray-2 bg-surface-base p-2">
            <span class="text-sm font-medium text-ink-gray-6">{{ __('None (else)') }}</span>
            <StepList :steps="step.else_steps" :meta="meta" />
          </div>
        </div>
        <Button
          class="mt-2"
          variant="ghost"
          :label="__('Add branch')"
          iconLeft="plus"
          @click="editor.addBranch(step)"
        />
      </div>

      <!-- split -->
      <div
        v-else-if="step.type == 'split'"
        class="group w-full rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3"
      >
        <div class="flex items-center justify-between">
          <Badge :label="__('Split test')" theme="blue" />
          <div class="flex shrink-0 items-center gap-1" @click.stop>
            <Button
              variant="ghost"
              icon="lucide-settings-2"
              @click="editor.editStep(steps, i)"
            />
            <Button variant="ghost" icon="lucide-trash-2" @click="steps.splice(i, 1)" />
          </div>
        </div>
        <div class="mt-3 grid gap-3" :class="gridClass(step.paths?.length || 1)">
          <div
            v-for="(path, pi) in step.paths"
            :key="pi"
            class="rounded-md border border-outline-gray-2 bg-surface-base p-2"
          >
            <div class="flex items-center justify-between gap-2">
              <span class="truncate text-sm font-medium text-ink-gray-8">
                {{ path.label || __('Path') + ' ' + (pi + 1) }}
              </span>
              <span class="text-xs text-ink-gray-5">{{ path.percent }}%</span>
            </div>
            <StepList :steps="path.steps" :meta="meta" />
          </div>
        </div>
      </div>

      <!-- plain step card -->
      <div
        v-else
        class="group w-full cursor-pointer rounded-lg border border-outline-gray-2 bg-surface-base p-3 hover:border-outline-gray-3"
        @click="editor.editStep(steps, i)"
      >
        <div class="flex items-center justify-between">
          <div class="flex min-w-0 items-center gap-2">
            <Badge :label="editor.stepLabel(step.type)" :theme="editor.stepTheme(step.type)" />
            <span v-if="step.label" class="text-xs text-ink-gray-4">#{{ step.label }}</span>
            <span v-if="step.condition" class="truncate text-xs text-ink-gray-5">
              {{ __('if') }} {{ editor.conditionSummary(step.condition) }}
            </span>
          </div>
          <div
            class="flex shrink-0 items-center gap-1 opacity-0 group-hover:opacity-100"
            @click.stop
          >
            <Button
              variant="ghost"
              icon="lucide-arrow-up"
              :disabled="i == 0"
              @click="editor.moveStep(steps, i, -1)"
            />
            <Button
              variant="ghost"
              icon="lucide-arrow-down"
              :disabled="i == steps.length - 1"
              @click="editor.moveStep(steps, i, 1)"
            />
            <Button variant="ghost" icon="lucide-trash-2" @click="steps.splice(i, 1)" />
          </div>
        </div>
        <div class="mt-1 truncate text-sm text-ink-gray-6">
          {{ editor.stepSummary(step) }}
        </div>
      </div>
    </template>

    <div class="h-4 w-px bg-outline-gray-3" />
    <Dropdown :options="editor.addStepOptions(steps)">
      <Button variant="subtle" :label="__('Add step')" iconLeft="plus" />
    </Dropdown>
  </div>
</template>

<script setup>
import { inject } from 'vue'
import { Dropdown } from 'frappe-ui'

defineOptions({ name: 'StepList' })

defineProps({
  steps: { type: Array, required: true },
  meta: { type: Object, default: () => ({}) },
})

const editor = inject('automation-editor')

function gridClass(n) {
  return n > 2 ? 'sm:grid-cols-3' : 'sm:grid-cols-2'
}
</script>
