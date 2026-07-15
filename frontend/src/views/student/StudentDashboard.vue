<template>
  <div class="page">
    <div class="page-header d-flex justify-content-between align-items-end flex-wrap gap-2">
      <div>
        <h1>Approved drives</h1>
        <p class="text-muted mb-0">Browse open placement drives and apply if you're eligible.</p>
      </div>
      <input class="form-control" style="max-width: 280px" placeholder="Search drives or companies…" v-model="q">
    </div>

    <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
    <loading-spinner v-if="loading"></loading-spinner>
    <empty-state v-else-if="!filteredDrives.length" message="No open drives match your search."></empty-state>

    <div v-else class="d-flex flex-column gap-3">
      <div class="card" v-for="d in filteredDrives" :key="d.id">
        <div class="card-body d-flex justify-content-between align-items-start flex-wrap gap-2">
          <div>
            <h2 class="h6 mb-1">{{ d.title }} <span class="text-muted fw-normal">— {{ d.company_name }}</span></h2>
            <p class="text-muted small mb-1">{{ d.description }}</p>
            <p class="small mb-0">
              Min CGPA {{ d.min_cgpa }} · Branches: {{ d.eligible_branches.join(', ') }} ·
              Years: {{ d.eligible_years.join(', ') }} · Deadline {{ d.deadline }}
            </p>
          </div>
          <div class="text-end">
            <div class="mb-2">
              <status-pill v-if="d.applied" status="Applied"></status-pill>
              <status-pill v-else-if="!d.eligible" status="Rejected"></status-pill>
              <status-pill v-else status="Approved"></status-pill>
            </div>
            <button
              class="btn btn-sm btn-primary"
              :disabled="d.applied || !d.eligible || applying === d.id"
              @click="apply(d)">
              {{ d.applied ? 'Already applied' : (d.eligible ? (applying === d.id ? 'Applying…' : 'Apply') : 'Not eligible') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from "@/services/api";

export default {
  name: "StudentDashboard",
  data() {
    return { profile: null, drives: [], q: "", loading: true, applying: null, error: "" };
  },
  computed: {
    filteredDrives() {
      if (!this.q.trim()) return this.drives;
      const q = this.q.trim().toLowerCase();
      return this.drives.filter(
        (d) => d.title.toLowerCase().includes(q) || (d.company_name || "").toLowerCase().includes(q)
      );
    },
  },
  async mounted() {
    await this.load();
  },
  methods: {
    async load() {
      this.loading = true;
      const data = await api.get("/student/dashboard");
      this.profile = data.profile;
      this.drives = data.drives;
      this.loading = false;
    },
    async apply(drive) {
      this.error = "";
      this.applying = drive.id;
      try {
        await api.post(`/student/drive/${drive.id}/apply`);
        await this.load();
      } catch (err) {
        this.error = (err.errors && Object.values(err.errors)[0]) || err.message;
      } finally {
        this.applying = null;
      }
    },
  },
};
</script>
