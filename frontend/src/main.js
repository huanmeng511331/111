import { createApp } from 'vue'
import { ElAlert } from 'element-plus/es/components/alert/index'
import { ElButton } from 'element-plus/es/components/button/index'
import { ElCheckbox } from 'element-plus/es/components/checkbox/index'
import { ElCol } from 'element-plus/es/components/col/index'
import { ElConfigProvider } from 'element-plus/es/components/config-provider/index'
import { ElAside, ElContainer, ElHeader, ElMain } from 'element-plus/es/components/container/index'
import { ElDatePicker } from 'element-plus/es/components/date-picker/index'
import {
  ElDescriptions,
  ElDescriptionsItem
} from 'element-plus/es/components/descriptions/index'
import { ElEmpty } from 'element-plus/es/components/empty/index'
import { ElForm, ElFormItem } from 'element-plus/es/components/form/index'
import { ElIcon } from 'element-plus/es/components/icon/index'
import { ElInput } from 'element-plus/es/components/input/index'
import { ElLink } from 'element-plus/es/components/link/index'
import { vLoading } from 'element-plus/es/components/loading/index'
import { ElMenu, ElMenuItem } from 'element-plus/es/components/menu/index'
import { ElOption, ElSelect } from 'element-plus/es/components/select/index'
import { ElPagination } from 'element-plus/es/components/pagination/index'
import { ElRadioButton, ElRadioGroup } from 'element-plus/es/components/radio/index'
import { ElRow } from 'element-plus/es/components/row/index'
import { ElStep, ElSteps } from 'element-plus/es/components/steps/index'
import { ElTable, ElTableColumn } from 'element-plus/es/components/table/index'
import { ElTag } from 'element-plus/es/components/tag/index'
import { ElTimeline, ElTimelineItem } from 'element-plus/es/components/timeline/index'
import 'element-plus/dist/index.css'
import 'element-plus/es/components/loading/style/css'

import App from './App.vue'
import router from './router'
import './styles/index.css'

const app = createApp(App)

// 按需注册用到的 Element Plus 组件，避免全量引入带来的体积与构建内存开销。
const components = {
  ElAlert,
  ElAside,
  ElButton,
  ElCheckbox,
  ElCol,
  ElConfigProvider,
  ElContainer,
  ElDatePicker,
  ElDescriptions,
  ElDescriptionsItem,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElHeader,
  ElIcon,
  ElInput,
  ElLink,
  ElMain,
  ElMenu,
  ElMenuItem,
  ElOption,
  ElPagination,
  ElRadioButton,
  ElRadioGroup,
  ElRow,
  ElSelect,
  ElStep,
  ElSteps,
  ElTable,
  ElTableColumn,
  ElTag,
  ElTimeline,
  ElTimelineItem
}

Object.entries(components).forEach(([name, component]) => {
  app.component(name, component)
})

app.directive('loading', vLoading)
app.use(router)
app.mount('#app')
