<template>
  <div class="page">
    <div class="card auth-card">
      <div class="card-body">
        <h1 class="h4 mb-1">Welcome back</h1>
        <p class="text-muted mb-4">Log in to your placement portal account.</p>

        <div v-if="generalError" class="alert alert-danger py-2">{{ generalError }}</div>

        <form novalidate @submit.prevent="submit">
          <div class="mb-3">
            <label class="form-label">Email</label>
            <input
              type="email" required
              class="form-control" :class="{'is-invalid': errors.email}"
              v-model="form.email" autocomplete="username">
            <field-error :error="errors.email"></field-error>
          </div>
          <div class="mb-3">
            <label class="form-label">Password</label>
            <input
              type="password" required
              class="form-control" :class="{'is-invalid': errors.password}"
              v-model="form.password" autocomplete="current-password">
            <field-error :error="errors.password"></field-error>
          </div>
          <button class="btn btn-primary w-100" :disabled="loading">
            {{ loading ? 'Logging in…' : 'Log in' }}
          </button>
        </form>

        <p class="text-muted small mt-4 mb-0">
          New student? <router-link to="/register/student">Register here</router-link><br>
          New company? <router-link to="/register/company">Register here</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from "@/services/api";
import { useAuthStore } from "@/stores/auth";

export default {
  name: "Login",
  setup() {
    return { store: useAuthStore() };
  },
  data() {
    return {
      form: { email: "", password: "" },
      errors: {},
      generalError: "",
      loading: false,
    };
  },
  methods: {
    async submit() {
      this.errors = {};
      this.generalError = "";
      this.loading = true;
      try {
        const data = await api.post("/login", this.form);
        this.store.setAuth(data.token, data.user);
        this.$router.push(`/${data.user.role}`);
      } catch (err) {
        if (err.errors) this.errors = err.errors;
        else this.generalError = err.message;
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>
