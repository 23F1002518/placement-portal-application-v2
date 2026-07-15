import { createRouter, createWebHashHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

import Login from "@/views/auth/Login.vue";
import RegisterStudent from "@/views/auth/RegisterStudent.vue";
import RegisterCompany from "@/views/auth/RegisterCompany.vue";

import AdminDashboard from "@/views/admin/AdminDashboard.vue";
import AdminCompanies from "@/views/admin/AdminCompanies.vue";
import AdminStudents from "@/views/admin/AdminStudents.vue";
import AdminDrives from "@/views/admin/AdminDrives.vue";
import AdminApplications from "@/views/admin/AdminApplications.vue";
import AdminReports from "@/views/admin/AdminReports.vue";

import CompanyDashboard from "@/views/company/CompanyDashboard.vue";
import CompanyApplicants from "@/views/company/CompanyApplicants.vue";

import StudentDashboard from "@/views/student/StudentDashboard.vue";
import StudentApplications from "@/views/student/StudentApplications.vue";
import StudentProfile from "@/views/student/StudentProfile.vue";

const routes = [
  { path: "/", redirect: "/login" },
  { path: "/login", component: Login, meta: { guestOnly: true } },
  { path: "/register/student", component: RegisterStudent, meta: { guestOnly: true } },
  { path: "/register/company", component: RegisterCompany, meta: { guestOnly: true } },

  { path: "/admin", component: AdminDashboard, meta: { roles: ["admin"] } },
  { path: "/admin/companies", component: AdminCompanies, meta: { roles: ["admin"] } },
  { path: "/admin/students", component: AdminStudents, meta: { roles: ["admin"] } },
  { path: "/admin/drives", component: AdminDrives, meta: { roles: ["admin"] } },
  { path: "/admin/applications", component: AdminApplications, meta: { roles: ["admin"] } },
  { path: "/admin/reports", component: AdminReports, meta: { roles: ["admin"] } },

  { path: "/company", component: CompanyDashboard, meta: { roles: ["company"] } },
  { path: "/company/drives/:id/applicants", component: CompanyApplicants, meta: { roles: ["company"] } },

  { path: "/student", component: StudentDashboard, meta: { roles: ["student"] } },
  { path: "/student/applications", component: StudentApplications, meta: { roles: ["student"] } },
  { path: "/student/profile", component: StudentProfile, meta: { roles: ["student"] } },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

router.beforeEach((to) => {
  const store = useAuthStore();
  const isAuthed = !!store.token;

  if (to.meta.guestOnly && isAuthed) {
    return `/${store.role}`;
  }
  if (to.meta.roles) {
    if (!isAuthed) return "/login";
    if (!to.meta.roles.includes(store.role)) return `/${store.role}`;
  }
  return true;
});

export default router;
