import { watch } from 'vue'
import { useRouter } from 'vue-router'

// A merged lead is hidden: send anyone who opens it (an old link, Back) on to
// the lead it was merged into. replace, so Back doesn't land on it again.
export function useMergedLeadRedirect(
  getDoc: () => { merged_into?: string } | null | undefined,
  leadId: string,
) {
  const router = useRouter()
  watch(
    getDoc,
    (doc) => {
      if (doc?.merged_into && doc.merged_into !== leadId) {
        router.replace({ name: 'Lead', params: { leadId: doc.merged_into } })
      }
    },
    { immediate: true },
  )
}
