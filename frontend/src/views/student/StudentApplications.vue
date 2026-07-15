<template>
  <div class="page">
    <div class="page-header d-flex justify-content-between align-items-end flex-wrap gap-2">
      <div>
        <h1>My applications</h1>
        <p class="text-muted mb-0">Your full placement application history.</p>
      </div>
      <div class="text-end">
        <button class="btn btn-outline-primary btn-sm" :disabled="exporting" @click="triggerExport">
          {{ exporting ? 'Preparing…' : 'Export as CSV' }}
        </button>
        <button v-if="exportState === 'SUCCESS' && readyFile" class="btn btn-primary btn-sm ms-2" @click="downloadExport">
          Download CSV
        </button>
        <div class="small text-muted mt-1" v-if="exporting">Preparing export… we're also emailing it to you.</div>
        <div class="small text-success mt-1" v-if="exportState === 'SUCCESS' && readyFile">Export ready — check your email or download it here.</div>
        <div class="small text-danger mt-1" v-if="exportError">{{ exportError }}</div>
      </div>
    </div>

    <div class="d-flex align-items-center gap-2 mb-3" v-if="!loading">
      <label class="form-label small mb-0 text-muted">Filter by status:</label>
      <select class="form-select form-select-sm w-auto" v-model="statusFilter" @change="load">
        <option value="">All</option>
        <option v-for="s in STATUSES" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>

    <loading-spinner v-if="loading"></loading-spinner>
    <empty-state v-else-if="!applications.length"
      :message="statusFilter ? `No ${statusFilter} applications.` : `You haven't applied to any drives yet.`"></empty-state>
    <div v-else class="card">
      <div class="table-responsive">
        <table class="table mb-0 align-middle">
          <thead><tr>
            <th>Drive</th><th>Company</th><th>Applied</th><th>Status</th><th>Interview</th><th>Remarks</th>
          </tr></thead>
          <tbody>
            <tr v-for="a in applications" :key="a.id">
              <td>{{ a.drive_title }}</td>
              <td class="text-muted">{{ a.company_name }}</td>
              <td>{{ a.applied_at ? a.applied_at.slice(0,10) : '' }}</td>
              <td><status-pill :status="a.status"></status-pill></td>
              <td>{{ a.interview_datetime ? a.interview_datetime.replace('T', ' ').slice(0,16) : '—' }}</td>
              <td>{{ a.remarks || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from "@/services/api";

export default {
  name: "StudentApplications",
  data() {
    return {
      applications: [], loading: true, exportState: null, exportError: "", exporting: false, readyFile: "",
      statusFilter: "",
      STATUSES: ["Applied", "Shortlisted", "Selected", "Rejected"],
    };
  },
  async mounted() {
    await this.load();
  },
  methods: {
    async load() {
      this.loading = true;
      const qs = this.statusFilter ? `?status=${encodeURIComponent(this.statusFilter)}` : "";
      this.applications = await api.get(`/student/applications${qs}`);
      this.loading = false;
    },
    async triggerExport() {
      this.exportError = "";
      this.readyFile = "";
      this.exporting = true;
      this.exportState = "starting";
      try {
        const { task_id } = await api.post("/student/export", {});
        this.pollExport(task_id);
      } catch (err) {
        this.exportError = err.message;
        this.exportState = null;
        this.exporting = false;
      }
    },
    async pollExport(taskId) {
      this.exportState = "PENDING";
      const poll = async () => {
        const result = await api.get(`/student/export/${taskId}`);
        this.exportState = result.state;
        if (result.state === "SUCCESS") {
          // Don't auto-download: store the filename and reveal a Download button.
          // The CSV is also emailed to the student by the Celery task.
          const file = result.result && result.result.file;
          this.readyFile = file ? file.split("/").pop() : "";
          this.exporting = false;
          return;
        }
        if (result.state === "FAILURE") {
          this.exportError = result.error || "Export failed";
          this.exporting = false;
          return;
        }
        setTimeout(poll, 1500);
      };
      poll();
    },
    async downloadExport() {
      if (!this.readyFile) return;
      try {
        await api.downloadBlob(`/student/export/download/${this.readyFile}`, this.readyFile);
      } catch (err) {
        this.exportError = err.message || "Download failed";
      }
    },
  },
};
</script>
