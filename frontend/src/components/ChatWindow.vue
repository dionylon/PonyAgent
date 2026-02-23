<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { sendMessage } from '../api/chat'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface Session {
  id: string
  title: string
  messages: Message[]
}

const STORAGE_KEY = 'ponyagent_sessions'
const ACTIVE_KEY = 'ponyagent_active'

function newSession(): Session {
  return { id: crypto.randomUUID(), title: '新对话', messages: [] }
}

function loadSessions(): Session[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch {}
  return []
}

const sessions = ref<Session[]>(loadSessions())
if (sessions.value.length === 0) sessions.value.push(newSession())

const activeId = ref<string>(
  localStorage.getItem(ACTIVE_KEY) ?? sessions.value[0].id
)
if (!sessions.value.find(s => s.id === activeId.value)) {
  activeId.value = sessions.value[0].id
}

const current = computed(() => sessions.value.find(s => s.id === activeId.value)!)

const input = ref('')
const loading = ref(false)
const messagesEl = ref<HTMLElement | null>(null)

watch(sessions, val => localStorage.setItem(STORAGE_KEY, JSON.stringify(val)), { deep: true })
watch(activeId, val => localStorage.setItem(ACTIVE_KEY, val))
watch(() => current.value?.messages.length, () => {
  nextTick(() => {
    if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  })
})

function createSession() {
  const s = newSession()
  sessions.value.unshift(s)
  activeId.value = s.id
}

function switchSession(id: string) {
  if (!loading.value) activeId.value = id
}

async function handleSend() {
  const text = input.value.trim()
  if (!text || loading.value) return

  const session = current.value
  session.messages.push({ role: 'user', content: text })
  if (session.title === '新对话') session.title = text.slice(0, 20)
  input.value = ''
  loading.value = true

  session.messages.push({ role: 'assistant', content: '' })
  const assistantMsg = session.messages[session.messages.length - 1]!

  try {
    for await (const event of sendMessage(text, session.id)) {
      if (event.type === 'text') assistantMsg.content += event.content
    }
  } catch {
    assistantMsg.content = '出错了，请重试。'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="app">
    <aside class="sidebar">
      <button class="new-btn" @click="createSession">+ 新对话</button>
      <div class="session-list">
        <div
          v-for="s in sessions"
          :key="s.id"
          :class="['session-item', { active: s.id === activeId }]"
          @click="switchSession(s.id)"
        >
          {{ s.title }}
        </div>
      </div>
    </aside>
    <div class="chat-window">
      <div class="messages" ref="messagesEl">
        <div
          v-for="(msg, i) in current.messages"
          :key="i"
          :class="['message', msg.role]"
        >
          <span class="role">{{ msg.role === 'user' ? '你' : 'AI' }}</span>
          <p>{{ msg.content }}</p>
        </div>
        <div v-if="current.messages.length === 0" class="empty">发送消息开始对话</div>
      </div>
      <div class="input-row">
        <input
          v-model="input"
          placeholder="输入消息..."
          :disabled="loading"
          @keydown.enter="handleSend"
        />
        <button :disabled="loading" @click="handleSend">
          {{ loading ? '...' : '发送' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app {
  display: flex;
  height: 100vh;
  font-family: sans-serif;
}
.sidebar {
  width: 220px;
  background: #1e1e2e;
  color: #cdd6f4;
  display: flex;
  flex-direction: column;
  padding: 0.75rem;
  gap: 0.5rem;
  flex-shrink: 0;
}
.new-btn {
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
}
.new-btn:hover { background: #4338ca; }
.session-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.session-item {
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #a6adc8;
}
.session-item:hover { background: #313244; color: #cdd6f4; }
.session-item.active { background: #313244; color: #cdd6f4; }
.chat-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 1rem;
  overflow: hidden;
}
.messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.empty {
  color: #9ca3af;
  text-align: center;
  margin-top: 2rem;
  font-size: 0.9rem;
}
.message {
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  max-width: 85%;
}
.message.user {
  align-self: flex-end;
  background: #4f46e5;
  color: white;
}
.message.assistant {
  align-self: flex-start;
  background: #f3f4f6;
  color: #111;
}
.role {
  font-size: 0.75rem;
  opacity: 0.6;
  display: block;
  margin-bottom: 0.2rem;
}
.input-row {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}
input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
}
button {
  padding: 0.5rem 1.25rem;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
button:disabled { opacity: 0.5; }
</style>
