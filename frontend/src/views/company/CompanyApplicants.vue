<template>
  <div class="page">
    <div class="page-header">
      <h1>Applicants</h1>
      <router-link to="/company" class="text-muted small">&larr; Back to dashboard</router-link>
    </div>

    <loading-spinner v-if="loading"></loading-spinner>
    <empty-state v-else-if="!applicants.length" message="No applicants yet."></empty-state>
    <div v-else class="d-flex flex-column gap-3">
      <div class="card" v-for="app in applicants" :key="app.id">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
            <div>
              <h2 class="h6 mb-1">{{ app.student_name }}</h2>
              <status-pill :status="app.status"></status-pill>
              <span class="text-muted small ms-2">Applied {{ app.applied_at ? app.applied_at.slice(0,10) : '' }}</span>
            </div>
            <div class="btn-group btn-group-sm">
              <button v-for="s in nextStatuses(app.status)" :key="s"
                class="btn btn-outline-primary" @click="setStatus(app, s)">{{ s }}</button>
              <button v-if="app.status === 'Selected' && !app.has_offer_letter"
                class="btn btn-outline-primary" @click="generateOffer(app)">Generate offer letter</button>
              <button v-if="app.has_offer_letter" class="btn btn-outline-secondary"
                @click="downloadOfferLetter(app)">Download offer letter</button>
              <button v-if="app.has_offer_letter" class="btn btn-outline-primary"
                :disabled="app._emailing" @click="emailOfferLetter(app)">
                {{ app._emailing ? 'Sending…' : 'Send email' }}</button>
              <button class="btn btn-outline-secondary" @click="viewResume(app)">View resume</button>
            </div>
          </div>

          <div class="row mt-3">
            <div class="col-md-6 mb-2">
              <label class="form-label small">Interview date &amp; time</label>
              <input type="datetime-local" class="form-control form-control-sm"
                v-model="app._interviewInput" :placeholder="app.interview_datetime">
            </div>
            <div class="col-md-6 mb-2">
              <label class="form-label small">Remarks</label>
              <input class="form-control form-control-sm" v-model="app.remarks">
            </div>
          </div>
          <button class="btn btn-sm btn-outline-secondary" @click="saveInterview(app)">Save interview &amp; remarks</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from "@/services/api";

export default {
  name: "CompanyApplicants",
  data() {
    return { applicants: [], loading: true };
  },
  async mounted() {
    await this.load();
  },
  methods: {
    async load() {
      this.loading = true;
      this.applicants = await api.get(`/company/drive/${this.$route.params.id}/applicants`);
      this.loading = false;
    },
    nextStatuses(current) {
      const transitions = {
        Applied: ["Shortlisted", "Rejected"],
        Shortlisted: ["Selected", "Rejected"],
        Selected: [],
        Rejected: [],
      };
      return transitions[current] || [];
    },
    async setStatus(app, status) {
      await api.put(`/company/application/${app.id}`, { status });
      await this.load();
    },
    async saveInterview(app) {
      await api.put(`/company/application/${app.id}`, {
        interview_datetime: app._interviewInput || null,
        remarks: app.remarks || "",
      });
      await this.load();
    },
    async generateOffer(app) {
      await api.post(`/company/application/${app.id}/offer-letter`);
      await this.load();
    },
    async downloadOfferLetter(app) {
      await api.downloadBlob(`/offer-letter/${app.id}`, `offer_letter_${app.student_name}.pdf`);
    },
    async emailOfferLetter(app) {
      app._emailing = true;
      try {
        await api.post(`/company/application/${app.id}/offer-letter/email`);
        alert(`Offer letter is being emailed to ${app.student_name}.`);
      } catch (e) {
        alert(e.message || "Failed to send the offer letter email.");
      } finally {
        app._emailing = false;
      }
    },
    async viewResume(app) {
      try {
        await api.downloadBlob(`/resume/${app.student_user_id}`, `resume_${app.student_name}`);
      } catch (e) {
        alert("No resume available for this student yet.");
      }
    },
  },
};
</script>
