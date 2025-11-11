<script lang="ts" context="module">
  export interface ToastMessage {
    id: number;
    type: 'success' | 'error' | 'warning' | 'info';
    message: string;
    duration?: number;
  }

  let nextId = 0;
  const toastsStore = writable<ToastMessage[]>([]);

  function addToast(
    type: ToastMessage['type'], 
    message: string, 
    duration = 5000
  ): number {
    const id = nextId++;
    const toast: ToastMessage = { id, type, message, duration };
    
    toastsStore.update(t => [...t, toast]);
    
    if (duration > 0) {
      setTimeout(() => removeToast(id), duration);
    }
    
    return id;
  }

  function removeToast(id: number) {
    toastsStore.update(t => t.filter(toast => toast.id !== id));
  }

  export const toast = {
    success: (message: string, duration?: number) => addToast('success', message, duration),
    error: (message: string, duration?: number) => addToast('error', message, duration),
    warning: (message: string, duration?: number) => addToast('warning', message, duration),
    info: (message: string, duration?: number) => addToast('info', message, duration),
  };
</script>

<script lang="ts">
  import { writable } from 'svelte/store';

  $: toasts = $toastsStore;
</script>

<div class="fixed top-4 right-4 z-[200] space-y-2 pointer-events-none">
  {#each toasts as toast (toast.id)}
    <div 
      class={`pointer-events-auto transform transition-all duration-300 ease-out max-w-md rounded-2xl shadow-2xl p-4 border-2 ${
        toast.type === 'success' 
          ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-300' 
          : toast.type === 'error'
          ? 'bg-gradient-to-r from-red-50 to-rose-50 border-red-300'
          : toast.type === 'warning'
          ? 'bg-gradient-to-r from-amber-50 to-orange-50 border-amber-300'
          : 'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-300'
      }`}
      role="alert"
    >
      <div class="flex items-start gap-3">
        <div class={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md ${
          toast.type === 'success' 
            ? 'bg-green-500' 
            : toast.type === 'error'
            ? 'bg-red-500'
            : toast.type === 'warning'
            ? 'bg-amber-500'
            : 'bg-blue-500'
        }`}>
          {#if toast.type === 'success'}
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          {:else if toast.type === 'error'}
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          {:else if toast.type === 'warning'}
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          {:else}
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          {/if}
        </div>
        <div class="flex-1 min-w-0">
          <p class={`text-sm font-bold ${
            toast.type === 'success' 
              ? 'text-green-900' 
              : toast.type === 'error'
              ? 'text-red-900'
              : toast.type === 'warning'
              ? 'text-amber-900'
              : 'text-blue-900'
          }`}>
            {toast.message}
          </p>
        </div>
        <button
          on:click={() => removeToast(toast.id)}
          class="w-6 h-6 rounded-lg hover:bg-black/5 transition-colors flex items-center justify-center flex-shrink-0"
          aria-label="Fermer"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  {/each}
</div>
