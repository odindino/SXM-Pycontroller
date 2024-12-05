import { createApp } from 'vue'
import App from './App.vue'
import './style.css'  // 引入全域樣式，包含 Tailwind CSS

// 創建 Vue 應用實例
const app = createApp(App)

// 錯誤處理
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue Error:', err)
  console.error('Error Info:', info)
}

// 全域屬性設定
app.config.globalProperties.$pywebview = window.pywebview

// 開發環境警告
if (import.meta.env.DEV) {
  app.config.warnHandler = (msg, vm, trace) => {
    console.warn('Vue Warning:', msg)
    console.warn('Trace:', trace)
  }
}

// 掛載應用
app.mount('#app')