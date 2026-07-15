import { createApp } from "vue";
import { createPinia } from "pinia";
import { Chart, registerables } from "chart.js";

import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";
import "@/assets/style.css";

import App from "@/App.vue";
import router from "@/router";
import { useAuthStore } from "@/stores/auth";

// Shared components registered globally so any view template can use them without
// local registration (matches the pre-Vite behavior).
import FieldError from "@/components/FieldError.vue";
import StatusPill from "@/components/StatusPill.vue";
import LoadingSpinner from "@/components/LoadingSpinner.vue";
import EmptyState from "@/components/EmptyState.vue";
import Navbar from "@/components/Navbar.vue";

Chart.register(...registerables);

const app = createApp(App);
const pinia = createPinia();
app.use(pinia);

app.component("field-error", FieldError);
app.component("status-pill", StatusPill);
app.component("loading-spinner", LoadingSpinner);
app.component("empty-state", EmptyState);
app.component("component-navbar", Navbar);

// Restore persisted auth before the router guard runs on first navigation.
useAuthStore().loadFromStorage();

app.use(router);
app.mount("#app");
