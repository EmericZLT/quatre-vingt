export type WsOptions = {
  url: string
  onOpen?: () => void
  onClose?: () => void
  onMessage?: (ev: MessageEvent) => void
}

export function createWsClient(opts: WsOptions) {
  let ws: WebSocket | null = null
  let retry = 0
  let closedByUser = false

  const connect = () => {
    ws = new WebSocket(opts.url)
    ws.onopen = () => {
      retry = 0
      opts.onOpen?.()
    }
    ws.onclose = () => {
      opts.onClose?.()
      if (!closedByUser) {
        const delay = Math.min(1000 * Math.pow(2, retry++), 10000)
        setTimeout(connect, delay)
      }
    }
    ws.onmessage = (ev) => opts.onMessage?.(ev)
  }

  const send = (data: unknown) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data))
    }
  }
  const close = () => {
    closedByUser = true
    ws?.close()
  }

  connect()
  return { send, close }
}


