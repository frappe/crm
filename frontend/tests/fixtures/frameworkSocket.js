// Stands for `@framework/ui/socket`: a test puts its fake socket on `globalThis.__testSocket`.
export const getSocketInstance = () => globalThis.__testSocket
