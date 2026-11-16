import { createApp } from 'vue'
import 'element-plus/dist/index.css'
import {
  Back,
  Bell,
  CircleCheck,
  DataAnalysis,
  EditPen,
  FirstAidKit,
  Plus,
  Refresh,
  Search,
  Tickets,
  Tools,
  UserFilled,
  View,
  WarningFilled,
} from '@element-plus/icons-vue'
import { ElLoadingDirective } from 'element-plus/es/components/loading/index'

import App from './App.vue'
import router from './router'
import './styles/global.css'

const app = createApp(App)

// 按需注册实际使用的图标，避免全量引入图标库
const icons = {
  Back,
  Bell,
  CircleCheck,
  DataAnalysis,
  EditPen,
  FirstAidKit,
  Plus,
  Refresh,
  Search,
  Tickets,
  Tools,
  UserFilled,
  View,
  WarningFilled,
}

for (const [name, component] of Object.entries(icons)) {
  app.component(name, component)
}

// 按需引入模式下显式注册 v-loading 指令
app.directive('loading', ElLoadingDirective)

app.use(router)
app.mount('#app')
