<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from './lib/stores/auth';
  import { router } from './lib/router';

  // Import UI components
  import Toast from './components/ui/Toast.svelte';

  // Import routes
  import Home from './routes/Home.svelte';
  import Login from './routes/Login.svelte';
  import PatientRegister from './routes/patients/PatientRegister.svelte';
  import PatientDashboard from './routes/patients/PatientDashboard.svelte';
  import DoctorRegister from './routes/doctors/DoctorRegister.svelte';
  import DoctorDashboard from './routes/doctors/DoctorDashboard.svelte';
  import DoctorAppointments from './routes/doctors/DoctorAppointments.svelte';
  import AdminLogin from './routes/admin/Login.svelte';
  import AdminRegister from './routes/admin/Register.svelte';
  import AdminDashboard from './routes/admin/AdminDashboard.svelte';
  import VerifyEmail from './routes/VerifyEmail.svelte';
  import RequestPasswordReset from './routes/RequestPasswordReset.svelte';
  import ResetPassword from './routes/ResetPassword.svelte';

  let currentPath = '/';
  let componentProps = {};
  let component: any = Home;

  // Subscribe to route changes
  router.subscribe(path => {
    currentPath = path;
  });

  // Initialize auth store on app load
  onMount(() => {
    authStore.init();
  });

  // Simple route matching with dynamic support for appointment details
  $: {
    componentProps = {};
    if (currentPath === '/') component = Home;
    else if (currentPath === '/login') component = Login;
    else if (currentPath === '/register/patient') component = PatientRegister;
    else if (currentPath === '/register/doctor') component = DoctorRegister;
    else if (currentPath === '/patients/dashboard') component = PatientDashboard;
    else if (currentPath === '/doctors/dashboard') component = DoctorDashboard;
    else if (currentPath === '/doctors/appointments') component = DoctorAppointments;
    else if (currentPath.startsWith('/doctors/appointments/')) {
      component = DoctorAppointments;
      const parts = currentPath.split('/');
      const id = parts[parts.length - 1];
      componentProps = { appointmentId: id };
    }
    else if (currentPath === '/admin/login') component = AdminLogin;
    else if (currentPath === '/admin/register') component = AdminRegister;
    else if (currentPath === '/admin' || currentPath === '/admin/dashboard') component = AdminDashboard;
    else if (currentPath === '/verify-email' || currentPath.startsWith('/verify-email?')) component = VerifyEmail;
    else if (currentPath === '/forgot-password') component = RequestPasswordReset;
    else if (currentPath === '/reset-password' || currentPath.startsWith('/reset-password?')) component = ResetPassword;
    else component = Home; // Default fallback
  }
</script>

<!-- Global Toast Notifications -->
<Toast />

<!-- Current Route Component -->
<svelte:component this={component} {...componentProps} />
