import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { hcpAPI } from '../../services/api';

export const fetchHCPs = createAsyncThunk(
  'hcps/fetchAll',
  async (params, { rejectWithValue }) => {
    try {
      const response = await hcpAPI.getAll(params);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch HCPs');
    }
  }
);

export const fetchHCPById = createAsyncThunk(
  'hcps/fetchById',
  async (id, { rejectWithValue }) => {
    try {
      const response = await hcpAPI.getById(id);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch HCP');
    }
  }
);

export const createHCP = createAsyncThunk(
  'hcps/create',
  async (data, { rejectWithValue }) => {
    try {
      const response = await hcpAPI.create(data);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to create HCP');
    }
  }
);

const hcpSlice = createSlice({
  name: 'hcps',
  initialState: {
    hcps: [],
    currentHcp: null,
    loading: false,
    error: null,
    filters: {
      search: '',
      specialty: '',
      tier: '',
    },
  },
  reducers: {
    setHcpFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearHcpError: (state) => {
      state.error = null;
    },
    setCurrentHcp: (state, action) => {
      state.currentHcp = action.payload;
    },
    clearCurrentHcp: (state) => {
      state.currentHcp = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // fetchHCPs
      .addCase(fetchHCPs.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchHCPs.fulfilled, (state, action) => {
        state.loading = false;
        if (Array.isArray(action.payload)) {
          state.hcps = action.payload;
        } else {
          state.hcps = action.payload.items || action.payload.hcps || [];
        }
      })
      .addCase(fetchHCPs.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // fetchHCPById
      .addCase(fetchHCPById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchHCPById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentHcp = action.payload;
      })
      .addCase(fetchHCPById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // createHCP
      .addCase(createHCP.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createHCP.fulfilled, (state, action) => {
        state.loading = false;
        state.hcps.unshift(action.payload);
      })
      .addCase(createHCP.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { setHcpFilters, clearHcpError, setCurrentHcp, clearCurrentHcp } = hcpSlice.actions;

export default hcpSlice.reducer;
