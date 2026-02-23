<script setup lang="ts">
import { ref } from 'vue'
import { sendMessage } from '../api/chat'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<Message[]>([])
const input = ref('')
const loading = ref(false)

async function handleSend() {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true

  messages.value.push({ role: 'assistant', content: '' })
  const assistantMsg = messages.value[messages.value.length - 1]!

  try {
    for await (const event of sendMessage(text)) {
      if (event.type === 'text') {
        assistantMsg.content += event.content
      }
    }
  } catch (e) {
    assistantMsg.content = '出错了，请重试。'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="chat-window">
    <div class="messages">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="['message', msg.role]"
      >
        <span class="role">{{ msg.role === 'user' ? '你' : 'AI' }}</span>
        <p>{{ msg.content }}</p>
      </div>
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
</template>

<style scoped>
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 720px;
  margin: 0 auto;
  padding: 1rem;
}
.messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
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
