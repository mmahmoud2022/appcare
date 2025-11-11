<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, fly, scale, blur } from 'svelte/transition';
  import { flip } from 'svelte/animate';
  import { elasticOut, cubicOut } from 'svelte/easing';
  import { getPatientPayments, type PatientPaymentHistory } from '../../lib/api-patient';
  import type { Payment } from '../../lib/api-doctor';

  let loading = true;
  let error: string | null = null;
  let payments: Payment[] = [];
  let total = 0;
  let page = 1;
  const pageSize = 10;
  let totalPages = 1;
  let hoveredPayment: number | null = null;

  const statusLabel: Record<Payment['status'], string> = {
    pending: 'En attente',
    completed: 'Payé',
    failed: 'Échoué',
    refunded: 'Remboursé'
  };

  const statusColors: Record<Payment['status'], string> = {
    pending: 'bg-amber-100 text-amber-700',
    completed: 'bg-emerald-100 text-emerald-700',
    failed: 'bg-red-100 text-red-700',
    refunded: 'bg-indigo-100 text-indigo-700'
  };
  
  const statusGradients: Record<Payment['status'], string> = {
    pending: 'from-amber-400 to-orange-500',
    completed: 'from-emerald-400 to-green-500',
    failed: 'from-red-400 to-rose-500',
    refunded: 'from-indigo-400 to-purple-500'
  };
  
  const statusIcons: Record<Payment['status'], string> = {
    pending: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
    completed: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    failed: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
    refunded: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15'
  };

  onMount(() => {
    void loadPayments();
  });

  const loadPayments = async (requestedPage = 1) => {
    if (requestedPage < 1) requestedPage = 1;
    loading = true;
    error = null;
    try {
      const response: PatientPaymentHistory = await getPatientPayments(requestedPage, pageSize);
      payments = response.items;
      total = response.total;
      page = response.page;
    } catch (err) {
      console.error('Erreur lors du chargement des paiements:', err);
      error = 'Impossible de récupérer vos paiements';
    } finally {
      loading = false;
    }
  };

  const hasNextPage = () => page * pageSize < total;

  $: totalPages = Math.max(1, Math.ceil(total / pageSize));

  const formatCurrency = (amount: number, currency: string) =>
    new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(amount);

  const formatDate = (value: string) =>
    new Date(value).toLocaleString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
    
  // Calculate stats
  $: totalAmount = payments.reduce((sum, p) => p.status === 'completed' ? sum + p.amount : sum, 0);
  $: pendingAmount = payments.reduce((sum, p) => p.status === 'pending' ? sum + p.amount : sum, 0);
  $: completedCount = payments.filter(p => p.status === 'completed').length;
  $: pendingCount = payments.filter(p => p.status === 'pending').length;
</script>

<!-- Professional Payments Dashboard -->
<div class="space-y-8" in:fade={{ duration: 400 }}>
  <!-- Clean Professional Header -->
  <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 p-8 shadow-lg">
    <div class="relative z-10 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <div class="w-16 h-16 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center shadow-lg">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
        </div>
        <div>
          <h2 class="text-3xl font-semibold text-white">Mes Paiements</h2>
          <p class="text-blue-100 mt-1">Gérez vos transactions et consultations</p>
        </div>
      </div>
      
      <button
        class="px-6 py-3 bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-xl transition-all shadow-md border border-white/30"
        on:click={() => loadPayments(page)}
        disabled={loading}
      >
        <div class="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span class="text-white font-semibold">Actualiser</span>
        </div>
      </button>
    </div>
  </div>

  <!-- Professional Stats Cards -->
  {#if !loading && !error && payments.length > 0}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <!-- Total Transactions -->
      <div 
        class="bg-white rounded-2xl p-6 shadow-md border border-gray-100 hover:shadow-lg transition-all"
        in:fly={{ y: 20, duration: 400, delay: 0 }}
      >
        <div class="flex items-start justify-between mb-4">
          <div class="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
        </div>
        <p class="text-sm font-medium text-gray-600 uppercase tracking-wide mb-1">Total</p>
        <p class="text-3xl font-semibold text-gray-900">{total}</p>
        <p class="text-xs text-gray-500 mt-1">Transactions</p>
      </div>

      <!-- Total Amount -->
      <div 
        class="bg-white rounded-2xl p-6 shadow-md border border-gray-100 hover:shadow-lg transition-all"
        in:fly={{ y: 20, duration: 400, delay: 50 }}
      >
        <div class="flex items-start justify-between mb-4">
          <div class="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
        <p class="text-sm font-medium text-gray-600 uppercase tracking-wide mb-1">Payé</p>
        <p class="text-3xl font-semibold text-gray-900">{formatCurrency(totalAmount, 'EUR').replace(/\s/g, ' ')}</p>
        <p class="text-xs text-gray-500 mt-1">{completedCount} paiement{completedCount > 1 ? 's' : ''}</p>
      </div>

      <!-- Pending Amount -->
      <div 
        class="bg-white rounded-2xl p-6 shadow-md border border-gray-100 hover:shadow-lg transition-all"
        in:fly={{ y: 20, duration: 400, delay: 100 }}
      >
        <div class="flex items-start justify-between mb-4">
          <div class="w-12 h-12 bg-amber-50 rounded-xl flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
        <p class="text-sm font-medium text-gray-600 uppercase tracking-wide mb-1">En attente</p>
        <p class="text-3xl font-semibold text-gray-900">{formatCurrency(pendingAmount, 'EUR').replace(/\s/g, ' ')}</p>
        <p class="text-xs text-gray-500 mt-1">{pendingCount} en cours</p>
      </div>

      <!-- Current Page -->
      <div 
        class="bg-white rounded-2xl p-6 shadow-md border border-gray-100 hover:shadow-lg transition-all"
        in:fly={{ y: 20, duration: 400, delay: 150 }}
      >
        <div class="flex items-start justify-between mb-4">
          <div class="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
        </div>
        <p class="text-sm font-medium text-gray-600 uppercase tracking-wide mb-1">Page</p>
        <p class="text-3xl font-semibold text-gray-900">{page} <span class="text-xl text-gray-400">/ {totalPages}</span></p>
        <p class="text-xs text-gray-500 mt-1">{payments.length} sur cette page</p>
      </div>
    </div>
  {/if}

  <!-- Payments List -->
  <div class="relative overflow-hidden bg-white rounded-2xl shadow-lg border border-gray-200">
    {#if loading}
      <div class="py-20 flex items-center justify-center" in:scale={{ duration: 400, easing: elasticOut }}>
        <div class="text-center">
          <div class="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p class="text-lg font-medium text-gray-900">Chargement des paiements...</p>
          <p class="text-sm text-gray-600 mt-2">Veuillez patienter</p>
        </div>
      </div>
    {:else if error}
      <div class="py-20 text-center" in:scale={{ duration: 400, easing: elasticOut }}>
        <div class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p class="text-xl font-semibold text-red-600 mb-2">{error}</p>
        <p class="text-gray-600">Réessayez dans quelques instants</p>
      </div>
    {:else if !payments.length}
      <div class="py-20 text-center" in:scale={{ duration: 400, easing: elasticOut }}>
        <div class="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
        </div>
        <h3 class="text-2xl font-semibold text-gray-900 mb-2">Aucun paiement trouvé</h3>
        <p class="text-gray-600">Vos transactions futures apparaîtront ici</p>
      </div>
    {:else}
      <!-- Desktop Table View -->
      <div class="hidden lg:block overflow-x-auto">
        <table class="min-w-full">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-200">
              <th scope="col" class="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Date</th>
              <th scope="col" class="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Praticien</th>
              <th scope="col" class="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Montant</th>
              <th scope="col" class="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Statut</th>
              <th scope="col" class="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Référence</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            {#each payments as payment, i (payment.id)}
              <tr 
                class="hover:bg-blue-50/50 transition-colors"
                on:mouseenter={() => hoveredPayment = payment.id}
                on:mouseleave={() => hoveredPayment = null}
                in:fly={{ y: 20, duration: 400, delay: i * 50 }}
                animate:flip={{ duration: 400 }}
              >
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <span class="text-sm font-medium text-gray-700">{formatDate(payment.created_at)}</span>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center gap-3">
                  <div class="w-10 h-10 bg-indigo-50 rounded-lg flex items-center justify-center font-bold text-indigo-600 text-sm">
                    Dr
                  </div>
                  <span class="text-sm font-medium text-gray-900">Docteur #{payment.doctor_id}</span>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span class="text-base font-semibold text-gray-900">{formatCurrency(payment.amount, payment.currency)}</span>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium ${statusColors[payment.status]}`}>
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="{statusIcons[payment.status]}" />
                    </svg>
                    {statusLabel[payment.status]}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="text-sm text-gray-500 font-mono bg-gray-50 px-3 py-1 rounded">{payment.transaction_id ?? '—'}</span>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <!-- Mobile Card View -->
      <div class="lg:hidden p-6 space-y-4">
        {#each payments as payment, i (payment.id)}
          <div 
            class="bg-white rounded-xl p-5 shadow-md border border-gray-200 hover:shadow-lg transition-all"
            in:fly={{ y: 20, duration: 400, delay: i * 50 }}
            animate:flip={{ duration: 400 }}
          >
            <!-- Header -->
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center gap-3">
                <div class="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center font-bold text-indigo-600 text-sm">
                  Dr
                </div>
                <div>
                  <p class="text-sm font-medium text-gray-900">Docteur #{payment.doctor_id}</p>
                  <p class="text-xs text-gray-500 font-medium">{formatDate(payment.created_at).split(',')[0]}</p>
                </div>
              </div>
              <span class={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium ${statusColors[payment.status]}`}>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="{statusIcons[payment.status]}" />
                </svg>
                {statusLabel[payment.status]}
              </span>
            </div>
            
            <!-- Amount -->
            <div class="mb-3">
              <p class="text-xs text-gray-600 font-medium uppercase tracking-wide mb-1">Montant</p>
              <p class="text-2xl font-semibold text-gray-900">{formatCurrency(payment.amount, payment.currency)}</p>
            </div>
            
            <!-- Reference -->
            {#if payment.transaction_id}
              <div class="pt-3 border-t border-gray-200">
                <p class="text-xs text-gray-600 font-medium uppercase tracking-wide mb-1">Référence</p>
                <p class="text-sm text-gray-500 font-mono bg-gray-50 px-3 py-1.5 rounded inline-block">{payment.transaction_id}</p>
              </div>
            {/if}
          </div>
        {/each}
      </div>

      <!-- Pagination -->
      <div class="border-t border-gray-200 bg-gray-50 px-6 py-4">
        <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div class="text-sm font-medium text-gray-700">
            Page <span class="text-blue-600 font-bold">{page}</span> sur <span class="text-blue-600 font-bold">{totalPages}</span>
          </div>
          <div class="flex gap-3">
            <button
              class="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-white hover:border-blue-500 hover:text-blue-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-sm"
              on:click={() => loadPayments(page - 1)}
              disabled={loading || page <= 1}
            >
              <span class="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
                </svg>
                Précédent
              </span>
            </button>
            <button
              class="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-md hover:shadow-lg"
              on:click={() => loadPayments(page + 1)}
              disabled={loading || !hasNextPage()}
            >
              <span class="flex items-center gap-2">
                Suivant
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </span>
            </button>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .animation-delay-150 {
    animation-delay: 150ms;
  }
</style>