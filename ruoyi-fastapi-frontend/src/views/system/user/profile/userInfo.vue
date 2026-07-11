<template>
   <el-form ref="userRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="用户昵称" prop="nickName">
         <el-input v-model="form.nickName" maxlength="30" />
      </el-form-item>
      <el-form-item label="手机号码" prop="phonenumber">
         <el-input v-model="form.phonenumber" maxlength="11" />
      </el-form-item>
      <el-form-item label="邮箱" prop="email">
         <el-input v-model="form.email" maxlength="50" />
      </el-form-item>
      <el-form-item label="性别">
         <el-radio-group v-model="form.sex">
            <el-radio value="0">男</el-radio>
            <el-radio value="1">女</el-radio>
         </el-radio-group>
      </el-form-item>

      <!-- v2.9：电子签名（审批时自动快照）-->
      <el-form-item label="电子签名">
        <div class="signature-pad">
          <canvas
            ref="sigCanvas"
            width="320"
            height="120"
            class="sig-canvas"
            @pointerdown="startDraw"
            @pointermove="draw"
            @pointerup="endDraw"
            @pointerleave="endDraw"
          ></canvas>
          <div class="sig-tip">在上方框内按住鼠标绘制您的签名（将用于审批通过时自动签章）</div>
          <div class="sig-actions">
            <el-button size="small" type="primary" @click="saveSignature" :loading="saving">
              保存签名
            </el-button>
            <el-button size="small" @click="clearSignature">清除</el-button>
            <span v-if="savedHasSig" class="sig-status">
              <el-icon color="#67c23a"><CircleCheckFilled /></el-icon>
              已保存签名
            </span>
            <span v-else class="sig-status gray">未设置签名</span>
          </div>
        </div>
      </el-form-item>

      <el-form-item>
      <el-button type="primary" @click="submit">保存</el-button>
      <el-button type="danger" @click="close">关闭</el-button>
      </el-form-item>
   </el-form>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheckFilled } from '@element-plus/icons-vue'
import { updateUserProfile } from "@/api/system/user";
import { updateSignature } from "@/api/biz/user";

const props = defineProps({
  user: {
    type: Object
  }
});

const { proxy } = getCurrentInstance();

const form = ref({});
const rules = ref({
  nickName: [{ required: true, message: "用户昵称不能为空", trigger: "blur" }],
  email: [{ required: true, message: "邮箱地址不能为空", trigger: "blur" }, { type: "email", message: "请输入正确的邮箱地址", trigger: ["blur", "change"] }],
  phonenumber: [{ required: true, message: "手机号码不能为空", trigger: "blur" }, { pattern: /^1[3|4|5|6|7|8|9][0-9]\d{8}$/, message: "请输入正确的手机号码", trigger: "blur" }],
});

/** 提交按钮 */
function submit() {
  proxy.$refs.userRef.validate(valid => {
    if (valid) {
      updateUserProfile(form.value).then(response => {
        proxy.$modal.msgSuccess("修改成功");
        props.user.phonenumber = form.value.phonenumber;
        props.user.email = form.value.email;
      });
    }
  });
};

/** 关闭按钮 */
function close() {
  proxy.$tab.closePage();
};

// 回显当前登录用户信息
watch(() => props.user, user => {
  if (user) {
    form.value = { nickName: user.nickName, phonenumber: user.phonenumber, email: user.email, sex: user.sex };
  }
},{ immediate: true });

// ========== v2.9 电子签名 canvas ==========
const sigCanvas = ref(null)
const saving = ref(false)
const savedHasSig = ref(false)
let ctx = null
let drawing = false
let lastPt = null
let hasInk = false

function startDraw(e) {
  if (!ctx) return
  drawing = true
  lastPt = ptFromEvent(e)
  hasInk = true
}
function draw(e) {
  if (!drawing || !ctx) return
  const pt = ptFromEvent(e)
  ctx.beginPath()
  ctx.moveTo(lastPt.x, lastPt.y)
  ctx.lineTo(pt.x, pt.y)
  ctx.strokeStyle = '#1f1f1f'
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.stroke()
  lastPt = pt
}
function endDraw() {
  drawing = false
  lastPt = null
}
function ptFromEvent(e) {
  const rect = sigCanvas.value.getBoundingClientRect()
  const cx = e.clientX - rect.left
  const cy = e.clientY - rect.top
  return { x: cx * (sigCanvas.value.width / rect.width), y: cy * (sigCanvas.value.height / rect.height) }
}

function clearSignature() {
  if (!ctx) return
  ctx.clearRect(0, 0, sigCanvas.value.width, sigCanvas.value.height)
  hasInk = false
}

async function saveSignature() {
  if (!hasInk) {
    ElMessage.warning('请先在框内绘制签名')
    return
  }
  saving.value = true
  try {
    const dataURI = sigCanvas.value.toDataURL('image/png')
    const res = await updateSignature(dataURI)
    savedHasSig.value = true
    ElMessage.success(res?.msg || '签名已保存，下次审批通过时将自动签章')
  } catch (e) {
    console.error(e)
    ElMessage.error('保存签名失败')
  } finally {
    saving.value = false
  }
}

function renderSignatureFromBase64(b64) {
  if (!ctx || !b64) return
  const img = new Image()
  img.onload = () => {
    ctx.clearRect(0, 0, sigCanvas.value.width, sigCanvas.value.height)
    ctx.drawImage(img, 0, 0, sigCanvas.value.width, sigCanvas.value.height)
    hasInk = true
  }
  img.src = b64
}

onMounted(async () => {
  await nextTick()
  ctx = sigCanvas.value?.getContext('2d')
  if (ctx) {
    ctx.fillStyle = '#fafafa'
    ctx.fillRect(0, 0, sigCanvas.value.width, sigCanvas.value.height)
  }
  // 如果已存在签名，加载到 canvas
  if (props.user && props.user.signature) {
    savedHasSig.value = true
    renderSignatureFromBase64(props.user.signature)
  }
})
</script>

<style scoped>
.signature-pad {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.sig-canvas {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fafafa;
  cursor: crosshair;
  touch-action: none;
}
.sig-tip { font-size: 12px; color: #909399; }
.sig-actions { display: flex; align-items: center; gap: 8px; }
.sig-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #67c23a;
}
.sig-status.gray { color: #909399; }
</style>
