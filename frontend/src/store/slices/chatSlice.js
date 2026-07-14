import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { agentAPI } from '../../services/api';

export const sendMessage = createAsyncThunk(
  'chat/sendMessage',
  async (message, { rejectWithValue }) => {
    try {
      const response = await agentAPI.chat(message);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to send message');
    }
  }
);

export const fetchAgentTools = createAsyncThunk(
  'chat/fetchAgentTools',
  async (_, { rejectWithValue }) => {
    try {
      const response = await agentAPI.getTools();
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch agent tools');
    }
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [],
    isTyping: false,
    agentTools: [],
    activeTools: [],
    error: null,
  },
  reducers: {
    addMessage: (state, action) => {
      state.messages.push(action.payload);
    },
    setTyping: (state, action) => {
      state.isTyping = action.payload;
    },
    clearMessages: (state) => {
      state.messages = [];
    },
    setActiveTools: (state, action) => {
      state.activeTools = action.payload;
    },
    clearActiveTools: (state) => {
      state.activeTools = [];
    },
    clearChatError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // sendMessage
      .addCase(sendMessage.pending, (state) => {
        state.isTyping = true;
        state.error = null;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.isTyping = false;
        const response = action.payload;
        if (response.tools_used && response.tools_used.length > 0) {
          state.activeTools = response.tools_used;
        }
        state.messages.push({
          id: Date.now(),
          role: 'assistant',
          content: response.response || response.message || response.content || JSON.stringify(response),
          tools: response.tools_used || [],
          timestamp: new Date().toISOString(),
        });
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.isTyping = false;
        state.error = action.payload;
        state.messages.push({
          id: Date.now(),
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your request. Please try again.',
          isError: true,
          timestamp: new Date().toISOString(),
        });
      })
      // fetchAgentTools
      .addCase(fetchAgentTools.pending, (state) => {
        state.error = null;
      })
      .addCase(fetchAgentTools.fulfilled, (state, action) => {
        state.agentTools = action.payload.tools || action.payload || [];
      })
      .addCase(fetchAgentTools.rejected, (state, action) => {
        state.error = action.payload;
      });
  },
});

export const {
  addMessage,
  setTyping,
  clearMessages,
  setActiveTools,
  clearActiveTools,
  clearChatError,
} = chatSlice.actions;

export default chatSlice.reducer;
