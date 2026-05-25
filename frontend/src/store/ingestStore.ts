import { create } from 'zustand';
import { IngestPreview, ChatMessage } from '../api/ingest';

interface SuccessData {
  loaded: number;
  families: string[];
  start: string;
  end: string;
}

interface IngestState {
  step: 'upload' | 'preview' | 'success';
  preview: IngestPreview | null;
  fileName: string;
  storeNbr: number;
  businessId: number | null;
  chatMessages: ChatMessage[];
  chatInput: string;
  salesUnit: 'CLP' | 'units' | null;
  successData: SuccessData | null;

  setStep: (step: IngestState['step']) => void;
  setPreview: (preview: IngestPreview | null) => void;
  setFileName: (fileName: string) => void;
  setStoreNbr: (storeNbr: number) => void;
  setBusinessId: (businessId: number | null) => void;
  setChatMessages: (messages: ChatMessage[]) => void;
  setChatInput: (input: string) => void;
  setSalesUnit: (unit: 'CLP' | 'units' | null) => void;
  setSuccessData: (data: SuccessData | null) => void;
  reset: () => void;
}

const initialState = {
  step: 'upload' as const,
  preview: null,
  fileName: '',
  storeNbr: 1,
  businessId: null as number | null,
  chatMessages: [],
  chatInput: '',
  salesUnit: null as null,
  successData: null,
};

export const useIngestStore = create<IngestState>()((set) => ({
  ...initialState,
  setStep: (step) => set({ step }),
  setPreview: (preview) => set({ preview }),
  setFileName: (fileName) => set({ fileName }),
  setStoreNbr: (storeNbr) => set({ storeNbr }),
  setBusinessId: (businessId) => set({ businessId }),
  setChatMessages: (chatMessages) => set({ chatMessages }),
  setChatInput: (chatInput) => set({ chatInput }),
  setSalesUnit: (salesUnit) => set({ salesUnit }),
  setSuccessData: (successData) => set({ successData }),
  reset: () => set(initialState),
}));
