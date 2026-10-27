import { describe, it, expect } from 'vitest'
import {
  formatTranscriptUtterances,
  normalizeTranscriptSpeaker,
  appendOrUpdateUtterance,
} from '@/utils/callTranscript'

describe('callTranscript utility', () => {
  describe('formatTranscriptUtterances', () => {
    it('returns empty string for null, undefined or empty array', () => {
      expect(formatTranscriptUtterances(null)).toBe('')
      expect(formatTranscriptUtterances(undefined)).toBe('')
      expect(formatTranscriptUtterances([])).toBe('')
    })

    it('formats a single customer utterance correctly', () => {
      const utterances = [
        { speaker: 'customer', text: 'Hello, I need help with my account.' },
      ]
      expect(formatTranscriptUtterances(utterances)).toBe(
        '[Customer]\nHello, I need help with my account.',
      )
    })

    it('formats alternating customer and agent utterances', () => {
      const utterances = [
        {
          speaker: 'customer',
          text: 'Hello, I am calling regarding your services.',
        },
        { speaker: 'agent', text: 'Sure, how can I assist you?' },
        { speaker: 'customer', text: 'We are interested in AI and automation.' },
        { speaker: 'agent', text: 'Great. Let me explain our solutions.' },
      ]
      const expected =
        '[Customer]\nHello, I am calling regarding your services.\n\n' +
        '[Agent]\nSure, how can I assist you?\n\n' +
        '[Customer]\nWe are interested in AI and automation.\n\n' +
        '[Agent]\nGreat. Let me explain our solutions.'

      expect(formatTranscriptUtterances(utterances)).toBe(expected)
    })

    it('filters out empty or whitespace-only utterances', () => {
      const utterances = [
        { speaker: 'customer', text: 'Valid message' },
        { speaker: 'agent', text: '   ' },
        null,
      ]
      expect(formatTranscriptUtterances(utterances)).toBe(
        '[Customer]\nValid message',
      )
    })
  })

  describe('normalizeTranscriptSpeaker', () => {
    it('normalizes explicit labels', () => {
      expect(normalizeTranscriptSpeaker('customer')).toBe('customer')
      expect(normalizeTranscriptSpeaker('caller')).toBe('customer')
      expect(normalizeTranscriptSpeaker('lead')).toBe('customer')
      expect(normalizeTranscriptSpeaker('agent')).toBe('agent')
      expect(normalizeTranscriptSpeaker('user')).toBe('agent')
      expect(normalizeTranscriptSpeaker('callee')).toBe('agent')
    })

    it('maps tracks correctly for Outgoing calls (agent initiates from browser)', () => {
      // Inbound track to Twilio is the agent speaking from CRM
      expect(normalizeTranscriptSpeaker('', 'inbound_track', 'Outgoing')).toBe(
        'agent',
      )
      // Outbound track from Twilio is the customer dialed
      expect(normalizeTranscriptSpeaker('', 'outbound_track', 'Outgoing')).toBe(
        'customer',
      )
    })

    it('maps tracks correctly for Incoming calls (customer calls in)', () => {
      // Inbound track to Twilio is the customer calling in
      expect(normalizeTranscriptSpeaker('', 'inbound_track', 'Incoming')).toBe(
        'customer',
      )
      // Outbound track from Twilio is forwarded to agent
      expect(normalizeTranscriptSpeaker('', 'outbound_track', 'Incoming')).toBe(
        'agent',
      )
    })

    it('falls back to customer if track is unrecognized', () => {
      expect(normalizeTranscriptSpeaker('', 'unknown_track', 'Outgoing')).toBe(
        'customer',
      )
    })
  })

  describe('appendOrUpdateUtterance', () => {
    it('appends a new utterance when list is empty', () => {
      const initial = []
      const result = appendOrUpdateUtterance(initial, {
        speaker: 'customer',
        text: 'Hello',
        isFinal: false,
      })
      expect(result).toHaveLength(1)
      expect(result[0]).toMatchObject({
        speaker: 'customer',
        text: 'Hello',
        isFinal: false,
      })
    })

    it('updates in-place when next message is partial from same speaker', () => {
      const initial = [
        {
          speaker: 'customer',
          text: 'Hello',
          isFinal: false,
          timestamp: '2026-10-28T02:00:00Z',
        },
      ]
      const result = appendOrUpdateUtterance(initial, {
        speaker: 'customer',
        text: 'Hello world',
        isFinal: false,
      })
      expect(result).toHaveLength(1)
      expect(result[0].text).toBe('Hello world')
      expect(result[0].isFinal).toBe(false)
    })

    it('finalizes the utterance in-place when isFinal is true', () => {
      const initial = [
        {
          speaker: 'customer',
          text: 'Hello world',
          isFinal: false,
          timestamp: '2026-10-28T02:00:00Z',
        },
      ]
      const result = appendOrUpdateUtterance(initial, {
        speaker: 'customer',
        text: 'Hello world!',
        isFinal: true,
      })
      expect(result).toHaveLength(1)
      expect(result[0].text).toBe('Hello world!')
      expect(result[0].isFinal).toBe(true)
    })

    it('appends a new utterance once the previous was finalized', () => {
      const initial = [
        {
          speaker: 'customer',
          text: 'Hello world!',
          isFinal: true,
          timestamp: '2026-10-28T02:00:00Z',
        },
      ]
      const result = appendOrUpdateUtterance(initial, {
        speaker: 'agent',
        text: 'Hi there',
        isFinal: false,
      })
      expect(result).toHaveLength(2)
      expect(result[1].speaker).toBe('agent')
      expect(result[1].text).toBe('Hi there')
    })
  })
})
