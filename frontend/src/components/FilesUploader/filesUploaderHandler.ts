interface UploadOptions {
  fileObj?: File
  private?: boolean
  fileUrl?: string
  folder?: string
  doctype?: string
  docname?: string
  type?: string
}

type EventListenerOption = 'start' | 'progress' | 'finish' | 'error'

declare global {
  interface Window {
    csrf_token?: string
  }
}

class FilesUploadHandler {
  listeners: { [event: string]: Function[] }
  failed: boolean

  constructor() {
    this.listeners = {}
    this.failed = false
  }

  on(event: EventListenerOption, handler: Function) {
    this.listeners[event] = this.listeners[event] || []
    this.listeners[event].push(handler)
  }

  trigger(event: string, data?: any) {
    let handlers = this.listeners[event] || []
    handlers.forEach((handler) => {
      handler.call(this, data)
    })
  }

  upload(file: File | null, options: UploadOptions): Promise<any> {
    return new Promise((resolve, reject) => {
      let xhr = new XMLHttpRequest()
      xhr.upload.addEventListener('loadstart', () => {
        this.trigger('start')
      })
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          this.trigger('progress', {
            uploaded: e.loaded,
            total: e.total,
          })
        }
      })
      xhr.upload.addEventListener('load', () => {
        this.trigger('finish')
      })
      xhr.addEventListener('error', () => {
        this.trigger('error')
        reject()
      })
      xhr.onreadystatechange = () => {
        if (xhr.readyState == XMLHttpRequest.DONE) {
          let error: any = null
          if (xhr.status === 200) {
            let r: any = null
            try {
              r = JSON.parse(xhr.responseText)
            } catch (e) {
              r = xhr.responseText
            }
            let out = r.message || r
            resolve(out)
          } else if (xhr.status === 403) {
            error = JSON.parse(xhr.responseText)
          } else if (xhr.status === 413) {
            this.failed = true
            error = 'Size exceeds the maximum allowed file size.'
          } else {
            this.failed = true
            try {
              error = JSON.parse(xhr.responseText)
            } catch (e) {
              // pass
            }
          }
          if (error && error.exc) {
            console.error(JSON.parse(error.exc)[0])
          }
          reject(error)
        }
      }

      xhr.open('POST', '/api/method/upload_file', true)
      xhr.setRequestHeader('Accept', 'application/json')

      if (window.csrf_token && window.csrf_token !== '{{ csrf_token }}') {
        xhr.setRequestHeader('X-Frappe-CSRF-Token', window.csrf_token)
      }

      let formData = new FormData()

      if (options.fileObj && file?.name) {
        formData.append('file', options.fileObj, file.name)
      }
      formData.append('is_private', options.private || false ? '1' : '0')
      formData.append('folder', options.folder || 'Home')

      if (options.fileUrl) {
        formData.append('file_url', options.fileUrl)
      }

      if (options.doctype) {
        formData.append('doctype', options.doctype)
      }

      if (options.docname) {
        formData.append('docname', options.docname)
      }

      if (options.type) {
        formData.append('type', options.type)
      }

      xhr.send(formData)
    })
  }
}

export default FilesUploadHandler
