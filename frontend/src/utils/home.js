export function greetingFor(date, name) {
  const hour = date.getHours()
  const greeting =
    hour < 12
      ? __('Good morning')
      : hour < 17
        ? __('Good afternoon')
        : __('Good evening')
  return name ? `${greeting}, ${name}` : greeting
}
