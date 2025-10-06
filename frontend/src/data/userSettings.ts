import { call } from 'frappe-ui'
import { ref, reactive, readonly, Ref } from 'vue'

export interface UserSettings {
  [key: string]: any
}

export interface UserSettingsCache {
  [doctype: string]: UserSettings
}

export interface UseUserSettingsReturn {
  loading: Ref<boolean>
  error: Ref<Error | null>
  get: (doctype: string) => Promise<UserSettings>
  save: (doctype: string, key: string, value: any) => Promise<UserSettings>
  remove: (doctype: string, key: string) => Promise<UserSettings>
  update: (doctype: string, userSettings: UserSettings) => Promise<UserSettings>
  getCached: (doctype: string, key?: string | null) => any
  clearCache: (doctype?: string | null) => void
  userSettingsCache: Readonly<UserSettingsCache>
}

export interface FrappeCallResponse {
  message?: string
  [key: string]: any
}

const userSettingsCache: UserSettingsCache = reactive({})

export function useUserSettings(): UseUserSettingsReturn {
  const loading: Ref<boolean> = ref(false)
  const error: Ref<Error | null> = ref(null)

  const get = async (doctype: string): Promise<UserSettings> => {
    if (!doctype) {
      throw new Error('Doctype is required')
    }

    try {
      loading.value = true
      error.value = null

      const response: string = await call(
        'frappe.model.utils.user_settings.get',
        {
          doctype,
        },
      )

      const settings: UserSettings = JSON.parse(response || '{}')
      userSettingsCache[doctype] = settings
      return settings
    } catch (err) {
      const errorObj = err instanceof Error ? err : new Error(String(err))
      error.value = errorObj
      console.error('Error getting user settings:', err)
      throw errorObj
    } finally {
      loading.value = false
    }
  }

  const save = async (
    doctype: string,
    key: string,
    value: any,
  ): Promise<UserSettings> => {
    if (!doctype || !key) {
      throw new Error('Doctype and key are required')
    }

    if ((window as any)?.frappe?.session?.user === 'Guest') {
      return Promise.resolve({})
    }

    try {
      loading.value = true
      error.value = null

      const oldUserSettings: UserSettings = userSettingsCache[doctype] || {}
      const newUserSettings: UserSettings = JSON.parse(
        JSON.stringify(oldUserSettings),
      )

      if (
        typeof value === 'object' &&
        value !== null &&
        !Array.isArray(value)
      ) {
        newUserSettings[key] = newUserSettings[key] || {}
        Object.assign(newUserSettings[key], value)
      } else {
        newUserSettings[key] = value
      }

      const oldString = JSON.stringify(oldUserSettings)
      const newString = JSON.stringify(newUserSettings)

      if (oldString !== newString) {
        return await update(doctype, newUserSettings)
      }

      return Promise.resolve(newUserSettings)
    } catch (err) {
      const errorObj = err instanceof Error ? err : new Error(String(err))
      error.value = errorObj
      console.error('Error saving user settings:', err)
      throw errorObj
    } finally {
      loading.value = false
    }
  }

  const remove = async (
    doctype: string,
    key: string,
  ): Promise<UserSettings> => {
    if (!doctype || !key) {
      throw new Error('Doctype and key are required')
    }

    try {
      loading.value = true
      error.value = null

      const userSettings: UserSettings = userSettingsCache[doctype] || {}
      const updatedSettings: UserSettings = { ...userSettings }
      delete updatedSettings[key]

      return await update(doctype, updatedSettings)
    } catch (err) {
      const errorObj = err instanceof Error ? err : new Error(String(err))
      error.value = errorObj
      console.error('Error removing user setting:', err)
      throw errorObj
    } finally {
      loading.value = false
    }
  }

  const update = async (
    doctype: string,
    userSettings: UserSettings,
  ): Promise<UserSettings> => {
    if (!doctype) {
      throw new Error('Doctype is required')
    }

    try {
      loading.value = true
      error.value = null

      const response: UserSettings = await call(
        'frappe.model.utils.user_settings.save',
        {
          doctype,
          user_settings: JSON.stringify(userSettings),
        },
      )

      userSettingsCache[doctype] = response
      return response
    } catch (err) {
      const errorObj = err instanceof Error ? err : new Error(String(err))
      error.value = errorObj
      console.error('Error updating user settings:', err)
      throw errorObj
    } finally {
      loading.value = false
    }
  }

  const getCached = (doctype: string, key: string | null = null): any => {
    const settings: UserSettings = userSettingsCache[doctype] || {}
    if (key) {
      return settings[key] || {}
    }
    return settings
  }

  const clearCache = (doctype: string | null = null): void => {
    if (doctype) {
      delete userSettingsCache[doctype]
    } else {
      Object.keys(userSettingsCache).forEach((key) => {
        delete userSettingsCache[key]
      })
    }
  }

  return {
    loading,
    error,
    get,
    save,
    remove,
    update,
    getCached,
    clearCache,
    userSettingsCache: readonly(userSettingsCache),
  }
}

export async function getUserSettings(
  doctype: string,
  key: string | null = null,
): Promise<any> {
  let settings: UserSettings = userSettingsCache[doctype]

  if (!settings) {
    const { get } = useUserSettings()
    settings = await get(doctype)
  }

  if (key) {
    return settings[key] || {}
  }
  return settings
}
