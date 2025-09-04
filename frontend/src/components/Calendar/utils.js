export function allTimeSlots() {
  const out = []
  for (let h = 0; h < 24; h++) {
    for (const m of [0, 15, 30, 45]) {
      const hh = String(h).padStart(2, '0')
      const mm = String(m).padStart(2, '0')
      const ampm = h >= 12 ? 'pm' : 'am'
      const hour12 = h % 12 === 0 ? 12 : h % 12
      out.push({
        value: `${hh}:${mm}`,
        label: `${hour12}:${mm} ${ampm}`,
      })
    }
  }
  return out
}
