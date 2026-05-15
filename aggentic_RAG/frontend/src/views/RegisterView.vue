<script setup>
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../composables/useAuth.js";
import { useToast } from "../composables/useToast.js";

const router = useRouter();
const { register } = useAuth();
const toast = useToast();

const username = ref("");
const password = ref("");
const password2 = ref("");
const error = ref("");
const loading = ref(false);

const pwStrength = computed(() => {
  const p = password.value || "";
  if (!p) return { level: 0, text: "", color: "" };
  let s = 0;
  if (p.length >= 6) s++;
  if (p.length >= 10) s++;
  if (/[A-Z]/.test(p)) s++;
  if (/[0-9]/.test(p)) s++;
  if (/[^A-Za-z0-9]/.test(p)) s++;
  if (s <= 1) return { level: 1, text: "弱", color: "var(--c-error)" };
  if (s <= 3) return { level: 2, text: "中", color: "var(--c-warning)" };
  return { level: 3, text: "强", color: "var(--c-success)" };
});

async function onSubmit() {
  error.value = "";
  if (!username.value.trim() || !password.value) { error.value = "请填写完整信息"; return; }
  if (password.value !== password2.value) { error.value = "两次密码不一致"; return; }
  if (password.value.length < 4) { error.value = "密码至少 4 位"; return; }
  loading.value = true;
  try {
    const data = await register(username.value.trim(), password.value);
    if (data.success) { toast.success("注册成功"); router.push("/"); }
    else { error.value = data.message || "注册失败"; }
  } catch { error.value = "网络错误"; }
  finally { loading.value = false; }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-bg" />
    <div class="auth-card card">
      <div class="auth-hero">
        <span style="font-size:2.5rem">✨</span>
        <h1 style="font-size:1.4rem;font-weight:700;margin:var(--s-2) 0 0">创建账号</h1>
        <p class="text-muted text-sm">开始你的智能旅行规划</p>
      </div>

      <div class="field">
        <label for="u">用户名</label>
        <input id="u" v-model="username" class="input" placeholder="2-30 个字符" :disabled="loading" @keyup.enter="onSubmit" />
      </div>
      <div class="field">
        <label for="p">密码</label>
        <input id="p" v-model="password" class="input" type="password" placeholder="至少 4 位" :disabled="loading" @keyup.enter="onSubmit" />
        <div v-if="password" class="pw-bar mt-1">
          <div class="pw-track"><div class="pw-fill" :style="{ width: (pwStrength.level / 3 * 100) + '%', background: pwStrength.color }" /></div>
          <span class="pw-label" :style="{ color: pwStrength.color }">{{ pwStrength.text }}</span>
        </div>
      </div>
      <div class="field">
        <label for="p2">确认密码</label>
        <input id="p2" v-model="password2" class="input" type="password" placeholder="再次输入" :disabled="loading" @keyup.enter="onSubmit" />
      </div>

      <p v-if="error" class="text-error text-sm mb-2">{{ error }}</p>

      <button class="btn btn-primary btn-lg" style="width:100%;justify-content:center" :disabled="loading" @click="onSubmit">
        {{ loading ? "注册中…" : "注册" }}
      </button>

      <p class="text-center text-sm text-muted mt-3">
        已有账号？<router-link to="/login" style="font-weight:600">去登录</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-page { position: relative; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: var(--s-6); }
.auth-bg { position: absolute; inset: 0; background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%); opacity: .06; z-index: 0; }
.auth-card { width: 380px; position: relative; z-index: 1; padding: var(--s-8); }
.auth-hero { text-align: center; margin-bottom: var(--s-6); }
.field { margin-bottom: var(--s-3); }
.field label { display: block; font-weight: 600; font-size: .85rem; margin-bottom: var(--s-1); }
.pw-bar { display: flex; align-items: center; gap: var(--s-2); }
.pw-track { flex: 1; height: 4px; background: var(--c-border-light); border-radius: 99px; overflow: hidden; }
.pw-fill { height: 100%; border-radius: 99px; transition: width .3s ease; }
.pw-label { font-size: .75rem; font-weight: 600; }
</style>
