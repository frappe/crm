import { defineStore } from 'pinia'

export const useOptInStore = defineStore('optin', {
  state: () => ({
    step: 0,
    showOtpGate: false,
    networkSlug: '',
    networkConfig: null,
    contact: {
      first_name: '',
      last_name: '',
      email: '',
      mobile_no: '',
      organisation: '',
      role: '',
    },
    otpChannel: 'email', // 'email' | 'sms' — how the verification code is delivered
    witness: {
      name: '',
      email: '',
    },
    signingToken: '',
    signingExpiry: 0,
    facilities: [],
    selectedFacilities: [],
    pricing: null,
    termsHtml: '',
    termsDocName: '',
    termsDocHash: '',
    termsAccepted: false,
    submissionRef: '',
  }),

  actions: {
    setStep(step) {
      this.step = step
    },

    setShowOtpGate(val) {
      this.showOtpGate = val
    },

    setNetworkConfig(config) {
      this.networkConfig = config
    },

    setContact(contact) {
      this.contact = { ...this.contact, ...contact }
    },

    setOtpChannel(channel) {
      this.otpChannel = channel === 'sms' ? 'sms' : 'email'
    },

    setWitness(witness) {
      this.witness = { ...this.witness, ...witness }
    },

    setSigningToken(token, expiry) {
      this.signingToken = token
      this.signingExpiry = expiry
    },

    setFacilities(facilities) {
      this.facilities = facilities
    },

    setSelectedFacilities(facilities) {
      this.selectedFacilities = facilities
    },

    setPricing(pricing) {
      this.pricing = pricing
    },

    setTerms(html, docName, docHash) {
      this.termsHtml = html
      this.termsDocName = docName
      this.termsDocHash = docHash
    },

    setTermsAccepted(val) {
      this.termsAccepted = val
    },

    setSubmissionRef(ref) {
      this.submissionRef = ref
    },

    resetTerms() {
      this.termsAccepted = false
      this.termsHtml = ''
      this.termsDocName = ''
      this.termsDocHash = ''
    },

    reset() {
      this.$reset()
    },
  },
})
