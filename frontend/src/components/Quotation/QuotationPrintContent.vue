<template>
  <div class="qp-sheet">
    <!-- Header -->
    <header class="qp-header">
      <img v-show="logoOk" class="qp-logo" :src="logoUrl" alt="logo" @error="logoOk = false" />
      <div class="qp-company">
        <h1>{{ COMPANY.name }}</h1>
        <p>{{ COMPANY.addr1 }}</p>
        <p>{{ COMPANY.addr2 }}</p>
        <p>Telp : {{ COMPANY.phone }}</p>
      </div>
    </header>

    <!-- Meta -->
    <div class="qp-meta">
      <div class="qp-meta-date">{{ COMPANY.city }}, {{ formattedDate }}</div>
      <div class="qp-meta-ref">
        <div class="qp-ref">REF : {{ doc.name }}</div>
        <div class="qp-doc">DOC NUMBER: {{ DOC_NUMBER }}</div>
      </div>
    </div>

    <!-- Customer -->
    <div class="qp-customer">
      <div class="qp-cust-name">{{ doc.account_name || doc.account || '—' }}</div>
      <div class="qp-attn">Attn : {{ doc.attention || doc.contact_name || '' }}</div>
    </div>

    <p class="qp-intro">We are pleased to quote our best offer as follows:</p>

    <!-- Detail -->
    <div class="qp-details">
      <div v-for="d in details" :key="d.label" class="qp-drow">
        <div class="qp-dlabel">{{ d.label }}</div>
        <div class="qp-dsep">:</div>
        <div class="qp-dvalue">{{ d.value || '—' }}</div>
      </div>
    </div>

    <!-- Tabel produk / trucking -->
    <h2 class="qp-section">{{ truckingTitle }}</h2>
    <table class="qp-table">
      <thead>
        <tr>
          <th>Item &amp; Description</th>
          <th class="qp-amount">Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(p, i) in products" :key="i">
          <td>
            <div class="qp-item-name">{{ p.product || 'Item' }}</div>
            <div v-if="p.remark" class="qp-item-desc">{{ p.remark }}</div>
            <div v-if="p.qty" class="qp-item-meta">&gt; Qty: {{ p.qty }}</div>
          </td>
          <td class="qp-amount">{{ money(p.amount) }}</td>
        </tr>
        <tr v-if="!products.length">
          <td><div class="qp-item-name">—</div></td>
          <td class="qp-amount">{{ money(0) }}</td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <td class="qp-total-label">Net Total</td>
          <td class="qp-amount qp-total">{{ money(doc.net_total) }}</td>
        </tr>
      </tfoot>
    </table>

    <!-- Include / Exclude / Terms -->
    <section v-if="rateInclude.length" class="qp-block">
      <h3 class="qp-block-title">INCLUDE</h3>
      <ul>
        <li v-for="(l, i) in rateInclude" :key="i">{{ l }}</li>
      </ul>
    </section>

    <section v-if="rateExclude.length" class="qp-block">
      <h3 class="qp-block-title">EXCLUDE</h3>
      <ul>
        <li v-for="(l, i) in rateExclude" :key="i">{{ l }}</li>
      </ul>
    </section>

    <section v-if="terms.length" class="qp-block">
      <h3 class="qp-block-title">{{ (doc.term_title || 'Terms & Conditions').toUpperCase() }}</h3>
      <ul>
        <li v-for="(l, i) in terms" :key="i">{{ l }}</li>
      </ul>
    </section>

    <!-- Validity & Payment -->
    <div class="qp-details qp-vp">
      <div class="qp-drow">
        <div class="qp-dlabel">Validity</div>
        <div class="qp-dsep">:</div>
        <div class="qp-dvalue">{{ doc.validity || '—' }}</div>
      </div>
      <div class="qp-drow">
        <div class="qp-dlabel">Payment Term</div>
        <div class="qp-dsep">:</div>
        <div class="qp-dvalue">{{ doc.payterm || '—' }}</div>
      </div>
    </div>

    <p v-if="doc.remark" class="qp-remark">{{ doc.remark }}</p>

    <p class="qp-note">
      Should you need further details or information, please do not hesitate to contact us, Thank you.
    </p>

    <!-- Tanda tangan -->
    <div class="qp-sign">
      <div class="qp-sign-col">
        <div class="qp-sign-head">Regards,</div>
        <div class="qp-sign-company">{{ COMPANY.name }}</div>
        <img v-show="signOk" class="qp-sign-img" :src="signUrl" alt="signature" @error="signOk = false" />
        <div v-show="!signOk" class="qp-sign-gap"></div>
        <div class="qp-sign-name">{{ printedByName }}</div>
      </div>
      <div class="qp-sign-col">
        <div class="qp-sign-head">Approved By.</div>
        <div class="qp-sign-company">{{ doc.account_name || doc.account || '' }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { usersStore } from '@/stores/users'

const props = defineProps({
  doc: { type: Object, required: true },
})

// ── Konstanta perusahaan (edit di sini bila perlu) ──
const COMPANY = {
  name: 'PT CAKRAINDO MITRA INTERNASIONAL',
  addr1: 'Kota Harapan Indah, Sentra Niaga 5 Blok 2 No 16',
  addr2: 'Bekasi Barat - West Java, Indonesia 17132',
  phone: '021-29477548',
  city: 'Bekasi',
}
const DOC_NUMBER = 'F-BDM-02-01'

const base = import.meta.env.BASE_URL
const logoUrl = base + 'quotation/logo.png'
const signUrl = base + 'quotation/signature.png'
const logoOk = ref(true)
const signOk = ref(true)

const { getUser } = usersStore()

const products = computed(() => props.doc?.products || [])

const printedByName = computed(() => {
  const u = props.doc?.printed_by
  if (!u) return '—'
  return getUser(u)?.full_name || u
})

const details = computed(() => [
  { label: 'Subject', value: props.doc.subject },
  { label: 'Packaging', value: props.doc.packaging },
  { label: 'Cargo', value: props.doc.cargo },
  { label: 'Loading', value: props.doc.loading },
  { label: 'Unloading', value: props.doc.unloading },
])

const truckingTitle = computed(() =>
  props.doc?.packaging ? `TRUCKING DTD ${props.doc.packaging}` : 'TRUCKING',
)

function toLines(t) {
  return (t || '')
    .split('\n')
    .map((s) => s.replace(/^[>\-•\s]+/, '').trim())
    .filter(Boolean)
}
const rateInclude = computed(() => toLines(props.doc?.rate_include))
const rateExclude = computed(() => toLines(props.doc?.rate_exclude))
const terms = computed(() => toLines(props.doc?.term_detail))

const formattedDate = computed(() => {
  const d = props.doc?.date
  if (!d) return ''
  const dt = new Date(d + 'T00:00:00')
  return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
})

function money(v) {
  const n = Number(v) || 0
  return 'IDR ' + new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n)
}
</script>

<style scoped>
@page {
  size: A4;
  margin: 0;
}

.qp-sheet {
  --accent: #0e7c66;
  --ink-9: #1f2933;
  --ink-7: #3e4c59;
  --ink-5: #7b8794;
  --line: #e4e7eb;
  width: 210mm;
  min-height: 297mm;
  margin: 18px auto;
  padding: 16mm 15mm;
  background: #fff;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.12);
  box-sizing: border-box;
  font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  font-size: 11.5px;
  line-height: 1.5;
  color: var(--ink-9);
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

.qp-header {
  display: flex;
  align-items: center;
  gap: 18px;
  padding-bottom: 12px;
}
.qp-logo {
  height: 64px;
  width: auto;
  object-fit: contain;
  flex-shrink: 0;
}
.qp-company {
  flex: 1;
  text-align: center;
}
.qp-company h1 {
  margin: 0 0 4px;
  font-size: 21px;
  font-weight: 800;
  letter-spacing: 0.3px;
}
.qp-company p {
  margin: 0;
  font-size: 11px;
  color: var(--ink-7);
}

.qp-meta {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-top: 2px solid var(--accent);
  padding-top: 10px;
  margin-bottom: 18px;
}
.qp-meta-date {
  font-weight: 700;
  color: var(--accent);
  font-size: 13px;
}
.qp-meta-ref {
  text-align: right;
}
.qp-ref {
  font-weight: 800;
  font-size: 13px;
  color: var(--accent);
}
.qp-doc {
  font-weight: 700;
  font-size: 11px;
  color: var(--ink-7);
}

.qp-customer {
  margin-bottom: 14px;
}
.qp-cust-name {
  font-weight: 800;
  font-size: 14px;
}
.qp-attn {
  font-weight: 600;
}
.qp-intro {
  margin: 0 0 16px;
}

.qp-details {
  margin-bottom: 18px;
}
.qp-drow {
  display: grid;
  grid-template-columns: 150px 14px 1fr;
  padding: 3px 0;
}
.qp-dlabel {
  color: var(--ink-7);
}
.qp-dsep {
  color: var(--ink-5);
}
.qp-dvalue {
  font-weight: 600;
}
.qp-vp {
  margin-top: 16px;
}

.qp-section {
  margin: 18px 0 8px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.4px;
  border-left: 4px solid var(--accent);
  padding-left: 8px;
}

.qp-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 6px;
}
.qp-table thead th {
  text-align: left;
  font-size: 12px;
  font-weight: 800;
  padding: 8px 4px;
  border-bottom: 2px solid var(--ink-9);
}
.qp-table thead th.qp-amount {
  text-align: right;
}
.qp-table tbody td {
  padding: 9px 4px;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}
.qp-amount {
  text-align: right;
  white-space: nowrap;
}
.qp-item-name {
  font-weight: 800;
  font-size: 12px;
}
.qp-item-desc {
  color: var(--ink-7);
  margin-top: 2px;
}
.qp-item-meta {
  color: var(--ink-5);
  font-size: 10.5px;
}
.qp-table tfoot td {
  padding: 8px 4px;
  font-weight: 800;
}
.qp-total-label {
  text-align: right;
  color: var(--ink-7);
}
.qp-total {
  color: var(--accent);
  border-top: 2px solid var(--ink-9);
}

.qp-block {
  margin: 14px 0;
}
.qp-block-title {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.4px;
}
.qp-block ul {
  margin: 0;
  padding-left: 16px;
}
.qp-block li {
  margin: 2px 0;
  color: var(--ink-7);
}

.qp-remark {
  margin: 12px 0;
  color: var(--ink-7);
}
.qp-note {
  margin: 22px 0 26px;
  color: var(--ink-7);
}

.qp-sign {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-top: 8px;
  page-break-inside: avoid;
}
.qp-sign-head {
  color: var(--ink-7);
  margin-bottom: 2px;
}
.qp-sign-company {
  font-weight: 800;
}
.qp-sign-img {
  height: 90px;
  width: auto;
  object-fit: contain;
  margin: 6px 0;
}
.qp-sign-gap {
  height: 96px;
}
.qp-sign-name {
  font-weight: 800;
  border-top: 1px solid var(--ink-9);
  display: inline-block;
  padding-top: 4px;
  min-width: 180px;
}

.qp-printed {
  margin-top: 28px;
  font-size: 10.5px;
  color: var(--ink-5);
  text-align: right;
}

@media print {
  .qp-sheet {
    width: auto;
    min-height: auto;
    margin: 0;
    padding: 14mm 15mm;
    box-shadow: none;
  }
}
</style>
