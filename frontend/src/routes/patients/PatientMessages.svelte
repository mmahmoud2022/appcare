<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { fade, fly, scale, blur } from 'svelte/transition';
  import { flip } from 'svelte/animate';
  import { elasticOut, cubicOut } from 'svelte/easing';
  import { getCurrentUser } from '../../lib/api';
  import {
    getPatientMessages,
    markMessageAsRead,
    type PatientMessageList
  } from '../../lib/api-patient';
  import type { DoctorMessage } from '../../lib/api-doctor';

  type Conversation = {
    userId: number;
    userName: string;
    messages: DoctorMessage[];
    lastMessage: DoctorMessage;
    unreadCount: number;
  };

  let loading = true;
  let error: string | null = null;
  let conversations: Map<number, Conversation> = new Map();
  let selectedConversation: number | null = null;
  let activeConversation: Conversation | null = null;
  let currentUserId: number | null = null;
  let pollingInterval: number | null = null;

  let messagesContainer: HTMLDivElement;
  let hoveredConversation: number | null = null;

  onMount(() => {
    let active = true;

    const initialise = async () => {
      const user = await getCurrentUser();
      if (!active) return;
      currentUserId = user.id;
      await loadMessages();
      if (!active) return;
      pollingInterval = window.setInterval(() => {
        void loadMessages(false);
      }, 10000);
    };

    void initialise();

    return () => {
      active = false;
      if (pollingInterval !== null) {
        window.clearInterval(pollingInterval);
        pollingInterval = null;
      }
    };
  });

  const loadMessages = async (showLoader = true) => {
    if (showLoader) loading = true;
    error = null;
    try {
      const response: PatientMessageList = await getPatientMessages(1, 200);
      buildConversations(response.items);
    } catch (err) {
      console.error('Erreur lors du chargement des messages:', err);
      error = "Impossible de récupérer vos messages";
    } finally {
      loading = false;
    }
  };

  const buildConversations = (messages: DoctorMessage[]) => {
    const map = new Map<number, Conversation>();
    messages.forEach((message) => {
      const otherUserId = message.sender_id === currentUserId ? message.recipient_id : message.sender_id;
      const otherUserName = message.sender_id === currentUserId
        ? `${message.recipient_first_name ?? ''} ${message.recipient_last_name ?? ''}`.trim() || 'Médecin'
        : `${message.sender_first_name ?? ''} ${message.sender_last_name ?? ''}`.trim() || 'Médecin';

      const conversation = map.get(otherUserId) ?? {
        userId: otherUserId,
        userName: otherUserName,
        messages: [],
        lastMessage: message,
        unreadCount: 0
      };

      conversation.messages.push(message);
      if (new Date(message.created_at) > new Date(conversation.lastMessage.created_at)) {
        conversation.lastMessage = message;
      }
      if (!message.is_read && message.recipient_id === currentUserId) {
        conversation.unreadCount += 1;
      }

      map.set(otherUserId, conversation);
    });

    map.forEach((conversation) => {
      conversation.messages.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
      conversation.lastMessage = conversation.messages[conversation.messages.length - 1];
    });

    conversations = map;
    if (selectedConversation === null && map.size > 0) {
      selectedConversation = map.keys().next().value ?? null;
    } else if (selectedConversation !== null && !map.has(selectedConversation)) {
      selectedConversation = map.keys().next().value ?? null;
    }
  };

  const conversationsArray = () => Array.from(conversations.values()).sort((a, b) => new Date(b.lastMessage.created_at).getTime() - new Date(a.lastMessage.created_at).getTime());

  $: activeConversation = selectedConversation !== null ? conversations.get(selectedConversation) ?? null : null;
  
  // Marquer les messages comme lus lorsqu'une conversation est sélectionnée
  $: if (activeConversation && currentUserId) {
    markConversationMessagesAsRead(activeConversation);
  }

  const markConversationMessagesAsRead = async (conversation: Conversation) => {
    // Récupérer les messages non lus reçus par le patient
    const unreadMessages = conversation.messages.filter(
      msg => !msg.is_read && msg.recipient_id === currentUserId
    );
    
    // Marquer chaque message non lu comme lu
    for (const message of unreadMessages) {
      try {
        await markMessageAsRead(message.id);
        // Mettre à jour localement
        message.is_read = true;
        message.read_at = new Date().toISOString();
      } catch (err) {
        console.error(`Erreur lors du marquage du message ${message.id} comme lu:`, err);
      }
    }
    
    // Mettre à jour le compteur de non lus
    if (unreadMessages.length > 0) {
      conversation.unreadCount = 0;
      conversations = conversations; // Trigger reactivity
    }
  };

  const formatTime = (value: string) => {
    const date = new Date(value);
    return date.toLocaleString('fr-FR', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isSentByPatient = (message: DoctorMessage) => currentUserId !== null && message.sender_id === currentUserId;

  const scrollToBottom = () => {
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  };
</script>

<!-- Modern Messaging Interface -->
<div 
  class="relative overflow-hidden rounded-3xl shadow-2xl h-[700px] flex"
  in:fade={{ duration: 400 }}
>
  <!-- Background gradient -->
  <div class="absolute inset-0 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 opacity-50"></div>
  
  <!-- Conversations Sidebar -->
  <div class="relative w-96 flex flex-col bg-white/80 backdrop-blur-xl border-r border-gray-200/50 z-10">
    <!-- Sidebar Header -->
    <div class="relative overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>
      <div class="absolute inset-0 bg-white/10 backdrop-blur-sm"></div>
      
      <div class="relative z-10 p-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-2xl font-black text-white mb-1 drop-shadow-lg">Messagerie</h2>
            <p class="text-sm text-blue-100 font-semibold">Messages de vos médecins</p>
          </div>
          <div class="group relative p-3 bg-white/20 backdrop-blur-sm rounded-2xl shadow-lg" title="Fonctionnalité bientôt disponible">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
        </div>
        
        <!-- Stats badges -->
        <div class="flex gap-3">
          <div class="flex-1 bg-white/20 backdrop-blur-sm rounded-xl px-4 py-2 border border-white/30">
            <p class="text-xs text-blue-100 font-semibold mb-0.5">Total</p>
            <p class="text-xl font-black text-white">{conversations.size}</p>
          </div>
          <div class="flex-1 bg-white/20 backdrop-blur-sm rounded-xl px-4 py-2 border border-white/30">
            <p class="text-xs text-blue-100 font-semibold mb-0.5">Non lus</p>
            <p class="text-xl font-black text-white">{conversationsArray().reduce((sum, c) => sum + c.unreadCount, 0)}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Conversations List -->
    <div class="flex-1 overflow-y-auto p-4 space-y-2">
      {#if loading}
        <div 
          class="flex flex-col items-center justify-center py-16"
          in:scale={{ duration: 400, easing: elasticOut }}
        >
          <div class="relative">
            <div class="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
            <div class="absolute inset-0 w-16 h-16 border-4 border-transparent border-b-indigo-600 rounded-full animate-spin animation-delay-150"></div>
          </div>
          <p class="mt-4 text-sm font-medium text-gray-600">Chargement des messages...</p>
        </div>
      {:else if conversations.size === 0}
        <div 
          class="relative overflow-hidden bg-gradient-to-br from-gray-50 to-blue-50 rounded-3xl p-12 text-center"
          in:scale={{ duration: 400, easing: elasticOut }}
        >
          <div class="absolute top-0 left-0 w-full h-full opacity-20">
            <div class="absolute top-5 left-5 w-16 h-16 bg-blue-400 rounded-full blur-xl animate-blob"></div>
            <div class="absolute top-10 right-5 w-20 h-20 bg-indigo-400 rounded-full blur-xl animate-blob animation-delay-2000"></div>
            <div class="absolute bottom-5 left-1/2 w-16 h-16 bg-purple-400 rounded-full blur-xl animate-blob animation-delay-4000"></div>
          </div>
          <div class="relative z-10">
            <div class="w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-xl">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <p class="text-lg font-medium text-gray-900 mb-2">Aucun message</p>
            <p class="text-sm text-gray-600">Commencez une nouvelle conversation</p>
          </div>
        </div>
      {:else}
        {#each conversationsArray() as conversation, i (conversation.userId)}
          <button
            class="group relative w-full text-left p-4 rounded-2xl transition-all duration-300 {selectedConversation === conversation.userId ? 'bg-gradient-to-r from-blue-500 to-indigo-500 shadow-lg scale-105' : 'bg-white/60 backdrop-blur-sm hover:bg-white/80 hover:shadow-md hover:scale-102'}"
            on:click={() => selectedConversation = conversation.userId}
            on:mouseenter={() => hoveredConversation = conversation.userId}
            on:mouseleave={() => hoveredConversation = null}
            in:fly={{ y: 20, duration: 400, delay: i * 50 }}
            animate:flip={{ duration: 400 }}
          >
            <!-- Glow effect -->
            {#if selectedConversation === conversation.userId}
              <div class="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl blur opacity-50"></div>
            {/if}
            
            <div class="relative z-10 flex items-start gap-3">
              <!-- Avatar -->
              <div class="relative flex-shrink-0">
                <div class={`w-14 h-14 rounded-2xl flex items-center justify-center font-black text-lg shadow-lg transform transition-transform duration-300 ${selectedConversation === conversation.userId ? 'bg-white text-blue-600 scale-110' : 'bg-gradient-to-br from-blue-400 to-indigo-500 text-white group-hover:scale-110'}`}>
                  {conversation.userName.charAt(0).toUpperCase()}
                </div>
                {#if conversation.unreadCount > 0}
                  <div 
                    class="absolute -top-1 -right-1 w-6 h-6 bg-gradient-to-r from-red-500 to-pink-500 rounded-full flex items-center justify-center border-2 border-white shadow-lg animate-pulse"
                    in:scale={{ duration: 400, easing: elasticOut }}
                  >
                    <span class="text-xs font-black text-white">{conversation.unreadCount}</span>
                  </div>
                {/if}
              </div>
              
              <!-- Content -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between mb-1">
                  <h3 class={`text-base font-black truncate ${selectedConversation === conversation.userId ? 'text-white' : 'text-gray-900'}`}>
                    {conversation.userName || `Praticien #${conversation.userId}`}
                  </h3>
                  <span class={`text-xs font-semibold ${selectedConversation === conversation.userId ? 'text-blue-100' : 'text-gray-500'}`}>
                    {formatTime(conversation.lastMessage.created_at).split(',')[0]}
                  </span>
                </div>
                <p class={`text-sm line-clamp-2 ${selectedConversation === conversation.userId ? 'text-blue-50' : 'text-gray-600'}`}>
                  {conversation.lastMessage.content}
                </p>
              </div>
            </div>
          </button>
        {/each}
      {/if}
    </div>
  </div>

  <!-- Messages Panel -->
  <div class="relative flex-1 flex flex-col bg-white/70 backdrop-blur-xl z-10">
    {#if error}
      <div 
        class="flex-1 flex items-center justify-center p-8"
        in:scale={{ duration: 400, easing: elasticOut }}
      >
        <div class="text-center">
          <div class="w-20 h-20 bg-gradient-to-br from-red-500 to-pink-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-xl">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p class="text-lg font-semibold text-red-600">{error}</p>
        </div>
      </div>
    {:else if !selectedConversation}
      <div 
        class="flex-1 flex items-center justify-center p-8"
        in:scale={{ duration: 400, easing: elasticOut }}
      >
        <div class="text-center relative">
          <!-- Animated background -->
          <div class="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-gradient-to-br from-blue-200 via-indigo-200 to-purple-200 rounded-full blur-3xl opacity-30 animate-pulse"></div>
          
          <div class="relative z-10">
            <div class="w-32 h-32 bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-2xl transform hover:rotate-6 transition-transform duration-500">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3 class="text-2xl font-black text-gray-900 mb-2">Sélectionnez une conversation</h3>
            <p class="text-base text-gray-600">Choisissez un contact pour voir vos messages</p>
          </div>
        </div>
      </div>
    {:else if activeConversation}
      <!-- Conversation Header -->
      <div class="relative overflow-hidden border-b border-gray-200/50">
        <div class="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-indigo-500/10 to-purple-500/10"></div>
        <div class="relative z-10 px-8 py-5 flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center font-black text-white text-lg shadow-lg">
              {activeConversation.userName.charAt(0).toUpperCase()}
            </div>
            <div>
              <h3 class="text-xl font-black text-gray-900">{activeConversation.userName || `Praticien #${activeConversation.userId}`}</h3>
              <p class="text-sm text-gray-600 font-semibold">
                {activeConversation.messages.length} message{activeConversation.messages.length > 1 ? 's' : ''}
              </p>
            </div>
          </div>
          
          <button
            on:click={() => loadMessages(true)}
            class="group p-3 bg-gradient-to-br from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 rounded-2xl transition-all duration-300 hover:scale-110 shadow-lg"
            title="Actualiser"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white transform group-hover:rotate-180 transition-transform duration-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Messages Area -->
      <div 
        bind:this={messagesContainer}
        class="flex-1 overflow-y-auto p-8 space-y-4"
        style="background: linear-gradient(180deg, rgba(249,250,251,0.5) 0%, rgba(243,244,246,0.8) 100%);"
      >
        {#each activeConversation.messages as message, i (message.id)}
          <div 
            class={`flex ${isSentByPatient(message) ? 'justify-end' : 'justify-start'}`}
            in:fly={{ y: 20, opacity: 0, duration: 400, delay: i * 30 }}
            animate:flip={{ duration: 400 }}
          >
            <div class="max-w-[75%] group">
              {#if message.subject}
                <div class={`mb-2 ${isSentByPatient(message) ? 'text-right' : 'text-left'}`}>
                  <span class="inline-block px-3 py-1 text-xs font-semibold uppercase tracking-wide bg-amber-100 text-amber-700 rounded-full border border-amber-300">
                    {message.subject}
                  </span>
                </div>
              {/if}
              
              <div class="relative">
                <!-- Glow effect -->
                {#if isSentByPatient(message)}
                  <div class="absolute -inset-1 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-3xl blur opacity-20 group-hover:opacity-40 transition-opacity duration-500"></div>
                {:else}
                  <div class="absolute -inset-1 bg-gradient-to-r from-gray-300 to-gray-400 rounded-3xl blur opacity-10 group-hover:opacity-20 transition-opacity duration-500"></div>
                {/if}
                
                <!-- Message bubble -->
                <div class={`relative rounded-3xl px-6 py-4 shadow-lg transform group-hover:scale-102 transition-all duration-300 ${
                  isSentByPatient(message) 
                    ? 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-br-md' 
                    : 'bg-white text-gray-900 rounded-bl-md border border-gray-200'
                }`}>
                  <p class="text-base leading-relaxed font-medium">{message.content}</p>
                  <div class={`flex items-center gap-2 mt-2 text-xs font-semibold ${isSentByPatient(message) ? 'text-blue-100' : 'text-gray-500'}`}>
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>{formatTime(message.created_at)}</span>
                    {#if isSentByPatient(message) && message.is_read}
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                      </svg>
                    {/if}
                  </div>
                </div>
              </div>
            </div>
          </div>
        {/each}
      </div>

      <!-- Message Input - Read Only Info -->
      <div class="relative border-t border-gray-200/50 p-6">
        <div class="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-indigo-500/5 to-purple-500/5"></div>
        <div class="relative z-10">
          <div class="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 rounded-2xl p-6 border-2 border-blue-200/50">
            <div class="flex items-start gap-4">
              <div class="flex-shrink-0">
                <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <div class="flex-1">
                <h4 class="text-lg font-black text-gray-900 mb-2">Mode lecture seule</h4>
                <p class="text-sm text-gray-700 leading-relaxed font-medium mb-3">
                  Pour des raisons de sécurité et de confidentialité médicale, seuls les praticiens peuvent initier et envoyer des messages. 
                  Vous pouvez consulter tous les messages que vos médecins vous envoient ici.
                </p>
                <div class="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-amber-100 to-yellow-100 border-2 border-amber-300 rounded-xl">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span class="text-sm font-bold text-amber-900">Réponse aux messages - Fonctionnalité bientôt disponible</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    {:else}
      <div 
        class="flex-1 flex items-center justify-center text-gray-500"
        in:scale={{ duration: 400 }}
      >
        <p class="text-lg font-semibold">Conversation introuvable</p>
      </div>
    {/if}
  </div>
</div>

<style>
  @keyframes blob {
    0%, 100% {
      transform: translate(0, 0) scale(1);
    }
    33% {
      transform: translate(30px, -50px) scale(1.1);
    }
    66% {
      transform: translate(-20px, 20px) scale(0.9);
    }
  }
  
  .animate-blob {
    animation: blob 7s infinite;
  }
  
  .animation-delay-2000 {
    animation-delay: 2s;
  }
  
  .animation-delay-4000 {
    animation-delay: 4s;
  }
  
  .animation-delay-150 {
    animation-delay: 150ms;
  }
  
  .line-clamp-1 {
    display: -webkit-box;
    -webkit-line-clamp: 1;
    line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  .scale-102 {
    transform: scale(1.02);
  }
  
  .hover\:scale-102:hover {
    transform: scale(1.02);
  }
</style>