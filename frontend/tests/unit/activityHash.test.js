import { parseActivityHash } from '@/utils/activityHash'

describe('parseActivityHash', () => {
  it('reads a tab hash as both tab and anchor', () => {
    expect(parseActivityHash('#notes')).toEqual({
      tab: 'notes',
      anchor: 'notes',
    })
  })

  it('reads a timeline row hash as its own anchor', () => {
    expect(parseActivityHash('#gbp9547ldc')).toEqual({
      tab: 'gbp9547ldc',
      anchor: 'gbp9547ldc',
    })
  })

  it('splits a note hash into the notes tab and the note', () => {
    expect(parseActivityHash('#notes/gbp2a9uafp')).toEqual({
      tab: 'notes',
      anchor: 'gbp2a9uafp',
    })
  })

  it('reads an empty hash as no tab', () => {
    expect(parseActivityHash('')).toEqual({ tab: '', anchor: '' })
  })
})
