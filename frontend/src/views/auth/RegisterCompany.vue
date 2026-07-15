<template>
  <div class="page">
    <div class="card auth-card">
      <div class="card-body">
        <h1 class="h4 mb-1">Company registration</h1>
        <p class="text-muted mb-4">Register your company. An admin must approve you before you can log in.</p>

        <div v-if="successMessage" class="alert alert-success py-2">
          {{ successMessage }} <router-link to="/login">Back to login →</router-link>
        </div>

        <form v-else novalidate @submit.prevent="submit">
          <div class="mb-3">
            <label class="form-label">Company name</label>
            <input required class="form-control" :class="{'is-invalid': errors.name}" v-model="form.name">
            <field-error :error="errors.name"></field-error>
          </div>
          <div class="mb-3">
            <label class="form-label">Email</label>
            <input type="email" required class="form-control" :class="{'is-invalid': errors.email}" v-model="form.email">
            <field-error :error="errors.email"></field-error>
          </div>
          <div class="mb-3">
            <label class="form-label">Password</label>
            <input
              type="password" required minlength="8" pattern="(?=.*[A-Za-z])(?=.*\d).{8,}"
              title="At least 8 characters, including a letter and a number"
              class="form-control" :class="{'is-invalid': errors.password}" v-model="form.password">
            <field-error :error="errors.password"></field-error>
          </div>
          <div class="mb-3">
            <label class="form-label">HR contact</label>
            <input required class="form-control" :class="{'is-invalid': errors.hr_contact}" v-model="form.hr_contact">
            <field-error :error="errors.hr_contact"></field-error>
          </div>
          <div class="mb-3">
            <label class="form-label">Website <span class="text-muted">(optional)</span></label>
            <input type="url" class="form-control" v-model="form.website" placeholder="https://">
          </div>
          <div class="mb-3">
            <label class="form-label">Description <span class="text-muted">(optional)</span></label>
            <textarea class="form-control" rows="2" v-model="form.description"></textarea>
          </div>
          <button class="btn btn-primary w-100" :disabled="loading">
            {{ loading ? 'Submitting…' : 'Submit registration' }}
          </button>
        </form>

        <p class="text-muted small mt-4 mb-0">
          Already approved? <router-link to="/login">Log in</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from "@/services/api";

export default {
  name: "RegisterCompany",
  data() {
    return {
      form: { name: "", email: "", password: "", hr_contact: "", website: "", description: "" },
      errors: {},
      successMessage: "",
      loading: false,
    };
  },
  methods: {
    async submit() {
      this.errors = {};
      this.loading = true;
      try {
        const data = await api.post("/register/company", this.form);
        this.successMessage = data.message;
      } catch (err) {
        if (err.errors) this.errors = err.errors;
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>
