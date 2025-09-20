<template>
    <div v-show="showCallPopup" v-bind="$attrs">
      <div ref="callPopup"
        class="fixed z-20 flex w-60 cursor-move select-none flex-col rounded-lg bg-surface-gray-7 p-4 text-ink-gray-2 shadow-2xl"
        :style="style">
        <div class="flex flex-row-reverse items-center gap-1">
          <MinimizeIcon class="h-4 w-4 cursor-pointer" @click="toggleCallWindow" />
        </div>
        <div class="flex flex-col items-center justify-center gap-3">
          <Avatar :image="contact?.image" :label="contact?.full_name ?? __('Unknown')"
            class="relative flex !h-24 !w-24 items-center justify-center [&>div]:text-[30px]"
            :class="onCall || calling ? '' : 'pulse'" />
          <div class="flex flex-col items-center justify-center gap-1">
            <div class="text-xl font-medium">
              {{ contact?.full_name ?? __('Unknown') }}
            </div>
            <div class="text-sm text-ink-gray-5">{{ contact?.mobile_no }}</div>
          </div>
          <CountUpTimer ref="counterUp">
            <div v-if="onCall" class="my-1 text-base">
              {{ counterUp?.updatedTime }}
            </div>
          </CountUpTimer>
          <div v-if="!onCall" class="my-1 text-base">
            {{
              callStatus == 'Setup'
                ? __('Initiating call...')
                : callStatus == 'Proceeding'
                  ? __('Ringing...')
                  : calling
                    ? __('Calling...')
                    : __('Incoming call...')
            }}
          </div>
          <div v-if="onCall" class="flex gap-2">
            <Button :icon="muted ? 'mic-off' : 'mic'" class="rounded-full" @click="toggleMute" />
            <Button
              class="rounded-full"
              :class="isRecording 
                ? 'bg-surface-red-5 hover:bg-surface-red-6' 
                : 'bg-white hover:bg-surface-gray-2 border border-surface-gray-4'"
              @click="toggleRecording"
            >
              <template #icon>
                <TheRecordIcon class="h-4 w-4" :is-recording="isRecording" />
              </template>
            </Button>
            <Button class="rounded-full">
              <template #icon>
                <NoteIcon class="h-4 w-4 cursor-pointer rounded-full text-ink-gray-9" @click="showNoteModal = true" />
              </template>
            </Button>
            <Button class="rounded-full bg-surface-red-5 hover:bg-surface-red-6">
              <template #icon>
                <PhoneIcon class="h-4 w-4 rotate-[135deg] fill-white text-ink-white" @click="endCall" />
              </template>
            </Button>
          </div>
          <div v-else-if="calling || callStatus == 'Setup'">
            <Button size="md" variant="solid" theme="red" :label="__('Cancel')" @click="endCall" class="rounded-lg"
              :disabled="callStatus == 'Setup'">
              <template #prefix>
                <PhoneIcon class="h-4 w-4 rotate-[135deg] fill-white" />
              </template>
            </Button>
          </div>
          <div v-else class="flex gap-2">
            <Button size="md" variant="solid" theme="green" :label="__('Accept')" class="rounded-lg"
              @click="acceptIncomingCall">
              <template #prefix>
                <PhoneIcon class="h-4 w-4 fill-white" />
              </template>
            </Button>
            <Button size="md" variant="solid" theme="red" :label="__('Reject')" class="rounded-lg"
              @click="rejectIncomingCall">
              <template #prefix>
                <PhoneIcon class="h-4 w-4 rotate-[135deg] fill-white" />
              </template>
            </Button>
          </div>
        </div>
      </div>
    </div>
    <div v-show="showSmallCallWindow"
      class="ml-2 flex cursor-pointer select-none items-center justify-between gap-3 rounded-lg bg-surface-gray-7 px-2 py-[7px] text-base text-ink-gray-2"
      @click="toggleCallWindow" v-bind="$attrs">
      <div class="flex items-center gap-2">
        <Avatar :image="contact?.image" :label="contact?.full_name ?? __('Unknown')"
          class="relative flex !h-5 !w-5 items-center justify-center" />
        <div class="max-w-[120px] truncate">
          {{ contact?.full_name ?? __('Unknown') }}
        </div>
      </div>
      <div v-if="onCall" class="flex items-center gap-2">
        <div class="my-1 min-w-[40px] text-center">
          {{ counterUp?.updatedTime }}
        </div>
        <Button variant="solid" theme="red" class="!h-6 !w-6 rounded-full">
          <template #icon>
            <PhoneIcon class="h-4 w-4 rotate-[135deg] fill-white" @click.stop="endCall" />
          </template>
        </Button>
      </div>
      <div v-else-if="calling" class="flex items-center gap-3">
        <div class="my-1">
          {{ callStatus == 'Proceeding' ? __('Ringing...') : __('Calling...') }}
        </div>
        <Button variant="solid" theme="red" class="!h-6 !w-6 rounded-full" @click.stop="endCall">
          <template #icon>
            <PhoneIcon class="h-4 w-4 rotate-[135deg] fill-white" />
          </template>
        </Button>
      </div>
      <div v-else class="flex items-center gap-2">
        <Button variant="solid" theme="green" class="pulse relative !h-6 !w-6 rounded-full"
          @click.stop="acceptIncomingCall">
          <template #icon>
            <PhoneIcon class="h-4 w-4 animate-pulse fill-white" />
          </template>
        </Button>
        <Button variant="solid" theme="red" class="!h-6 !w-6 rounded-full" @click.stop="rejectIncomingCall">
          <template #icon>
            <PhoneIcon class="h-4 w-4 rotate-[135deg] fill-white" />
          </template>
        </Button>
      </div>
    </div>
    <NoteModal v-model="showNoteModal" :note="note" doctype="CRM Call Log" @after="updateNote" />
    <!-- Hidden video elements for WebRTC streams -->
    <video id="remoteVideo" autoplay playsinline></video>
    <video id="localVideo" autoplay muted playsinline></video>
  </template>
  <script setup>
  import NoteIcon from '@/components/Icons/NoteIcon.vue'
  import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
  import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
  import CountUpTimer from '@/components/CountUpTimer.vue'
  import NoteModal from '@/components/Modals/NoteModal.vue'
  import TheRecordIcon from '@/components/Icons/TheRecordIcon.vue'
  import { useDraggable, useWindowSize } from '@vueuse/core'
  import { Avatar, call, createResource } from 'frappe-ui'
  import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
  import RingCentralWebPhone from 'ringcentral-web-phone'
  
  console.log('Imported RingCentralWebPhone:', RingCentralWebPhone)
  
  let webPhone = ref(null)
  let session = ref(null)
  let log = ref('Connecting...')
  let showCallPopup = ref(false)
  let showSmallCallWindow = ref(false)
  let onCall = ref(false)
  let calling = ref(false)
  let muted = ref(false)
  let callPopup = ref(null)
  let counterUp = ref(null)
  let callStatus = ref('')
  const telephonySessionId = ref(null)
  const phoneNumber = ref('')
  const isAuthenticated = ref(false)
  const callLogId = ref(null)
  const isRecording = ref(false)
  const rcCredentials = ref(null) // For token and server_url
  const contact = ref({
    full_name: '',
    image: '',
    mobile_no: '',
  })
  
  watch(phoneNumber, (value) => {
    if (!value) return
    getContact.fetch()
  })
  
  const getContact = createResource({
    url: 'crm.integrations.api.get_contact_by_phone_number',
    makeParams() {
      return {
        phone_number: phoneNumber.value
      }
    },
    onSuccess(data) {
      console.log('Raw API response:', data)
      console.log('Data type:', typeof data)
      console.log('Data keys:', Object.keys(data))
      contact.value = { ...data }
      console.log('Contact after assignment:', contact.value)
    },
    onError(error) {
      console.error('Contact API Error:', error)
    }
  })
  
  const checkAuthStatus = createResource({
    url: 'crm.integrations.ringcentral.api.check_auth_status',
    onSuccess(data) {
      isAuthenticated.value = data.is_authorized
      console.log('check_auth_status response:', data)
      if (data.is_authorized) {
        console.log('Authentication successful, starting client')
        startupClient()
      } else {
        console.log('Authentication failed, isAuthenticated: false')
      }
    },
    onError(error) {
      log.value = `Auth check failed: ${error}`
      console.error('Auth check error:', error)
      isAuthenticated.value = false
    },
  })
  
  const getAuthorizeUrl = createResource({
    url: 'crm.integrations.ringcentral.api.get_authorize_url',
    onSuccess(data) {
      window.open(data.authorize_url, '_blank')
    },
    onError(error) {
      log.value = `Failed to get authorization URL: ${error}`
      console.error(error)
    },
  })
  
  async function startOAuthFlow() {
    log.value = 'Starting OAuth flow...'
    getAuthorizeUrl.fetch()
  }
  
  function handleOAuthCallback(event) {
    if (event.origin !== window.location.origin) return
    if (event.data === 'OAuth flow completed. You can close this window.') {
      log.value = 'OAuth callback received, checking authentication...'
      checkAuthStatus.fetch()
    }
  }
  
  const showNoteModal = ref(false)
  const note = ref({
    name: '',
    title: '',
    content: '',
  })
  
  async function updateNote(_note, insert_mode = false) {
    note.value = _note
    if (insert_mode && _note.name && session.value) {
      await call('crm.integrations.api.add_note_to_call_log', {
        call_sid: session.value._callId,
        note: _note,
      })
    }
  }
  
  
  async function fetchTelephonySessionId(fromNumber, toNumber, token, server_url) {
    if (!token || !server_url) {
      console.warn('Missing token or server_url for fetchTelephonySessionId');
      return null;
    }
  
    try {
      const response = await fetch(`${server_url}/restapi/v1.0/account/~/extension/~/presence?detailedTelephonyState=true`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/json'
        }
      });
      
      const data = await response.json();
      console.log('Presence API response:', data);
      
      const activeCalls = data.activeCalls || [];
      console.log('Active calls details:', activeCalls);
  
      // Match by phone numbers (more reliable than session ID)
      const matchingCall = activeCalls.find(c => {
        const callFrom = c.from?.phoneNumber || c.from;
        const callTo = c.to?.phoneNumber || c.to;
        return (callFrom === fromNumber && callTo === toNumber) ||
               (callFrom === toNumber && callTo === fromNumber);
      });
  
      if (matchingCall && matchingCall.telephonySessionId) {
        telephonySessionId.value = matchingCall.telephonySessionId;
        console.log('Fetched telephonySessionId:', telephonySessionId.value);
        
        // Update call log with telephony session ID
        await call('crm.integrations.ringcentral.api.update_call_log', {
          call_sid: session.value._callId,
          custom_telephony_session_id: telephonySessionId.value
        }).catch(error => console.error('Failed to update call log with telephonySessionId:', error));
        
        return telephonySessionId.value;
      } else {
        console.warn('No matching active call found in presence API, falling back to call-log API');
        
        // Use phone number and time-based query instead of sessionId
        const startTime = new Date(Date.now() - 300000).toISOString(); // Last 5 minutes
        try {
          const callLogResponse = await fetch(
            `${server_url}/restapi/v1.0/account/~/extension/~/call-log?` +
            `dateFrom=${startTime}&phoneNumber=${fromNumber}&view=Detailed`,
            {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/json'
              }
            }
          );
          
          const callLogData = await callLogResponse.json();
          console.log('Call-log fallback response:', callLogData);
          
          // Find the most recent matching call
          const record = callLogData.records?.find(r => 
            (r.from?.phoneNumber === fromNumber && r.to?.phoneNumber === toNumber) ||
            (r.from?.phoneNumber === toNumber && r.to?.phoneNumber === fromNumber)
          );
          
          if (record && record.telephonySessionId) {
            telephonySessionId.value = record.telephonySessionId;
            console.log('Fetched telephonySessionId from call-log:', telephonySessionId.value);
            
            await call('crm.integrations.ringcentral.api.update_call_log', {
              call_sid: session.value._callId,
              custom_telephony_session_id: telephonySessionId.value
            }).catch(error => console.error('Failed to update call log with telephonySessionId:', error));
            
            return telephonySessionId.value;
          } else {
            console.warn('No matching call found in call-log either');
            return null;
          }
        } catch (fallbackError) {
          console.error('Call-log fallback also failed:', fallbackError);
          return null;
        }
      }
    } catch (error) {
      console.error('Failed to fetch telephony session ID:', error);
      return null;
    }
  }
  
  async function updateRecording(telephonySessionId, token, server_url, callSid) {
    if (!token || !server_url || !telephonySessionId) {
      console.warn('Missing token, server_url, or telephonySessionId for updateRecording');
      return null;
    }
  
    console.log('updateRecording called with callSid:', callSid, 'telephonySessionId:', telephonySessionId);
  
    const maxRetries = 2;
    const retryDelays = [12000, 15000, 20000]; // 30s, 60s, 120s
  
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        console.log(`Attempt ${attempt + 1}: Fetching recording for telephonySessionId: ${telephonySessionId}`);
        
        // Wait before querying (skip on first attempt)
        if (attempt > 0) {
          await new Promise(resolve => setTimeout(resolve, retryDelays[attempt - 1]));
        }
  
        // Query call log with telephonySessionId
        const response = await fetch(
          `${server_url}/restapi/v1.0/account/~/extension/~/call-log?` +
          `telephonySessionId=${telephonySessionId}&view=Detailed&withRecording=true`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Accept': 'application/json'
            }
          }
        );
  
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
  
        const data = await response.json();
        console.log('Call-log recording response:', JSON.stringify(data, null, 2));
  
        const record = data.records?.[0];
        if (record && record.recording) {
          console.log('Recording found:', record.recording);
          
          const custom_recording_id = record.recording.id;
          const recording_url = record.recording.contentUri; // Keep for logging only
          
          console.log('Recording ID:', custom_recording_id);
          console.log('Recording URL (for reference):', recording_url);
  
          // Update call log with recording information
          if (typeof call === 'function') {
            console.log('Calling update_recording_url with callSid:', callSid);
            const res = await call('crm.integrations.ringcentral.api.update_recording_url', {
              call_sid: callSid || session.value?._callId || callLogId.value,
              custom_recording_id: custom_recording_id,
              // Do NOT pass recording_url to let backend generate proxy URL
              custom_telephony_session_id: telephonySessionId
            });
  
            if (res.ok) {
              console.log('Recording URL updated successfully');
              return { custom_recording_id, recording_url: `/api/method/crm.integrations.ringcentral.api.get_recording_audio?custom_recording_id=${custom_recording_id}` };
            } else {
              console.error('Failed to update recording URL:', res.error);
              return null;
            }
          } else {
            console.warn('call function is not available for update_recording_url');
            return null;
          }
        } else {
          console.warn(`No recording found in call log for attempt ${attempt + 1}`);
        }
      } catch (error) {
        console.error(`Attempt ${attempt + 1} failed to fetch recording:`, error);
      }
  
      // Fallback query by from/to numbers if telephonySessionId fails
      if (attempt === maxRetries) {
        console.log('Falling back to query by phone numbers...');
        try {
          const fromNumber = rcCredentials.value?.from_number;
          const toNumber = phoneNumber.value ;
          if (!fromNumber || !toNumber) {
            console.error('Cannot query call-log: missing fromNumber or toNumber');
            return null;
          }
  
          const startTime = new Date(Date.now() - 600000).toISOString(); // Last 10 minutes
          const fallbackResponse = await fetch(
            `${server_url}/restapi/v1.0/account/~/extension/~/call-log?` +
            `dateFrom=${startTime}&from=${fromNumber}&to=${toNumber}&view=Detailed&withRecording=true`,
            {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/json'
              }
            }
          );
  
          if (!fallbackResponse.ok) {
            throw new Error(`HTTP ${fallbackResponse.status}: ${response.statusText}`);
          }
  
          const fallbackData = await fallbackResponse.json();
          console.log('Fallback call-log response:', JSON.stringify(fallbackData, null, 2));
  
          const record = fallbackData.records?.find(r =>
            (r.from?.phoneNumber === fromNumber && r.to?.phoneNumber === toNumber) ||
            (r.from?.phoneNumber === toNumber && r.to?.phoneNumber === fromNumber)
          );
  
          if (record && record.recording) {
            console.log('Recording found in fallback query:', record.recording);
            
            const custom_recording_id = record.recording.id;
            const recording_url = record.recording.contentUri; // Keep for logging only
  
            if (typeof call === 'function') {
              console.log('Calling update_recording_url with callSid:', callSid);
              const res = await call('crm.integrations.ringcentral.api.update_recording_url', {
                call_sid: callSid || session.value?._callId || callLogId.value,
                custom_recording_id: recustom_recording_idding_id,
                // Do NOT pass recording_url to let backend generate proxy URL
                custom_telephony_session_id: record.telephonySessionId || telephonySessionId
              });
  
              if (res.ok) {
                console.log('Recording URL updated successfully via fallback');
                return { custom_recording_id, recording_url: `/api/method/crm.integrations.ringcentral.api.get_recording_audio?custom_recording_id=${custom_recording_id}` };
              } else {
                console.error('Failed to update recording URL via fallback:', res.error);
                return null;
              }
            }
          } else {
            console.warn('No recording found in fallback query');
          }
        } catch (fallbackError) {
          console.error('Fallback query failed:', fallbackError);
        }
      }
    }  
  }
  
  async function stopRecording() {
    if (session.value && isRecording.value) {
      try {
        const response = await session.value.stopRecording()
        if (response?.result?.code === -6) {
          console.warn('Recording already stopped or in progress:', response)
        } else {
          isRecording.value = false
          log.value += ' Recording stopped.'
          console.log('Recording stopped manually for call:', session.value._callId)
        }
      } catch (error) {
        console.error('Failed to stop recording:', error)
        if (error.message.includes('The same operation in progress')) {
          console.warn('Recording stop ignored: operation in progress')
        } else {
          log.value += ` Failed to stop recording: ${error.message}`
        }
      }
    }
  }
  
  
  // async function endCall() {
  //   if (!session.value) {
  //     console.error('No active session to end');
  //     resetCallState();
  //     return;
  //   }
  
  //   try {
  //     console.log('Ending call with session:', session.value._callId);
      
  //     // Stop recording if active
  //     if (isRecording.value) {
  //       await stopRecording();
  //     }
  
  //     // Hang up the call
  //     if (typeof session.value.hangup === 'function') {
  //       await session.value.hangup();
  //     }
  
  //     // Wait a moment for the call to fully terminate
  //     await new Promise(resolve => setTimeout(resolve, 1000));
  
  //     // Update call log with final status
  //     const callSid = session.value._callId || callLogId.value;
  //     const duration = counterUp.value?.seconds || 0;
  //     const endTime = new Date().toISOString();
      
  //     await updateCallLog(
  //       onCall.value ? 'Completed' : 'Canceled',
  //       duration,
  //       endTime
  //     );
  
  //     // Schedule updateRecording with a 15-second delay (increased from 5s)
  //     console.log('Scheduling updateRecording for telephonySessionId:', telephonySessionId.value, 'callSid:', callSid);
  //     await new Promise((resolve, reject) => {
  //       setTimeout(async () => {
  //         try {
  //           const result = await updateRecording(telephonySessionId.value, rcCredentials.value.token, rcCredentials.value.server_url, callSid);
  //           if (result) {
  //             console.log('Recording successfully retrieved and updated:', result);
  //           } else {
  //             console.log('No recording found or failed to retrieve');
  //           }
  //           resolve();
  //         } catch (error) {
  //           console.error('Failed to fetch recording:', error);
  //           reject(error);
  //         }
  //       }, 15000);
  //     });
  
  //     // Reset call state after updateRecording completes
  //     resetCallState();
  //     log.value = 'Call ended successfully';
  
  //   } catch (error) {
  //     console.error('End call error:', error);
  //     log.value = `Failed to end call: ${error.message}`;
      
  //     // Try to update call log as failed
  //     try {
  //       await updateCallLog('Failed');
  //     } catch (e) {
  //       console.error('Also failed to update call log as failed:', e);
  //     }
      
  //     resetCallState();
  //   }
  // }
  
  async function endCall() {
    if (!session.value) {
      console.error('No active session to end');
      resetCallState();
      return;
    }
    try {
      console.log('Ending call with session:', session.value._callId);
  
      // Stop recording if active
      if (isRecording.value) {
        await stopRecording();
      }
  
      // Hang up the call
      if (typeof session.value.hangup === 'function') {
        await session.value.hangup();
      }
  
      // Wait a moment for the call to fully terminate
      await new Promise(resolve => setTimeout(resolve, 1000));
  
      // Capture call details before reset
      const callSid = session.value._callId || callLogId.value;
      const duration = counterUp.value?.seconds || 0;
      const endTime = new Date().toISOString();
      const wasConnected = onCall.value && callStatus.value === 'In Progress';
  
      // Update call log with final status
      await updateCallLog(
        wasConnected ? 'Completed' : 'Canceled',
        duration,
        endTime
      );
  
      // Reset state immediately so popup goes away
      resetCallState();
      log.value = 'Call ended successfully';
  
      // 🔄 Background recording fetch
      if (wasConnected && rcCredentials.value) {
        console.log(
          'Scheduling background updateRecording for telephonySessionId:',
          telephonySessionId.value,
          'callSid:',
          callSid
        );
  
        setTimeout(async () => {
          try {
            const result = await updateRecording(
              telephonySessionId.value,
              rcCredentials.value.token,
              rcCredentials.value.server_url,
              callSid
            );
            if (result) {
              console.log('Recording successfully retrieved and updated:', result);
            } else {
              console.log('No recording found or failed to retrieve');
            }
          } catch (error) {
            console.error('Failed to fetch recording in background:', error);
          }
        }, 5000); // Delay before attempting recording fetch
      } else {
        console.log('Skipping updateRecording (call not connected or credentials missing)');
      }
  
    } catch (error) {
      console.error('End call error:', error);
      log.value = `Failed to end call: ${error.message}`;
      try {
        await updateCallLog('Failed');
      } catch (e) {
        console.error('Also failed to update call log as failed:', e);
      }
      resetCallState();
    }
  }
  
  
  
  const { width, height } = useWindowSize()
  let { style } = useDraggable(callPopup, {
    initialValue: { x: width.value - 280, y: height.value - 310 },
    preventDefault: true,
  })
  
  async function startupClient() {
    if (!isAuthenticated.value) {
      log.value = 'Not authenticated, please authorize RingCentral'
      return
    }
    log.value = 'Requesting RingCentral credentials...'
    try {
      const data = await call('crm.integrations.ringcentral.api.get_webphone_credentials')
      console.log('Credentials:', data)
      if (!data.ok) {
        throw new Error(data.error || 'Failed to get credentials')
      }
      log.value = 'Got credentials, initializing WebPhone...'
      await initializeWebPhone(data)
      log.value = 'WebPhone initialized successfully!'
      rcCredentials.value = data // Store for token/server_url
      console.log('rcCredentials set:', rcCredentials.value)
    } catch (err) {
      log.value = `Credential error: ${err.message}`
      console.error('[v2] WebPhone startup failed:', err)
      isAuthenticated.value = false
    }
  }
  
  async function initializeWebPhone(credentials) {
    try {
      console.log('Credentials received:', credentials)
      if (!credentials.sipInfo) {
        throw new Error('Missing sipInfo in credentials')
      }
      const instanceId = credentials.token.endpoint_id || localStorage.getItem('ringcentralInstanceId') || crypto.randomUUID()
      if (!localStorage.getItem('ringcentralInstanceId')) {
        localStorage.setItem('ringcentralInstanceId', instanceId)
      }
      webPhone.value = new RingCentralWebPhone({
        sipInfo: credentials.sipInfo,
        instanceId: instanceId,
        debug: true,
        autoAnswer: false,
      })
      if (!webPhone.value) {
        throw new Error('WebPhone failed to initialize')
      }
      let attempts = 0
      const maxAttempts = 3
      while (attempts < maxAttempts) {
        try {
          await webPhone.value.start()
          break
        } catch (err) {
          attempts++
          if (err.message.includes('SIP/2.0 603 Too Many Contacts') && attempts < maxAttempts) {
            log.value = `Registration failed (Too Many Contacts), waiting ${attempts * 30} seconds before retry...`
            console.warn('Too Many Contacts, retrying...', err)
            await new Promise(resolve => setTimeout(resolve, attempts * 30000))
          } else {
            throw err
          }
        }
      }
      addWebPhoneListeners()
      log.value = 'WebPhone initialized and registered successfully!'
      console.log('WebPhone initialized:', webPhone.value)
    } catch (error) {
      log.value = `Failed to initialize WebPhone: ${error.message}`
      console.error('WebPhone initialization error:', error)
      webPhone.value = null
      if (error.message.includes('authentication') || error.message.includes('token')) {
        startOAuthFlow()
      }
    }
  }
  
  function toggleMute() {
    if (session.value) {
      if (muted.value) {
        session.value.unmute()
        muted.value = false
      } else {
        session.value.mute()
        muted.value = true
      }
    }
  }
  
  async function startRecording() {
    if (session.value && !isRecording.value) {
      try {
        const recordingResponse = await session.value.startRecording()
        isRecording.value = true
        log.value += ' Recording started.'
        console.log('Recording started manually for call:', session.value._callId)
        // Capture recordingId if provided by the SDK
        if (recordingResponse?.id) {
          console.log('Captured recordingId from startRecording:', recordingResponse.id);
          await call('crm.integrations.ringcentral.api.update_call_log', {
            call_sid: session.value._callId,
            custom_recording_id: recordingResponse.id
          })
          console.log('Stored recordingId:', recordingResponse.id)
        }
      } catch (error) {
        log.value += ` Failed to start recording: ${error.message}`
        console.error('Failed to start recording:', error)
      }
    }
  }
  
  function toggleRecording() {
    if (isRecording.value) {
      stopRecording()
    } else {
      startRecording()
    }
  }
  
  async function handleIncomingCall(incomingSession) {
    const fromNumber = incomingSession.remotePeer?.match(/sip:([^@>]+)/)?.[1] || 'Unknown';
    const toNumber = incomingSession.localPeer?.match(/sip:([^@>]+)/)?.[1] || 'Unknown';
    log.value = `Incoming call from ${fromNumber}`;
    phoneNumber.value = fromNumber;
    showCallPopup.value = true;
    session.value = incomingSession;
    console.log('Incoming call details:', {
      fromNumber,
      toNumber,
      session: incomingSession,
    });
  
    // Store callSid
    const callSid = incomingSession._callId;
  
    // Get credentials for token and server_url
    let credentials = rcCredentials.value;
    if (!credentials) {
      try {
        credentials = await call('crm.integrations.ringcentral.api.get_webphone_credentials');
        if (!credentials.ok) {
          throw new Error(credentials.error || 'Failed to get credentials');
        }
        rcCredentials.value = credentials; // Store credentials
      } catch (error) {
        console.error('Failed to get credentials:', error);
        log.value = `Failed to get credentials: ${error.message}`;
        return;
      }
    }
  
    // Create call log
    const call_details = {
      id: callSid,
      from: fromNumber,
      to: toNumber,
      type: 'Incoming',
      callStatus: 'Initiated',
      startTime: new Date().toISOString(),
    };
  
    try {
      console.log('Creating call log with details:', call_details);
      const callLogResponse = await call('crm.integrations.ringcentral.api.create_call_log', {
        call_details: call_details,
      });
      console.log('Incoming call log creation response:', callLogResponse);
      if (!callLogResponse.ok) {
        log.value = `Failed to create call log: ${callLogResponse.error}`;
        console.error('Failed to create call log:', callLogResponse.error);
      } else {
        callLogId.value = callLogResponse.call_sid;
        console.log('Call log created with ID:', callLogId.value);
      }
    } catch (error) {
      log.value = `Failed to create call log: ${error.message}`;
      console.error('Call log creation error:', error);
    }
  
    // Set up call end handler to update recording
    incomingSession.on('terminated', async () => {
      console.log('Call ended, scheduling updateRecording for callSid:', callSid);
      if (rcCredentials.value && callLogId.value) {
        try {
          const recordingResult = await updateRecording(
            telephonySessionId.value, // Use stored telephonySessionId
            rcCredentials.value.token,
            rcCredentials.value.server_url,
            callSid
          );
          console.log('Recording update result:', recordingResult);
          if (recordingResult) {
            log.value = 'Call ended successfully. Recording updated.';
          } else {
            log.value = 'Call ended successfully. No recording found or failed to retrieve.';
          }
        } catch (error) {
          console.error('Failed to update recording:', error);
          log.value = `Failed to update recording: ${error.message}`;
        }
      } else {
        console.warn('Missing credentials or callLogId for updateRecording');
        log.value = 'Call ended, but unable to update recording due to missing credentials or call log ID';
      }
      resetCallState();
    });
  }
  
  async function acceptIncomingCall() {
    if (session.value) {
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true }).catch((err) => {
          log.value = `Microphone permission denied: ${err.message}`;
          throw new Error(`Microphone permission denied: ${err.message}`);
        });
        await session.value.answer({
          media: {
            remote: document.getElementById('remoteVideo'),
            local: document.getElementById('localVideo'),
          },
        });
        log.value = 'Accepted incoming call.';
        onCall.value = true;
        callStatus.value = 'In Progress';
        if (counterUp.value) {
          counterUp.value.start();
        } else {
          console.error('CounterUp not initialized');
        }
  
        // Fetch telephonySessionId after call is answered
        if (rcCredentials.value) {
          try {
            telephonySessionId.value = await fetchTelephonySessionId(
              phoneNumber.value, // fromNumber
              rcCredentials.value.from_number, // toNumber
              rcCredentials.value.token,
              rcCredentials.value.server_url
            );
            console.log('Fetched telephonySessionId after accepting call:', telephonySessionId.value);
          } catch (error) {
            console.error('Failed to fetch telephonySessionId for incoming call:', error);
            telephonySessionId.value = null;
          }
        } else {
          console.warn('No credentials available to fetch telephonySessionId');
        }
  
        updateCallLog('In Progress');
      } catch (error) {
        log.value = `Failed to accept call: ${error.message}`;
        console.error('Accept call error:', error);
        updateCallLog('Failed');
        resetCallState();
      }
    } else {
      console.error('Invalid session object in acceptIncomingCall:', session.value);
      log.value = 'Failed to accept call: Session is invalid';
      updateCallLog('Failed');
      resetCallState();
    }
  }
  
  async function rejectIncomingCall() {
    if (session.value) {
      try {
        await session.value.decline();
        log.value = 'Rejected incoming call';
        updateCallLog('No Answer');
        resetCallState();
      } catch (error) {
        log.value = `Failed to reject call: ${error.message}`;
        console.error('Reject call error:', error);
        updateCallLog('Failed');
        resetCallState();
      }
    } else {
      console.error('Invalid session object in rejectIncomingCall:', session.value);
      log.value = 'Failed to reject call: Session is invalid';
      updateCallLog('Failed');
      resetCallState();
    }
  }
  
  async function updateCallLog(status, duration = 0, end_time = null) {
    if (!session.value || !session.value._callId) {
      console.error('Cannot update call log: session or callId missing');
      return false;
    }
  
    try {
      const updateData = {
        call_sid: session.value._callId,
        status: status,
        duration: duration,
        end_time: end_time || new Date().toISOString(),
      };
  
      if (telephonySessionId.value) {
        updateData.custom_telephony_session_id = telephonySessionId.value;
      }
  
      console.log('Updating call log with:', updateData);
      
      const response = await call('crm.integrations.ringcentral.api.update_call_log', updateData);
      
      console.log(`Call log updated with status: ${status}`, response);
      return true;
      
    } catch (error) {
      console.error('Failed to update call log:', error);
      log.value = `Failed to update call log: ${error.message}`;
      return false;
    }
  }
  
  function resetCallState() {
    console.log('resetCallState called', { session: session.value, counterUp: counterUp.value })
    showCallPopup.value = false
    showSmallCallWindow.value = false
    onCall.value = false
    calling.value = false
    isRecording.value = false
    callStatus.value = ''
    muted.value = false
    session.value = null
    callLogId.value = null
    if (counterUp.value) {
      counterUp.value.stop()
    }
    note.value = { name: '', title: '', content: '' }
  }
  
  function addWebPhoneListeners() {
    webPhone.value.on('inboundCall', (callSession) => {
      handleIncomingCall(callSession)
    })
    webPhone.value.on('connecting', () => {
      log.value = 'WebPhone connecting...'
    })
    webPhone.value.on('connected', () => {
      log.value = 'Ready to make and receive calls!'
    })
    webPhone.value.on('disconnected', () => {
      log.value = 'WebPhone disconnected'
    })
  }
  
  async function makeOutgoingCall(number) {
    console.log("Full session object:", session.value)
    console.log("INVITE headers:", session.value?.request?.headers)
    if (!webPhone.value) {
      log.value = 'WebPhone not initialized'
      console.error('WebPhone is not initialized')
      return
    }
    phoneNumber.value = number
    showCallPopup.value = true
    calling.value = true
    callStatus.value = 'Setup'
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true }).catch((err) => {
        log.value = `Microphone permission denied: ${err.message}`
        throw new Error(`Microphone permission denied: ${err.message}`)
      })
      const credentials = await call('crm.integrations.ringcentral.api.get_webphone_credentials')
      if (!credentials.ok) {
        throw new Error(credentials.error || 'Failed to get credentials')
      }
      const from_number = credentials.from_number
      console.log('Credentials received for call:', { from_number, number })
      log.value = `Attempting to call ${number}...`
      session.value = await webPhone.value.call(number, {
        fromNumber: from_number,
        media: {
          audio: true,
          remote: document.getElementById('remoteVideo'),
          local: document.getElementById('localVideo'),
        },
      })
      rcCredentials.value = credentials // Store for token/server_url
      // Fetch telephonySessionId in background (non-blocking)
      fetchTelephonySessionId(from_number, number, credentials.token, credentials.server_url).catch(error => {
        console.error('Failed to fetch telephonySessionId for outgoing call:', error)
      })
      const call_details = {
        id: session.value?._callId || `call-${Date.now()}`,
        from: from_number,
        to: number,
        type: 'Outgoing',
        callStatus: 'Initiated',
        startTime: new Date().toISOString(),
      }
      console.log('Creating call log with details:', call_details)
      console.log('Session callId:', session.value._callId)
      const callLogResponse = await call('crm.integrations.ringcentral.api.create_call_log', {
        call_details: call_details,
      })
      console.log('Full callLogResponse:', callLogResponse)
      if (!callLogResponse.ok) {
        log.value = `Failed to create call log: ${callLogResponse.error}`
        console.error('Failed to create call log:', callLogResponse.error)
      } else {
        callLogId.value = callLogResponse.call_sid
        console.log('Call log created with ID:', callLogId.value)
      }
      log.value = 'Call setup in progress...'
      onCall.value = true
      callStatus.value = 'In Progress'
      if (counterUp.value) {
        counterUp.value.start()
      } else {
        console.error('CounterUp not initialized')
      }
      updateCallLog('In Progress')
      // Fetch telephonySessionId in background after call is active
      fetchTelephonySessionId(from_number, number, credentials.token, credentials.server_url).catch(error => {
        console.error('Failed to fetch telephonySessionId for outgoing call:', error)
      })
    } catch (error) {
      log.value = `Could not make call: ${error.message}`
      console.error('Call error:', error)
      updateCallLog('Failed')
      resetCallState()
      showCallPopup.value = false
    }
  }
  
  function toggleCallWindow() {
    showCallPopup.value = !showCallPopup.value
    showSmallCallWindow.value = !showSmallCallWindow.value
  }
  
  onMounted(async () => {
    await checkAuthStatus.fetch()
    console.log('isAuthenticated after fetch:', isAuthenticated.value)
    window.addEventListener('message', handleOAuthCallback)
  })
  
  onBeforeUnmount(() => {
    window.removeEventListener('message', handleOAuthCallback)
    if (webPhone.value) {
      webPhone.value.stop()
    }
  })
  
  window.onbeforeunload = () => {
    if (webPhone.value) {
      webPhone.value.stop()
    }
  }
  
  watch(
    () => log.value,
    (value) => {
      console.log(value)
    },
    { immediate: true },
  )
  
  defineExpose({ makeOutgoingCall, setup: startupClient })
  </script>
  
  <style scoped>
  .pulse::before {
    content: '';
    position: absolute;
    border: 1px solid green;
    width: calc(100% + 20px);
    height: calc(100% + 20px);
    border-radius: 50%;
    animation: pulse 1s linear infinite;
  }
  
  .pulse::after {
    content: '';
    position: absolute;
    border: 1px solid green;
    width: calc(100% + 20px);
    height: calc(100% + 20px);
    border-radius: 50%;
    animation: pulse 1s linear infinite;
    animation-delay: 0.3s;
  }
  
  @keyframes pulse {
    0% {
      transform: scale(0.5);
      opacity: 0;
    }
  
    50% {
      transform: scale(1);
      opacity: 1;
    }
  
    100% {
      transform: scale(1.3);
      opacity: 0;
    }
  }
  
  #remoteVideo,
  #localVideo {
    display: none;
  }
  </style>