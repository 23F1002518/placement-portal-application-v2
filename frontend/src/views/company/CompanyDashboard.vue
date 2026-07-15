<template>
  <div class="page">
    <div class="page-header">
      <h1>Company dashboard</h1>
      <p class="text-muted mb-0" v-if="profile">
        {{ profile.name }}
        <status-pill :status="profile.approved ? 'Approved' : 'Pending'"></status-pill>
      </p>
    </div>

    <loading-spinner v-if="loading"></loading-spinner>

    <template v-else>
      <div v-if="!profile.approved" class="alert alert-warning">
        Your company is awaiting admin approval. You can create drives once approved.
      </div>

      <div class="d-flex justify-content-between align-items-center mb-3">
        <h2 class="h6 mb-0">Your placement drives</h2>
        <button class="btn btn-primary btn-sm" :disabled="!profile.approved" @click="startCreate">+ New drive</button>
      </div>

      <div class="card mb-4" v-if="showForm">
        <div class="card-body">
          <h3 class="h6 mb-3">{{ editingId ? 'Edit drive' : 'Create drive' }}</h3>
          <div v-if="hasErrors" class="alert alert-danger py-2">
            Please fix the highlighted field(s) below.
            <div v-for="(msg, key) in generalErrors" :key="key">{{ msg }}</div>
          </div>
          <form novalidate @submit.prevent="submitDrive">
            <div class="mb-3">
              <label class="form-label">Job title</label>
              <input required class="form-control" :class="{'is-invalid': errors.title}" v-model="form.title">
              <field-error :error="errors.title"></field-error>
            </div>
            <div class="mb-3">
              <label class="form-label">Description</label>
              <textarea required rows="3" class="form-control" :class="{'is-invalid': errors.description}" v-model="form.description"></textarea>
              <field-error :error="errors.description"></field-error>
            </div>
            <div class="mb-3">
              <label class="form-label">Eligible branches</label>
              <div class="d-flex flex-wrap gap-3">
                <div class="form-check" v-for="b in branches" :key="b">
                  <input type="checkbox" class="form-check-input" :id="'b-'+b" :value="b" v-model="form.eligible_branches">
                  <label class="form-check-label" :for="'b-'+b">{{ b }}</label>
                </div>
              </div>
              <field-error :error="errors.eligible_branches"></field-error>
            </div>
            <div class="row">
              <div class="col-6 mb-3">
                <label class="form-label">Minimum CGPA</label>
                <input type="number" required min="0" max="10" step="0.01"
                  class="form-control" :class="{'is-invalid': errors.min_cgpa}" v-model="form.min_cgpa">
                <field-error :error="errors.min_cgpa"></field-error>
              </div>
              <div class="col-6 mb-3">
                <label class="form-label">Application deadline</label>
                <input type="date" required
                  class="form-control" :class="{'is-invalid': errors.deadline}" v-model="form.deadline">
                <field-error :error="errors.deadline"></field-error>
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label">Eligible graduation years</label>
              <div class="d-flex flex-wrap gap-3">
                <div class="form-check" v-for="y in yearOptions" :key="y">
                  <input type="checkbox" class="form-check-input" :id="'y-'+y" :value="y" v-model="form.eligible_years">
                  <label class="form-check-label" :for="'y-'+y">{{ y }}</label>
                </div>
              </div>
              <field-error :error="errors.eligible_years"></field-error>
            </div>
            <div class="d-flex gap-2">
              <button class="btn btn-primary" :disabled="saving">{{ saving ? 'Saving…' : 'Save drive' }}</button>
              <button type="button" class="btn btn-outline-secondary" @click="cancelForm">Cancel</button>
            </div>
          </form>
        </div>
      </div>

      <empty-state v-if="!drives.length" message="No drives created yet."></empty-state>
      <div v-else class="card">
        <div class="table-responsive">
          <table class="table mb-0 align-middle">
            <thead><tr>
              <th>Title</th><th>Deadline</th><th>Applicants</th><th>Status</th><th></th>
            </tr></thead>
            <tbody>
              <tr v-for="d in drives" :key="d.id">
                <td>{{ d.title }}</td>
                <td>{{ d.deadline }}</td>
                <td>{{ d.applicant_count }}</td>
                <td><status-pill :status="d.status"></status-pill></td>
                <td class="text-end">
                  <div class="btn-group btn-group-sm">
                    <router-link class="btn btn-outline-primary" :to="'/company/drives/' + d.id + '/applicants'">Applicants</router-link>
                    <button class="btn btn-outline-secondary" @click="startEdit(d)">Edit</button>
                    <button v-if="d.status !== 'Closed'" class="btn btn-outline-danger" @click="closeDrive(d)">Close</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { api } from "@/services/api";
import { BRANCHES } from "@/constants";

function emptyDriveForm() {
  const year = new Date().getFullYear();
  return {
    title: "",
    description: "",
    eligible_branches: [],
    min_cgpa: "",
    eligible_years: [year],
    deadline: "",
  };
}

export default {
  name: "CompanyDashboard",
  data() {
    return {
      branches: BRANCHES,
      profile: null,
      drives: [],
      loading: true,
      showForm: false,
      editingId: null,
      form: emptyDriveForm(),
      errors: {},
      saving: false,
    };
  },
  computed: {
    yearOptions() {
      const y = new Date().getFullYear();
      return [y, y + 1, y + 2, y + 3];
    },
    hasErrors() {
      return Object.keys(this.errors).length > 0;
    },
    // Error keys not bound to a specific input (e.g. "company", "general") — shown in the banner.
    generalErrors() {
      const fieldKeys = ["title", "description", "eligible_branches", "min_cgpa", "deadline", "eligible_years"];
      const out = {};
      for (const [k, v] of Object.entries(this.errors)) {
        if (!fieldKeys.includes(k)) out[k] = v;
      }
      return out;
    },
  },
  async mounted() {
    await this.load();
  },
  methods: {
    async load() {
      this.loading = true;
      const data = await api.get("/company/dashboard");
      this.profile = data.profile;
      this.drives = data.drives;
      this.loading = false;
    },
    startCreate() {
      this.editingId = null;
      this.form = emptyDriveForm();
      this.errors = {};
      this.showForm = true;
    },
    startEdit(drive) {
      this.editingId = drive.id;
      this.form = {
        title: drive.title,
        description: drive.description,
        eligible_branches: [...drive.eligible_branches],
        min_cgpa: drive.min_cgpa,
        eligible_years: [...drive.eligible_years],
        deadline: drive.deadline,
      };
      this.errors = {};
      this.showForm = true;
    },
    cancelForm() {
      this.showForm = false;
    },
    async submitDrive() {
      this.errors = {};
      this.saving = true;
      try {
        if (this.editingId) {
          await api.put(`/company/drive/${this.editingId}`, this.form);
        } else {
          await api.post("/company/drive", this.form);
        }
        this.showForm = false;
        await this.load();
      } catch (err) {
        if (err.errors) this.errors = err.errors;
        else if (err.message) this.errors = { general: err.message };
      } finally {
        this.saving = false;
      }
    },
    async closeDrive(drive) {
      const ok = confirm(
        `Close the drive "${drive.title}"? Students will no longer be able to apply. This cannot be undone.`
      );
      if (!ok) return;
      await api.post(`/company/drive/${drive.id}/close`);
      await this.load();
    },
  },
};
</script>
