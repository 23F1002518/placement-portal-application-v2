<template>
  <div class="page">
    <div class="page-header">
      <h1>My profile</h1>
      <p class="text-muted mb-0">Keep your details current so companies see accurate eligibility.</p>
    </div>

    <loading-spinner v-if="loading"></loading-spinner>
    <div v-else class="row g-3">
      <div class="col-md-7">
        <div class="card">
          <div class="card-body">
            <div v-if="saved" class="alert alert-success py-2">Profile updated.</div>
            <form novalidate @submit.prevent="submit">
              <div class="mb-3">
                <label class="form-label">Full name</label>
                <input required class="form-control" :class="{'is-invalid': errors.name}" v-model="form.name">
                <field-error :error="errors.name"></field-error>
              </div>
              <div class="row">
                <div class="col-8 mb-3">
                  <label class="form-label">Branch</label>
                  <select required class="form-select" :class="{'is-invalid': errors.branch}" v-model="form.branch">
                    <option v-for="b in branches" :key="b" :value="b">{{ b }}</option>
                  </select>
                  <field-error :error="errors.branch"></field-error>
                </div>
                <div class="col-4 mb-3">
                  <label class="form-label">CGPA</label>
                  <input type="number" required min="0" max="10" step="0.01"
                    class="form-control" :class="{'is-invalid': errors.cgpa}" v-model="form.cgpa">
                  <field-error :error="errors.cgpa"></field-error>
                </div>
              </div>
              <div class="row">
                <div class="col-6 mb-3">
                  <label class="form-label">Graduation year</label>
                  <input type="number" required :min="currentYear" :max="currentYear + 6"
                    class="form-control" :class="{'is-invalid': errors.graduation_year}" v-model="form.graduation_year">
                  <field-error :error="errors.graduation_year"></field-error>
                </div>
                <div class="col-6 mb-3">
                  <label class="form-label">Phone</label>
                  <input type="tel" pattern="\d{10}" class="form-control" :class="{'is-invalid': errors.phone}" v-model="form.phone">
                  <field-error :error="errors.phone"></field-error>
                </div>
              </div>
              <button class="btn btn-primary" :disabled="saving">{{ saving ? 'Saving…' : 'Save profile' }}</button>
            </form>
          </div>
        </div>
      </div>

      <div class="col-md-5">
        <div class="card">
          <div class="card-body">
            <h2 class="h6 mb-2">Resume</h2>
            <p class="text-muted small" v-if="profile.resume_path">A resume is on file.</p>
            <p class="text-muted small" v-else>No resume uploaded yet.</p>
            <input type="file" class="form-control form-control-sm mb-2" accept=".pdf,.doc,.docx" @change="onFileChange">
            <div v-if="resumeError" class="text-danger small mb-2">{{ resumeError }}</div>
            <button class="btn btn-sm btn-outline-primary" :disabled="resumeUploading" @click="uploadResume">
              {{ resumeUploading ? 'Uploading…' : 'Upload resume' }}
            </button>
            <p class="text-muted small mt-2 mb-0">PDF, DOC, or DOCX. Max 5 MB.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from "@/services/api";
import { useAuthStore } from "@/stores/auth";
import { BRANCHES } from "@/constants";

export default {
  name: "StudentProfile",
  setup() {
    return { store: useAuthStore() };
  },
  data() {
    return {
      branches: BRANCHES,
      profile: null,
      form: {},
      errors: {},
      saving: false,
      saved: false,
      resumeFile: null,
      resumeError: "",
      resumeUploading: false,
      loading: true,
    };
  },
  computed: {
    currentYear() {
      return new Date().getFullYear();
    },
  },
  async mounted() {
    const data = await api.get("/student/dashboard");
    this.profile = data.profile;
    this.form = { ...data.profile };
    this.loading = false;
  },
  methods: {
    async submit() {
      this.errors = {};
      this.saved = false;
      this.saving = true;
      try {
        this.profile = await api.put("/student/profile", this.form);
        const stored = { ...this.store.user, profile: this.profile };
        this.store.setAuth(this.store.token, stored);
        this.saved = true;
      } catch (err) {
        if (err.errors) this.errors = err.errors;
      } finally {
        this.saving = false;
      }
    },
    onFileChange(e) {
      this.resumeFile = e.target.files[0] || null;
    },
    async uploadResume() {
      this.resumeError = "";
      if (!this.resumeFile) {
        this.resumeError = "Select a resume file first";
        return;
      }
      this.resumeUploading = true;
      try {
        const formData = new FormData();
        formData.append("resume", this.resumeFile);
        this.profile = await api.postForm("/student/resume", formData);
      } catch (err) {
        this.resumeError = (err.errors && err.errors.resume) || err.message;
      } finally {
        this.resumeUploading = false;
      }
    },
  },
};
</script>
