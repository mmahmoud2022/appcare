<script lang="ts">
  import { onMount, afterUpdate } from 'svelte';
  import { fade, fly, slide, scale } from 'svelte/transition';
  import { flip } from 'svelte/animate';
  import { cubicOut } from 'svelte/easing';
  import { 
    getCurrentDoctorProfile,
    getDoctorMessages,
    sendMessage,
    getMyPatients,
    type DoctorMessage,
    type PatientInfo
  } from '../../lib/api-doctor';
  
  let messages: DoctorMessage[] = [];
  let loading = true;
  let error: string | null = null;
  let selectedConversation: number | null = null;
  let newMessageText = '';
  let sending = false;
  let messagesContainer: HTMLDivElement;
  let searchQuery = '';
  let showNewMessageModal = false;
  let newPatientId = '';
  let newPatientName = '';
  let availablePatients: PatientInfo[] = [];
  let loadingPatients = false;
  let selectedPatientId: number | null = null;

  type Conversation = {
    userId: number;
    userName: string;
    messages: DoctorMessage[];
    lastMessage: DoctorMessage;
    unreadCount: number;
  };

  // Group messages by conversation (sender/receiver pair)
  let conversations: Map<number, Conversation> = new Map();
  let currentDoctorUserId: number | null = null;

  onMount(() => {
    void loadMessages();
    // Poll for new messages every 10 seconds
    const interval = window.setInterval(() => {
      void loadMessages();
    }, 10000);
    return () => clearInterval(interval);
  });

  afterUpdate(() => {
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  });

  const loadMessages = async () => {
    loading = messages.length === 0;
    error = null;
    try {
      const doctorId = await ensureDoctorId();
      const response = await getDoctorMessages(1, 100);
      messages = response.items || [];
      
      // Group messages by conversation
      const convMap = new Map<number, Conversation>();

      messages.forEach(msg => {
        const otherUserId = msg.sender_id === doctorId ? msg.recipient_id : msg.sender_id;
        const otherUserName = msg.sender_id === doctorId ? 
          formatFullName(msg.recipient_first_name, msg.recipient_last_name) : 
          formatFullName(msg.sender_first_name, msg.sender_last_name);

        const conversation = convMap.get(otherUserId) ?? {
          userId: otherUserId,
          userName: otherUserName,
          messages: [],
          lastMessage: msg,
          unreadCount: 0
        };

        conversation.messages.push(msg);

        if (new Date(msg.created_at).getTime() > new Date(conversation.lastMessage.created_at).getTime()) {
          conversation.lastMessage = msg;
        }

        if (!msg.is_read && msg.recipient_id === doctorId) {
          conversation.unreadCount += 1;
        }

        convMap.set(otherUserId, conversation);
      });
      
      // Sort messages within each conversation
      convMap.forEach(conv => {
        conv.messages.sort((a: DoctorMessage, b: DoctorMessage) => 
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        );
        conv.lastMessage = conv.messages[conv.messages.length - 1];
      });
      
      // Preserve selected conversation if it still exists
      const previousSelection = selectedConversation;
      
      conversations = convMap;
      
      if (convMap.size > 0) {
        // If we had a selection and it still exists, keep it
        if (previousSelection !== null && convMap.has(previousSelection)) {
          selectedConversation = previousSelection;
        } 
        // Otherwise select first conversation if we don't have a selection
        else if (selectedConversation === null) {
          const firstConversationId = convMap.keys().next().value as number | undefined;
          selectedConversation = firstConversationId ?? null;
        }
        // If selected conversation no longer exists, select first one
        else if (!convMap.has(selectedConversation)) {
          const firstConversationId = convMap.keys().next().value as number | undefined;
          selectedConversation = firstConversationId ?? null;
        }
      } else {
        selectedConversation = null;
      }
    } catch (err: any) {
      console.error('Error loading messages:', err);
      error = 'Erreur lors du chargement des messages';
    } finally {
      loading = false;
    }
  };

  const ensureDoctorId = async (): Promise<number> => {
    if (currentDoctorUserId !== null) {
      return currentDoctorUserId;
    }

    const profile = await getCurrentDoctorProfile();
    const doctorId = profile.user?.id;

    if (doctorId == null) {
      throw new Error('Identifiant utilisateur du médecin introuvable');
    }

    currentDoctorUserId = doctorId;
    return doctorId;
  };

  const isSentByDoctor = (message: DoctorMessage) => 
    currentDoctorUserId !== null && message.sender_id === currentDoctorUserId;

  const handleSendMessage = async () => {
    if (!newMessageText.trim() || !selectedConversation) return;
    
    sending = true;
    try {
      await sendMessage({
        recipient_id: selectedConversation,
        content: newMessageText.trim()
      });
      
      newMessageText = '';
      await loadMessages();
    } catch (err: any) {
      console.error('Error sending message:', err);
      alert('Erreur lors de l\'envoi du message');
    } finally {
      sending = false;
    }
  };

  const formatFullName = (first?: string | null, last?: string | null) => {
    const parts = [first, last].filter(Boolean) as string[];
    return parts.length ? parts.join(' ') : 'Utilisateur';
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit'
      });
    } else if (diffInHours < 48) {
      return 'Hier ' + date.toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit'
      });
    } else {
      return date.toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'short'
      });
    }
  };

  const selectConversation = (userId: number) => {
    selectedConversation = userId;
  };

  const getInitials = (name: string) => {
    return name.split(' ')
      .map(part => part[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const openNewMessageModal = async () => {
    showNewMessageModal = true;
    newPatientId = '';
    newPatientName = '';
    selectedPatientId = null;
    
    // Load patients list
    loadingPatients = true;
    try {
      const response = await getMyPatients(1, 100);
      availablePatients = response.items || [];
    } catch (err) {
      console.error('Error loading patients:', err);
      availablePatients = [];
    } finally {
      loadingPatients = false;
    }
  };

  const startNewConversation = () => {
    let patientId: number;
    let patientName: string;
    
    // Prioritize patient selection from list
    if (selectedPatientId !== null) {
      const patient = availablePatients.find(p => p.id === selectedPatientId);
      if (!patient) {
        alert('Patient non trouvé');
        return;
      }
      patientId = patient.id;
      patientName = `${patient.first_name} ${patient.last_name}`;
    } else if (newPatientId && newPatientName.trim()) {
      // Fallback to manual input only if no patient selected
      patientId = parseInt(newPatientId);
      if (isNaN(patientId)) {
        alert('ID patient invalide');
        return;
      }
      patientName = newPatientName.trim();
    } else {
      alert('Veuillez sélectionner un patient dans la liste');
      return;
    }

    // Check if conversation already exists
    if (!conversations.has(patientId)) {
      // Create a new conversation with a placeholder message
      const placeholderMessage: DoctorMessage = {
        id: -1, // Temporary ID
        sender_id: currentDoctorUserId || 0,
        recipient_id: patientId,
        sender_first_name: '',
        sender_last_name: '',
        recipient_first_name: patientName.split(' ')[0] || '',
        recipient_last_name: patientName.split(' ')[1] || '',
        subject: '',
        content: '',
        is_read: false,
        read_at: null,
        created_at: new Date().toISOString(),
        appointment_id: undefined
      };
      
      conversations.set(patientId, {
        userId: patientId,
        userName: patientName,
        messages: [],
        lastMessage: placeholderMessage,
        unreadCount: 0
      });
      conversations = conversations; // Trigger reactivity
    }
    
    // Select the conversation
    selectedConversation = patientId;
    showNewMessageModal = false;
    
    // Clear form
    newPatientId = '';
    newPatientName = '';
    selectedPatientId = null;
  };

  const closeNewMessageModal = () => {
    showNewMessageModal = false;
    newPatientId = '';
    newPatientName = '';
    selectedPatientId = null;
    availablePatients = [];
  };

  $: conversationsArray = Array.from(conversations.values())
    .filter(conv => {
      // Keep conversations that match search query
      if (searchQuery && !conv.userName.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      return true;
    })
    .sort((a, b) => {
      // Sort by last message date, or put new conversations (no messages yet) at top
      if (!a.lastMessage || a.lastMessage.id === -1) return -1;
      if (!b.lastMessage || b.lastMessage.id === -1) return 1;
      return new Date(b.lastMessage.created_at).getTime() - new Date(a.lastMessage.created_at).getTime();
    });

  $: selectedConversationData = selectedConversation ? conversations.get(selectedConversation) : null;
  $: totalUnread = Array.from(conversations.values()).reduce((sum, conv) => sum + conv.unreadCount, 0);
</script>


<!-- Modern Messaging Interface -->
<div class="space-y-6">
  <!-- Ultra Modern Header -->
  <div class="relative overflow-hidden bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 rounded-[2rem] shadow-2xl p-1">
    <div class="absolute inset-0 bg-grid-white/10 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))]"></div>
    <div class="absolute top-0 left-0 w-72 h-72 bg-white/20 rounded-full blur-3xl -ml-36 -mt-36 animate-blob"></div>
    <div class="absolute bottom-0 right-0 w-72 h-72 bg-pink-300/20 rounded-full blur-3xl -mr-36 -mb-36 animate-blob animation-delay-2000"></div>
    
    <div class="relative bg-white/10 backdrop-blur-2xl rounded-[1.75rem] p-8 border border-white/20">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-6">
          <div class="relative">
            <div class="w-20 h-20 bg-gradient-to-br from-white/40 to-white/20 rounded-3xl flex items-center justify-center backdrop-blur-sm border-2 border-white/30 shadow-2xl transform hover:rotate-12 transition-transform duration-500">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white drop-shadow-lg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            {#if totalUnread > 0}
              <div class="absolute -top-1 -right-1 w-7 h-7 bg-red-500 rounded-full flex items-center justify-center border-2 border-white shadow-lg animate-pulse" transition:scale={{ duration: 300 }}>
                <span class="text-xs font-black text-white">{totalUnread}</span>
              </div>
            {/if}
          </div>
          <div>
            <h2 class="text-4xl font-black text-white drop-shadow-lg mb-2 tracking-tight">Messagerie</h2>
            <p class="text-lg text-white/90 font-medium">Communication avec vos patients</p>
          </div>
        </div>
        <button
          on:click={loadMessages}
          class="group relative px-6 py-3 bg-white text-indigo-600 rounded-2xl hover:bg-white/90 transition-all shadow-2xl hover:shadow-3xl font-bold overflow-hidden transform hover:scale-105 active:scale-95"
          disabled={loading}
        >
          <div class="absolute inset-0 bg-gradient-to-r from-indigo-600/20 to-purple-600/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div class="relative flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="{loading ? 'animate-spin' : ''} h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Actualiser
          </div>
        </button>
      </div>
    </div>
  </div>

  <!-- Main Chat Interface -->
  <div class="flex h-[700px] bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border-2 border-gray-100 overflow-hidden">
    <!-- Conversations Sidebar -->
    <div class="w-96 border-r border-gray-200 flex flex-col bg-gradient-to-b from-gray-50 to-white">
      <!-- Search Bar -->
      <div class="p-6 border-b border-gray-200">
        <div class="relative mb-3">
          <input
            type="text"
            bind:value={searchQuery}
            placeholder="Rechercher une conversation..."
            class="w-full pl-12 pr-4 py-3 bg-white border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all font-medium text-gray-900 placeholder-gray-400"
          />
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        
        <!-- New Message Button -->
        <button
          on:click={openNewMessageModal}
          class="group w-full relative px-4 py-3 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white rounded-2xl hover:shadow-2xl transition-all font-bold overflow-hidden transform hover:scale-105 active:scale-95 shadow-xl"
        >
          <div class="absolute inset-0 bg-gradient-to-r from-white/20 to-white/0 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div class="relative flex items-center justify-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Nouveau message
          </div>
        </button>
      </div>
      
      <!-- Conversations List -->
      <div class="flex-1 overflow-y-auto">
        {#if loading}
          <div class="flex flex-col items-center justify-center py-24" transition:fade={{ duration: 300 }}>
            <div class="relative">
              <div class="w-20 h-20 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
              <div class="absolute inset-0 w-20 h-20 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin animation-delay-150" style="animation-direction: reverse;"></div>
            </div>
            <p class="mt-6 text-gray-600 font-medium">Chargement...</p>
          </div>
        {:else if conversationsArray.length === 0}
          <div class="text-center py-24 px-6" transition:scale={{ duration: 400, easing: cubicOut }}>
            <div class="w-24 h-24 bg-gradient-to-br from-gray-200 to-gray-300 rounded-full flex items-center justify-center mx-auto mb-6 shadow-xl">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h3 class="text-xl font-black text-gray-700 mb-2">Aucune conversation</h3>
            <p class="text-sm text-gray-500">{searchQuery ? 'Aucun résultat trouvé' : 'Vos conversations apparaîtront ici'}</p>
          </div>
        {:else}
          {#each conversationsArray as conversation, i (conversation.userId)}
            <button
              on:click={() => selectConversation(conversation.userId)}
              class="w-full p-5 hover:bg-indigo-50 transition-all border-b border-gray-100 text-left group relative overflow-hidden {selectedConversation === conversation.userId ? 'bg-gradient-to-r from-indigo-50 to-purple-50 border-l-4 border-l-indigo-600' : ''}"
              transition:fly={{ x: -20, duration: 400, delay: i * 50 }}
              animate:flip={{ duration: 400 }}
            >
              <!-- Selection indicator -->
              {#if selectedConversation === conversation.userId}
                <div class="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-indigo-600 to-purple-600" transition:slide={{ axis: 'x', duration: 300 }}></div>
              {/if}
              
              <div class="flex items-start gap-4">
                <!-- Avatar with initials -->
                <div class="relative flex-shrink-0">
                  <div class="w-14 h-14 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg transform group-hover:scale-110 group-hover:rotate-6 transition-all duration-300">
                    <span class="text-white font-black text-lg">{getInitials(conversation.userName)}</span>
                  </div>
                  {#if conversation.unreadCount > 0}
                    <div class="absolute -top-1 -right-1 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center border-2 border-white shadow-lg" transition:scale={{ duration: 200 }}>
                      <span class="text-xs font-black text-white">{conversation.unreadCount}</span>
                    </div>
                  {/if}
                </div>
                
                <!-- Conversation details -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between mb-2">
                    <h4 class="font-black text-gray-900 truncate text-base group-hover:text-indigo-600 transition-colors">
                      {conversation.userName}
                    </h4>
                    {#if conversation.lastMessage && conversation.lastMessage.id !== -1}
                      <p class="text-xs font-medium text-gray-500 ml-2 flex-shrink-0">
                        {formatTime(conversation.lastMessage.created_at)}
                      </p>
                    {/if}
                  </div>
                  {#if conversation.lastMessage && conversation.lastMessage.content}
                    <p class="text-sm text-gray-600 truncate leading-relaxed">
                      {#if isSentByDoctor(conversation.lastMessage)}
                        <span class="text-indigo-600 font-semibold">Vous: </span>
                      {/if}
                      {conversation.lastMessage.content}
                    </p>
                  {:else}
                    <p class="text-sm text-gray-400 italic">
                      Nouvelle conversation - Commencez à échanger
                    </p>
                  {/if}
                </div>
              </div>
            </button>
          {/each}
        {/if}
      </div>
    </div>

    <!-- Chat Area -->
    <div class="flex-1 flex flex-col bg-gradient-to-br from-gray-50 via-white to-indigo-50/30">
      {#if selectedConversationData}
        <!-- Chat Header -->
        <div class="p-6 border-b border-gray-200 bg-white/80 backdrop-blur-xl" transition:slide={{ duration: 300 }}>
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-xl transform hover:scale-110 hover:rotate-6 transition-all duration-300">
              <span class="text-white font-black text-lg">{getInitials(selectedConversationData.userName)}</span>
            </div>
            <div class="flex-1">
              <h3 class="font-black text-gray-900 text-xl">{selectedConversationData.userName}</h3>
              <div class="flex items-center gap-2 mt-1">
                <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <p class="text-sm text-gray-600 font-medium">
                  {selectedConversationData.messages.length} message{selectedConversationData.messages.length > 1 ? 's' : ''}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Messages -->
        <div 
          bind:this={messagesContainer}
          class="flex-1 overflow-y-auto p-6 space-y-4"
        >
          {#if selectedConversationData.messages.length === 0}
            <!-- Empty state for new conversations -->
            <div class="flex flex-col items-center justify-center h-full" transition:scale={{ duration: 400, easing: cubicOut }}>
              <div class="w-24 h-24 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-full flex items-center justify-center mb-6 shadow-xl">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 class="text-xl font-black text-gray-700 mb-2">Nouvelle conversation</h3>
              <p class="text-sm text-gray-500 text-center max-w-sm">
                Commencez à échanger avec {selectedConversationData.userName} en envoyant un message ci-dessous.
              </p>
            </div>
          {:else}
            {#each selectedConversationData.messages as message, i (message.id)}
              <div 
                class="flex {isSentByDoctor(message) ? 'justify-end' : 'justify-start'}"
                transition:fly={{ 
                  y: 20, 
                  duration: 400, 
                  delay: i * 50,
                  easing: cubicOut 
                }}
                animate:flip={{ duration: 400 }}
              >
                <div class="max-w-md lg:max-w-lg group">
                  <div class="relative {isSentByDoctor(message) ? 'ml-auto' : 'mr-auto'}">
                    <!-- Message bubble -->
                    <div class="relative rounded-3xl p-4 shadow-lg transform transition-all duration-300 hover:scale-105 {
                      isSentByDoctor(message) 
                        ? 'bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 text-white' 
                        : 'bg-white border-2 border-gray-200 text-gray-900'
                    }">
                      <!-- Glow effect -->
                      <div class="absolute -inset-1 bg-gradient-to-r {isSentByDoctor(message) ? 'from-indigo-600 to-purple-600' : 'from-gray-300 to-gray-400'} rounded-3xl blur opacity-0 group-hover:opacity-30 transition-opacity duration-300 -z-10"></div>
                      
                      <p class="text-sm leading-relaxed font-medium break-words">{message.content}</p>
                    </div>
                    
                    <!-- Timestamp and status -->
                    <div class="flex items-center gap-2 mt-2 {isSentByDoctor(message) ? 'justify-end' : 'justify-start'}">
                      <p class="text-xs font-medium {isSentByDoctor(message) ? 'text-gray-500' : 'text-gray-500'}">
                        {formatTime(message.created_at)}
                      </p>
                      {#if isSentByDoctor(message)}
                        <div class="flex items-center gap-1">
                          {#if message.is_read}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-indigo-600 -ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                          {:else}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                          {/if}
                        </div>
                      {/if}
                    </div>
                  </div>
                </div>
              </div>
            {/each}
          {/if}
        </div>

        <!-- Message Input -->
        <div class="p-6 border-t border-gray-200 bg-white/80 backdrop-blur-xl" transition:slide={{ duration: 300, axis: 'y' }}>
          <form on:submit|preventDefault={handleSendMessage} class="flex gap-3">
            <div class="flex-1 relative">
              <input
                type="text"
                bind:value={newMessageText}
                placeholder="Écrivez votre message..."
                class="w-full pl-5 pr-12 py-4 bg-white border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all font-medium text-gray-900 placeholder-gray-400 shadow-lg"
                disabled={sending}
              />
              <button
                type="button"
                aria-label="Ajouter un emoji"
                class="absolute right-3 top-1/2 -translate-y-1/2 p-2 hover:bg-gray-100 rounded-xl transition-colors"
                disabled={sending}
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
            </div>
            <button
              type="submit"
              class="group relative px-8 py-4 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white rounded-2xl hover:shadow-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed font-bold overflow-hidden transform hover:scale-105 active:scale-95 shadow-xl"
              disabled={sending || !newMessageText.trim()}
            >
              <div class="absolute inset-0 bg-gradient-to-r from-white/20 to-white/0 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div class="relative flex items-center gap-2">
                {#if sending}
                  <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Envoi...
                {:else}
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                  Envoyer
                {/if}
              </div>
            </button>
          </form>
        </div>
      {:else}
        <!-- Empty State -->
        <div class="flex-1 flex items-center justify-center" transition:fade={{ duration: 300 }}>
          <div class="text-center px-6" transition:scale={{ duration: 400, easing: cubicOut }}>
            <div class="relative mx-auto mb-8 w-32 h-32">
              <div class="absolute inset-0 bg-gradient-to-br from-indigo-200 to-purple-200 rounded-full blur-2xl opacity-50 animate-pulse"></div>
              <div class="relative w-full h-full bg-gradient-to-br from-indigo-100 to-purple-100 rounded-full flex items-center justify-center shadow-2xl">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
            </div>
            <h3 class="text-2xl font-black text-gray-900 mb-3">Sélectionnez une conversation</h3>
            <p class="text-gray-600 font-medium">Choisissez un patient pour commencer à discuter</p>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- New Message Modal -->
{#if showNewMessageModal}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div 
    class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    on:click={closeNewMessageModal}
    transition:fade={{ duration: 200 }}
  >
    <div 
      class="bg-white rounded-3xl shadow-2xl max-w-2xl w-full max-h-[600px] flex flex-col overflow-hidden"
      on:click|stopPropagation
      transition:scale={{ duration: 300, easing: cubicOut }}
    >
      <!-- Modal Header -->
      <div class="relative overflow-hidden bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 p-6">
        <div class="absolute inset-0 bg-grid-white/10"></div>
        <div class="relative flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 bg-white/20 backdrop-blur-xl rounded-2xl flex items-center justify-center border-2 border-white/30 shadow-xl">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
            </div>
            <div>
              <h3 class="text-2xl font-black text-white">Nouveau message</h3>
              <p class="text-white/80 font-medium">Sélectionnez un patient</p>
            </div>
          </div>
          <button
            on:click={closeNewMessageModal}
            aria-label="Fermer"
            class="group w-10 h-10 bg-white/20 hover:bg-white/30 backdrop-blur-xl rounded-xl flex items-center justify-center transition-all border-2 border-white/30 hover:scale-110 active:scale-95"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Modal Content -->
      <div class="flex-1 overflow-y-auto p-8">
        {#if loadingPatients}
          <div class="flex flex-col items-center justify-center py-12">
            <div class="relative">
              <div class="w-16 h-16 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
            </div>
            <p class="mt-4 text-gray-600 font-medium">Chargement des patients...</p>
          </div>
        {:else if availablePatients.length > 0}
          <div class="space-y-4">
            <div>
              <h3 class="block text-sm font-bold text-gray-900 mb-3">
                Sélectionnez un patient
              </h3>
              <div class="space-y-2 max-h-96 overflow-y-auto">
                {#each availablePatients as patient}
                  <button
                    type="button"
                    class="w-full p-4 rounded-2xl border-2 transition-all text-left {
                      selectedPatientId === patient.id
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-gray-200 hover:border-indigo-300 bg-white hover:bg-gray-50'
                    }"
                    on:click={() => selectedPatientId = patient.id}
                  >
                    <div class="flex items-center gap-4">
                      <div class="w-12 h-12 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-xl flex items-center justify-center flex-shrink-0">
                        <span class="text-white font-black text-sm">{getInitials(`${patient.first_name} ${patient.last_name}`)}</span>
                      </div>
                      <div class="flex-1 min-w-0">
                        <h4 class="font-bold text-gray-900 truncate">
                          {patient.first_name} {patient.last_name}
                        </h4>
                        <p class="text-sm text-gray-600 truncate">{patient.email}</p>
                        {#if patient.phone}
                          <p class="text-sm text-gray-500">{patient.phone}</p>
                        {/if}
                      </div>
                      {#if selectedPatientId === patient.id}
                        <div class="flex-shrink-0">
                          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                          </svg>
                        </div>
                      {/if}
                    </div>
                  </button>
                {/each}
              </div>
            </div>

            <!-- Manual input fallback -->
            <div class="mt-6 pt-6 border-t border-gray-200">
              <p class="text-sm font-bold text-gray-900 mb-3">Ou saisir manuellement</p>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label for="patientId" class="block text-sm font-medium text-gray-700 mb-1">
                    ID du patient
                  </label>
                  <input
                    id="patientId"
                    type="number"
                    bind:value={newPatientId}
                    placeholder="Ex: 123"
                    class="w-full px-4 py-3 bg-white border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all font-medium text-gray-900 placeholder-gray-400"
                  />
                </div>
                <div>
                  <label for="patientName" class="block text-sm font-medium text-gray-700 mb-1">
                    Nom du patient
                  </label>
                  <input
                    id="patientName"
                    type="text"
                    bind:value={newPatientName}
                    placeholder="Ex: Jean Dupont"
                    class="w-full px-4 py-3 bg-white border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all font-medium text-gray-900 placeholder-gray-400"
                  />
                </div>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex gap-3 pt-4">
              <button
                type="button"
                on:click={closeNewMessageModal}
                class="flex-1 px-6 py-3 bg-gray-100 text-gray-700 rounded-2xl hover:bg-gray-200 transition-all font-bold"
              >
                Annuler
              </button>
              <button
                type="button"
                on:click={startNewConversation}
                class="flex-1 group relative px-6 py-3 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white rounded-2xl hover:shadow-2xl transition-all font-bold overflow-hidden transform hover:scale-105 active:scale-95 shadow-xl"
              >
                <div class="absolute inset-0 bg-gradient-to-r from-white/20 to-white/0 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="relative flex items-center justify-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  Démarrer la conversation
                </div>
              </button>
            </div>
          </div>
        {:else}
          <div class="text-center py-12">
            <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <p class="text-gray-600 font-medium mb-6">Aucun patient trouvé</p>
            
            <!-- Manual input fallback -->
            <div class="max-w-md mx-auto">
              <p class="text-sm font-bold text-gray-900 mb-3 text-left">Saisir manuellement</p>
              <form on:submit|preventDefault={startNewConversation} class="space-y-4">
                <div>
                  <label for="patientId-manual" class="block text-sm font-medium text-gray-700 mb-1 text-left">
                    ID du patient <span class="text-red-500">*</span>
                  </label>
                  <input
                    id="patientId-manual"
                    type="number"
                    bind:value={newPatientId}
                    placeholder="Ex: 123"
                    required
                    class="w-full px-4 py-3 bg-white border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all font-medium text-gray-900 placeholder-gray-400"
                  />
                </div>
                <div>
                  <label for="patientName-manual" class="block text-sm font-medium text-gray-700 mb-1 text-left">
                    Nom du patient <span class="text-red-500">*</span>
                  </label>
                  <input
                    id="patientName-manual"
                    type="text"
                    bind:value={newPatientName}
                    placeholder="Ex: Jean Dupont"
                    required
                    class="w-full px-4 py-3 bg-white border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all font-medium text-gray-900 placeholder-gray-400"
                  />
                </div>

                <!-- Action Buttons -->
                <div class="flex gap-3 pt-2">
                  <button
                    type="button"
                    on:click={closeNewMessageModal}
                    class="flex-1 px-6 py-3 bg-gray-100 text-gray-700 rounded-2xl hover:bg-gray-200 transition-all font-bold"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    class="flex-1 group relative px-6 py-3 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white rounded-2xl hover:shadow-2xl transition-all font-bold overflow-hidden transform hover:scale-105 active:scale-95 shadow-xl"
                  >
                    <div class="absolute inset-0 bg-gradient-to-r from-white/20 to-white/0 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <div class="relative flex items-center justify-center gap-2">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      Démarrer la conversation
                    </div>
                  </button>
                </div>
              </form>
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

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
  
  .animation-delay-150 {
    animation-delay: 150ms;
  }
  
  /* Scrollbar styling */
  :global(.overflow-y-auto::-webkit-scrollbar) {
    width: 8px;
  }
  
  :global(.overflow-y-auto::-webkit-scrollbar-track) {
    background: transparent;
  }
  
  :global(.overflow-y-auto::-webkit-scrollbar-thumb) {
    background: #d1d5db;
    border-radius: 4px;
  }
  
  :global(.overflow-y-auto::-webkit-scrollbar-thumb:hover) {
    background: #9ca3af;
  }
</style>
