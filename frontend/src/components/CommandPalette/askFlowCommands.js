import {
  ask,
  canAskFlow,
  recordContext,
  showAskFlow,
} from '@/components/FlowChat/askFlow'

const MIN_QUESTION = 3
// After every match while typing.
const ASK_RANK = 0.1

/** The palette's Ask Flow row, for the typed text. */
export function askFlowCommands(query, route) {
  const question = query.trim()
  if (!canAskFlow.value || question.length < MIN_QUESTION) return []
  return [askCommand(question, route)]
}

export function askCommand(question, route) {
  const context = recordContext(route, document.title)
  return {
    id: 'ask-flow',
    title: __('Ask Flow: {0}', [question]),
    translate: false,
    subtitle: context ? __('About {0}', [context.title || context.name]) : '',
    group: 'Ask',
    icon: 'sparkles',
    rank: ASK_RANK,
    keepOpen: true,
    perform: () => {
      showAskFlow()
      ask(question, { context })
    },
  }
}
