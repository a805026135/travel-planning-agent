<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../composables/useAuth.js";
import { useToast } from "../composables/useToast.js";

const router = useRouter();
const { login } = useAuth();
const toast = useToast();

const username = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

async function onSubmit() {
  error.value = ""; if (!username.value.trim() || !password.value.trim()) { error.value = "请填写用户名和密码"; return; }
  loading.value = true;
  try {
    const data = await login(username.value.trim(), password.value);
    if (data.success) { toast.success("登录成功"); router.push("/"); }
    else { error.value = data.message || "登录失败"; }
  } catch (e) { error.value = "网络错误"; }
  finally { loading.value = false; }
}

async function demoLogin() {
  loading.value = true; error.value = "";
  try {
    // 尝试注册演示账号（如果不存在）
    await fetch("/api/auth/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: "demo", password: "demo1234" }) });
  } catch {}
  try {
    const data = await login("demo", "demo1234");
    if (data.success) { toast.success("演示账号登录成功"); router.push("/"); }
    else { error.value = data.message; }
  } catch { error.value = "演示登录失败"; }
  finally { loading.value = false; }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-bg" />
    <div class="auth-card card">
      <div class="auth-hero">
        <span style="font-size:2.5rem">✈️</span>
        <h1 style="font-size:1.4rem;font-weight:700;margin:var(--s-2) 0 0">智能旅行规划</h1>
        <p class="text-muted text-sm">登录以访问你的旅行计划</p>
      </div>

      <div class="field">
        <label for="u">用户名</label>
        <input id="u" v-model="username" class="input" placeholder="输入用户名" :disabled="loading" @keyup.enter="onSubmit" />
      </div>
      <div class="field">
        <label for="p">密码</label>
        <input id="p" v-model="password" class="input" type="password" placeholder="输入密码" :disabled="loading" @keyup.enter="onSubmit" />
      </div>

      <p v-if="error" class="text-error text-sm mb-2">{{ error }}</p>

      <button class="btn btn-primary btn-lg" style="width:100%;justify-content:center" :disabled="loading" @click="onSubmit">
        {{ loading ? "登录中…" : "登录" }}
      </button>

      <button class="btn btn-ghost btn-sm mt-1" style="width:100%;justify-content:center" @click="demoLogin">
        🎭 演示账号快速登录
      </button>

      <p class="text-center text-sm text-muted mt-3">
        还没有账号？<router-link to="/register" style="font-weight:600">立即注册</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-page { position: relative; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: var(--s-6); }
.auth-bg { position: absolute; inset: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); opacity: .06; z-index: 0; }
.auth-card { width: 380px; position: relative; z-index: 1; padding: var(--s-8); }
.auth-hero { text-align: center; margin-bottom: var(--s-6); }
.field { margin-bottom: var(--s-3); }
.field label { display: block; font-weight: 600; font-size: .85rem; margin-bottom: var(--s-1); }
</style>
