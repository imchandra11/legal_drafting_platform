import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../api/documentClient';

export const fetchTemplates = createAsyncThunk(
    'document/fetchTemplates',
    async () => {
        const response = await api.getTemplates();
        return response.data;
    }
);

export const saveDraft = createAsyncThunk(
    'document/saveDraft',
    async (draftData) => {
        const response = await api.saveDraft(draftData);
        return response.data;
    }
);

const documentSlice = createSlice({
    name: 'document',
    initialState: {
        templates: [],
        currentDraft: null,
        status: 'idle',
        error: null
    },
    reducers: {
        setCurrentDraft: (state, action) => {
            state.currentDraft = action.payload;
        }
    },
    extraReducers: (builder) => {
        builder
            .addCase(fetchTemplates.pending, (state) => {
                state.status = 'loading';
            })
            .addCase(fetchTemplates.fulfilled, (state, action) => {
                state.status = 'succeeded';
                state.templates = action.payload;
            })
            .addCase(saveDraft.fulfilled, (state, action) => {
                state.currentDraft = action.payload;
            })
    }
});

export const { setCurrentDraft } = documentSlice.actions;
export default documentSlice.reducer;