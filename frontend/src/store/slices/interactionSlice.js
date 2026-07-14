import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { interactionAPI } from '../../services/api';

export const fetchInteractions = createAsyncThunk(
  'interactions/fetchAll',
  async (params, { rejectWithValue }) => {
    try {
      const response = await interactionAPI.getAll(params);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch interactions');
    }
  }
);

export const fetchInteractionById = createAsyncThunk(
  'interactions/fetchById',
  async (id, { rejectWithValue }) => {
    try {
      const response = await interactionAPI.getById(id);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch interaction');
    }
  }
);

export const createInteraction = createAsyncThunk(
  'interactions/create',
  async (data, { rejectWithValue }) => {
    try {
      const response = await interactionAPI.create(data);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to create interaction');
    }
  }
);

export const updateInteraction = createAsyncThunk(
  'interactions/update',
  async ({ id, data }, { rejectWithValue }) => {
    try {
      const response = await interactionAPI.update(id, data);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to update interaction');
    }
  }
);

export const deleteInteraction = createAsyncThunk(
  'interactions/delete',
  async (id, { rejectWithValue }) => {
    try {
      await interactionAPI.delete(id);
      return id;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to delete interaction');
    }
  }
);

export const processNotes = createAsyncThunk(
  'interactions/processNotes',
  async (notes, { rejectWithValue }) => {
    try {
      const response = await interactionAPI.processNotes(notes);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to process notes');
    }
  }
);

const interactionSlice = createSlice({
  name: 'interactions',
  initialState: {
    interactions: [],
    currentInteraction: null,
    loading: false,
    error: null,
    filters: {
      search: '',
      interactionType: '',
      sentiment: '',
      dateFrom: '',
      dateTo: '',
    },
    processedNotes: null,
    processingNotes: false,
    totalCount: 0,
    page: 1,
    pageSize: 20,
  },
  reducers: {
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {
        search: '',
        interactionType: '',
        sentiment: '',
        dateFrom: '',
        dateTo: '',
      };
    },
    clearError: (state) => {
      state.error = null;
    },
    setCurrentInteraction: (state, action) => {
      state.currentInteraction = action.payload;
    },
    clearProcessedNotes: (state) => {
      state.processedNotes = null;
    },
    setPage: (state, action) => {
      state.page = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // fetchInteractions
      .addCase(fetchInteractions.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.loading = false;
        if (Array.isArray(action.payload)) {
          state.interactions = action.payload;
          state.totalCount = action.payload.length;
        } else {
          state.interactions = action.payload.items || action.payload.interactions || [];
          state.totalCount = action.payload.total || state.interactions.length;
        }
      })
      .addCase(fetchInteractions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // fetchInteractionById
      .addCase(fetchInteractionById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchInteractionById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentInteraction = action.payload;
      })
      .addCase(fetchInteractionById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // createInteraction
      .addCase(createInteraction.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createInteraction.fulfilled, (state, action) => {
        state.loading = false;
        state.interactions.unshift(action.payload);
        state.totalCount += 1;
      })
      .addCase(createInteraction.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // updateInteraction
      .addCase(updateInteraction.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateInteraction.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.interactions.findIndex((i) => i.id === action.payload.id);
        if (index !== -1) {
          state.interactions[index] = action.payload;
        }
        if (state.currentInteraction?.id === action.payload.id) {
          state.currentInteraction = action.payload;
        }
      })
      .addCase(updateInteraction.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // deleteInteraction
      .addCase(deleteInteraction.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteInteraction.fulfilled, (state, action) => {
        state.loading = false;
        state.interactions = state.interactions.filter((i) => i.id !== action.payload);
        state.totalCount -= 1;
        if (state.currentInteraction?.id === action.payload) {
          state.currentInteraction = null;
        }
      })
      .addCase(deleteInteraction.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // processNotes
      .addCase(processNotes.pending, (state) => {
        state.processingNotes = true;
        state.error = null;
      })
      .addCase(processNotes.fulfilled, (state, action) => {
        state.processingNotes = false;
        state.processedNotes = action.payload;
      })
      .addCase(processNotes.rejected, (state, action) => {
        state.processingNotes = false;
        state.error = action.payload;
      });
  },
});

export const {
  setFilters,
  clearFilters,
  clearError,
  setCurrentInteraction,
  clearProcessedNotes,
  setPage,
} = interactionSlice.actions;

export default interactionSlice.reducer;
