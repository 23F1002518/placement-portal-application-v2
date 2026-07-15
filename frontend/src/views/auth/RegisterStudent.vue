<template>
  <div class="page">
    <div class="card auth-card">
      <div class="card-body">
        <h1 class="h4 mb-1">Student registration</h1>
        <p class="text-muted mb-4">Create your student account.</p>

        <div v-if="successMessage" class="alert alert-success py-2">
          {{ successMessage }} <router-link to="/login">Log in →</router-link>
        </div>

        <form v-else novalidate @submit.prevent="submit">
          <div class="mb-3">
            <label class="form-label">Full name</label>
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
          <div class="row">
            <div class="col-8 mb-3">
              <label class="form-label">Branch</label>
              <select required class="form-select" :class="{'is-invalid': errors.branch}" v-model="form.branch">
                <option value="" disabled>Select branch</option>
                <option v-for="b in branches" :key="b" :value="b">{{ b }}</option>
              </select>
              <field-error :error="errors.branch"></field-error>
            </div>
            <div class="col-4 mb-3">
              <label class="form-label">CGPA</label>
              <input
                type="number" required min="0" max="10" step="0.01"
                class="form-control" :class="{'is-invalid': errors.cgpa}" v-model="form.cgpa">
              <field-error :error="errors.cgpa"></field-error>
            </div>
          </div>
          <div class="row">
            <div class="col-6 mb-3">
              <label class="form-label">Graduation year</label>
              <input
                type="number" required :min="currentYear" :max="currentYear + 6"
                class="form-control" :class="{'is-invalid': errors.graduation_year}" v-model="form.graduation_year">
              <field-error :error="errors.graduation_year"></field-error>
            </div>
            <div class="col-6 mb-3">
              <label class="form-label">Phone <span class="text-muted">(optional)</span></label>
              <input
                type="tel" pattern="\d{10}" title="10 digit phone number"
                class="form-control" :class="{'is-invalid': errors.phone}" v-model="form.phone">
              <field-error :error="errors.phone"></field-error>
            </div>
          </div>
          <button class="btn btn-primary w-100" :disabled="loading">
            {{ loading ? 'Creating account…' : 'Create account' }}
          </button>
        </form>

        <p class="text-muted small mt-4 mb-0">
          Already registered? <router-link to="/login">Log in</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from "@/services/api";
import { BRANCHES } from "@/constants";

export default {
  name: "RegisterStudent",
  data() {
    return {
      branches: BRANCHES,
      form: { name: "", email: "", password: "", branch: "", cgpa: "", graduation_year: "", phone: "" },
      errors: {},
      successMessage: "",
      loading: false,
    };
  },
  computed: {
    currentYear() {
      return new Date().getFullYear();
    },
  },
  methods: {
    async submit() {
      this.errors = {};
      this.loading = true;
      try {
        const data = await api.post("/register/student", this.form);
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
