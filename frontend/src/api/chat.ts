export interface TextEvent {
  type: 'text'
  content: string
}

export interface DoneEvent {
  type: 'done'
}

export type ChatEvent = TextEvent | DoneEvent

export async function* sendMessage(
  message: string,
  threadId = 'default',
): AsyncGenerator<ChatEvent> {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, thread_id: threadId }),
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const event: ChatEvent = JSON.parse(line.slice(6))
        yield event
      }
    }
  }
}
