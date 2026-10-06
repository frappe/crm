// translation.js sets these at runtime; declared here so TS code can use them.
export {}

declare global {
  function __(
    message: string,
    replace?: unknown[],
    context?: string | null,
  ): string
}

declare module 'vue' {
  interface ComponentCustomProperties {
    __: typeof __
  }
}
