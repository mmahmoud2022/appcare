<script lang="ts">
  import { onMount } from 'svelte';
  import { 
    getMyReviews,
    respondToReview,
    type DoctorReview
  } from '../../lib/api-doctor';
  
  let reviews: DoctorReview[] = [];
  let loading = true;
  let error: string | null = null;
  let totalReviews = 0;
  let averageRating = 0;
  let replyingTo: number | null = null;
  let responseText = '';
  let responding = false;
  let responseSuccess: string | null = null;

  type RatingValue = 1 | 2 | 3 | 4 | 5;
  const RATING_VALUES: RatingValue[] = [5, 4, 3, 2, 1];

  const createInitialDistribution = (): Record<RatingValue, number> => ({
    5: 0,
    4: 0,
    3: 0,
    2: 0,
    1: 0
  });

  // Rating distribution
  let ratingDistribution: Record<RatingValue, number> = createInitialDistribution();

  onMount(async () => {
    await loadData();
  });

  const loadData = async () => {
    loading = true;
    error = null;
    try {
      const response = await getMyReviews(1, 100);
      reviews = response.items || [];
      totalReviews = response.total;
      
      // Calculate rating distribution
      ratingDistribution = createInitialDistribution();
      let sum = 0;
      
      reviews.forEach(review => {
        const rating = Math.min(5, Math.max(1, Math.round(review.rating))) as RatingValue;
        ratingDistribution[rating]++;
        sum += review.rating;
      });
      
      averageRating = reviews.length > 0 ? sum / reviews.length : 0;
    } catch (err: any) {
      console.error('Error loading reviews:', err);
      error = 'Erreur lors du chargement des avis';
    } finally {
      loading = false;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  };

  const getStars = (rating: number) => {
    return '⭐'.repeat(rating) + '☆'.repeat(5 - rating);
  };

  const getRatingPercentage = (rating: RatingValue) => {
    if (totalReviews === 0) return 0;
    return (ratingDistribution[rating] / totalReviews) * 100;
  };

  const getPatientName = (review: DoctorReview) => {
    const parts = [review.patient_first_name, review.patient_last_name].filter(Boolean);
    return parts.length ? parts.join(' ') : 'Patient';
  };

  const openResponseForm = (review: DoctorReview) => {
    replyingTo = review.id;
    responseText = review.doctor_response ?? '';
    responseSuccess = null;
    error = null;
  };

  const cancelResponse = () => {
    replyingTo = null;
    responseText = '';
  };

  const handleSubmitResponse = async (reviewId: number) => {
    if (!responseText.trim()) {
      error = "Veuillez saisir une réponse à l'avis.";
      return;
    }

    responding = true;
    error = null;
    responseSuccess = null;
    try {
      const updated = await respondToReview(reviewId, responseText.trim());
      reviews = reviews.map(review => review.id === reviewId ? updated : review);
      replyingTo = null;
      responseText = '';
      responseSuccess = 'Réponse envoyée au patient';
      setTimeout(() => responseSuccess = null, 3000);
    } catch (err: any) {
  console.error('Error responding to review:', err);
  error = "Erreur lors de l'envoi de la réponse";
    } finally {
      responding = false;
    }
  };
</script>

<div class="space-y-6">
  <!-- Header -->
  <div>
    <h2 class="text-2xl font-bold text-gray-900">Avis et Évaluations</h2>
    <p class="text-gray-600 mt-1">Ce que vos patients pensent de vous</p>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-12">
      <svg class="animate-spin h-8 w-8 text-emerald-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>
  {:else if error}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
      <p class="text-red-800">{error}</p>
    </div>
  {:else}
    <!-- Rating Overview -->
    <div class="bg-white rounded-lg border border-gray-200 p-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <!-- Average Rating -->
        <div class="text-center">
          <div class="text-6xl font-bold text-gray-900 mb-2">
            {averageRating.toFixed(1)}
          </div>
          <div class="text-3xl mb-3">
            {getStars(Math.round(averageRating))}
          </div>
          <p class="text-gray-600">
            Basé sur <span class="font-semibold">{totalReviews}</span> avis
          </p>
        </div>
        
        <!-- Rating Distribution -->
        <div class="space-y-2">
          {#each RATING_VALUES as rating (rating)}
            <div class="flex items-center gap-3">
              <span class="text-sm font-medium text-gray-700 w-12">
                {rating} ⭐
              </span>
              <div class="flex-1 bg-gray-200 rounded-full h-3 overflow-hidden">
                <div 
                  class="bg-yellow-400 h-full transition-all duration-500"
                  style="width: {getRatingPercentage(rating)}%"
                ></div>
              </div>
              <span class="text-sm text-gray-600 w-16 text-right">
                {ratingDistribution[rating]} 
                ({getRatingPercentage(rating).toFixed(0)}%)
              </span>
            </div>
          {/each}
        </div>
      </div>
    </div>

    {#if reviews.length === 0}
      <div class="text-center py-12 bg-white rounded-lg border border-gray-200">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
        </svg>
        <p class="text-gray-600">Aucun avis pour le moment</p>
        <p class="text-sm text-gray-500 mt-2">Les avis de vos patients apparaîtront ici</p>
      </div>
    {:else}
      <!-- Reviews List -->
      <div class="space-y-4">
        {#each reviews as review}
          <div class="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div class="flex items-start gap-4">
              <!-- Avatar -->
              <div class="w-12 h-12 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full flex items-center justify-center flex-shrink-0">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              
              <!-- Review Content -->
              <div class="flex-1">
                <div class="flex items-start justify-between mb-2">
                  <div>
                    <h4 class="font-semibold text-gray-900">
                      {getPatientName(review)}
                    </h4>
                    <p class="text-sm text-gray-500">{formatDate(review.created_at)}</p>
                  </div>
                  <div class="text-right">
                    <div class="text-2xl mb-1">{getStars(review.rating)}</div>
                    <span class="text-sm font-semibold text-gray-700">{review.rating}/5</span>
                  </div>
                </div>
                
                {#if review.comment}
                  <div class="bg-gray-50 rounded-lg p-4 mt-3">
                    <p class="text-gray-700 leading-relaxed">{review.comment}</p>
                  </div>
                {/if}
                
                {#if review.appointment_id}
                  <div class="mt-3 flex items-center gap-2 text-sm text-gray-500">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Avis vérifié - Rendez-vous #{review.appointment_id}</span>
                  </div>
                {/if}

                {#if review.doctor_response}
                  <div class="mt-4 border border-emerald-200 bg-emerald-50 rounded-lg p-4">
                    <div class="flex items-center gap-2 text-emerald-700 mb-2">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l5-5H7a2 2 0 01-2-2V7a2 2 0 012-2h10a2 2 0 012 2v7" />
                      </svg>
                      <span class="font-semibold">Votre réponse</span>
                    </div>
                    <p class="text-sm text-emerald-900 whitespace-pre-wrap">{review.doctor_response}</p>
                    {#if review.responded_at}
                      <p class="mt-2 text-xs text-emerald-700">Répondu le {formatDate(review.responded_at)}</p>
                    {/if}
                  </div>
                {/if}

                {#if replyingTo === review.id}
                  <form class="mt-4 space-y-3" on:submit|preventDefault={() => handleSubmitResponse(review.id)}>
                    <label for={`review-response-${review.id}`} class="block text-sm font-medium text-gray-700">
                      Votre réponse au patient
                    </label>
                    <textarea
                      id={`review-response-${review.id}`}
                      class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                      rows="4"
                      bind:value={responseText}
                      placeholder="Merci pour votre retour..."
                      disabled={responding}
                    ></textarea>
                    <div class="flex items-center gap-3 justify-end">
                      <button
                        type="button"
                        class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                        on:click={cancelResponse}
                        disabled={responding}
                      >
                        Annuler
                      </button>
                      <button
                        type="submit"
                        class="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50"
                        disabled={responding}
                      >
                        {responding ? 'Envoi...' : 'Envoyer la réponse'}
                      </button>
                    </div>
                  </form>
                {:else if !review.doctor_response}
                  <div class="mt-4 flex justify-end">
                    <button
                      class="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
                      on:click={() => openResponseForm(review)}
                    >
                      Répondre à cet avis
                    </button>
                  </div>
                {/if}
              </div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  {/if}

  {#if responseSuccess}
    <div class="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
      <p class="text-emerald-800">{responseSuccess}</p>
    </div>
  {/if}
</div>

<style>
  /* Add smooth animations */
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .bg-white {
    animation: slideIn 0.3s ease-out;
  }
</style>
