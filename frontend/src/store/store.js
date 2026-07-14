import { configureStore } from '@reduxjs/toolkit';
import interactionReducer from './slices/interactionSlice';
import hcpReducer from './slices/hcpSlice';
import chatReducer from './slices/chatSlice';

export const store = configureStore({
  reducer: {
    interactions: interactionReducer,
    hcps: hcpReducer,
    chat: chatReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});
