import { h, type FunctionalComponent } from 'vue'

// `<component is="button">` resolves an app-registered `Button` first; h() always renders the native element.
const NativeTag: FunctionalComponent<{ as: string }> = (props, { slots }) =>
  h(props.as, null, slots.default?.())

NativeTag.props = ['as']

export default NativeTag
