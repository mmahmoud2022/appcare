<script lang="ts">
  export let show = false;
  
  function close() {
    show = false;
  }
</script>

{#if show}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div 
    class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    on:click={close}
  >
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div 
      class="bg-white rounded-3xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto"
      on:click|stopPropagation
    >
      <!-- Header -->
      <div class="sticky top-0 bg-gradient-to-r from-green-500 to-emerald-600 px-8 py-6 rounded-t-3xl">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h2 class="text-3xl font-black text-white">Téléconsultation</h2>
              <p class="text-green-100 font-semibold">Consultations médicales en ligne via Jitsi Meet</p>
            </div>
          </div>
          <button 
            on:click={close}
            class="w-10 h-10 bg-white/20 hover:bg-white/30 rounded-xl flex items-center justify-center transition-colors"
            aria-label="Fermer la fenêtre d'aide"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="p-8 space-y-6">
        <!-- Introduction -->
        <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border-2 border-blue-200">
          <h3 class="text-xl font-black text-blue-900 mb-3 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Qu'est-ce que la téléconsultation ?
          </h3>
          <p class="text-blue-800 font-medium leading-relaxed">
            La téléconsultation permet de consulter votre médecin à distance par vidéo, sans vous déplacer. 
            C'est pratique, sécurisé et aussi efficace qu'une consultation en cabinet pour de nombreux cas.
          </p>
        </div>

        <!-- How it works -->
        <div>
          <h3 class="text-2xl font-black text-gray-900 mb-4 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Comment ça marche ?
          </h3>
          <div class="space-y-4">
            <div class="flex gap-4">
              <div class="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center text-white font-black shadow-lg">1</div>
              <div>
                <h4 class="font-bold text-gray-900 mb-1">Réservez un rendez-vous</h4>
                <p class="text-gray-600 font-medium">Choisissez "Téléconsultation" lors de la prise de rendez-vous avec votre médecin.</p>
              </div>
            </div>
            <div class="flex gap-4">
              <div class="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center text-white font-black shadow-lg">2</div>
              <div>
                <h4 class="font-bold text-gray-900 mb-1">Recevez le lien de consultation</h4>
                <p class="text-gray-600 font-medium">Un lien de visioconférence unique et sécurisé sera généré automatiquement pour votre rendez-vous.</p>
              </div>
            </div>
            <div class="flex gap-4">
              <div class="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center text-white font-black shadow-lg">3</div>
              <div>
                <h4 class="font-bold text-gray-900 mb-1">Rejoignez à l'heure prévue</h4>
                <p class="text-gray-600 font-medium">15 minutes avant le rendez-vous, cliquez sur le bouton "Rejoindre" pour accéder à la salle de consultation.</p>
              </div>
            </div>
            <div class="flex gap-4">
              <div class="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center text-white font-black shadow-lg">4</div>
              <div>
                <h4 class="font-bold text-gray-900 mb-1">Consultez votre médecin</h4>
                <p class="text-gray-600 font-medium">Parlez avec votre médecin en face à face via vidéo, comme dans un cabinet médical.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Requirements -->
        <div class="bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl p-6 border-2 border-amber-200">
          <h3 class="text-xl font-black text-amber-900 mb-3 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Ce dont vous avez besoin
          </h3>
          <ul class="space-y-2">
            <li class="flex items-start gap-2 text-amber-800 font-medium">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              Une connexion Internet stable (Wi-Fi ou 4G/5G)
            </li>
            <li class="flex items-start gap-2 text-amber-800 font-medium">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              Une webcam et un microphone (ordinateur, smartphone ou tablette)
            </li>
            <li class="flex items-start gap-2 text-amber-800 font-medium">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              Un navigateur moderne (Chrome, Firefox, Safari, Edge)
            </li>
            <li class="flex items-start gap-2 text-amber-800 font-medium">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              Un endroit calme et privé pour la consultation
            </li>
          </ul>
        </div>

        <!-- Security & Privacy -->
        <div class="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6 border-2 border-purple-200">
          <h3 class="text-xl font-black text-purple-900 mb-3 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            Sécurité et confidentialité
          </h3>
          <ul class="space-y-2">
            <li class="flex items-start gap-2 text-purple-800 font-medium">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-purple-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Connexions chiffrées de bout en bout
            </li>
            <li class="flex items-start gap-2 text-purple-800 font-medium">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-purple-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Salles de consultation privées et uniques
            </li>
            <li class="flex items-start gap-2 text-purple-800 font-medium">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-purple-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Conformité RGPD et secret médical
            </li>
            <li class="flex items-start gap-2 text-purple-800 font-medium">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-purple-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Aucun enregistrement permanent des consultations
            </li>
          </ul>
        </div>

        <!-- Tips -->
        <div>
          <h3 class="text-2xl font-black text-gray-900 mb-4 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            Conseils pratiques
          </h3>
          <ul class="space-y-3">
            <li class="flex items-start gap-3">
              <div class="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p class="text-gray-700 font-medium">Testez votre connexion et votre matériel avant l'heure du rendez-vous</p>
            </li>
            <li class="flex items-start gap-3">
              <div class="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p class="text-gray-700 font-medium">Préparez vos questions et documents médicaux à l'avance</p>
            </li>
            <li class="flex items-start gap-3">
              <div class="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p class="text-gray-700 font-medium">Assurez-vous d'avoir un éclairage suffisant pour que le médecin vous voie bien</p>
            </li>
            <li class="flex items-start gap-3">
              <div class="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p class="text-gray-700 font-medium">Connectez-vous quelques minutes avant l'heure prévue</p>
            </li>
          </ul>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-6 border-t border-gray-200 bg-gray-50 rounded-b-3xl">
        <button
          on:click={close}
          class="w-full px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold rounded-xl shadow-lg hover:shadow-xl hover:from-green-600 hover:to-emerald-700 transition-all duration-300"
        >
          J'ai compris
        </button>
      </div>
    </div>
  </div>
{/if}
