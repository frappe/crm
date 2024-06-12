<template>
  <div ref="reference">
    <div
      ref="target"
      :class="['flex', $attrs.class]"
      @click="updatePosition"
      @focusin="updatePosition"
      @keydown="updatePosition"
      @mouseover="onMouseover"
      @mouseleave="onMouseleave"
    >
      <slot
        name="target"
        v-bind="{ togglePopover, updatePosition, open, close, isOpen }"
      />
    </div>
    <teleport to="#frappeui-popper-root">
      <div
        ref="popover"
        class="relative z-[100]"
        :class="[popoverContainerClass, popoverClass]"
        :style="{ minWidth: targetWidth ? targetWidth + 'px' : null }"
        @mouseover="pointerOverTargetOrPopup = true"
        @mouseleave="onMouseleave"
      >
        <transition v-bind="popupTransition">
          <div v-show="isOpen">
            <slot
              name="body"
              v-bind="{ togglePopover, updatePosition, open, close, isOpen }"
            >
              <div class="rounded-lg border border-gray-100 bg-white shadow-xl">
                <slot
                  name="body-main"
                  v-bind="{
                    togglePopover,
                    updatePosition,
                    open,
                    close,
                    isOpen,
                  }"
                />
              </div>
            </slot>
          </div>
        </transition>
      </div>
    </teleport>
  </div>
</template>

<script>
import { createPopper } from '@popperjs/core'

export default {
  name: 'Popover',
  inheritAttrs: false,
  props: {
    show: {
      default: undefined,
    },
    trigger: {
      type: String,
      default: 'click', // click, hover
    },
    hoverDelay: {
      type: Number,
      default: 0,
    },
    leaveDelay: {
      type: Number,
      default: 0,
    },
    placement: {
      type: String,
      default: 'bottom-start',
    },
    popoverClass: [String, Object, Array],
    transition: {
      default: null,
    },
    hideOnBlur: {
      default: true,
    },
  },
  emits: ['open', 'close', 'update:show'],
  expose: ['open', 'close'],
  data() {
    return {
      popoverContainerClass: 'body-container',
      showPopup: false,
      targetWidth: null,
      pointerOverTargetOrPopup: false,
    }
  },
  watch: {
    show(val) {
      if (val) {
        this.open()
      } else {
        this.close()
      }
    },
  },
  created() {
    if (typeof window === 'undefined') return
    if (!document.getElementById('frappeui-popper-root')) {
      const root = document.createElement('div')
      root.id = 'frappeui-popper-root'
      document.body.appendChild(root)
    }
  },
  mounted() {
    this.listener = (e) => {
      const clickedElement = e.target
      const reference = this.$refs.reference
      const popoverBody = this.$refs.popover
      const insideClick =
        clickedElement === reference ||
        clickedElement === popoverBody ||
        reference?.contains(clickedElement) ||
        popoverBody?.contains(clickedElement)
      if (insideClick) {
        return
      }

      const root = document.getElementById('frappeui-popper-root')
      const insidePopoverRoot = root.contains(clickedElement)
      if (!insidePopoverRoot) {
        return this.close()
      }

      const bodyClass = `.${this.popoverContainerClass}`
      const clickedElementBody = clickedElement?.closest(bodyClass)
      const currentPopoverBody = reference?.closest(bodyClass)
      const isSiblingClicked =
        clickedElementBody &&
        currentPopoverBody &&
        clickedElementBody === currentPopoverBody

      if (isSiblingClicked) {
        this.close()
      }
    }
    if (this.hideOnBlur) {
      document.addEventListener('click', this.listener)
      document.addEventListener('mousedown', this.listener)
    }
    this.$nextTick(() => {
      this.targetWidth = this.$refs['target'].clientWidth
    })
  },
  beforeDestroy() {
    this.popper && this.popper.destroy()
    document.removeEventListener('click', this.listener)
    document.removeEventListener('mousedown', this.listener)
  },
  computed: {
    showPropPassed() {
      return this.show != null
    },
    isOpen: {
      get() {
        if (this.showPropPassed) {
          return this.show
        }
        return this.showPopup
      },
      set(val) {
        val = Boolean(val)
        if (this.showPropPassed) {
          this.$emit('update:show', val)
        } else {
          this.showPopup = val
        }
        if (val === false) {
          this.$emit('close')
        } else if (val === true) {
          this.$emit('open')
        }
      },
    },
    popupTransition() {
      let templates = {
        default: {
          enterActiveClass: 'transition duration-150 ease-out',
          enterFromClass: 'translate-y-1 opacity-0',
          enterToClass: 'translate-y-0 opacity-100',
          leaveActiveClass: 'transition duration-150 ease-in',
          leaveFromClass: 'translate-y-0 opacity-100',
          leaveToClass: 'translate-y-1 opacity-0',
        },
      }
      if (typeof this.transition === 'string') {
        return templates[this.transition]
      }
      return this.transition
    },
  },
  methods: {
    setupPopper() {
      if (!this.popper) {
        this.popper = createPopper(this.$refs.reference, this.$refs.popover, {
          placement: this.placement,
        })
      } else {
        this.updatePosition()
      }
    },
    updatePosition() {
      this.popper && this.popper.update()
    },
    togglePopover(flag) {
      if (flag instanceof Event) {
        flag = null
      }
      if (flag == null) {
        flag = !this.isOpen
      }
      flag = Boolean(flag)
      if (flag) {
        this.open()
      } else {
        this.close()
      }
    },
    open() {
      this.isOpen = true
      this.$nextTick(() => this.setupPopper())
    },
    close() {
      this.isOpen = false
    },
    onMouseover() {
      this.pointerOverTargetOrPopup = true
      if (this.leaveTimer) {
        clearTimeout(this.leaveTimer)
        this.leaveTimer = null
      }
      if (this.trigger === 'hover') {
        if (this.hoverDelay) {
          this.hoverTimer = setTimeout(() => {
            if (this.pointerOverTargetOrPopup) {
              this.open()
            }
          }, Number(this.hoverDelay) * 1000)
        } else {
          this.open()
        }
      }
    },
    onMouseleave(e) {
      this.pointerOverTargetOrPopup = false
      if (this.hoverTimer) {
        clearTimeout(this.hoverTimer)
        this.hoverTimer = null
      }
      if (this.trigger === 'hover') {
        if (this.leaveTimer) {
          clearTimeout(this.leaveTimer)
        }
        if (this.leaveDelay) {
          this.leaveTimer = setTimeout(() => {
            if (!this.pointerOverTargetOrPopup) {
              this.close()
            }
          }, Number(this.leaveDelay) * 1000)
        } else {
          if (!this.pointerOverTargetOrPopup) {
            this.close()
          }
        }
      }
    },
  },
}
</script>
